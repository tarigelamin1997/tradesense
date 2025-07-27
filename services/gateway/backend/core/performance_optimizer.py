"""
API Performance Optimization Module

Provides utilities for optimizing API performance including:
- Query optimization
- Response compression
- Rate limiting
- Connection pooling monitoring
"""

import time
import gzip
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
import asyncio

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from core.cache import cache_manager, cache_response
from core.db.session import engine, get_pool_status

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor and log API performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.slow_query_threshold = 1.0  # 1 second
        self.request_times: Dict[str, List[float]] = {}
        
    def record_request_time(self, endpoint: str, duration: float):
        """Record API request duration"""
        if endpoint not in self.request_times:
            self.request_times[endpoint] = []
        
        self.request_times[endpoint].append(duration)
        
        # Keep only last 1000 entries per endpoint
        if len(self.request_times[endpoint]) > 1000:
            self.request_times[endpoint] = self.request_times[endpoint][-1000:]
        
        # Log slow requests
        if duration > self.slow_query_threshold:
            logger.warning(f"Slow request detected: {endpoint} took {duration:.2f}s")
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, float]:
        """Get performance statistics for an endpoint"""
        if endpoint not in self.request_times:
            return {}
        
        times = self.request_times[endpoint]
        if not times:
            return {}
        
        return {
            "count": len(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "p50": sorted(times)[len(times) // 2],
            "p95": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
            "p99": sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times)
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all endpoints"""
        return {
            endpoint: self.get_endpoint_stats(endpoint)
            for endpoint in self.request_times
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def track_performance(func: Callable) -> Callable:
    """Decorator to track API endpoint performance"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint_name = f"{func.__module__}.{func.__name__}"
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            performance_monitor.record_request_time(endpoint_name, duration)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint_name = f"{func.__module__}.{func.__name__}"
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            performance_monitor.record_request_time(endpoint_name, duration)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

class ResponseCompressor:
    """Compress API responses for better network performance"""
    
    @staticmethod
    def should_compress(content: bytes, content_type: str) -> bool:
        """Determine if response should be compressed"""
        # Don't compress if too small
        if len(content) < 1000:  # Less than 1KB
            return False
        
        # Only compress JSON and text responses
        compressible_types = ['application/json', 'text/plain', 'text/html']
        return any(ct in content_type for ct in compressible_types)
    
    @staticmethod
    def compress_response(content: bytes) -> bytes:
        """Compress response content using gzip"""
        return gzip.compress(content, compresslevel=6)

async def compression_middleware(request: Request, call_next):
    """Middleware to compress responses when beneficial"""
    response = await call_next(request)
    
    # Check if client accepts gzip
    accept_encoding = request.headers.get('accept-encoding', '')
    if 'gzip' not in accept_encoding:
        return response
    
    # For streaming responses, we can't compress
    if hasattr(response, 'body_iterator'):
        return response
    
    # Get response body
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    
    # Check if we should compress
    content_type = response.headers.get('content-type', 'text/plain')
    if ResponseCompressor.should_compress(body, content_type):
        compressed_body = ResponseCompressor.compress_response(body)
        
        # Only use compressed if it's actually smaller
        if len(compressed_body) < len(body):
            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    'content-encoding': 'gzip',
                    'content-length': str(len(compressed_body))
                }
            )
    
    # Return original response
    return Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers)
    )

class QueryOptimizer:
    """Optimize database queries for better performance"""
    
    @staticmethod
    def add_query_hints(query, hints: Dict[str, Any]):
        """Add performance hints to SQLAlchemy queries"""
        # Example: query.execution_options(synchronize_session=False)
        if hints.get('no_autoflush'):
            query = query.execution_options(no_autoflush=True)
        if hints.get('synchronize_session') is False:
            query = query.execution_options(synchronize_session=False)
        return query
    
    @staticmethod
    def optimize_bulk_insert(session: Session, objects: List[Any], batch_size: int = 1000):
        """Optimize bulk insert operations"""
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            session.bulk_insert_mappings(type(batch[0]), [obj.__dict__ for obj in batch])
            session.flush()
    
    @staticmethod
    def optimize_pagination(query, page: int, per_page: int = 20):
        """Optimize pagination queries"""
        # Use LIMIT and OFFSET efficiently
        return query.limit(per_page).offset((page - 1) * per_page)

# Database query monitoring
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    conn.info.setdefault('query_start_time', []).append(time.time())
    
@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time"""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.5:  # Log queries taking more than 500ms
        logger.warning(f"Slow query ({total:.2f}s): {statement[:100]}...")

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit"""
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < window_seconds
        ]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_reset_time(self, key: str, window_seconds: int) -> int:
        """Get time until rate limit resets"""
        if key not in self.requests or not self.requests[key]:
            return 0
        
        oldest_request = min(self.requests[key])
        reset_time = oldest_request + window_seconds
        return max(0, int(reset_time - time.time()))

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator to rate limit API endpoints"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(request: Request, *args, **kwargs):
            # Use IP address as rate limit key
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"{client_ip}:{request.url.path}"
            
            if not rate_limiter.is_allowed(rate_key, max_requests, window_seconds):
                reset_time = rate_limiter.get_reset_time(rate_key, window_seconds)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": reset_time
                    },
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time)
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return async_wrapper
    return decorator

def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics"""
    return {
        "api_performance": performance_monitor.get_all_stats(),
        "database_pool": get_pool_status(),
        "cache_stats": cache_manager.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Preload commonly used data on startup
async def preload_cache():
    """Preload frequently accessed data into cache"""
    logger.info("Preloading cache with common data...")
    
    # This would be called on application startup
    # Example: preload user preferences, common lookups, etc.
    
def optimize_json_response(data: Any) -> JSONResponse:
    """Optimize JSON responses for better performance"""
    # Use orjson for faster JSON serialization if available
    try:
        import orjson
        content = orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS)
        return JSONResponse(content=content, media_type="application/json")
    except ImportError:
        # Fall back to standard json
        return JSONResponse(content=data)