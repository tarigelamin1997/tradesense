"""
Isolated authentication service tests that import models only when needed
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

def test_auth_service_import_isolated():
    """Test importing AuthService in isolation"""
    # Mock the database session first
    with patch('backend.core.db.session.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock the models to avoid SQLAlchemy registration
        with patch('backend.models.user.User') as mock_user_class:
            mock_user = Mock()
            mock_user_class.return_value = mock_user
            
            try:
                # Import the service only when needed
                from api.v1.auth.service import AuthService
                assert AuthService is not None
                print("✅ Successfully imported AuthService in isolation")
            except Exception as e:
                pytest.fail(f"Failed to import AuthService: {e}")

def test_auth_service_creation_isolated():
    """Test creating AuthService instance in isolation"""
    # Mock the database session
    with patch('backend.core.db.session.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock the models
        with patch('backend.models.user.User') as mock_user_class:
            mock_user = Mock()
            mock_user_class.return_value = mock_user
            
            # Import the service
            from api.v1.auth.service import AuthService
            service = AuthService(mock_db)
            
            assert service is not None
            assert hasattr(service, 'db')
            print("✅ Successfully created AuthService instance in isolation")

def test_auth_service_methods_isolated():
    """Test AuthService methods with mocked dependencies"""
    # Mock the database session
    with patch('backend.core.db.session.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock the models
        with patch('backend.models.user.User') as mock_user_class:
            mock_user = Mock()
            mock_user.id = "test-user-123"
            mock_user.email = "test@example.com"
            mock_user.username = "testuser"
            mock_user.hashed_password = "hashed_password"
            mock_user.is_active = True
            mock_user_class.return_value = mock_user
            
            # Import the service
            from api.v1.auth.service import AuthService
            service = AuthService(mock_db)
            
            # Test authentication method
            with patch.object(service, 'get_user_by_email') as mock_get_user, \
                 patch.object(service, 'verify_password') as mock_verify:
                
                mock_get_user.return_value = mock_user
                mock_verify.return_value = True
                
                result = service.authenticate_user("test@example.com", "correct_password")
                
                assert result == mock_user
                mock_verify.assert_called_once_with("correct_password", "hashed_password")
                print("✅ Authentication method test passed in isolation")

def test_auth_service_user_creation_isolated():
    """Test user creation with mocked dependencies in isolation"""
    # Mock the database session
    with patch('backend.core.db.session.get_db') as mock_get_db:
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock the models
        with patch('backend.models.user.User') as mock_user_class:
            mock_user = Mock()
            mock_user_class.return_value = mock_user
            
            # Import the service and schemas
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
                mock_new_user = Mock()
                mock_new_user.email = "new@example.com"
                mock_new_user.username = "newuser"
                mock_user_class.return_value = mock_new_user
                
                result = service.create_user(user_data)
                
                assert result.email == "new@example.com"
                assert result.username == "newuser"
                print("✅ User creation test passed in isolation") 