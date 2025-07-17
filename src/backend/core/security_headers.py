"""
Security headers middleware for FastAPI
"""
from fastapi import Request
from fastapi.responses import Response
import os


async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to all responses
    """
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # HSTS only in production
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Content Security Policy
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com",  # Allow inline scripts for development
        "style-src 'self' 'unsafe-inline'",  # Allow inline styles
        "img-src 'self' data: https: blob:",  # Allow images from various sources
        "font-src 'self' data:",
        "connect-src 'self' https://api.stripe.com wss://tradesense.com ws://localhost:* http://localhost:*",  # Allow WebSocket and local connections
        "frame-src 'self' https://js.stripe.com https://hooks.stripe.com",  # Allow Stripe frames
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'"
    ]
    
    # More permissive CSP in development
    if os.getenv("ENVIRONMENT") != "production":
        csp_directives[1] = "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com http://localhost:*"
        csp_directives[4] = "connect-src 'self' https://api.stripe.com wss://tradesense.com ws://localhost:* http://localhost:* ws://0.0.0.0:*"
    
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    # Remove server header if present
    if "server" in response.headers:
        del response.headers["server"]
    
    return response