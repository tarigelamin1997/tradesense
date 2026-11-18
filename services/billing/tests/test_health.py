"""Health endpoint contract: always 200, status reports overall health."""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    # "degraded" is valid when an optional dependency (Stripe, Redis, OpenAI,
    # downstream services) is not configured, as in CI.
    assert data["status"] in ("healthy", "degraded")
    assert "timestamp" in data


def test_health_database_check(client):
    data = client.get("/health").json()
    if "database" in data:
        assert data["database"] in ("healthy", "unhealthy")


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
