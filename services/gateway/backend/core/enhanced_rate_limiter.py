"""
Enhanced rate limiting with Redis backend
Provides distributed rate limiting for scaled deployments
"""
import time
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import logging

from core.redis_enhancements import rate_limiter as redis_rate_limiter, redis_client

logger = logging.getLogger(__name__)


class EnhancedRateLimiter:
    """
    Enhanced rate limiter that uses Redis when available
    Falls back to in-memory for development
    """
    
    def __init__(self):
        self.redis_limiter = redis_rate_limiter
        self.memory_limits = {}  # Fallback for when Redis is not available
    
    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        strategy: str = "sliding_window"
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier for rate limit (e.g., "login:192.168.1.1")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            strategy: Rate limiting strategy (sliding_window, token_bucket, fixed_window)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        # Try Redis first
        if self.redis_limiter and redis_client:
            try:
                return self.redis_limiter.check_rate_limit(
                    key,
                    max_requests,
                    window_seconds,
                    strategy
                )
            except Exception as e:
                logger.error(f"Redis rate limit failed, falling back to memory: {e}")
        
        # Fallback to in-memory rate limiting
        return self._memory_rate_limit(key, max_requests, window_seconds)
    
    def _memory_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """In-memory rate limiting fallback"""
        now = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(now - window_seconds)
        
        # Initialize key if not exists
        if key not in self.memory_limits:
            self.memory_limits[key] = []
        
        # Get requests in current window
        requests = self.memory_limits[key]
        requests_in_window = [
            req_time for req_time in requests
            if req_time > now - window_seconds
        ]
        
        # Check limit
        if len(requests_in_window) >= max_requests:
            return False, 0
        
        # Add current request
        requests_in_window.append(now)
        self.memory_limits[key] = requests_in_window
        
        remaining = max_requests - len(requests_in_window)
        return True, remaining
    
    def _cleanup_old_entries(self, cutoff_time: float):
        """Clean up old entries from memory limits"""
        keys_to_delete = []
        
        for key, requests in self.memory_limits.items():
            # Filter out old requests
            filtered = [req for req in requests if req > cutoff_time]
            
            if not filtered:
                keys_to_delete.append(key)
            else:
                self.memory_limits[key] = filtered
        
        # Delete empty keys
        for key in keys_to_delete:
            del self.memory_limits[key]
    
    async def record_attempt(self, key: str):
        """Record a failed attempt (for tracking)"""
        # This is handled automatically by check_rate_limit
        pass
    
    async def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a specific key"""
        if self.redis_limiter and redis_client:
            try:
                return self.redis_limiter.reset_limit(key)
            except Exception as e:
                logger.error(f"Failed to reset Redis rate limit: {e}")
        
        # Reset in-memory
        if key in self.memory_limits:
            del self.memory_limits[key]
            return True
        
        return False
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get information about current rate limit status"""
        info = {
            "key": key,
            "backend": "redis" if redis_client else "memory"
        }
        
        if not redis_client and key in self.memory_limits:
            info["requests"] = len(self.memory_limits[key])
        
        return info


# Global rate limiter instance
enhanced_rate_limiter = EnhancedRateLimiter()


# Rate limit configurations
class RateLimitConfig:
    """Standard rate limit configurations"""
    
    # Authentication
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_WINDOW_SECONDS = 300  # 5 minutes
    
    REGISTRATION_MAX_ATTEMPTS = 3
    REGISTRATION_WINDOW_SECONDS = 3600  # 1 hour
    
    PASSWORD_RESET_MAX_ATTEMPTS = 3
    PASSWORD_RESET_WINDOW_SECONDS = 3600  # 1 hour
    
    # API endpoints
    API_DEFAULT_MAX_REQUESTS = 100
    API_DEFAULT_WINDOW_SECONDS = 60  # 1 minute
    
    API_HEAVY_MAX_REQUESTS = 10
    API_HEAVY_WINDOW_SECONDS = 60  # 1 minute
    
    # File uploads
    UPLOAD_MAX_ATTEMPTS = 10
    UPLOAD_WINDOW_SECONDS = 3600  # 1 hour
    
    # Analytics
    ANALYTICS_MAX_REQUESTS = 50
    ANALYTICS_WINDOW_SECONDS = 300  # 5 minutes
    
    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS = 5
    WEBSOCKET_WINDOW_SECONDS = 60  # 1 minute
    
    # AI/ML endpoints
    AI_MAX_REQUESTS = 10
    AI_WINDOW_SECONDS = 300  # 5 minutes


# Middleware functions for easy integration
async def check_endpoint_rate_limit(
    endpoint: str,
    identifier: str,
    max_requests: Optional[int] = None,
    window: Optional[int] = None
) -> Tuple[bool, int]:
    """
    Check rate limit for a specific endpoint
    
    Args:
        endpoint: API endpoint path
        identifier: User ID or IP address
        max_requests: Override default max requests
        window: Override default window seconds
    """
    # Use defaults if not specified
    if max_requests is None:
        max_requests = RateLimitConfig.API_DEFAULT_MAX_REQUESTS
    if window is None:
        window = RateLimitConfig.API_DEFAULT_WINDOW_SECONDS
    
    # Special handling for heavy endpoints
    heavy_endpoints = ["/analytics", "/ai", "/reports", "/export"]
    if any(endpoint.startswith(ep) for ep in heavy_endpoints):
        max_requests = max_requests or RateLimitConfig.API_HEAVY_MAX_REQUESTS
        window = window or RateLimitConfig.API_HEAVY_WINDOW_SECONDS
    
    key = f"endpoint:{endpoint}:{identifier}"
    return await enhanced_rate_limiter.check_rate_limit(key, max_requests, window)


async def check_user_rate_limit(
    user_id: str,
    action: str,
    max_requests: int,
    window: int
) -> Tuple[bool, int]:
    """Check rate limit for user-specific action"""
    key = f"user:{user_id}:{action}"
    return await enhanced_rate_limiter.check_rate_limit(key, max_requests, window)


async def check_ip_rate_limit(
    ip_address: str,
    action: str,
    max_requests: int,
    window: int
) -> Tuple[bool, int]:
    """Check rate limit for IP-specific action"""
    key = f"ip:{ip_address}:{action}"
    return await enhanced_rate_limiter.check_rate_limit(key, max_requests, window)


# Decorator for rate limiting
def rate_limit(
    max_requests: int = 100,
    window: int = 60,
    key_func: Optional[callable] = None,
    strategy: str = "sliding_window"
):
    """
    Decorator for rate limiting endpoints
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
        key_func: Function to generate rate limit key from request
        strategy: Rate limiting strategy
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if hasattr(arg, 'client'):  # FastAPI Request object
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                # Default: use IP address
                if request and hasattr(request, 'client'):
                    key = f"default:{request.client.host}"
                else:
                    key = "default:unknown"
            
            # Check rate limit
            allowed, remaining = await enhanced_rate_limiter.check_rate_limit(
                key,
                max_requests,
                window,
                strategy
            )
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + window),
                        "Retry-After": str(window)
                    }
                )
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
            
            return response
        
        def sync_wrapper(*args, **kwargs):
            # Similar logic for sync functions
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if key_func:
                key = key_func(request)
            else:
                if request and hasattr(request, 'client'):
                    key = f"default:{request.client.host}"
                else:
                    key = "default:unknown"
            
            # For sync, we'll use the basic check
            import asyncio
            loop = asyncio.new_event_loop()
            allowed, remaining = loop.run_until_complete(
                enhanced_rate_limiter.check_rate_limit(
                    key,
                    max_requests,
                    window,
                    strategy
                )
            )
            loop.close()
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator