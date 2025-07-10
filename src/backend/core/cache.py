"""
Caching system for API responses and database queries
"""
import time
import hashlib
import json
import logging
from typing import Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class CacheManager:
    """In-memory cache manager with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = 1000
        self._cleanup_interval = 300  # 5 minutes
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None
            
        cache_entry = self._cache[key]
        if time.time() > cache_entry['expires_at']:
            del self._cache[key]
            return None
            
        logger.debug(f"Cache hit for key: {key}")
        return cache_entry['value']
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL"""
        if len(self._cache) >= self._max_size:
            self._cleanup_expired()
            
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = sum(
            1 for entry in self._cache.values()
            if current_time <= entry['expires_at']
        )
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries,
            'max_size': self._max_size
        }

# Global cache instance
cache_manager = CacheManager()

def cache_response(ttl: int = 300, key_prefix: str = "api"):
    """Decorator to cache API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_key(key_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str) -> None:
    """Invalidate cache entries matching a pattern"""
    keys_to_delete = [
        key for key in cache_manager._cache.keys()
        if pattern in key
    ]
    for key in keys_to_delete:
        cache_manager.delete(key)
    
    if keys_to_delete:
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")

class QueryCache:
    """Database query result caching"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def cache_query(self, ttl: int = 60):
        """Decorator to cache database query results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                cache_key = f"query:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute query and cache result
                result = await func(*args, **kwargs)
                self.cache.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache entries for a specific user"""
        invalidate_cache_pattern(f"user:{user_id}")
    
    def invalidate_trade_cache(self, user_id: str) -> None:
        """Invalidate trade-related cache for a user"""
        invalidate_cache_pattern(f"trades:{user_id}")
        invalidate_cache_pattern(f"analytics:{user_id}")

# Global query cache instance
query_cache = QueryCache(cache_manager) 