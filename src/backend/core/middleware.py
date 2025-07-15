"""
Custom middleware for error handling, logging, and request tracking
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import json
import uuid
from typing import Callable
import asyncio
from fastapi.responses import JSONResponse
import os

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Log request
        start_time = time.time()
        logger.info(f"Request {request_id}: {request.method} {request.url}")
        
        # Add request ID to headers
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(f"Request {request_id} completed in {process_time:.4f}s - Status: {response.status_code}")
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request {request_id} failed in {process_time:.4f}s - Error: {str(e)}")
            raise


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size"""
    def __init__(self, app, max_size: int = 100 * 1024):  # 100KB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "error": "RequestEntityTooLarge",
                    "message": f"Request body too large. Maximum size is {self.max_size} bytes.",
                    "details": {
                        "max_size": self.max_size,
                        "request_size": int(content_length)
                    },
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )
        
        # For requests without content-length, we need to check during reading
        # This is handled by the validation middleware
        return await call_next(request)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unhandled error in {request.url}: {str(e)}", exc_info=True)
            
            # Return appropriate error response
            from fastapi.responses import JSONResponse
            
            # In production, don't expose error details
            if os.getenv("ENVIRONMENT", "development") == "production":
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "message": "An unexpected error occurred",
                        "request_id": getattr(request.state, 'request_id', 'unknown')
                    }
                )
            else:
                # In development, include more details for debugging
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "message": str(e),
                        "request_id": getattr(request.state, 'request_id', 'unknown')
                    }
                )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove potentially sensitive headers
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        if "Server" in response.headers:
            del response.headers["Server"]
        
        # Mask technology stack in production
        if os.getenv("ENVIRONMENT", "development") == "production":
            response.headers["Server"] = "TradeSense"
        
        return response


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Add request timeout protection"""
    def __init__(self, app, timeout_seconds: float = 30.0):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Create a task for the actual request processing
            response_task = asyncio.create_task(call_next(request))
            
            # Wait for either the response or timeout
            response = await asyncio.wait_for(response_task, timeout=self.timeout_seconds)
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {self.timeout_seconds}s: {request.method} {request.url}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Request timeout",
                    "message": f"Request processing exceeded {self.timeout_seconds} seconds",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )
        except Exception as e:
            logger.error(f"Timeout middleware error: {str(e)}")
            raise


def setup_middleware(app):
    """Setup all middleware in the correct order"""
    # Timeout protection should be innermost (closest to the actual handlers)
    app.add_middleware(TimeoutMiddleware, timeout_seconds=30.0)
    # Request size limit middleware
    app.add_middleware(RequestSizeLimitMiddleware, max_size=100 * 1024)  # 100KB limit
    # Security headers should be applied to all responses
    app.add_middleware(SecurityHeadersMiddleware)
    # Logging should happen for all requests
    app.add_middleware(LoggingMiddleware)
    # Error handling should be the outermost middleware
    app.add_middleware(ErrorHandlingMiddleware)
