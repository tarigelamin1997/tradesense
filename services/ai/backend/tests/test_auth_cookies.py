"""
Test httpOnly cookie authentication
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from core.db.session import get_db
from sqlalchemy.orm import Session
from models.user import User
from api.v1.auth.service import AuthService

client = TestClient(app)

@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    auth_service = AuthService(db)
    user_data = {
        "email": "cookie@test.com",
        "username": "cookieuser",
        "password": "TestPass123!"
    }
    
    # Check if user exists
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    if existing:
        return existing
    
    # Create user
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        hashed_password=auth_service.get_password_hash(user_data["password"]),
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_sets_httponly_cookie(test_user):
    """Test that login sets httpOnly cookie"""
    response = client.post("/api/v1/auth/login", json={
        "email": "cookie@test.com",
        "password": "TestPass123!"
    })
    
    assert response.status_code == 200
    
    # Check that cookie is set
    assert "auth-token" in response.cookies
    
    # Check response still contains token for backward compatibility
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "cookie@test.com"


def test_protected_endpoint_with_cookie(test_user):
    """Test accessing protected endpoint with cookie"""
    # Login first
    login_response = client.post("/api/v1/auth/login", json={
        "email": "cookie@test.com",
        "password": "TestPass123!"
    })
    
    assert login_response.status_code == 200
    
    # Access protected endpoint - cookies are automatically sent
    me_response = client.get("/api/v1/auth/me")
    
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == "cookie@test.com"


def test_protected_endpoint_with_bearer_token(test_user):
    """Test that bearer token still works for API compatibility"""
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": "cookie@test.com", 
        "password": "TestPass123!"
    })
    
    token = login_response.json()["access_token"]
    
    # Clear cookies to test header auth
    client.cookies.clear()
    
    # Access with Authorization header
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "cookie@test.com"


def test_logout_clears_cookie(test_user):
    """Test that logout clears the httpOnly cookie"""
    # Login
    login_response = client.post("/api/v1/auth/login", json={
        "email": "cookie@test.com",
        "password": "TestPass123!"
    })
    
    assert "auth-token" in login_response.cookies
    
    # Logout
    logout_response = client.post("/api/v1/auth/logout")
    
    assert logout_response.status_code == 200
    
    # Check cookie is cleared
    # The test client should show an empty cookie value
    assert logout_response.cookies.get("auth-token") == ""


def test_unauthorized_without_cookie_or_token():
    """Test that protected endpoints require authentication"""
    # Clear any cookies
    client.cookies.clear()
    
    # Try to access protected endpoint
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_cookie_preferred_over_header(test_user):
    """Test that cookie is preferred when both cookie and header are present"""
    # Create two users
    auth_service = AuthService(next(get_db()))
    
    # Login as first user (sets cookie)
    login1 = client.post("/api/v1/auth/login", json={
        "email": "cookie@test.com",
        "password": "TestPass123!"
    })
    
    cookie_token = login1.json()["access_token"]
    
    # Create a different token (in real scenario, this would be for a different user)
    # For this test, we'll just use an invalid token
    invalid_token = "invalid.token.here"
    
    # Access with both cookie and (invalid) header
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    # Should succeed because valid cookie is preferred
    assert response.status_code == 200
    assert response.json()["email"] == "cookie@test.com"