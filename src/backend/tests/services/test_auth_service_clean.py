"""
Authentication service tests with clean database session
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_auth_service_basic_functionality():
    """Test basic AuthService functionality with clean imports"""
    # Create a mock database session
    mock_db = Mock()
    
    # Mock the User model
    mock_user = Mock()
    mock_user.id = "test-user-123"
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    mock_user.hashed_password = "hashed_password"
    mock_user.is_active = True
    
    # Mock the database query
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_user
    mock_db.query.return_value = mock_query
    
    try:
        # Import the service directly without going through the full import chain
        from api.v1.auth.service import AuthService
        
        # Create service instance
        service = AuthService(mock_db)
        
        # Test basic functionality
        assert service is not None
        assert hasattr(service, 'db')
        assert hasattr(service, 'authenticate_user')
        assert hasattr(service, 'create_user')
        assert hasattr(service, 'get_user_by_email')
        assert hasattr(service, 'get_user_by_username')
        
        print("✅ AuthService basic functionality test passed")
        
    except Exception as e:
        pytest.fail(f"AuthService test failed: {e}")

def test_auth_service_password_hashing():
    """Test password hashing functionality"""
    # Create a mock database session
    mock_db = Mock()
    
    try:
        # Import the service
        from api.v1.auth.service import AuthService
        
        # Create service instance
        service = AuthService(mock_db)
        
        # Test password hashing
        password = "test_password"
        hashed = service.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > len(password)
        assert service.verify_password(password, hashed) == True
        assert service.verify_password("wrong_password", hashed) == False
        
        print("✅ Password hashing test passed")
        
    except Exception as e:
        pytest.fail(f"Password hashing test failed: {e}")

def test_auth_service_user_creation():
    """Test user creation functionality"""
    # Create a mock database session
    mock_db = Mock()
    
    # Mock the User model
    mock_user = Mock()
    mock_user.email = "new@example.com"
    mock_user.username = "newuser"
    
    # Mock the database query and add operations
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None  # User doesn't exist
    mock_db.query.return_value = mock_query
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    try:
        # Import the service and schemas
        from api.v1.auth.service import AuthService
        from api.v1.auth.schemas import UserRegistration
        
        # Create service instance
        service = AuthService(mock_db)
        
        # Create user data
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
        
        # Mock the User model creation
        with patch('backend.models.user.User', return_value=mock_user):
            # Mock the password hashing
            with patch.object(service, 'get_password_hash', return_value="hashed_password"):
                result = service.create_user(user_data)
                
                assert result.email == "new@example.com"
                assert result.username == "newuser"
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                
                print("✅ User creation test passed")
                
    except Exception as e:
        pytest.fail(f"User creation test failed: {e}")

def test_auth_service_authentication():
    """Test user authentication functionality"""
    # Create a mock database session
    mock_db = Mock()
    
    # Mock the User model
    mock_user = Mock()
    mock_user.id = "test-user-123"
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    mock_user.hashed_password = "hashed_password"
    mock_user.is_active = True
    
    # Mock the database query
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_user
    mock_db.query.return_value = mock_query
    
    try:
        # Import the service
        from api.v1.auth.service import AuthService
        
        # Create service instance
        service = AuthService(mock_db)
        
        # Mock the password verification
        with patch.object(service, 'verify_password', return_value=True):
            result = service.authenticate_user("test@example.com", "correct_password")
            
            assert result == mock_user
            service.verify_password.assert_called_once_with("correct_password", "hashed_password")
            
            print("✅ Authentication test passed")
            
    except Exception as e:
        pytest.fail(f"Authentication test failed: {e}")

def test_auth_service_user_lookup():
    """Test user lookup functionality"""
    # Create a mock database session
    mock_db = Mock()
    
    # Mock the User model
    mock_user = Mock()
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    
    # Mock the database query
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_user
    mock_db.query.return_value = mock_query
    
    try:
        # Import the service
        from api.v1.auth.service import AuthService
        
        # Create service instance
        service = AuthService(mock_db)
        
        # Test email lookup
        result = service.get_user_by_email("test@example.com")
        assert result == mock_user
        
        # Test username lookup
        result = service.get_user_by_username("testuser")
        assert result == mock_user
        
        print("✅ User lookup test passed")
        
    except Exception as e:
        pytest.fail(f"User lookup test failed: {e}") 