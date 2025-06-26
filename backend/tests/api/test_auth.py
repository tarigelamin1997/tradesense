"""
Test authentication endpoints and functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.models.user import User
from backend.core.security import SecurityManager


class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_user_success(self, client, db_session):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePassword123"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["email"] == user_data["email"]

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.username == user_data["username"]

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "username": "anotheruser",
            "email": test_user.email,
            "password": "SecurePassword123"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    def test_login_success(self, client, test_user, test_user_data):
        """Test successful login"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == test_user.username

    def test_login_invalid_credentials(self, client, test_user_data):
        """Test login with invalid credentials"""
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/trades/")

        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/api/v1/trades/", headers=auth_headers)

        assert response.status_code == 200

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/trades/", headers=headers)

        assert response.status_code == 401

    def test_token_refresh(self, client, auth_headers):
        """Test token refresh functionality"""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_logout(self, client, auth_headers):
        """Test logout functionality"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"


class TestSecurityManager:
    """Test SecurityManager utility functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123"
        hashed = SecurityManager.hash_password(password)

        assert hashed != password
        assert SecurityManager.verify_password(password, hashed) is True
        assert SecurityManager.verify_password("wrongpassword", hashed) is False

    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        user_data = {
            "user_id": "123",
            "username": "testuser",
            "email": "test@example.com"
        }

        token = SecurityManager.create_access_token(user_data)
        assert token is not None

        decoded = SecurityManager.verify_token(token)
        assert decoded["user_id"] == user_data["user_id"]
        assert decoded["username"] == user_data["username"]

    def test_token_expiration(self):
        """Test token expiration"""
        user_data = {"user_id": "123", "username": "testuser"}

        with patch('backend.core.security.datetime') as mock_datetime:
            # Create token
            token = SecurityManager.create_access_token(user_data)

            # Simulate time passing beyond expiration
            import datetime
            mock_datetime.utcnow.return_value = datetime.datetime.utcnow() + datetime.timedelta(hours=25)

            # Verify token is invalid
            decoded = SecurityManager.verify_token(token)
            assert decoded is None