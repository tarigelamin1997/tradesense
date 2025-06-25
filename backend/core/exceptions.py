
"""
Custom exception classes for TradeSense backend
"""
from typing import Any, Dict, Optional


class TradeSenseException(Exception):
    """Base exception for TradeSense application"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(TradeSenseException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(TradeSenseException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


class ValidationError(TradeSenseException):
    """Data validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class NotFoundError(TradeSenseException):
    """Resource not found errors"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class BusinessLogicError(TradeSenseException):
    """Business logic related errors"""
    
    def __init__(self, message: str = "Business logic error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class ExternalServiceError(TradeSenseException):
    """External service integration errors"""
    
    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, details=details)
