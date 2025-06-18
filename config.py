
import os
from typing import Dict, Any

class Config:
    """Production configuration management."""
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tradesense.db')
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '5'))
    
    # Security settings
    SECRET_KEY = os.getenv('TRADESENSE_MASTER_KEY')
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    
    # Performance settings
    CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', '50'))
    MAX_MEMORY_USAGE = int(os.getenv('MAX_MEMORY_USAGE', '80'))
    
    # Feature flags
    ENABLE_DEBUG = os.getenv('ENABLE_DEBUG', 'false').lower() == 'true'
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status."""
        issues = []
        
        if not cls.SECRET_KEY:
            issues.append("TRADESENSE_MASTER_KEY not set")
        
        if cls.ENABLE_DEBUG:
            issues.append("Debug mode enabled in production")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }

# Global config instance
config = Config()
