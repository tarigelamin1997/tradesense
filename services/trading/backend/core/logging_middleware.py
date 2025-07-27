"""
Logging middleware for request/response tracking

Captures detailed information about all HTTP requests and responses
for debugging and monitoring purposes.
"""

import time
import json
import uuid
from typing import Optional, Dict, Any
from typing import Callable, Dict, Any
from datetime import datetime

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.logging_config import (
    get_logger, get_performance_logger, set_request_context, 
    clear_request_context, request_id_var
)
from core.metrics import metrics_collector
from core.error_tracking import error_tracker

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user info if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        
        # Set logging context
        set_request_context(request_id, user_id)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, duration, request_id)
            
            # Record metrics
            self._record_metrics(request, response, duration)
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            await self._log_error(request, e, duration, request_id)
            
            # Record error metrics
            self._record_error_metrics(request, duration)
            
            # Track error
            error_tracker.capture_exception(e, {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration": duration
            })
            
            raise
        finally:
            # Clear logging context
            clear_request_context()
    
    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details"""
        # Get request body (if JSON)
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and request.headers.get("content-type") == "application/json":
                    body = json.loads(body)
                    # Sanitize sensitive fields
                    body = self._sanitize_data(body)
                else:
                    body = f"<{len(body)} bytes>"
            except:
                body = "<unable to read body>"
        
        # Log request
        logger.info(
            f"HTTP Request: {request.method} {request.url.path}",
            extra={
                "http_request": True,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._sanitize_headers(dict(request.headers)),
                "body": body,
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
    
    async def _log_response(self, request: Request, response: Response, duration: float, request_id: str) -> None:
        """Log response details"""
        logger.info(
            f"HTTP Response: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "http_response": True,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_headers": dict(response.headers)
            }
        )
        
        # Log performance metrics for slow requests
        if duration > 1.0:  # Requests taking more than 1 second
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} took {duration:.2f}s",
                extra={
                    "slow_request": True,
                    "request_id": request_id,
                    "duration_seconds": duration
                }
            )
    
    async def _log_error(self, request: Request, error: Exception, duration: float, request_id: str) -> None:
        """Log error details"""
        logger.error(
            f"HTTP Error: {request.method} {request.url.path} - {type(error).__name__}",
            extra={
                "http_error": True,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "duration_ms": round(duration * 1000, 2)
            },
            exc_info=True
        )
    
    def _sanitize_data(self, data: Any) -> Any:
        """Remove sensitive information from logged data"""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_fields = {
                'password', 'token', 'secret', 'api_key', 'authorization',
                'credit_card', 'card_number', 'cvv', 'ssn'
            }
            
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    sanitized[key] = '[REDACTED]'
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_data(value)
                else:
                    sanitized[key] = value
            
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers"""
        sanitized = {}
        sensitive_headers = {'authorization', 'cookie', 'x-api-key', 'x-auth-token'}
        
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _record_metrics(self, request: Request, response: Response, duration: float) -> None:
        """Record request metrics"""
        metrics_collector.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
    
    def _record_error_metrics(self, request: Request, duration: float) -> None:
        """Record error metrics"""
        metrics_collector.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status=500,
            duration=duration
        )

class LoggingRoute(APIRoute):
    """Custom route class that adds request ID to route context"""
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            # Ensure request has an ID
            if not hasattr(request.state, "request_id"):
                request.state.request_id = str(uuid.uuid4())
            
            # Add request ID to context
            request_id_var.set(request.state.request_id)
            
            response = await original_route_handler(request)
            return response
        
        return custom_route_handler

# Utility functions for structured logging
def log_business_event(event_type: str, user_id: str, metadata: Dict[str, Any]) -> None:
    """Log business events for analytics"""
    logger.info(
        f"Business event: {event_type}",
        extra={
            "business_event": True,
            "event_type": event_type,
            "user_id": user_id,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

def log_security_event(event_type: str, user_id: Optional[str], ip_address: str, metadata: Dict[str, Any]) -> None:
    """Log security events for monitoring"""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "security_event": True,
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

def log_performance_event(operation: str, duration: float, metadata: Dict[str, Any]) -> None:
    """Log performance events for optimization"""
    logger.info(
        f"Performance event: {operation}",
        extra={
            "performance_event": True,
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
    )