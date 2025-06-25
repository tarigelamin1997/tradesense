
"""
Health check and system status endpoints
"""
from fastapi import APIRouter
from datetime import datetime
import sys
import platform
import logging

from backend.core.response import ResponseHandler, APIResponse
from backend.core.config import settings
from backend.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=APIResponse, summary="Basic Health Check")
async def health_check() -> APIResponse:
    """
    Basic health check endpoint
    
    Returns service status and timestamp
    """
    try:
        db_healthy = DatabaseManager.health_check()
        status = "healthy" if db_healthy else "degraded"
        
        return ResponseHandler.success(
            data={
                "status": status,
                "service": settings.app_name,
                "version": settings.version,
                "database": "healthy" if db_healthy else "unhealthy",
                "timestamp": datetime.utcnow()
            },
            message=f"Service is {status}"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return ResponseHandler.error(
            error="HealthCheckError",
            message="Health check failed"
        )


@router.get("/health/detailed", response_model=APIResponse, summary="Detailed Health Check")
async def detailed_health_check() -> APIResponse:
    """
    Detailed health check with system information
    
    Returns comprehensive system status and metrics
    """
    try:
        db_stats = DatabaseManager.get_stats()
        
        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "cpu_count": platform.machine(),
            "architecture": platform.architecture()[0]
        }
        
        return ResponseHandler.success(
            data={
                "status": "healthy",
                "service": settings.app_name,
                "version": settings.version,
                "database": db_stats,
                "system": system_info,
                "configuration": {
                    "debug": settings.debug,
                    "cors_origins": len(settings.allowed_origins),
                    "max_file_size": settings.max_file_size
                },
                "timestamp": datetime.utcnow()
            },
            message="Detailed health check completed"
        )
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return ResponseHandler.error(
            error="DetailedHealthCheckError",
            message="Detailed health check failed"
        )


@router.get("/status", response_model=APIResponse, summary="Service Status")
async def service_status() -> APIResponse:
    """
    Service status endpoint
    
    Returns current service status and uptime information
    """
    try:
        return ResponseHandler.success(
            data={
                "service": settings.app_name,
                "version": settings.version,
                "status": "running",
                "timestamp": datetime.utcnow(),
                "uptime": "Service running"  # In production, calculate actual uptime
            },
            message="Service is running normally"
        )
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return ResponseHandler.error(
            error="StatusCheckError",
            message="Status check failed"
        )


@router.get("/version", response_model=APIResponse, summary="API Version")
async def get_version() -> APIResponse:
    """
    Get API version information
    
    Returns version and build information
    """
    try:
        return ResponseHandler.success(
            data={
                "name": settings.app_name,
                "version": settings.version,
                "description": settings.description,
                "api_version": "v1",
                "build_date": datetime.utcnow().isoformat()
            },
            message="Version information retrieved"
        )
    except Exception as e:
        logger.error(f"Version endpoint failed: {str(e)}")
        return ResponseHandler.error(
            error="VersionError",
            message="Failed to retrieve version information"
        )
