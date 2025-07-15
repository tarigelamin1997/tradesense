"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import os
from core.db.session import get_db, engine
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.cache import cache_manager

# Try to import psutil, but make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.6.1"
    }


@router.get("/health/detailed")
async def health_detailed(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
    
    # Get system info if psutil is available
    if PSUTIL_AVAILABLE:
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            system_info = {
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "cpu_usage": psutil.cpu_percent(interval=1)
            }
        except Exception:
            system_info = {
                "memory_usage": "N/A",
                "disk_usage": "N/A", 
                "cpu_usage": "N/A"
            }
    else:
        system_info = {
            "memory_usage": "N/A",
            "disk_usage": "N/A",
            "cpu_usage": "N/A"
        }
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.6.1",
        "database": {
            "status": db_status
        },
        "system": system_info,
        "uptime": "N/A"  # Could implement actual uptime tracking
    }


@router.get("/health/ready")
async def readiness_probe():
    """Readiness probe for Kubernetes deployments"""
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/version")
async def get_version():
    """Get application version information"""
    return {
        "data": {
            "version": "2.6.1",
            "build_time": datetime.utcnow().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "message": "Version information retrieved successfully"
    }


@router.get("/health/db")
async def database_health():
    """Check database connection pool health"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        pool = engine.pool
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "checked_out_connections": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.total(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/cache-stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        stats = cache_manager.get_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }