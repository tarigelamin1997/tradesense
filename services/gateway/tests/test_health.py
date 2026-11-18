"""Gateway health contract: aggregates downstream service health."""


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    # Downstream services are not running in CI, so "degraded" is expected there.
    assert data["status"] in ("healthy", "degraded")
    assert data["gateway"] == "healthy"
    assert isinstance(data["services"], dict)
    assert "timestamp" in data


def test_services_endpoint(client):
    assert client.get("/services").status_code == 200


def test_root_endpoint(client):
    data = client.get("/").json()
    assert data["status"] == "operational"
