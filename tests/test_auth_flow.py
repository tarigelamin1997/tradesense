
import pytest
import requests
import json
from datetime import datetime

BASE_URL = "http://0.0.0.0:8000"

def test_health_check():
    """Test that the API is running"""
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_user_registration():
    """Test user registration flow"""
    user_data = {
        "username": f"testuser_{datetime.now().timestamp()}",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_user_login():
    """Test user login flow"""
    # First register a user
    timestamp = datetime.now().timestamp()
    username = f"logintest_{timestamp}"
    email = f"logintest_{timestamp}@example.com"
    password = "testpassword123"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password
    }
    
    register_response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    assert register_response.status_code == 200
    
    # Now test login
    login_data = {
        "username": username,
        "password": password
    }
    
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route():
    """Test accessing protected route with token"""
    # Register and login first
    timestamp = datetime.now().timestamp()
    username = f"protectedtest_{timestamp}"
    email = f"protectedtest_{timestamp}@example.com"
    password = "testpassword123"
    
    # Register
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password
    }
    requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    
    # Login
    login_data = {"username": username, "password": password}
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Test protected route
    headers = {"Authorization": f"Bearer {token}"}
    dashboard_response = requests.get(f"{BASE_URL}/api/analytics/dashboard", headers=headers)
    assert dashboard_response.status_code == 200
    data = dashboard_response.json()
    assert "total_trades" in data
