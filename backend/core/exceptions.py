"""
Custom Exception Classes

Custom exceptions for the TradeSense application.
"""
from typing import Any, Dict, Optional
from datetime import datetime

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

class BusinessLogicError(TradeSenseException):
    """Raised when business logic validation fails"""
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

def setup_exception_handlers(app):
    from fastapi.responses import JSONResponse
    from fastapi import Request, status
    from fastapi.exceptions import RequestValidationError
    import logging
    
    logger = logging.getLogger(__name__)
    
    @app.exception_handler(TradeSenseException)
    async def tradesense_exception_handler(request: Request, exc: TradeSenseException):
        """Handle custom TradeSense exceptions"""
        logger.error(f"TradeSense exception: {exc.__class__.__name__} - {exc.message}")
        
        # Determine appropriate status code based on exception type
        status_code = 400
        if isinstance(exc, NotFoundError):
            status_code = 404
        elif isinstance(exc, AuthenticationError):
            status_code = 401
        elif isinstance(exc, AuthorizationError):
            status_code = 403
        elif isinstance(exc, ConflictError):
            status_code = 409
        elif isinstance(exc, RateLimitError):
            status_code = 429
        elif isinstance(exc, (DatabaseError, ExternalServiceError)):
            status_code = 500
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        logger.warning(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": exc.errors()
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": {
                    "error_type": exc.__class__.__name__
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )