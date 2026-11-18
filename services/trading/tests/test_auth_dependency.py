"""Downstream auth: token goes in a header; 401 for bad tokens, 503 only when auth is down."""
import functools

import httpx
import pytest
from fastapi import FastAPI, Header

import main

REAL_CLIENT = httpx.AsyncClient


def _fake_auth(valid_token="good", require_header=True):
    app = FastAPI()
    seen = {}

    if require_header:
        @app.post("/auth/verify")
        async def verify(authorization: str = Header(None)):
            seen["authorization"] = authorization
            return {"valid": authorization == f"Bearer {valid_token}", "username": "alice"}
    else:  # pre-upgrade auth service: token only as query parameter
        @app.post("/auth/verify")
        async def verify(token: str):
            return {"valid": token == valid_token, "username": "alice"}

    return app, seen


@pytest.fixture
def use_auth(monkeypatch):
    def _use(app):
        monkeypatch.setattr(
            main.httpx, "AsyncClient",
            functools.partial(REAL_CLIENT, transport=httpx.ASGITransport(app=app), base_url="http://auth"),
        )
    return _use


def test_valid_token(client, use_auth):
    app, seen = _fake_auth()
    use_auth(app)
    assert client.get("/trades", headers={"Authorization": "Bearer good"}).status_code == 200
    assert seen["authorization"] == "Bearer good"


def test_invalid_token_is_401_not_503(client, use_auth):
    use_auth(_fake_auth()[0])
    assert client.get("/trades", headers={"Authorization": "Bearer bad"}).status_code == 401


def test_missing_header_is_401(client):
    assert client.get("/trades").status_code == 401


def test_falls_back_for_old_auth_service(client, use_auth):
    use_auth(_fake_auth(require_header=False)[0])
    assert client.get("/trades", headers={"Authorization": "Bearer good"}).status_code == 200


def test_auth_unreachable_is_503(client, monkeypatch):
    def down(request):
        raise httpx.ConnectError("auth down")
    monkeypatch.setattr(
        main.httpx, "AsyncClient",
        functools.partial(REAL_CLIENT, transport=httpx.MockTransport(down)),
    )
    assert client.get("/trades", headers={"Authorization": "Bearer good"}).status_code == 503
