
"""
Health endpoint tests
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_check_success(self, client):
        """Test basic health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_health_detailed(self, client):
        """Test detailed health check"""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "version" in data
        assert "uptime" in data

    def test_version_endpoint(self, client):
        """Test version endpoint"""
        response = client.get("/version")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data["data"]
        assert "build_time" in data["data"]
"""
Test health check endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test system health endpoints"""

    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_detailed(self, client):
        """Test detailed health check"""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_readiness_probe(self, client):
        """Test readiness probe for deployments"""
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
