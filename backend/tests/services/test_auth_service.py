
"""
Authentication service tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.api.v1.auth.service import AuthService
from backend.core.security import SecurityManager
from backend.core.exceptions import AuthenticationError, ValidationError


class TestAuthService:
    """Test AuthService business logic"""

    def test_create_user_success(self):
        """Test successful user creation"""
        service = AuthService()
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePassword123"
        }
        
        with patch.object(service, '_validate_user_data') as mock_validate, \
             patch.object(service, '_check_user_exists') as mock_check, \
             patch.object(service, '_hash_password') as mock_hash, \
             patch.object(service, '_save_user') as mock_save:
            
            mock_validate.return_value = True
            mock_check.return_value = False
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {"user_id": "new-user-123"}
            
            result = service.create_user(user_data)
            
            assert result["success"] is True
            assert "user_id" in result

    def test_create_user_duplicate_email(self):
        """Test user creation with duplicate email"""
        service = AuthService()
        user_data = {
            "username": "testuser",
            "email": "existing@example.com",
            "password": "SecurePassword123"
        }
        
        with patch.object(service, '_validate_user_data') as mock_validate, \
             patch.object(service, '_check_user_exists') as mock_check:
            
            mock_validate.return_value = True
            mock_check.return_value = True  # User exists
            
            result = service.create_user(user_data)
            
            assert result["success"] is False
            assert "already exists" in result["error"].lower()

    def test_create_user_validation_error(self):
        """Test user creation with validation errors"""
        service = AuthService()
        user_data = {
            "username": "",
            "email": "invalid-email",
            "password": "weak"
        }
        
        with patch.object(service, '_validate_user_data') as mock_validate:
            mock_validate.side_effect = ValidationError("Invalid user data")
            
            with pytest.raises(ValidationError):
                service.create_user(user_data)

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        service = AuthService()
        credentials = {
            "username": "testuser",
            "password": "correct_password"
        }
        
        mock_user = {
            "user_id": "test-123",
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "is_active": True
        }
        
        with patch.object(service, '_get_user_by_username') as mock_get_user, \
             patch.object(SecurityManager, 'verify_password') as mock_verify:
            
            mock_get_user.return_value = mock_user
            mock_verify.return_value = True
            
            result = service.authenticate_user(credentials["username"], credentials["password"])
            
            assert result is not None
            assert result["user_id"] == "test-123"
            assert result["username"] == "testuser"

    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password"""
        service = AuthService()
        
        mock_user = {
            "user_id": "test-123",
            "username": "testuser",
            "password_hash": "hashed_password",
            "is_active": True
        }
        
        with patch.object(service, '_get_user_by_username') as mock_get_user, \
             patch.object(SecurityManager, 'verify_password') as mock_verify:
            
            mock_get_user.return_value = mock_user
            mock_verify.return_value = False
            
            result = service.authenticate_user("testuser", "wrong_password")
            
            assert result is None

    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        service = AuthService()
        
        with patch.object(service, '_get_user_by_username') as mock_get_user:
            mock_get_user.return_value = None
            
            result = service.authenticate_user("nonexistent", "password")
            
            assert result is None

    def test_authenticate_user_inactive(self):
        """Test authentication with inactive user"""
        service = AuthService()
        
        mock_user = {
            "user_id": "test-123",
            "username": "testuser",
            "password_hash": "hashed_password",
            "is_active": False
        }
        
        with patch.object(service, '_get_user_by_username') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            result = service.authenticate_user("testuser", "password")
            
            assert result is None

    def test_refresh_user_token_success(self):
        """Test successful token refresh"""
        service = AuthService()
        current_user = {
            "user_id": "test-123",
            "username": "testuser",
            "email": "test@example.com"
        }
        
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(SecurityManager, 'create_access_token') as mock_create_token:
            
            mock_get_user.return_value = current_user
            mock_create_token.return_value = "new_access_token"
            
            result = service.refresh_user_token(current_user)
            
            assert result["access_token"] == "new_access_token"
            assert result["user"]["user_id"] == "test-123"

    def test_refresh_user_token_user_not_found(self):
        """Test token refresh when user no longer exists"""
        service = AuthService()
        current_user = {"user_id": "nonexistent-123"}
        
        with patch.object(service, '_get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(AuthenticationError):
                service.refresh_user_token(current_user)

    def test_get_user_by_id_success(self):
        """Test successful user retrieval by ID"""
        service = AuthService()
        user_id = "test-123"
        
        mock_user = {
            "user_id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": datetime.now()
        }
        
        with patch.object(service, '_get_user_by_id') as mock_get:
            mock_get.return_value = mock_user
            
            result = service.get_user_by_id(user_id)
            
            assert result["user_id"] == user_id
            assert result["username"] == "testuser"

    def test_get_user_by_id_not_found(self):
        """Test user retrieval when user doesn't exist"""
        service = AuthService()
        
        with patch.object(service, '_get_user_by_id') as mock_get:
            mock_get.return_value = None
            
            result = service.get_user_by_id("nonexistent")
            
            assert result is None

    def test_invalidate_token_success(self):
        """Test successful token invalidation"""
        service = AuthService()
        token = "valid_token"
        
        with patch.object(service, '_add_token_to_blacklist') as mock_blacklist:
            mock_blacklist.return_value = True
            
            result = service.invalidate_token(token)
            
            assert result["success"] is True

    def test_validate_user_data_success(self):
        """Test successful user data validation"""
        service = AuthService()
        valid_data = {
            "username": "validuser",
            "email": "valid@example.com",
            "password": "ValidPassword123"
        }
        
        # This should not raise any exceptions
        result = service._validate_user_data(valid_data)
        assert result is True

    def test_validate_user_data_invalid_email(self):
        """Test user data validation with invalid email"""
        service = AuthService()
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "ValidPassword123"
        }
        
        with pytest.raises(ValidationError):
            service._validate_user_data(invalid_data)

    def test_validate_user_data_weak_password(self):
        """Test user data validation with weak password"""
        service = AuthService()
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }
        
        with pytest.raises(ValidationError):
            service._validate_user_data(invalid_data)

    def test_password_strength_validation(self):
        """Test password strength validation"""
        service = AuthService()
        
        # Test weak passwords
        weak_passwords = [
            "short",
            "nouppercase123",
            "NOLOWERCASE123",
            "NoNumbers",
            "password"
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError):
                service._validate_password_strength(password)
        
        # Test strong password
        strong_password = "StrongPassword123"
        result = service._validate_password_strength(strong_password)
        assert result is True

    def test_email_validation(self):
        """Test email format validation"""
        service = AuthService()
        
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@domain.org"
        ]
        
        for email in valid_emails:
            assert service._validate_email_format(email) is True
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user.domain.com"
        ]
        
        for email in invalid_emails:
            assert service._validate_email_format(email) is False


class TestAuthServiceIntegration:
    """Integration tests for AuthService"""

    def test_user_registration_and_login_flow(self):
        """Test complete user registration and login flow"""
        service = AuthService()
        
        # Registration data
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "IntegrationTest123"
        }
        
        with patch.object(service, '_check_user_exists') as mock_check, \
             patch.object(service, '_save_user') as mock_save, \
             patch.object(service, '_get_user_by_username') as mock_get_user, \
             patch.object(SecurityManager, 'hash_password') as mock_hash, \
             patch.object(SecurityManager, 'verify_password') as mock_verify:
            
            # Setup mocks for registration
            mock_check.return_value = False
            mock_hash.return_value = "hashed_password"
            mock_save.return_value = {"user_id": "integration-123"}
            
            # Register user
            register_result = service.create_user(user_data)
            assert register_result["success"] is True
            
            # Setup mocks for login
            mock_user = {
                "user_id": "integration-123",
                "username": user_data["username"],
                "email": user_data["email"],
                "password_hash": "hashed_password",
                "is_active": True
            }
            mock_get_user.return_value = mock_user
            mock_verify.return_value = True
            
            # Login with same credentials
            login_result = service.authenticate_user(
                user_data["email"], 
                user_data["password"]
            )
            
            assert login_result is not None
            assert login_result["user_id"] == "integration-123"
            assert login_result["email"] == user_data["email"]

    def test_token_lifecycle(self):
        """Test token creation, validation, and invalidation"""
        service = AuthService()
        
        user_data = {
            "user_id": "token-test-123",
            "username": "tokenuser",
            "email": "token@example.com"
        }
        
        with patch.object(service, '_get_user_by_id') as mock_get_user, \
             patch.object(service, '_add_token_to_blacklist') as mock_blacklist:
            
            mock_get_user.return_value = user_data
            
            # Create token via refresh
            token_result = service.refresh_user_token(user_data)
            access_token = token_result["access_token"]
            
            # Token should be valid
            assert access_token is not None
            assert len(access_token) > 50
            
            # Invalidate token
            mock_blacklist.return_value = True
            invalidate_result = service.invalidate_token(access_token)
            
            assert invalidate_result["success"] is True
