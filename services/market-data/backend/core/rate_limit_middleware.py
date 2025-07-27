"""
Rate Limiting Middleware

Applies rate limiting to API endpoints based on configuration.
"""
import time
import json
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from core.advanced_rate_limiter import (
    apply_rate_limit,
    release_concurrent_slot,
    RateLimitConfig,
    RateLimitExceeded,
    get_rate_limit_key
)
from core.metrics import rate_limit_hits, rate_limit_violations

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for applying rate limiting to requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.route_configs = self._build_route_configs()
    
    def _build_route_configs(self) -> Dict[str, Dict[str, Any]]:
        """Build rate limit configurations for different routes"""
        return {
            # Authentication routes
            "/api/v1/auth/login": RateLimitConfig.AUTH_LOGIN,
            "/api/v1/auth/register": RateLimitConfig.AUTH_REGISTER,
            "/api/v1/auth/password-reset": RateLimitConfig.AUTH_PASSWORD_RESET,
            "/api/v1/auth/forgot-password": RateLimitConfig.AUTH_PASSWORD_RESET,
            
            # Analytics routes (heavier operations)
            "/api/v1/analytics": RateLimitConfig.API_ANALYTICS,
            "/api/v1/analytics/advanced": RateLimitConfig.API_ANALYTICS,
            "/api/v1/analytics/performance": RateLimitConfig.API_ANALYTICS,
            "/api/v1/analytics/confidence": RateLimitConfig.API_ANALYTICS,
            
            # Upload routes
            "/api/v1/trades/upload": RateLimitConfig.API_UPLOAD,
            "/api/v1/uploads": RateLimitConfig.API_UPLOAD,
            
            # WebSocket routes
            "/api/v1/ws": RateLimitConfig.WEBSOCKET,
            "/api/v1/websocket": RateLimitConfig.WEBSOCKET,
            
            # Default for all other API routes
            "/api/v1": RateLimitConfig.API_GENERAL,
        }
    
    def _get_route_config(self, path: str) -> Optional[Dict[str, Any]]:
        """Get rate limit configuration for a route"""
        # Check exact match first
        if path in self.route_configs:
            return self.route_configs[path]
        
        # Check prefix matches (longest match first)
        for route_prefix in sorted(self.route_configs.keys(), key=len, reverse=True):
            if path.startswith(route_prefix):
                return self.route_configs[route_prefix]
        
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests"""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/api/v1/monitoring/health"]:
            return await call_next(request)
        
        # Skip rate limiting for static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)
        
        # Get rate limit configuration for this route
        config = self._get_route_config(request.url.path)
        
        if not config:
            # No rate limiting for this route
            return await call_next(request)
        
        # Extract user ID if authenticated
        user_id = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        
        # Apply rate limiting
        try:
            start_time = time.time()
            rate_limit_key = get_rate_limit_key(request, user_id)
            
            metadata = await apply_rate_limit(
                request,
                config,
                user_id=user_id,
                key_suffix=request.url.path
            )
            
            # Record metric
            rate_limit_hits.labels(
                endpoint=request.url.path,
                method=request.method
            ).inc()
            
            # Add rate limit headers to response
            response = await call_next(request)
            
            # Add rate limit headers
            if "tokens_remaining" in metadata:
                # Token bucket headers
                response.headers["X-RateLimit-Limit"] = str(metadata.get("capacity", 100))
                response.headers["X-RateLimit-Remaining"] = str(metadata["tokens_remaining"])
                response.headers["X-RateLimit-RefillRate"] = str(metadata.get("refill_rate", 1))
            elif "requests_in_window" in metadata:
                # Window-based headers
                response.headers["X-RateLimit-Limit"] = str(metadata["max_requests"])
                remaining = max(0, metadata["max_requests"] - metadata["requests_in_window"])
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(metadata.get("reset_time", 0))
            
            # Release concurrent slot if needed
            await release_concurrent_slot(request)
            
            # Log rate limit usage for monitoring
            if remaining <= 5:
                logger.warning(
                    f"Rate limit nearly exhausted for {rate_limit_key} "
                    f"on {request.url.path}: {remaining} remaining"
                )
            
            return response
            
        except RateLimitExceeded as e:
            # Record violation metric
            rate_limit_violations.labels(
                endpoint=request.url.path,
                method=request.method
            ).inc()
            
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded for {get_rate_limit_key(request, user_id)} "
                f"on {request.url.path}"
            )
            
            # Return rate limit error response
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "detail": e.detail,
                    "type": "rate_limit_exceeded",
                    "retry_after": int(e.headers.get("Retry-After", 60))
                },
                headers=e.headers
            )
        
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {str(e)}")
            # Don't block request on rate limiter errors
            return await call_next(request)


class PerUserRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for per-user rate limiting based on subscription tier"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.tier_limits = {
            "free": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "concurrent_requests": 5
            },
            "pro": {
                "requests_per_minute": 300,
                "requests_per_hour": 10000,
                "concurrent_requests": 20
            },
            "enterprise": {
                "requests_per_minute": 1000,
                "requests_per_hour": 100000,
                "concurrent_requests": 100
            }
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply per-user rate limiting based on subscription tier"""
        # Skip if no user is authenticated
        if not hasattr(request.state, "user") or not request.state.user:
            return await call_next(request)
        
        user = request.state.user
        tier = getattr(user, "subscription_tier", "free")
        limits = self.tier_limits.get(tier, self.tier_limits["free"])
        
        # Apply per-minute limit
        try:
            minute_config = {
                "strategy": "sliding_window",
                "max_requests": limits["requests_per_minute"],
                "window_seconds": 60
            }
            
            await apply_rate_limit(
                request,
                minute_config,
                user_id=str(user.id),
                key_suffix="per_minute"
            )
            
            # Apply per-hour limit
            hour_config = {
                "strategy": "sliding_window",
                "max_requests": limits["requests_per_hour"],
                "window_seconds": 3600
            }
            
            await apply_rate_limit(
                request,
                hour_config,
                user_id=str(user.id),
                key_suffix="per_hour"
            )
            
            # Apply concurrent request limit
            concurrent_config = {
                "strategy": "concurrent",
                "max_concurrent": limits["concurrent_requests"]
            }
            
            await apply_rate_limit(
                request,
                concurrent_config,
                user_id=str(user.id),
                key_suffix="concurrent"
            )
            
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "detail": f"Rate limit exceeded for {tier} tier",
                    "type": "tier_rate_limit_exceeded",
                    "tier": tier,
                    "limits": limits,
                    "retry_after": int(e.headers.get("Retry-After", 60))
                },
                headers=e.headers
            )
        
        response = await call_next(request)
        
        # Add tier information to response headers
        response.headers["X-Subscription-Tier"] = tier
        response.headers["X-Tier-Limit-PerMinute"] = str(limits["requests_per_minute"])
        response.headers["X-Tier-Limit-PerHour"] = str(limits["requests_per_hour"])
        
        return response


def create_custom_rate_limiter(
    max_requests: int,
    window_seconds: int,
    strategy: str = "sliding_window"
) -> Callable:
    """
    Create a custom rate limiter decorator for specific endpoints
    
    Usage:
        @router.get("/api/endpoint")
        @create_custom_rate_limiter(max_requests=10, window_seconds=60)
        async def endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            config = {
                "strategy": strategy,
                "max_requests": max_requests,
                "window_seconds": window_seconds
            }
            
            # Extract user ID if available
            user_id = None
            if "current_user" in kwargs:
                user_id = str(kwargs["current_user"].id)
            
            # Apply rate limiting
            await apply_rate_limit(
                request,
                config,
                user_id=user_id,
                key_suffix=func.__name__
            )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator