"""
Custom Exception Classes

Custom exceptions for the TradeSense application.
"""
from typing import Any, Dict, Optional

class TradeSenseException(Exception):
    """Base exception class for TradeSense application"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(TradeSenseException):
    """Raised when data validation fails"""
    pass

class AuthenticationError(TradeSenseException):
    """Raised when authentication fails"""
    pass

class AuthorizationError(TradeSenseException):
    """Raised when authorization fails"""
    pass

class NotFoundError(TradeSenseException):
    """Raised when a requested resource is not found"""
    pass

class ConflictError(TradeSenseException):
    """Raised when a resource conflict occurs"""
    pass

class DatabaseError(TradeSenseException):
    """Raised when a database operation fails"""
    pass

class ExternalServiceError(TradeSenseException):
    """Raised when an external service call fails"""
    pass

class RateLimitError(TradeSenseException):
    """Raised when rate limit is exceeded"""
    pass

class ConfigurationError(TradeSenseException):
    """Raised when configuration is invalid"""
    pass