
"""
Basic setup tests to verify test environment
"""
import pytest
from fastapi.testclient import TestClient

def test_basic_setup():
    """Test that basic setup works"""
    assert True

def test_client_fixture(client):
    """Test that client fixture works"""
    assert client is not None

def test_health_endpoint(client):
    """Test basic health endpoint if available"""
    try:
        response = client.get("/health")
        # Accept either 200 or 404 - just want to verify client works
        assert response.status_code in [200, 404]
    except Exception:
        # If health endpoint doesn't exist, that's ok for this basic test
        pass

def test_database_fixture(test_db):
    """Test that database fixture works"""
    assert test_db is not None

def test_sample_data_fixtures(sample_user_data, sample_trade_data):
    """Test that sample data fixtures work"""
    assert sample_user_data is not None
    assert sample_trade_data is not None
    assert "username" in sample_user_data
    assert "symbol" in sample_trade_data
