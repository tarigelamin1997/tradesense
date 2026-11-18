"""Stripe webhooks are accepted only with a valid signature."""
import json
import time

import pytest
import stripe

import main

SECRET = "whsec_test_secret"
EVENT = {
    "id": "evt_test", "object": "event", "type": "checkout.session.completed",
    "data": {"object": {"customer": "cus_1", "subscription": "sub_1",
                        "metadata": {"username": "alice", "plan": "pro"}}},
}


def _signed(payload, secret=SECRET):
    ts = int(time.time())
    sig = stripe.WebhookSignature._compute_signature(f"{ts}.{payload}", secret)
    return {"Stripe-Signature": f"t={ts},v1={sig}"}


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setattr(main, "STRIPE_WEBHOOK_SECRET", SECRET)


def test_rejected_when_secret_not_configured(client, monkeypatch):
    monkeypatch.setattr(main, "STRIPE_WEBHOOK_SECRET", None)
    payload = json.dumps(EVENT)
    assert client.post("/billing/webhook", content=payload, headers=_signed(payload)).status_code == 503


def test_rejects_missing_signature(client, secret):
    assert client.post("/billing/webhook", content=json.dumps(EVENT)).status_code == 400


def test_rejects_wrong_signature(client, secret):
    payload = json.dumps(EVENT)
    headers = _signed(payload, secret="whsec_attacker")
    assert client.post("/billing/webhook", content=payload, headers=headers).status_code == 400


def test_accepts_valid_signature(client, secret):
    payload = json.dumps(EVENT)
    r = client.post("/billing/webhook", content=payload, headers=_signed(payload))
    assert r.status_code == 200
    assert r.json() == {"received": True}
