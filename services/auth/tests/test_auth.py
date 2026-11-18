"""Auth service: registration, login, token verification, removed debug route."""
import uuid


def _register_and_login(client):
    name = f"user{uuid.uuid4().hex[:8]}"
    r = client.post("/auth/register", json={
        "email": f"{name}@example.com", "username": name,
        "password": "Str0ngPassw0rd!", "full_name": "Test User",
    })
    assert r.status_code == 200, r.text
    r = client.post("/auth/token", data={"username": name, "password": "Str0ngPassw0rd!"})
    assert r.status_code == 200, r.text
    return name, r.json()["access_token"]


def test_health(client):
    assert client.get("/health").status_code == 200


def test_login_wrong_password(client):
    name, _ = _register_and_login(client)
    r = client.post("/auth/token", data={"username": name, "password": "wrong"})
    assert r.status_code == 401


def test_verify_token_in_header(client):
    name, token = _register_and_login(client)
    r = client.post("/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert r.json() == {"valid": True, "username": name}


def test_verify_query_param_still_accepted_during_rollout(client):
    name, token = _register_and_login(client)
    assert client.post("/auth/verify", params={"token": token}).json()["valid"] is True


def test_verify_rejects_bad_or_missing_token(client):
    assert client.post("/auth/verify", headers={"Authorization": "Bearer nope"}).json() == {"valid": False}
    assert client.post("/auth/verify").json() == {"valid": False}


def test_debug_user_lookup_removed(client):
    assert client.get("/auth/debug/check-user", params={"email": "x@example.com"}).status_code == 404
