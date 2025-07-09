"""
Direct authentication service tests that avoid the full import chain
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

def test_auth_service_direct_import():
    """Test importing AuthService directly without the full API chain"""
    # Mock the problematic imports
    with patch('backend.api.v1.users.router') as mock_users_router, \
         patch('backend.api.v1.trades') as mock_trades, \
         patch('backend.api.v1.notes.router') as mock_notes_router, \
         patch('backend.api.v1.strategies.router') as mock_strategies_router, \
         patch('backend.api.v1.tags.router') as mock_tags_router, \
         patch('backend.api.v1.emotions.router') as mock_emotions_router, \
         patch('backend.api.v1.portfolio.router') as mock_portfolio_router, \
         patch('backend.api.v1.auth.router') as mock_auth_router:
        
        try:
            # Import the service directly
            from backend.api.v1.auth.service import AuthService
            assert AuthService is not None
            print("✅ Successfully imported AuthService directly")
        except Exception as e:
            pytest.fail(f"Failed to import AuthService directly: {e}")

def test_auth_service_password_hashing_direct():
    """Test password hashing functionality directly"""
    # Mock the problematic imports
    with patch('backend.api.v1.users.router') as mock_users_router, \
         patch('backend.api.v1.trades') as mock_trades, \
         patch('backend.api.v1.notes.router') as mock_notes_router, \
         patch('backend.api.v1.strategies.router') as mock_strategies_router, \
         patch('backend.api.v1.tags.router') as mock_tags_router, \
         patch('backend.api.v1.emotions.router') as mock_emotions_router, \
         patch('backend.api.v1.portfolio.router') as mock_portfolio_router, \
         patch('backend.api.v1.auth.router') as mock_auth_router:
        
        try:
            # Import the service
            from backend.api.v1.auth.service import AuthService
            
            # Create service instance with mock db
            mock_db = Mock()
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

def test_auth_service_user_creation_direct():
    """Test user creation functionality directly"""
    # Mock the problematic imports
    with patch('backend.api.v1.users.router') as mock_users_router, \
         patch('backend.api.v1.trades') as mock_trades, \
         patch('backend.api.v1.notes.router') as mock_notes_router, \
         patch('backend.api.v1.strategies.router') as mock_strategies_router, \
         patch('backend.api.v1.tags.router') as mock_tags_router, \
         patch('backend.api.v1.emotions.router') as mock_emotions_router, \
         patch('backend.api.v1.portfolio.router') as mock_portfolio_router, \
         patch('backend.api.v1.auth.router') as mock_auth_router:
        
        try:
            # Import the service and schemas
            from backend.api.v1.auth.service import AuthService
            from backend.api.v1.auth.schemas import UserRegistration
            
            # Create service instance with mock db
            mock_db = Mock()
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
            
            # Mock the database operations
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # User doesn't exist
            mock_db.query.return_value = mock_query
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock the User model
            mock_user = Mock()
            mock_user.email = "new@example.com"
            mock_user.username = "newuser"
            
            with patch('backend.models.user.User', return_value=mock_user):
                result = service.create_user(user_data)
                
                assert result.email == "new@example.com"
                assert result.username == "newuser"
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                
                print("✅ User creation test passed")
                
        except Exception as e:
            pytest.fail(f"User creation test failed: {e}")

def test_auth_service_authentication_direct():
    """Test user authentication functionality directly"""
    # Mock the problematic imports
    with patch('backend.api.v1.users.router') as mock_users_router, \
         patch('backend.api.v1.trades') as mock_trades, \
         patch('backend.api.v1.notes.router') as mock_notes_router, \
         patch('backend.api.v1.strategies.router') as mock_strategies_router, \
         patch('backend.api.v1.tags.router') as mock_tags_router, \
         patch('backend.api.v1.emotions.router') as mock_emotions_router, \
         patch('backend.api.v1.portfolio.router') as mock_portfolio_router, \
         patch('backend.api.v1.auth.router') as mock_auth_router:
        
        try:
            # Import the service
            from backend.api.v1.auth.service import AuthService
            
            # Create service instance with mock db
            mock_db = Mock()
            service = AuthService(mock_db)
            
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
            
            # Mock the password verification
            with patch.object(service, 'verify_password', return_value=True):
                result = service.authenticate_user("test@example.com", "correct_password")
                
                assert result == mock_user
                service.verify_password.assert_called_once_with("correct_password", "hashed_password")
                
                print("✅ Authentication test passed")
                
        except Exception as e:
            pytest.fail(f"Authentication test failed: {e}")

def test_auth_service_user_lookup_direct():
    """Test user lookup functionality directly"""
    # Mock the problematic imports
    with patch('backend.api.v1.users.router') as mock_users_router, \
         patch('backend.api.v1.trades') as mock_trades, \
         patch('backend.api.v1.notes.router') as mock_notes_router, \
         patch('backend.api.v1.strategies.router') as mock_strategies_router, \
         patch('backend.api.v1.tags.router') as mock_tags_router, \
         patch('backend.api.v1.emotions.router') as mock_emotions_router, \
         patch('backend.api.v1.portfolio.router') as mock_portfolio_router, \
         patch('backend.api.v1.auth.router') as mock_auth_router:
        
        try:
            # Import the service
            from backend.api.v1.auth.service import AuthService
            
            # Create service instance with mock db
            mock_db = Mock()
            service = AuthService(mock_db)
            
            # Mock the User model
            mock_user = Mock()
            mock_user.email = "test@example.com"
            mock_user.username = "testuser"
            
            # Mock the database query
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_user
            mock_db.query.return_value = mock_query
            
            # Test email lookup
            result = service.get_user_by_email("test@example.com")
            assert result == mock_user
            
            # Test username lookup
            result = service.get_user_by_username("testuser")
            assert result == mock_user
            
            print("✅ User lookup test passed")
            
        except Exception as e:
            pytest.fail(f"User lookup test failed: {e}") 