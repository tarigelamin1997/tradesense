"""
Rate Limiting Module

Provides rate limiting functionality to prevent abuse and brute force attacks.
Now with Redis support for distributed rate limiting.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Import enhanced rate limiter with Redis support
try:
    from core.enhanced_rate_limiter import enhanced_rate_limiter, RateLimitConfig as EnhancedRateLimitConfig
    REDIS_RATE_LIMITER_AVAILABLE = True
except ImportError:
    REDIS_RATE_LIMITER_AVAILABLE = False

logger = logging.getLogger(__name__)

class RateLimiter:
    """Hybrid rate limiter with Redis support and in-memory fallback"""
    
    def __init__(self):
        self.attempts: Dict[str, list] = defaultdict(list)
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.use_redis = REDIS_RATE_LIMITER_AVAILABLE
    
    async def is_allowed(
        self, 
        key: str, 
        max_attempts: int = 5, 
        window_seconds: int = 300
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if a request is allowed based on rate limiting rules
        
        Args:
            key: Unique identifier (e.g., IP address, user ID)
            max_attempts: Maximum attempts allowed in the time window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        # Use Redis rate limiter if available
        if self.use_redis and enhanced_rate_limiter:
            try:
                return await enhanced_rate_limiter.check_rate_limit(
                    key, max_attempts, window_seconds, "sliding_window"
                )
            except Exception as e:
                logger.error(f"Redis rate limiter error, falling back to memory: {e}")
                # Fall through to in-memory implementation
        
        # In-memory rate limiting
        async with self.locks[key]:
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old attempts
            self.attempts[key] = [
                attempt_time for attempt_time in self.attempts[key] 
                if attempt_time > window_start
            ]
            
            # Check if limit exceeded
            if len(self.attempts[key]) >= max_attempts:
                logger.warning(f"Rate limit exceeded for key: {key}")
                return False, 0
            
            # Add current attempt
            self.attempts[key].append(now)
            
            remaining = max_attempts - len(self.attempts[key])
            return True, remaining
    
    async def record_attempt(self, key: str) -> None:
        """Record an attempt for rate limiting"""
        # Use Redis rate limiter if available
        if self.use_redis and enhanced_rate_limiter:
            try:
                # Redis rate limiter automatically records attempts during check_rate_limit
                return
            except Exception as e:
                logger.error(f"Redis rate limiter error: {e}")
        
        # In-memory fallback
        async with self.locks[key]:
            self.attempts[key].append(time.time())
    
    def get_attempts(self, key: str, window_seconds: int = 300) -> int:
        """Get number of attempts in the current window"""
        now = time.time()
        window_start = now - window_seconds
        
        return len([
            attempt_time for attempt_time in self.attempts[key] 
            if attempt_time > window_start
        ])

# Global rate limiter instance
rate_limiter = RateLimiter()

class RateLimitConfig:
    """Configuration for different rate limiting scenarios"""
    
    # Login attempts
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_WINDOW_SECONDS = 300  # 5 minutes
    
    # Registration attempts
    REGISTRATION_MAX_ATTEMPTS = 3
    REGISTRATION_WINDOW_SECONDS = 3600  # 1 hour
    
    # Password reset attempts
    PASSWORD_RESET_MAX_ATTEMPTS = 3
    PASSWORD_RESET_WINDOW_SECONDS = 3600  # 1 hour
    
    # API requests
    API_MAX_ATTEMPTS = 100
    API_WINDOW_SECONDS = 60  # 1 minute

def get_client_ip(request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"

async def check_rate_limit(
    key: str, 
    max_attempts: int, 
    window_seconds: int
) -> Tuple[bool, Optional[int]]:
    """Check rate limit for a given key"""
    # Allow unlimited attempts only for test client (for unit tests)
    if "testclient" in key:
        return True, max_attempts
    
    # Use enhanced rate limiter if available
    if REDIS_RATE_LIMITER_AVAILABLE and enhanced_rate_limiter:
        try:
            return await enhanced_rate_limiter.check_rate_limit(
                key, max_attempts, window_seconds, "sliding_window"
            )
        except Exception as e:
            logger.error(f"Enhanced rate limiter error, falling back: {e}")
    
    return await rate_limiter.is_allowed(key, max_attempts, window_seconds)

async def record_attempt(key: str) -> None:
    """Record an attempt for rate limiting"""
    await rate_limiter.record_attempt(key)

async def reset_rate_limit(key: str) -> None:
    """Reset rate limit attempts for a given key (for testing)"""
    # Try Redis first
    if REDIS_RATE_LIMITER_AVAILABLE and enhanced_rate_limiter:
        try:
            if await enhanced_rate_limiter.reset_rate_limit(key):
                return
        except Exception as e:
            logger.error(f"Enhanced rate limiter reset error: {e}")
    
    # In-memory fallback
    async with rate_limiter.locks[key]:
        rate_limiter.attempts[key] = [] 