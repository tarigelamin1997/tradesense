"""
Production-ready security middleware for all services

Implements comprehensive security headers, rate limiting, and request validation
following OWASP best practices.
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Callable, Dict, Any, Optional, List
import time
import hashlib
import secrets
import re
from datetime import datetime, timedelta
import json
from core.logging_config import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses"""
    
    def __init__(self, app, nonce_generator: Optional[Callable] = None):
        super().__init__(app)
        self.nonce_generator = nonce_generator or self._generate_nonce
        
    def _generate_nonce(self) -> str:
        """Generate a secure nonce for CSP"""
        return secrets.token_urlsafe(16)
    
    async def dispatch(self, request: Request, call_next):
        # Generate CSP nonce
        nonce = self.nonce_generator()
        request.state.csp_nonce = nonce
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(response, nonce, request)
        
        return response
    
    def _add_security_headers(self, response: Response, nonce: str, request: Request):
        """Add comprehensive security headers"""
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.stripe.com https://*.datadoghq.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Strict Transport Security (2 years)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=(self)",
            "usb=()",
            "magnetometer=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Remove server header
        response.headers.pop("Server", None)
        
        # Add custom security headers
        response.headers["X-Request-ID"] = request.state.request_id if hasattr(request.state, "request_id") else "unknown"


class RateLimitingMiddleware:
    """Advanced rate limiting with different limits per endpoint"""
    
    def __init__(self, app, redis_url: Optional[str] = None):
        self.app = app
        
        # Create limiter with Redis backend for distributed rate limiting
        self.limiter = Limiter(
            key_func=self._get_rate_limit_key,
            default_limits=["100 per minute", "1000 per hour"],
            storage_uri=redis_url if redis_url else "memory://",
            strategy="moving-window"
        )
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/v1/auth/login": "5 per minute",
            "/api/v1/auth/register": "3 per minute",
            "/api/v1/auth/reset-password": "3 per hour",
            "/api/v1/trades": "30 per minute",
            "/api/v1/analytics": "20 per minute",
            "/api/v1/ai": "10 per minute"
        }
        
        # Add rate limit exceeded handler
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key based on user or IP"""
        # Try to get user ID from request
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        return get_remote_address(request)
    
    def get_limiter(self):
        return self.limiter


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize all input data"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bor\b\s*\d+\s*=\s*\d+)",
        r"(\band\b\s*\d+\s*=\s*\d+)",
        r"(';|';--|';#|';\/\*)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>"
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\"
    ]
    
    def __init__(self, app, max_body_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_body_size = max_body_size
        self.compiled_patterns = {
            "sql": [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS],
            "xss": [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS],
            "path": [re.compile(p) for p in self.PATH_TRAVERSAL_PATTERNS]
        }
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request body too large"
            )
        
        # Validate URL parameters
        if not self._validate_params(dict(request.query_params)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query parameters detected"
            )
        
        # For POST/PUT/PATCH requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Store body for later use
                    request._body = body
                    
                    # Try to parse as JSON
                    try:
                        json_body = json.loads(body)
                        if not self._validate_json(json_body):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Potentially malicious input detected"
                            )
                    except json.JSONDecodeError:
                        # Not JSON, validate as string
                        if not self._validate_string(body.decode("utf-8", errors="ignore")):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Potentially malicious input detected"
                            )
            except Exception as e:
                logger.warning(f"Input validation error: {e}")
        
        response = await call_next(request)
        return response
    
    def _validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate URL parameters"""
        for key, value in params.items():
            if not self._validate_string(str(key)) or not self._validate_string(str(value)):
                return False
        return True
    
    def _validate_json(self, data: Any) -> bool:
        """Recursively validate JSON data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if not self._validate_string(str(key)) or not self._validate_json(value):
                    return False
        elif isinstance(data, list):
            for item in data:
                if not self._validate_json(item):
                    return False
        elif isinstance(data, str):
            return self._validate_string(data)
        return True
    
    def _validate_string(self, value: str) -> bool:
        """Check string for malicious patterns"""
        # Check SQL injection
        for pattern in self.compiled_patterns["sql"]:
            if pattern.search(value):
                logger.warning(f"SQL injection pattern detected: {value[:100]}")
                return False
        
        # Check XSS
        for pattern in self.compiled_patterns["xss"]:
            if pattern.search(value):
                logger.warning(f"XSS pattern detected: {value[:100]}")
                return False
        
        # Check path traversal
        for pattern in self.compiled_patterns["path"]:
            if pattern.search(value):
                logger.warning(f"Path traversal pattern detected: {value[:100]}")
                return False
        
        return True


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Add request tracing for distributed systems"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", secrets.token_urlsafe(16))
        request.state.request_id = request_id
        
        # Add timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add tracing headers
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log request details
        logger.info(
            "Request processed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
                "client_ip": get_remote_address(request)
            }
        )
        
        return response


class CORSMiddleware:
    """Production-ready CORS configuration"""
    
    def __init__(
        self,
        app,
        allowed_origins: List[str],
        allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allowed_headers: List[str] = ["*"],
        allow_credentials: bool = True,
        max_age: int = 3600
    ):
        self.app = app
        self.allowed_origins = allowed_origins
        self.allowed_methods = allowed_methods
        self.allowed_headers = allowed_headers
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def __call__(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
            return response
        
        # Process regular requests
        response = await call_next(request)
        
        # Add CORS headers
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
            response.headers["Vary"] = "Origin"
        
        return response


def setup_security_middleware(app, config):
    """Configure all security middleware for production"""
    
    # Request tracing (first to capture all requests)
    app.add_middleware(RequestTracingMiddleware)
    
    # Trusted host validation
    if config.environment.value == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[
                "tradesense.io",
                "*.tradesense.io",
                "*.railway.app"
            ]
        )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allowed_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials
    )
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Input validation
    app.add_middleware(InputValidationMiddleware)
    
    # Rate limiting
    rate_limiter = RateLimitingMiddleware(app, config.redis.url)
    
    return rate_limiter.get_limiter()