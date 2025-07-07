
import pytest
import requests
from datetime import datetime

BASE_URL = "http://0.0.0.0:8000"

def get_auth_token():
    """Helper function to get auth token"""
    timestamp = datetime.now().timestamp()
    username = f"journaltest_{timestamp}"
    email = f"journaltest_{timestamp}@example.com"
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
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    return response.json()["access_token"]

def test_create_journal_entry():
    """Test creating a journal entry"""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    entry_data = {
        "title": "Test Trade Reflection",
        "content": "This was a good trade because...",
        "tags": ["profitable", "patience"]
    }
    
    response = requests.post(f"{BASE_URL}/api/journal/entries", json=entry_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == entry_data["title"]
    assert "id" in data

def test_get_journal_entries():
    """Test retrieving journal entries"""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/journal/entries", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
