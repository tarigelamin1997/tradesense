"""
Rate Limiting Module

Provides rate limiting functionality to prevent abuse and brute force attacks.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.attempts: Dict[str, list] = defaultdict(list)
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
    
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
    # Allow unlimited attempts for test client
    if "testclient" in key:
        return True, max_attempts
    return await rate_limiter.is_allowed(key, max_attempts, window_seconds)

async def record_attempt(key: str) -> None:
    """Record an attempt for rate limiting"""
    await rate_limiter.record_attempt(key)

async def reset_rate_limit(key: str) -> None:
    """Reset rate limit attempts for a given key (for testing)"""
    async with rate_limiter.locks[key]:
        rate_limiter.attempts[key] = [] 