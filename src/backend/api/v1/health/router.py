"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import os
from core.db.session import get_db
from sqlalchemy.orm import Session

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