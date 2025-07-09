"""
Authentication service tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.api.v1.auth.service import AuthService
from backend.core.security import SecurityManager
from backend.core.exceptions import AuthenticationError, ValidationError
from backend.api.v1.auth.schemas import UserRegistration, UserUpdate


class TestAuthService:
    """Test AuthService business logic"""

    def test_create_user_success(self, test_db):
        """Test successful user creation"""
        service = AuthService(test_db)
        user_data = UserRegistration(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123!",
            first_name="Test",
            last_name="User",
            trading_experience="intermediate",
            preferred_markets="stocks,forex",
            timezone="UTC"
        )
        
        with patch.object(service, 'get_user_by_email') as mock_get_email, \
             patch.object(service, 'get_user_by_username') as mock_get_username, \
             patch.object(service, 'get_password_hash') as mock_hash:
            
            mock_get_email.return_value = None
            mock_get_username.return_value = None
            mock_hash.return_value = "hashed_password"
            
            result = service.create_user(user_data)
            
            assert result.email == "test@example.com"
            assert result.username == "testuser"

    def test_create_user_duplicate_email(self, test_db):
        """Test user creation with duplicate email"""
        service = AuthService(test_db)
        user_data = UserRegistration(
            username="testuser",
            email="existing@example.com",
            password="SecurePassword123!",
            first_name="Test",
            last_name="User",
            trading_experience="intermediate",
            preferred_markets="stocks,forex",
            timezone="UTC"
        )
        
        with patch.object(service, 'get_user_by_email') as mock_get_email:
            mock_get_email.return_value = Mock()  # User exists
            
            with pytest.raises(ValidationError, match="User already exists"):
                service.create_user(user_data)

    def test_create_user_duplicate_username(self, test_db):
        """Test user creation with duplicate username"""
        service = AuthService(test_db)
        user_data = UserRegistration(
            username="existinguser",
            email="test@example.com",
            password="SecurePassword123!",
            first_name="Test",
            last_name="User",
            trading_experience="intermediate",
            preferred_markets="stocks,forex",
            timezone="UTC"
        )
        
        with patch.object(service, 'get_user_by_email') as mock_get_email, \
             patch.object(service, 'get_user_by_username') as mock_get_username:
            
            mock_get_email.return_value = None
            mock_get_username.return_value = Mock()  # Username exists
            
            with pytest.raises(ValidationError, match="User already exists"):
                service.create_user(user_data)

    def test_create_user_weak_password(self, test_db):
        """Test user creation with weak password"""
        service = AuthService(test_db)
        user_data = UserRegistration(
            username="testuser",
            email="test@example.com",
            password="weak",
            first_name="Test",
            last_name="User",
            trading_experience="intermediate",
            preferred_markets="stocks,forex",
            timezone="UTC"
        )
        
        with patch.object(service, 'get_user_by_email') as mock_get_email, \
             patch.object(service, 'get_user_by_username') as mock_get_username:
            
            mock_get_email.return_value = None
            mock_get_username.return_value = None
            
            with pytest.raises(ValidationError, match="Password must be at least 8 characters"):
                service.create_user(user_data)

    def test_authenticate_user_success(self, test_db):
        """Test successful user authentication"""
        service = AuthService(test_db)
        
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"
        mock_user.is_active = True
        
        with patch.object(service, 'get_user_by_email') as mock_get_user, \
             patch.object(service, 'verify_password') as mock_verify:
            
            mock_get_user.return_value = mock_user
            mock_verify.return_value = True
            
            result = service.authenticate_user("test@example.com", "correct_password")
            
            assert result == mock_user
            mock_verify.assert_called_once_with("correct_password", "hashed_password")

    def test_authenticate_user_invalid_password(self, test_db):
        """Test authentication with invalid password"""
        service = AuthService(test_db)
        
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"
        mock_user.is_active = True
        
        with patch.object(service, 'get_user_by_email') as mock_get_user, \
             patch.object(service, 'verify_password') as mock_verify:
            
            mock_get_user.return_value = mock_user
            mock_verify.return_value = False
            
            result = service.authenticate_user("test@example.com", "wrong_password")
            
            assert result is None

    def test_authenticate_user_not_found(self, test_db):
        """Test authentication with non-existent user"""
        service = AuthService(test_db)
        
        with patch.object(service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = None
            
            result = service.authenticate_user("nonexistent@example.com", "password")
            
            assert result is None

    def test_authenticate_user_inactive(self, test_db):
        """Test authentication with inactive user"""
        service = AuthService(test_db)
        
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"
        mock_user.is_active = False
        
        with patch.object(service, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            result = service.authenticate_user("test@example.com", "password")
            
            assert result is None

    def test_get_user_by_id_success(self, test_db):
        """Test successful user retrieval by ID"""
        service = AuthService(test_db)
        user_id = "test-123"
        
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        
        with patch.object(service, 'get_user_by_id') as mock_get:
            mock_get.return_value = mock_user
            
            result = service.get_user_by_id(user_id)
            
            assert result == mock_user
            mock_get.assert_called_once_with(user_id)

    def test_get_user_by_id_not_found(self, test_db):
        """Test user retrieval when user doesn't exist"""
        service = AuthService(test_db)
        user_id = "nonexistent-123"
        
        with patch.object(service, 'get_user_by_id') as mock_get:
            mock_get.return_value = None
            
            result = service.get_user_by_id(user_id)
            
            assert result is None
            mock_get.assert_called_once_with(user_id)

    def test_get_user_by_email_success(self, test_db):
        """Test successful user retrieval by email"""
        service = AuthService(test_db)
        email = "test@example.com"
        
        mock_user = Mock()
        mock_user.email = email
        mock_user.username = "testuser"
        
        with patch.object(service, 'get_user_by_email') as mock_get:
            mock_get.return_value = mock_user
            
            result = service.get_user_by_email(email)
            
            assert result == mock_user
            mock_get.assert_called_once_with(email)

    def test_get_user_by_username_success(self, test_db):
        """Test successful user retrieval by username"""
        service = AuthService(test_db)
        username = "testuser"
        
        mock_user = Mock()
        mock_user.username = username
        mock_user.email = "test@example.com"
        
        with patch.object(service, 'get_user_by_username') as mock_get:
            mock_get.return_value = mock_user
            
            result = service.get_user_by_username(username)
            
            assert result == mock_user
            mock_get.assert_called_once_with(username)

    def test_update_user_success(self, test_db):
        """Test successful user update"""
        service = AuthService(test_db)
        user_id = "test-123"
        
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "old@example.com"
        mock_user.username = "olduser"
        mock_user.first_name = "Old"
        mock_user.last_name = "Name"
        
        update_data = UserUpdate(
            email="new@example.com",
            first_name="New",
            last_name="Name"
        )
        
        with patch.object(service, 'get_user_by_id') as mock_get_user, \
             patch.object(service, 'get_user_by_email') as mock_get_email:
            
            mock_get_user.return_value = mock_user
            mock_get_email.return_value = None  # New email not taken
            
            result = service.update_user(user_id, update_data)
            
            assert result == mock_user
            assert mock_user.email == "new@example.com"
            assert mock_user.first_name == "New"
            assert mock_user.last_name == "Name"

    def test_update_user_not_found(self, test_db):
        """Test updating non-existent user"""
        service = AuthService(test_db)
        user_id = "nonexistent-123"
        
        update_data = UserUpdate(first_name="New")
        
        with patch.object(service, 'get_user_by_id') as mock_get_user:
            mock_get_user.return_value = None
            
            result = service.update_user(user_id, update_data)
            
            assert result is None

    def test_password_strength_validation(self, test_db):
        """Test password strength validation"""
        service = AuthService(test_db)
        
        # Test strong password
        strong_password = "StrongPassword123!"
        assert service._validate_password_strength(strong_password) is True
        
        # Test weak passwords
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecial123"  # No special characters
        ]
        
        for password in weak_passwords:
            assert service._validate_password_strength(password) is False

    def test_verify_password(self, test_db):
        """Test password verification"""
        service = AuthService(test_db)
        
        password = "testpassword123"
        hashed_password = service.get_password_hash(password)
        
        # Test correct password
        assert service.verify_password(password, hashed_password) is True
        
        # Test incorrect password
        assert service.verify_password("wrongpassword", hashed_password) is False

    def test_create_access_token(self, test_db):
        """Test JWT token creation"""
        service = AuthService(test_db)
        
        data = {"sub": "test-user-123", "username": "testuser"}
        
        token = service.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self, test_db):
        """Test JWT token verification"""
        service = AuthService(test_db)
        
        data = {"sub": "test-user-123", "username": "testuser"}
        token = service.create_access_token(data)
        
        # Test valid token
        user_id = service.verify_token(token)
        assert user_id == "test-user-123"
        
        # Test invalid token
        invalid_user_id = service.verify_token("invalid_token")
        assert invalid_user_id is None


class TestAuthServiceIntegration:
    """Integration tests for AuthService"""

    def test_user_registration_and_login_flow(self, test_db):
        """Test complete user registration and login flow"""
        service = AuthService(test_db)
        
        # Test user registration
        user_data = UserRegistration(
            username="integration_user",
            email="integration@example.com",
            password="SecurePassword123!",
            first_name="Integration",
            last_name="User",
            trading_experience="intermediate",
            preferred_markets="stocks,forex",
            timezone="UTC"
        )
        
        with patch.object(service, 'get_user_by_email') as mock_get_email, \
             patch.object(service, 'get_user_by_username') as mock_get_username, \
             patch.object(service, 'get_password_hash') as mock_hash:
            
            mock_get_email.return_value = None
            mock_get_username.return_value = None
            mock_hash.return_value = "hashed_password"
            
            created_user = service.create_user(user_data)
            assert created_user.email == "integration@example.com"
            
            # Test login
            mock_user = Mock()
            mock_user.email = "integration@example.com"
            mock_user.hashed_password = "hashed_password"
            mock_user.is_active = True
            
            with patch.object(service, 'verify_password') as mock_verify:
                mock_verify.return_value = True
                
                logged_in_user = service.authenticate_user("integration@example.com", "SecurePassword123!")
                assert logged_in_user == mock_user

    def test_token_lifecycle(self, test_db):
        """Test token creation and verification"""
        service = AuthService(test_db)
        
        # Test token creation
        user_data = {"sub": "token-test-123", "username": "tokenuser"}
        token = service.create_access_token(user_data)
        
        assert token is not None
        
        # Test token verification
        user_id = service.verify_token(token)
        assert user_id == "token-test-123"
        
        # Test invalid token
        invalid_user_id = service.verify_token("invalid_token")
        assert invalid_user_id is None
