"""
Simple test to verify authentication endpoints work with httpOnly cookies
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test the authentication directly without full app import
def test_auth_endpoints_exist():
    """Basic test that auth router has the required endpoints"""
    try:
        from api.v1.auth.router import router
        # Check that router has login and logout endpoints
        routes = [route.path for route in router.routes]
        assert "/login" in routes
        assert "/logout" in routes
        assert "/me" in routes
        print("✅ Auth endpoints exist")
    except Exception as e:
        print(f"❌ Failed to import auth router: {e}")
        raise


def test_auth_service_exists():
    """Test that auth service can create tokens"""
    try:
        from api.v1.auth.service import AuthService
        from datetime import timedelta
        
        # Create a mock AuthService instance (None for db since we're not using it)
        auth_service = AuthService(None)
        
        # Test token creation (doesn't need DB)
        token = auth_service.create_access_token(
            data={"sub": "test-user-id"},
            expires_delta=timedelta(minutes=30)
        )
        assert token is not None
        assert isinstance(token, str)
        print("✅ Auth service can create tokens")
    except Exception as e:
        print(f"❌ Failed to test auth service: {e}")
        raise


def test_deps_supports_cookies():
    """Test that deps.py supports cookie authentication"""
    try:
        from api.deps import get_current_user
        import inspect
        
        # Check function signature includes cookie parameter
        sig = inspect.signature(get_current_user)
        params = list(sig.parameters.keys())
        
        # Should have token_from_cookie parameter
        assert "token_from_cookie" in params
        print("✅ Deps supports cookie authentication")
    except Exception as e:
        print(f"❌ Failed to test deps: {e}")
        raise


if __name__ == "__main__":
    print("Running simple authentication tests...")
    test_auth_endpoints_exist()
    test_auth_service_exists()
    test_deps_supports_cookies()
    print("✅ All simple tests passed!")