"""
Production-ready Redis caching implementation

Provides caching layer with automatic serialization, TTL management,
and cache invalidation strategies
"""

import os
import json
import pickle
import hashlib
from typing import Any, Optional, Union, List, Dict, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from contextlib import asynccontextmanager
import redis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError, ConnectionError
from pydantic import BaseModel
import msgpack

from core.config_env import get_env_config
from core.logging_config import get_logger
from core.monitoring_enhanced import tracer

logger = get_logger(__name__)

T = TypeVar('T')


class CacheConfig(BaseModel):
    """Redis cache configuration"""
    url: str
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    decode_responses: bool = False
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    # Cache settings
    default_ttl: int = 300  # 5 minutes
    max_ttl: int = 86400  # 24 hours
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    
    # Serialization
    serializer: str = "msgpack"  # msgpack, json, pickle
    
    # Cache key settings
    key_prefix: str = "ts:"
    namespace_separator: str = ":"


class CacheSerializer:
    """Handle different serialization formats"""
    
    @staticmethod
    def serialize(data: Any, format: str = "msgpack", compress: bool = False) -> bytes:
        """Serialize data to bytes"""
        if format == "msgpack":
            serialized = msgpack.packb(data, use_bin_type=True)
        elif format == "json":
            serialized = json.dumps(data).encode('utf-8')
        elif format == "pickle":
            serialized = pickle.dumps(data)
        else:
            raise ValueError(f"Unknown serialization format: {format}")
        
        if compress:
            import zlib
            serialized = zlib.compress(serialized)
        
        return serialized
    
    @staticmethod
    def deserialize(data: bytes, format: str = "msgpack", compressed: bool = False) -> Any:
        """Deserialize bytes to data"""
        if compressed:
            import zlib
            data = zlib.decompress(data)
        
        if format == "msgpack":
            return msgpack.unpackb(data, raw=False)
        elif format == "json":
            return json.loads(data.decode('utf-8'))
        elif format == "pickle":
            return pickle.loads(data)
        else:
            raise ValueError(f"Unknown serialization format: {format}")


class CacheKey:
    """Cache key builder with namespace support"""
    
    def __init__(self, prefix: str = "ts:", separator: str = ":"):
        self.prefix = prefix
        self.separator = separator
    
    def build(self, namespace: str, *parts: Any) -> str:
        """Build cache key from namespace and parts"""
        key_parts = [self.prefix, namespace]
        
        for part in parts:
            if isinstance(part, (dict, list)):
                # Hash complex objects
                part = hashlib.md5(str(part).encode()).hexdigest()[:8]
            key_parts.append(str(part))
        
        return self.separator.join(key_parts)
    
    def pattern(self, namespace: str, pattern: str = "*") -> str:
        """Build pattern for key matching"""
        return f"{self.prefix}{namespace}{self.separator}{pattern}"


class RedisCache:
    """Redis cache implementation with monitoring"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.serializer = CacheSerializer()
        self.key_builder = CacheKey(config.key_prefix, config.namespace_separator)
        
        # Connection pools
        self._sync_pool = None
        self._async_pool = None
        
        # Stats
        self._stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "evictions": 0
        }
    
    @property
    def sync_client(self) -> redis.Redis:
        """Get synchronous Redis client"""
        if not self._sync_pool:
            self._sync_pool = redis.ConnectionPool.from_url(
                self.config.url,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=self.config.decode_responses,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval
            )
        
        return redis.Redis(connection_pool=self._sync_pool)
    
    @property
    async def async_client(self) -> AsyncRedis:
        """Get asynchronous Redis client"""
        if not self._async_pool:
            self._async_pool = redis.asyncio.ConnectionPool.from_url(
                self.config.url,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                decode_responses=self.config.decode_responses,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval
            )
        
        return AsyncRedis(connection_pool=self._async_pool)
    
    def _should_compress(self, data: bytes) -> bool:
        """Check if data should be compressed"""
        return (
            self.config.enable_compression and 
            len(data) > self.config.compression_threshold
        )
    
    # Synchronous methods
    def get(self, namespace: str, key: Any, default: Any = None) -> Any:
        """Get value from cache"""
        cache_key = self.key_builder.build(namespace, key)
        
        try:
            with tracer.trace("redis.get", resource=namespace):
                data = self.sync_client.get(cache_key)
                
                if data is None:
                    self._stats["misses"] += 1
                    return default
                
                self._stats["hits"] += 1
                
                # Check if compressed (first byte is 0x78 for zlib)
                compressed = data[0] == 0x78 if data else False
                
                return self.serializer.deserialize(
                    data, 
                    self.config.serializer,
                    compressed
                )
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._stats["errors"] += 1
            return default
    
    def set(
        self, 
        namespace: str, 
        key: Any, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set value in cache"""
        cache_key = self.key_builder.build(namespace, key)
        ttl = ttl or self.config.default_ttl
        
        # Validate TTL
        ttl = min(ttl, self.config.max_ttl)
        
        try:
            with tracer.trace("redis.set", resource=namespace):
                data = self.serializer.serialize(value, self.config.serializer)
                
                # Compress if needed
                compressed = self._should_compress(data)
                if compressed:
                    import zlib
                    data = zlib.compress(data)
                
                return self.sync_client.set(
                    cache_key,
                    data,
                    ex=ttl,
                    nx=nx,
                    xx=xx
                )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._stats["errors"] += 1
            return False
    
    def delete(self, namespace: str, *keys: Any) -> int:
        """Delete keys from cache"""
        cache_keys = [self.key_builder.build(namespace, key) for key in keys]
        
        try:
            with tracer.trace("redis.delete", resource=namespace):
                return self.sync_client.delete(*cache_keys)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._stats["errors"] += 1
            return 0
    
    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        pattern = self.key_builder.pattern(namespace)
        
        try:
            with tracer.trace("redis.clear_namespace", resource=namespace):
                # Use SCAN to avoid blocking
                deleted = 0
                for key in self.sync_client.scan_iter(pattern, count=100):
                    self.sync_client.delete(key)
                    deleted += 1
                
                self._stats["evictions"] += deleted
                return deleted
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self._stats["errors"] += 1
            return 0
    
    # Asynchronous methods
    async def aget(self, namespace: str, key: Any, default: Any = None) -> Any:
        """Async get value from cache"""
        cache_key = self.key_builder.build(namespace, key)
        
        try:
            async with tracer.trace("redis.get", resource=namespace):
                client = await self.async_client
                data = await client.get(cache_key)
                
                if data is None:
                    self._stats["misses"] += 1
                    return default
                
                self._stats["hits"] += 1
                
                compressed = data[0] == 0x78 if data else False
                
                return self.serializer.deserialize(
                    data,
                    self.config.serializer,
                    compressed
                )
        except Exception as e:
            logger.error(f"Async cache get error: {e}")
            self._stats["errors"] += 1
            return default
    
    async def aset(
        self,
        namespace: str,
        key: Any,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Async set value in cache"""
        cache_key = self.key_builder.build(namespace, key)
        ttl = ttl or self.config.default_ttl
        ttl = min(ttl, self.config.max_ttl)
        
        try:
            async with tracer.trace("redis.set", resource=namespace):
                data = self.serializer.serialize(value, self.config.serializer)
                
                compressed = self._should_compress(data)
                if compressed:
                    import zlib
                    data = zlib.compress(data)
                
                client = await self.async_client
                return await client.set(
                    cache_key,
                    data,
                    ex=ttl,
                    nx=nx,
                    xx=xx
                )
        except Exception as e:
            logger.error(f"Async cache set error: {e}")
            self._stats["errors"] += 1
            return False
    
    # Decorator for caching
    def cached(
        self,
        namespace: str,
        ttl: Optional[int] = None,
        key_func: Optional[Callable] = None
    ):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key generation
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                result = await self.aget(namespace, cache_key)
                if result is not None:
                    return result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.aset(namespace, cache_key, result, ttl)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                result = self.get(namespace, cache_key)
                if result is not None:
                    return result
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache result
                self.set(namespace, cache_key, result, ttl)
                
                return result
            
            # Return appropriate wrapper
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        return {
            **self._stats,
            "hit_rate": hit_rate,
            "total_requests": total
        }
    
    async def close(self):
        """Close all connections"""
        if self._sync_pool:
            self._sync_pool.disconnect()
        
        if self._async_pool:
            await self._async_pool.disconnect()


# Cache strategies
class CacheStrategy:
    """Base cache strategy"""
    
    def should_cache(self, key: Any, value: Any) -> bool:
        """Determine if value should be cached"""
        return True
    
    def get_ttl(self, key: Any, value: Any) -> int:
        """Get TTL for cache entry"""
        return 300  # 5 minutes default


class SizeBasedCacheStrategy(CacheStrategy):
    """Cache based on data size"""
    
    def __init__(self, max_size: int = 1024 * 1024):  # 1MB
        self.max_size = max_size
    
    def should_cache(self, key: Any, value: Any) -> bool:
        """Only cache if size is reasonable"""
        try:
            size = len(json.dumps(value))
            return size <= self.max_size
        except:
            return True


class TimeBasedCacheStrategy(CacheStrategy):
    """Cache with time-based TTL"""
    
    def __init__(self, base_ttl: int = 300, peak_hours_ttl: int = 60):
        self.base_ttl = base_ttl
        self.peak_hours_ttl = peak_hours_ttl
        self.peak_hours = [(9, 17), (19, 22)]  # 9am-5pm, 7pm-10pm
    
    def get_ttl(self, key: Any, value: Any) -> int:
        """Get TTL based on current time"""
        current_hour = datetime.now().hour
        
        # Check if in peak hours
        for start, end in self.peak_hours:
            if start <= current_hour < end:
                return self.peak_hours_ttl
        
        return self.base_ttl


# Global cache instance
_cache: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get global cache instance"""
    global _cache
    
    if _cache is None:
        env_config = get_env_config()
        cache_config = CacheConfig(
            url=env_config.redis.url or "redis://localhost:6379/0",
            max_connections=env_config.redis.max_connections,
            default_ttl=env_config.cache.default_ttl_seconds,
            enable_compression=env_config.cache.compression
        )
        _cache = RedisCache(cache_config)
    
    return _cache


# Common cache namespaces
class CacheNamespace:
    """Common cache namespaces"""
    USER = "user"
    TRADE = "trade"
    ANALYTICS = "analytics"
    MARKET_DATA = "market"
    SESSION = "session"
    RATE_LIMIT = "ratelimit"
    FEATURE_FLAG = "feature"
    TEMP = "temp"