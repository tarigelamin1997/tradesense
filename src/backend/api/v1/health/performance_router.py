"""
Performance Monitoring Router

Provides endpoints for monitoring system performance, query statistics, and optimization metrics.
"""
from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
import logging
import time
import psutil
from sqlalchemy.orm import Session

from core.db.session import get_db, engine
from core.cache import cache_manager

logger = logging.getLogger(__name__)

router = APIRouter()

# Performance tracking
_request_times = {}

@router.get("/metrics")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        db_pool_size = engine.pool.size()
        db_checked_in = engine.pool.checkedin()
        db_checked_out = engine.pool.checkedout()
        
        # Cache metrics
        cache_stats = cache_manager.get_stats()
        
        # Request timing metrics
        avg_request_time = sum(_request_times.values()) / len(_request_times) if _request_times else 0
        
        return {
            "status": "success",
            "data": {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                "database": {
                    "pool_size": db_pool_size,
                    "checked_in": db_checked_in,
                    "checked_out": db_checked_out,
                    "overflow": db_pool_size - db_checked_in - db_checked_out
                },
                "cache": cache_stats,
                "requests": {
                    "total_requests": len(_request_times),
                    "avg_response_time_ms": round(avg_request_time * 1000, 2)
                }
            },
            "message": "Performance metrics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return {"error": "Failed to retrieve performance metrics"}

@router.get("/cache/stats")
async def get_cache_statistics():
    """Get cache statistics"""
    try:
        stats = cache_manager.get_stats()
        return {
            "status": "success",
            "data": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"error": "Failed to retrieve cache statistics"}

@router.post("/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        cache_manager.clear()
        return {
            "status": "success",
            "data": {"cleared": True},
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return {"error": "Failed to clear cache"}

@router.get("/database/health")
async def get_database_health(db: Session = Depends(get_db)):
    """Check database health and performance"""
    try:
        start_time = time.time()
        
        # Test database connection
        result = db.execute("SELECT 1").scalar()
        
        # Test query performance
        query_start = time.time()
        db.execute("SELECT COUNT(*) FROM trades LIMIT 1")
        query_time = time.time() - query_start
        
        total_time = time.time() - start_time
        
        return {
            "status": "success",
            "data": {
                "status": "healthy",
                "connection_test": result == 1,
                "query_performance_ms": round(query_time * 1000, 2),
                "total_response_time_ms": round(total_time * 1000, 2)
            },
            "message": "Database health check completed"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"error": "Database health check failed", "details": str(e)}

@router.get("/endpoints/performance")
async def get_endpoint_performance():
    """Get endpoint performance statistics"""
    try:
        # Calculate endpoint-specific metrics
        endpoint_stats = {}
        for endpoint, times in _request_times.items():
            if times:
                endpoint_stats[endpoint] = {
                    "avg_response_time_ms": round(sum(times) / len(times) * 1000, 2),
                    "min_response_time_ms": round(min(times) * 1000, 2),
                    "max_response_time_ms": round(max(times) * 1000, 2),
                    "request_count": len(times)
                }
        
        return {
            "status": "success",
            "data": endpoint_stats,
            "message": "Endpoint performance statistics retrieved"
        }
    except Exception as e:
        logger.error(f"Error getting endpoint performance: {e}")
        return {"error": "Failed to retrieve endpoint performance"}

def track_request_performance(request: Request, endpoint: str):
    """Track request performance for monitoring"""
    start_time = time.time()
    
    def track_response_time():
        response_time = time.time() - start_time
        if endpoint not in _request_times:
            _request_times[endpoint] = []
        _request_times[endpoint].append(response_time)
        
        # Keep only last 100 requests per endpoint
        if len(_request_times[endpoint]) > 100:
            _request_times[endpoint] = _request_times[endpoint][-100:]
    
    return track_response_time 