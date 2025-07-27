"""
Test configuration for TradeSense backend
"""
import os
from core.config import Settings

class TestSettings(Settings):
    # Override database URL for tests
    database_url: str = "postgresql://postgres:postgres@localhost/tradesense_test"
    
    # Use a test-specific JWT secret
    jwt_secret_key: str = "test-secret-key-for-testing-only"
    
    # Disable JWT validation in __init__ for tests
    def __init__(self, **kwargs):
        # Call parent __init__ without super() to avoid validation
        object.__setattr__(self, '_initialized', False)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._initialized = True
    
test_settings = TestSettings()