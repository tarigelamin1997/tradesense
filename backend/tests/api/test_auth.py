
"""
Authentication API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json

from backend.core.security import SecurityManager


class TestAuthAPI:
    """Test authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePassword123"
        }
        
        with patch('backend.api.v1.auth.service.AuthService.create_user') as mock_create:
            mock_create.return_value = {
                "success": True,
                "user_id": "new-user-123",
                "message": "User created successfully"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "user_id" in data["data"]

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        user_data = {
            "username": "testuser",
            "email": "existing@example.com",
            "password": "SecurePassword123"
        }
        
        with patch('backend.api.v1.auth.service.AuthService.create_user') as mock_create:
            mock_create.return_value = {
                "success": False,
                "error": "Email already exists"
            }
            
            response = client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == 400

    def test_register_invalid_password(self, client):
        """Test registration with weak password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        with patch('backend.api.v1.auth.service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                "user_id": "test-user-123",
                "username": test_user_data["username"],
                "email": test_user_data["email"]
            }
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data["data"]
            assert data["data"]["token_type"] == "bearer"
            assert "user" in data["data"]

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        with patch('backend.api.v1.auth.service.AuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = None
            
            response = client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == 401

    def test_refresh_token_success(self, client, test_user_token):
        """Test successful token refresh"""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        
        with patch('backend.api.v1.auth.service.AuthService.refresh_user_token') as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new-token-here",
                "user": {
                    "user_id": "test-user-123",
                    "username": "testuser",
                    "email": "test@example.com"
                }
            }
            
            response = client.post("/api/v1/auth/refresh", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data["data"]

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        
        response = client.post("/api/v1/auth/refresh", headers=headers)
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        with patch('backend.api.v1.auth.service.AuthService.get_user_by_id') as mock_get_user:
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "username": "testuser",
                "email": "test@example.com",
                "created_at": "2024-01-01T00:00:00"
            }
            
            response = client.get("/api/v1/auth/me", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["username"] == "testuser"

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_logout_success(self, client, auth_headers):
        """Test successful logout"""
        with patch('backend.api.v1.auth.service.AuthService.invalidate_token') as mock_logout:
            mock_logout.return_value = {"success": True}
            
            response = client.post("/api/v1/auth/logout", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestAuthSecurity:
    """Test authentication security features"""

    def test_token_validation(self):
        """Test JWT token creation and validation"""
        token_data = {"user_id": "test-123", "username": "testuser"}
        
        # Create token
        token = SecurityManager.create_access_token(token_data)
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically longer
        
        # Validate token
        decoded = SecurityManager.verify_token(token)
        assert decoded["user_id"] == "test-123"
        assert decoded["username"] == "testuser"

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123"
        
        # Hash password
        hashed = SecurityManager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 chars
        
        # Verify password
        assert SecurityManager.verify_password(password, hashed) is True
        assert SecurityManager.verify_password("wrongpassword", hashed) is False

    def test_invalid_token_handling(self):
        """Test handling of invalid tokens"""
        with pytest.raises(Exception):  # Should raise AuthenticationError
            SecurityManager.verify_token("invalid.token.here")

    def test_expired_token_handling(self):
        """Test handling of expired tokens"""
        from datetime import timedelta
        
        # Create token with very short expiration
        token_data = {"user_id": "test-123"}
        token = SecurityManager.create_access_token(
            token_data, 
            expires_delta=timedelta(microseconds=1)
        )
        
        # Token should be expired immediately
        import time
        time.sleep(0.001)
        
        with pytest.raises(Exception):  # Should raise AuthenticationError
            SecurityManager.verify_token(token)


@pytest.mark.integration
class TestAuthIntegration:
    """Integration tests for auth flow"""

    def test_complete_auth_flow(self, client):
        """Test complete registration -> login -> protected access flow"""
        # 1. Register
        register_data = {
            "username": "flowtest",
            "email": "flowtest@example.com",
            "password": "FlowTest123"
        }
        
        with patch('backend.api.v1.auth.service.AuthService.create_user') as mock_create, \
             patch('backend.api.v1.auth.service.AuthService.authenticate_user') as mock_auth, \
             patch('backend.api.v1.auth.service.AuthService.get_user_by_id') as mock_get_user:
            
            # Mock registration
            mock_create.return_value = {
                "success": True,
                "user_id": "flow-test-123"
            }
            
            register_response = client.post("/api/v1/auth/register", json=register_data)
            assert register_response.status_code == 201
            
            # 2. Login
            login_data = {
                "username": register_data["email"],
                "password": register_data["password"]
            }
            
            mock_auth.return_value = {
                "user_id": "flow-test-123",
                "username": register_data["username"],
                "email": register_data["email"]
            }
            
            login_response = client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200
            
            token_data = login_response.json()
            access_token = token_data["data"]["access_token"]
            
            # 3. Access protected endpoint
            headers = {"Authorization": f"Bearer {access_token}"}
            
            mock_get_user.return_value = {
                "user_id": "flow-test-123",
                "username": register_data["username"],
                "email": register_data["email"]
            }
            
            me_response = client.get("/api/v1/auth/me", headers=headers)
            assert me_response.status_code == 200
            
            user_data = me_response.json()
            assert user_data["data"]["email"] == register_data["email"]
