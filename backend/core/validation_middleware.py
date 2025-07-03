"""
Validation Middleware

Provides automatic request validation and sanitization for FastAPI endpoints.
"""
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.validation import (
    sanitize_input_data,
    validate_pagination_params,
    validate_date_format,
    validate_uuid,
    ValidationError
)
from backend.core.responses import error_response

logger = logging.getLogger(__name__)

class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic request validation and sanitization"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = {
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/performance/metrics"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through validation middleware"""
        
        # Skip validation for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        try:
            # Validate and sanitize query parameters
            if request.query_params:
                sanitized_query = sanitize_input_data(dict(request.query_params))
                
                # Validate pagination parameters if present
                if 'page' in sanitized_query or 'per_page' in sanitized_query:
                    page = int(sanitized_query.get('page', 1))
                    per_page = int(sanitized_query.get('per_page', 20))
                    is_valid, errors = validate_pagination_params(page, per_page)
                    if not is_valid:
                        return JSONResponse(
                            status_code=400,
                            content=error_response(
                                message="Invalid pagination parameters",
                                error=", ".join(errors)
                            )
                        )
                
                # Validate date parameters if present
                for key, value in sanitized_query.items():
                    if 'date' in key.lower() and not validate_date_format(value):
                        return JSONResponse(
                            status_code=400,
                            content=error_response(
                                message=f"Invalid date format for {key}",
                                error="Date must be in ISO format (YYYY-MM-DDTHH:MM:SS)"
                            )
                        )
                
                # Validate UUID parameters if present
                for key, value in sanitized_query.items():
                    if 'id' in key.lower() and not validate_uuid(value):
                        return JSONResponse(
                            status_code=400,
                            content=error_response(
                                message=f"Invalid UUID format for {key}",
                                error="UUID must be in standard format"
                            )
                        )
            
            # Validate and sanitize request body for POST/PUT/PATCH
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.json()
                    if body:
                        sanitized_body = sanitize_input_data(body)
                        # Replace request body with sanitized version
                        request._body = sanitized_body
                except Exception:
                    # Not JSON body, skip validation
                    pass
            
            # Process request
            response = await call_next(request)
            return response
            
        except ValidationError as e:
            logger.warning(f"Validation error in {request.url.path}: {str(e)}")
            return JSONResponse(
                status_code=400,
                content=error_response(
                    message="Validation error",
                    error=str(e)
                )
            )
        except Exception as e:
            logger.error(f"Unexpected error in validation middleware: {str(e)}")
            return JSONResponse(
                status_code=500,
                content=error_response(
                    message="Internal server error",
                    error="Validation processing failed"
                )
            )

def setup_validation_middleware(app: ASGIApp):
    """Setup validation middleware for FastAPI app"""
    app.add_middleware(ValidationMiddleware)
    logger.info("Validation middleware configured") 