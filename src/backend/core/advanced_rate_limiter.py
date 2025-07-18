"""
Advanced Rate Limiting Module with Redis Support

Provides distributed rate limiting with multiple strategies:
- Token bucket algorithm
- Sliding window counter
- Fixed window counter
- Concurrent requests limiter
"""
import time
import asyncio
import json
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

from core.config import settings
from core.cache import get_redis_client

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    CONCURRENT = "concurrent"


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )


class AdvancedRateLimiter:
    """Advanced rate limiter with multiple strategies and Redis support"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.local_cache: Dict[str, Any] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        if self.redis:
            return self.redis
        return await get_redis_client()
    
    async def token_bucket(
        self,
        key: str,
        capacity: int,
        refill_rate: float,
        tokens_required: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Token bucket algorithm for smooth rate limiting
        
        Args:
            key: Unique identifier
            capacity: Maximum tokens in bucket
            refill_rate: Tokens added per second
            tokens_required: Tokens needed for this request
        
        Returns:
            Tuple of (allowed, metadata)
        """
        redis_client = await self._get_redis()
        
        if not redis_client:
            # Fallback to local implementation
            return await self._local_token_bucket(key, capacity, refill_rate, tokens_required)
        
        now = time.time()
        bucket_key = f"rate_limit:token_bucket:{key}"
        
        # Lua script for atomic token bucket operations
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_required = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now
        
        -- Calculate tokens to add
        local time_passed = now - last_refill
        local tokens_to_add = time_passed * refill_rate
        tokens = math.min(capacity, tokens + tokens_to_add)
        
        if tokens >= tokens_required then
            tokens = tokens - tokens_required
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            return {1, tokens, capacity}
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, 3600)
            return {0, tokens, capacity}
        end
        """
        
        result = await redis_client.eval(
            lua_script,
            1,
            bucket_key,
            capacity,
            refill_rate,
            tokens_required,
            now
        )
        
        allowed = bool(result[0])
        metadata = {
            "tokens_remaining": int(result[1]),
            "capacity": int(result[2]),
            "refill_rate": refill_rate
        }
        
        return allowed, metadata
    
    async def sliding_window(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sliding window counter algorithm
        
        Args:
            key: Unique identifier
            max_requests: Maximum requests in window
            window_seconds: Window size in seconds
        
        Returns:
            Tuple of (allowed, metadata)
        """
        redis_client = await self._get_redis()
        
        if not redis_client:
            return await self._local_sliding_window(key, max_requests, window_seconds)
        
        now = time.time()
        window_key = f"rate_limit:sliding_window:{key}"
        window_start = now - window_seconds
        
        # Remove old entries and count current window
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(window_key, 0, window_start)
        pipe.zcard(window_key)
        pipe.zadd(window_key, {str(now): now})
        pipe.expire(window_key, window_seconds)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        if current_requests > max_requests:
            # Remove the just-added entry
            await redis_client.zrem(window_key, str(now))
            allowed = False
            requests_in_window = current_requests - 1
        else:
            allowed = True
            requests_in_window = current_requests
        
        metadata = {
            "requests_in_window": requests_in_window,
            "max_requests": max_requests,
            "window_seconds": window_seconds,
            "reset_time": int(now + window_seconds)
        }
        
        return allowed, metadata
    
    async def fixed_window(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Fixed window counter algorithm
        
        Args:
            key: Unique identifier
            max_requests: Maximum requests per window
            window_seconds: Window size in seconds
        
        Returns:
            Tuple of (allowed, metadata)
        """
        redis_client = await self._get_redis()
        
        if not redis_client:
            return await self._local_fixed_window(key, max_requests, window_seconds)
        
        now = int(time.time())
        window_start = (now // window_seconds) * window_seconds
        window_key = f"rate_limit:fixed_window:{key}:{window_start}"
        
        # Increment counter
        current_requests = await redis_client.incr(window_key)
        
        # Set expiry on first request
        if current_requests == 1:
            await redis_client.expire(window_key, window_seconds)
        
        allowed = current_requests <= max_requests
        
        metadata = {
            "requests_in_window": min(current_requests, max_requests + 1),
            "max_requests": max_requests,
            "window_seconds": window_seconds,
            "reset_time": window_start + window_seconds
        }
        
        return allowed, metadata
    
    async def concurrent_requests(
        self,
        key: str,
        max_concurrent: int,
        request_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Limit concurrent requests
        
        Args:
            key: Unique identifier
            max_concurrent: Maximum concurrent requests
            request_id: Unique request identifier
        
        Returns:
            Tuple of (allowed, metadata)
        """
        redis_client = await self._get_redis()
        
        if not redis_client:
            return True, {"max_concurrent": max_concurrent}
        
        set_key = f"rate_limit:concurrent:{key}"
        
        # Add request to set
        await redis_client.sadd(set_key, request_id)
        await redis_client.expire(set_key, 300)  # 5 minute expiry
        
        # Check concurrent count
        current_concurrent = await redis_client.scard(set_key)
        
        if current_concurrent > max_concurrent:
            # Remove this request
            await redis_client.srem(set_key, request_id)
            allowed = False
        else:
            allowed = True
        
        metadata = {
            "current_concurrent": min(current_concurrent, max_concurrent + 1),
            "max_concurrent": max_concurrent
        }
        
        return allowed, metadata
    
    async def release_concurrent(self, key: str, request_id: str):
        """Release a concurrent request slot"""
        redis_client = await self._get_redis()
        
        if redis_client:
            set_key = f"rate_limit:concurrent:{key}"
            await redis_client.srem(set_key, request_id)
    
    # Local implementations for fallback
    async def _local_token_bucket(
        self, key: str, capacity: int, refill_rate: float, tokens_required: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Local token bucket implementation"""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            now = time.time()
            
            if key not in self.local_cache:
                self.local_cache[key] = {
                    "tokens": capacity,
                    "last_refill": now
                }
            
            bucket = self.local_cache[key]
            time_passed = now - bucket["last_refill"]
            tokens_to_add = time_passed * refill_rate
            
            bucket["tokens"] = min(capacity, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now
            
            if bucket["tokens"] >= tokens_required:
                bucket["tokens"] -= tokens_required
                allowed = True
            else:
                allowed = False
            
            metadata = {
                "tokens_remaining": int(bucket["tokens"]),
                "capacity": capacity,
                "refill_rate": refill_rate
            }
            
            return allowed, metadata
    
    async def _local_sliding_window(
        self, key: str, max_requests: int, window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Local sliding window implementation"""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            now = time.time()
            window_start = now - window_seconds
            
            if key not in self.local_cache:
                self.local_cache[key] = []
            
            # Clean old entries
            self.local_cache[key] = [
                t for t in self.local_cache[key] if t > window_start
            ]
            
            current_requests = len(self.local_cache[key])
            
            if current_requests < max_requests:
                self.local_cache[key].append(now)
                allowed = True
                requests_in_window = current_requests + 1
            else:
                allowed = False
                requests_in_window = current_requests
            
            metadata = {
                "requests_in_window": requests_in_window,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "reset_time": int(now + window_seconds)
            }
            
            return allowed, metadata
    
    async def _local_fixed_window(
        self, key: str, max_requests: int, window_seconds: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Local fixed window implementation"""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            now = int(time.time())
            window_start = (now // window_seconds) * window_seconds
            window_key = f"{key}:{window_start}"
            
            if window_key not in self.local_cache:
                self.local_cache[window_key] = 0
            
            self.local_cache[window_key] += 1
            current_requests = self.local_cache[window_key]
            
            allowed = current_requests <= max_requests
            
            metadata = {
                "requests_in_window": min(current_requests, max_requests + 1),
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "reset_time": window_start + window_seconds
            }
            
            return allowed, metadata


# Global rate limiter instance
advanced_rate_limiter = AdvancedRateLimiter()


class RateLimitConfig:
    """Rate limiting configurations for different endpoints"""
    
    # Authentication endpoints
    AUTH_LOGIN = {
        "strategy": RateLimitStrategy.SLIDING_WINDOW,
        "max_requests": 5,
        "window_seconds": 300  # 5 minutes
    }
    
    AUTH_REGISTER = {
        "strategy": RateLimitStrategy.FIXED_WINDOW,
        "max_requests": 3,
        "window_seconds": 3600  # 1 hour
    }
    
    AUTH_PASSWORD_RESET = {
        "strategy": RateLimitStrategy.FIXED_WINDOW,
        "max_requests": 3,
        "window_seconds": 3600  # 1 hour
    }
    
    # API endpoints
    API_GENERAL = {
        "strategy": RateLimitStrategy.TOKEN_BUCKET,
        "capacity": 100,
        "refill_rate": 2.0  # 2 requests per second
    }
    
    API_ANALYTICS = {
        "strategy": RateLimitStrategy.TOKEN_BUCKET,
        "capacity": 30,
        "refill_rate": 0.5  # 1 request per 2 seconds
    }
    
    API_UPLOAD = {
        "strategy": RateLimitStrategy.CONCURRENT,
        "max_concurrent": 3
    }
    
    # WebSocket connections
    WEBSOCKET = {
        "strategy": RateLimitStrategy.CONCURRENT,
        "max_concurrent": 5
    }


def get_rate_limit_key(request: Request, user_id: Optional[str] = None) -> str:
    """Generate rate limit key from request"""
    if user_id:
        return f"user:{user_id}"
    
    # Get client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.headers.get("X-Real-IP", request.client.host if request.client else "unknown")
    
    return f"ip:{ip}"


async def apply_rate_limit(
    request: Request,
    config: Dict[str, Any],
    user_id: Optional[str] = None,
    key_suffix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply rate limiting based on configuration
    
    Args:
        request: FastAPI request
        config: Rate limit configuration
        user_id: Optional user ID for user-based limiting
        key_suffix: Optional suffix for the rate limit key
    
    Returns:
        Rate limit metadata
    
    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    key = get_rate_limit_key(request, user_id)
    if key_suffix:
        key = f"{key}:{key_suffix}"
    
    strategy = config.get("strategy", RateLimitStrategy.TOKEN_BUCKET)
    
    if strategy == RateLimitStrategy.TOKEN_BUCKET:
        allowed, metadata = await advanced_rate_limiter.token_bucket(
            key,
            config["capacity"],
            config["refill_rate"],
            config.get("tokens_required", 1)
        )
    elif strategy == RateLimitStrategy.SLIDING_WINDOW:
        allowed, metadata = await advanced_rate_limiter.sliding_window(
            key,
            config["max_requests"],
            config["window_seconds"]
        )
    elif strategy == RateLimitStrategy.FIXED_WINDOW:
        allowed, metadata = await advanced_rate_limiter.fixed_window(
            key,
            config["max_requests"],
            config["window_seconds"]
        )
    elif strategy == RateLimitStrategy.CONCURRENT:
        request_id = f"{time.time()}:{id(request)}"
        allowed, metadata = await advanced_rate_limiter.concurrent_requests(
            key,
            config["max_concurrent"],
            request_id
        )
        if allowed:
            # Store request ID for cleanup
            request.state.rate_limit_request_id = request_id
            request.state.rate_limit_key = key
    else:
        allowed = True
        metadata = {}
    
    if not allowed:
        retry_after = metadata.get("reset_time", int(time.time()) + 60) - int(time.time())
        raise RateLimitExceeded(retry_after=max(1, retry_after))
    
    return metadata


async def release_concurrent_slot(request: Request):
    """Release concurrent request slot if applicable"""
    if hasattr(request.state, "rate_limit_request_id"):
        await advanced_rate_limiter.release_concurrent(
            request.state.rate_limit_key,
            request.state.rate_limit_request_id
        )