"""
Caching system for API responses and database queries

Enhanced with Redis support for distributed caching while maintaining
in-memory fallback for development environments.
"""
import time
import hashlib
import json
import logging
import os
from typing import Any, Optional, Dict, List, Union
from functools import wraps
from datetime import datetime, timedelta
import asyncio

try:
    import redis
    from fakeredis import FakeRedis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheManager:
    """Hybrid cache manager with Redis and in-memory fallback"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = 1000
        self._cleanup_interval = 300  # 5 minutes
        self._redis_client = None
        self._use_redis = False
        
        # Initialize Redis if available
        if REDIS_AVAILABLE:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            # Try to get Redis URL from environment or config
            # Railway provides REDIS_URL or sometimes REDIS_PRIVATE_URL
            redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_PRIVATE_URL")
            
            # Only use localhost in development
            if not redis_url:
                if os.getenv("ENVIRONMENT") == "production":
                    logger.warning("No Redis URL configured in production - caching disabled")
                    return
                else:
                    redis_url = "redis://localhost:6379/0"
            
            # Try real Redis first
            try:
                self._redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1
                )
                # Test connection
                self._redis_client.ping()
                self._use_redis = True
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                # Fallback to FakeRedis for development
                logger.warning(f"Failed to connect to Redis: {e}. Using FakeRedis.")
                self._redis_client = FakeRedis(decode_responses=True)
                self._use_redis = True
                
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}. Using in-memory cache.")
            self._use_redis = False
        
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if self._use_redis:
            try:
                value = self._redis_client.get(key)
                if value:
                    logger.debug(f"Redis cache hit for key: {key}")
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                # Fall through to in-memory cache
        
        # In-memory fallback
        if key not in self._cache:
            return None
            
        cache_entry = self._cache[key]
        if time.time() > cache_entry['expires_at']:
            del self._cache[key]
            return None
            
        logger.debug(f"Memory cache hit for key: {key}")
        return cache_entry['value']
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL"""
        if self._use_redis:
            try:
                self._redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)  # Handle datetime serialization
                )
                logger.debug(f"Redis cache set for key: {key} with TTL: {ttl}s")
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                # Fall through to in-memory cache
        
        # In-memory cache (always set for fallback)
        if len(self._cache) >= self._max_size:
            self._cleanup_expired()
            
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        logger.debug(f"Memory cache set for key: {key} with TTL: {ttl}s")
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if self._use_redis:
            try:
                self._redis_client.delete(key)
                logger.debug(f"Redis cache deleted for key: {key}")
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        # Always delete from in-memory cache too
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Memory cache deleted for key: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        if self._use_redis:
            try:
                self._redis_client.flushdb()
                logger.info("Redis cache cleared")
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        self._cache.clear()
        logger.info("Memory cache cleared")
    
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
        stats = {}
        
        # Redis stats
        if self._use_redis:
            try:
                if isinstance(self._redis_client, FakeRedis):
                    stats['redis'] = {
                        'type': 'FakeRedis',
                        'connected': True,
                        'message': 'Using in-memory Redis for testing'
                    }
                else:
                    info = self._redis_client.info()
                    stats['redis'] = {
                        'type': 'Redis',
                        'connected': True,
                        'used_memory': info.get('used_memory_human'),
                        'connected_clients': info.get('connected_clients'),
                        'total_commands': info.get('total_commands_processed'),
                        'keyspace_hits': info.get('keyspace_hits', 0),
                        'keyspace_misses': info.get('keyspace_misses', 0),
                        'hit_rate': self._calculate_hit_rate(info)
                    }
            except Exception as e:
                stats['redis'] = {'connected': False, 'error': str(e)}
        else:
            stats['redis'] = {'connected': False, 'message': 'Redis not configured'}
        
        # In-memory stats
        current_time = time.time()
        active_entries = sum(
            1 for entry in self._cache.values()
            if current_time <= entry['expires_at']
        )
        
        stats['memory'] = {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': len(self._cache) - active_entries,
            'max_size': self._max_size
        }
        
        return stats
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        return round((hits / total * 100), 2) if total > 0 else 0.0

# Global cache instance
cache_manager = CacheManager()

def cache_response(ttl: Union[int, timedelta] = 300, key_prefix: str = "api", user_aware: bool = False):
    """
    Decorator to cache API responses
    
    Args:
        ttl: Cache expiration in seconds or timedelta
        key_prefix: Prefix for cache keys
        user_aware: If True, includes user_id in cache key
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract user_id if user_aware
            user_id = None
            if user_aware:
                # Try to find user_id in kwargs or args
                user_id = kwargs.get('user_id')
                if not user_id and args:
                    # Check if first arg has user_id attribute
                    if hasattr(args[0], 'user_id'):
                        user_id = args[0].user_id
                    elif hasattr(args[0], 'id'):
                        user_id = args[0].id
            
            # Generate cache key
            if user_id and user_aware:
                cache_key = f"{key_prefix}:user_{user_id}:{cache_manager._generate_key('', *args[1:], **kwargs)}"
            else:
                cache_key = cache_manager._generate_key(key_prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Calculate expiration
            exp_seconds = ttl.total_seconds() if isinstance(ttl, timedelta) else ttl
            cache_manager.set(cache_key, result, int(exp_seconds))
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic for sync functions
            user_id = None
            if user_aware:
                user_id = kwargs.get('user_id')
                if not user_id and args:
                    if hasattr(args[0], 'user_id'):
                        user_id = args[0].user_id
                    elif hasattr(args[0], 'id'):
                        user_id = args[0].id
            
            if user_id and user_aware:
                cache_key = f"{key_prefix}:user_{user_id}:{cache_manager._generate_key('', *args[1:], **kwargs)}"
            else:
                cache_key = cache_manager._generate_key(key_prefix, *args, **kwargs)
            
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            exp_seconds = ttl.total_seconds() if isinstance(ttl, timedelta) else ttl
            cache_manager.set(cache_key, result, int(exp_seconds))
            
            return result
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def invalidate_cache_pattern(pattern: str) -> None:
    """Invalidate cache entries matching a pattern"""
    deleted_count = 0
    
    # Invalidate Redis cache
    if cache_manager._use_redis:
        try:
            # Redis supports pattern matching with wildcards
            redis_pattern = f"*{pattern}*" if '*' not in pattern else pattern
            keys = list(cache_manager._redis_client.scan_iter(match=redis_pattern))
            for key in keys:
                cache_manager._redis_client.delete(key)
            deleted_count += len(keys)
        except Exception as e:
            logger.error(f"Redis pattern invalidation error: {e}")
    
    # Invalidate in-memory cache
    keys_to_delete = [
        key for key in cache_manager._cache.keys()
        if pattern in key
    ]
    for key in keys_to_delete:
        del cache_manager._cache[key]
    deleted_count += len(keys_to_delete)
    
    if deleted_count > 0:
        logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")

def invalidate_user_cache(user_id: int, cache_type: Optional[str] = None):
    """Invalidate cache for a specific user"""
    if cache_type:
        pattern = f"{cache_type}:user_{user_id}"
    else:
        pattern = f"user_{user_id}"
    
    invalidate_cache_pattern(pattern)
    logger.info(f"Invalidated cache for user {user_id}, type: {cache_type or 'all'}")

def invalidate_analytics_cache(user_id: Optional[int] = None):
    """Invalidate analytics cache"""
    if user_id:
        invalidate_cache_pattern(f"analytics:user_{user_id}")
    else:
        invalidate_cache_pattern("analytics:")

def invalidate_trades_cache(user_id: Optional[int] = None):
    """Invalidate trades cache"""
    if user_id:
        invalidate_cache_pattern(f"trades:user_{user_id}")
    else:
        invalidate_cache_pattern("trades:")

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

# Export redis_client for backward compatibility
redis_client = cache_manager._redis_client if cache_manager._redis_client else None 