"""
Simplified authentication service tests that mock database dependencies
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Mock the database session
mock_db = Mock()

# Mock the models
mock_user = Mock()
mock_user.id = "test-user-123"
mock_user.email = "test@example.com"
mock_user.username = "testuser"
mock_user.hashed_password = "hashed_password"
mock_user.is_active = True

def test_auth_service_import():
    """Test that we can import AuthService without database issues"""
    with patch('backend.models.user.User', mock_user):
        with patch('backend.core.db.session.get_db', return_value=mock_db):
            try:
                from api.v1.auth.service import AuthService
                assert AuthService is not None
                print("✅ Successfully imported AuthService")
            except Exception as e:
                pytest.fail(f"Failed to import AuthService: {e}")

def test_auth_service_creation():
    """Test creating AuthService instance"""
    with patch('backend.models.user.User', mock_user):
        with patch('backend.core.db.session.get_db', return_value=mock_db):
            from api.v1.auth.service import AuthService
            service = AuthService(mock_db)
            assert service is not None
            assert hasattr(service, 'db')
            print("✅ Successfully created AuthService instance")

def test_mock_authentication():
    """Test authentication with mocked dependencies"""
    with patch('backend.models.user.User', mock_user):
        with patch('backend.core.db.session.get_db', return_value=mock_db):
            from api.v1.auth.service import AuthService
            
            service = AuthService(mock_db)
            
            # Mock the get_user_by_email method
            with patch.object(service, 'get_user_by_email') as mock_get_user, \
                 patch.object(service, 'verify_password') as mock_verify:
                
                mock_get_user.return_value = mock_user
                mock_verify.return_value = True
                
                result = service.authenticate_user("test@example.com", "correct_password")
                
                assert result == mock_user
                mock_verify.assert_called_once_with("correct_password", "hashed_password")
                print("✅ Authentication test passed")

def test_mock_user_creation():
    """Test user creation with mocked dependencies"""
    with patch('backend.models.user.User', mock_user):
        with patch('backend.core.db.session.get_db', return_value=mock_db):
            from api.v1.auth.service import AuthService
            from api.v1.auth.schemas import UserRegistration
            
            service = AuthService(mock_db)
            
            user_data = UserRegistration(
                username="newuser",
                email="new@example.com",
                password="SecurePassword123!",
                first_name="New",
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
                
                # Mock the User model creation
                with patch('backend.models.user.User') as mock_user_class:
                    mock_new_user = Mock()
                    mock_new_user.email = "new@example.com"
                    mock_new_user.username = "newuser"
                    mock_user_class.return_value = mock_new_user
                    
                    result = service.create_user(user_data)
                    
                    assert result.email == "new@example.com"
                    assert result.username == "newuser"
                    print("✅ User creation test passed") 