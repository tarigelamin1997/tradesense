
"""
Admin Router
Handles admin dashboard, user management, and system monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.services.admin_service import AdminService
from app.services.auth_service import get_current_user, require_admin

router = APIRouter()
admin_service = AdminService()
logger = logging.getLogger(__name__)

@router.get("/dashboard")
async def get_admin_dashboard(admin=Depends(require_admin)):
    """Get admin dashboard overview"""
    try:
        dashboard_data = await admin_service.get_dashboard_stats()
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Admin dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load admin dashboard")

@router.get("/users")
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    admin=Depends(require_admin)
):
    """Get paginated user list"""
    try:
        users = await admin_service.get_users(limit=limit, offset=offset)
        return {
            "success": True,
            "users": users,
            "pagination": {"limit": limit, "offset": offset}
        }
    except Exception as e:
        logger.error(f"Get users failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.get("/system-health")
async def get_system_health(admin=Depends(require_admin)):
    """Get system health metrics"""
    try:
        health_data = await admin_service.get_system_health()
        return {
            "success": True,
            "health": health_data
        }
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check system health")

@router.post("/users/{user_id}/disable")
async def disable_user(user_id: int, admin=Depends(require_admin)):
    """Disable user account"""
    try:
        success = await admin_service.disable_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User {user_id} disabled by admin {admin.id}")
        return {"success": True, "message": "User disabled"}
    except Exception as e:
        logger.error(f"Disable user failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to disable user")

@router.get("/analytics/usage")
async def get_usage_analytics(admin=Depends(require_admin)):
    """Get platform usage analytics"""
    try:
        analytics = await admin_service.get_usage_analytics()
        return {
            "success": True,
            "analytics": analytics
        }
    except Exception as e:
        logger.error(f"Usage analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage analytics")
