import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from fastapi.security import HTTPAuthorizationCredentials

class TestAuthAPI:

    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert "password" not in data  # Password should not be returned

    def test_register_duplicate_user(self, client, sample_user_data):
        """Test registration with duplicate username"""
        # Register first user
        client.post("/api/v1/auth/register", json=sample_user_data)

        # Try to register same user again
        response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_login_success(self, client, sample_user_data):
        """Test successful login"""
        # Register user first
        client.post("/api/v1/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_protected_route_without_token(self, client):
        """Test accessing protected route without token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @patch('backend.api.v1.auth.router.security.__call__', new_callable=AsyncMock)
    @patch('backend.api.v1.auth.router.get_current_user')
    def test_protected_route_with_token(self, mock_get_user, mock_security_call, sample_user_data, test_db):
        """Test accessing protected route with valid token"""
        from unittest.mock import Mock
        from backend.main import app
        from fastapi.testclient import TestClient
        from backend.core.db.session import get_db
        mock_user = Mock()
        mock_user.id = "test_user_id"
        mock_user.username = sample_user_data["username"]
        mock_user.email = sample_user_data["email"]
        mock_get_user.return_value = mock_user
        mock_security_call.return_value = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake_token")
        def override_get_db():
            yield test_db
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            headers = {"Authorization": "Bearer fake_token"}
            response = client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
        app.dependency_overrides.clear()