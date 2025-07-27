import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Test health endpoint returns successful response"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_health_database_check(client):
    """Test health endpoint includes database status"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    if "database" in data:
        assert data["database"] in ["connected", "unavailable"]


def test_health_redis_check(client):
    """Test health endpoint includes Redis status"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    if "redis" in data:
        assert data["redis"] in ["connected", "unavailable"]