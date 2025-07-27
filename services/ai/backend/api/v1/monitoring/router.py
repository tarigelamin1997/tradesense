"""
Comprehensive monitoring and observability endpoints

Provides health checks, metrics, logs, and system information
for monitoring the TradeSense application.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response, JSONResponse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import sys
import platform
import psutil

from sqlalchemy.orm import Session
from sqlalchemy import text

from core.db.session import get_db, engine, get_pool_status
from core.cache import cache_manager
from core.metrics import metrics_collector, CONTENT_TYPE_LATEST
from core.error_tracking import error_tracker, error_analyzer
from core.logging_config import get_logger
from core.performance_optimizer import performance_monitor
from api.deps import get_current_user

logger = get_logger(__name__)

router = APIRouter(tags=["monitoring"])

# Health Check Endpoints
@router.get("/health")
async def health_check():
    """Basic health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tradesense-backend",
        "version": "2.0.0"
    }

@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe - checks if service is alive"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """Kubernetes readiness probe - checks if service is ready to serve traffic"""
    checks = {
        "database": False,
        "cache": False,
        "disk_space": False
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except:
        pass
    
    # Check cache
    try:
        cache_manager.set("health_check", "ok", ttl=5)
        if cache_manager.get("health_check") == "ok":
            checks["cache"] = True
    except:
        pass
    
    # Check disk space
    try:
        disk = psutil.disk_usage('/')
        if disk.percent < 90:  # Less than 90% used
            checks["disk_space"] = True
    except:
        checks["disk_space"] = True  # Don't fail if can't check
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/detailed")
async def detailed_health(db: Session = Depends(get_db)):
    """Comprehensive health check with all subsystems"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "subsystems": {}
    }
    
    # Database health
    try:
        result = db.execute(text("SELECT version()"))
        db_version = result.scalar()
        pool_status = get_pool_status()
        
        health_status["subsystems"]["database"] = {
            "status": "healthy",
            "version": db_version,
            "pool": pool_status
        }
    except Exception as e:
        health_status["subsystems"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Cache health
    try:
        cache_stats = cache_manager.get_stats()
        health_status["subsystems"]["cache"] = {
            "status": "healthy",
            "stats": cache_stats
        }
    except Exception as e:
        health_status["subsystems"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # System resources
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["subsystems"]["system"] = {
            "status": "healthy",
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": disk.percent
            }
        }
        
        # Set status based on resource usage
        if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
            health_status["subsystems"]["system"]["status"] = "warning"
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
                
    except Exception as e:
        health_status["subsystems"]["system"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # Error tracking health
    try:
        error_stats = error_tracker.get_error_stats()
        error_health = error_analyzer._calculate_error_health(error_stats, {})
        
        health_status["subsystems"]["error_tracking"] = {
            "status": error_health,
            "total_errors": error_stats["total_errors"],
            "sentry_enabled": error_stats["sentry_enabled"]
        }
    except Exception as e:
        health_status["subsystems"]["error_tracking"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    return health_status

# Metrics Endpoints
@router.get("/metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    """Prometheus-compatible metrics endpoint"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    metrics_data = metrics_collector.get_metrics()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST if CONTENT_TYPE_LATEST else "text/plain"
    )

@router.get("/metrics/custom")
async def get_custom_metrics(current_user: dict = Depends(get_current_user)):
    """Get custom application metrics"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Collect current metrics
    metrics_collector.collect_system_metrics()
    
    # Get performance stats
    perf_stats = performance_monitor.get_all_stats()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "performance": perf_stats,
        "cache": cache_manager.get_stats(),
        "database": get_pool_status(),
        "errors": error_tracker.get_error_stats()
    }

# Logging Endpoints
@router.get("/logs/recent")
async def get_recent_logs(
    level: Optional[str] = Query("INFO", description="Minimum log level"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get recent application logs"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # This would typically read from a centralized logging system
    # For now, return a placeholder
    return {
        "logs": [],
        "message": "Log aggregation not yet implemented"
    }

# Error Tracking Endpoints
@router.get("/errors/recent")
async def get_recent_errors(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get recent errors from error tracking"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    recent_errors = error_tracker.get_recent_errors(limit=limit)
    error_summary = error_analyzer.get_error_summary()
    
    return {
        "recent_errors": recent_errors,
        "summary": error_summary
    }

@router.get("/errors/trends")
async def get_error_trends(
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(get_current_user)
):
    """Get error trends over time"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    trends = error_analyzer.get_error_trends(hours=hours)
    
    return {
        "period_hours": hours,
        "trends": trends
    }

# System Information Endpoints
@router.get("/system/info")
async def get_system_info(current_user: dict = Depends(get_current_user)):
    """Get detailed system information"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get process info
    process = psutil.Process()
    
    system_info = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        },
        "process": {
            "pid": process.pid,
            "status": process.status(),
            "cpu_percent": process.cpu_percent(),
            "memory_info": {
                "rss_mb": round(process.memory_info().rss / (1024**2), 2),
                "vms_mb": round(process.memory_info().vms / (1024**2), 2),
                "percent": process.memory_percent()
            },
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        },
        "resources": {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": dict(psutil.virtual_memory()._asdict()),
            "disk": dict(psutil.disk_usage('/')._asdict()),
            "network": dict(psutil.net_io_counters()._asdict())
        }
    }
    
    return system_info

@router.get("/system/dependencies")
async def get_dependencies(current_user: dict = Depends(get_current_user)):
    """Get system dependencies and versions"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import pkg_resources
    
    dependencies = {}
    for dist in pkg_resources.working_set:
        dependencies[dist.key] = dist.version
    
    return {
        "python_version": sys.version,
        "dependencies": dependencies
    }

# Performance Monitoring Endpoints
@router.get("/performance/endpoints")
async def get_endpoint_performance(current_user: dict = Depends(get_current_user)):
    """Get performance statistics for API endpoints"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = performance_monitor.get_all_stats()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": stats
    }

@router.get("/performance/slow-queries")
async def get_slow_queries(
    threshold_ms: int = Query(1000, description="Threshold in milliseconds"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get slow database queries"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # This would typically query a slow query log
    # For now, return a placeholder
    return {
        "threshold_ms": threshold_ms,
        "slow_queries": [],
        "message": "Slow query logging not yet implemented"
    }

# Debugging Endpoints (only in development)
@router.get("/debug/config")
async def get_debug_config(current_user: dict = Depends(get_current_user)):
    """Get current configuration (sanitized)"""
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=404, detail="Not found")
    
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get sanitized config
    from core.config import settings
    
    config = {}
    for key in dir(settings):
        if not key.startswith('_'):
            value = getattr(settings, key)
            # Sanitize sensitive values
            if any(sensitive in key.lower() for sensitive in ['secret', 'password', 'key', 'token']):
                config[key] = '[REDACTED]'
            else:
                config[key] = str(value)
    
    return config