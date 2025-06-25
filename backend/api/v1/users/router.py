
"""
User management router - handles all user-related endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from backend.api.v1.users.schemas import (
    UserCreate, 
    UserRead, 
    UserUpdate,
    UserListResponse,
    UserFilterParams,
    UserStatsResponse
)
from backend.api.v1.users.service import UserService
from backend.core.db.session import get_db
from backend.core.security import get_current_active_user, get_admin_user
from backend.core.response import ResponseHandler, APIResponse
from backend.core.exceptions import TradeSenseException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])
user_service = UserService()


@router.post("/", response_model=UserRead, summary="Create New User")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> UserRead:
    """
    Create a new user account (Admin only)
    
    - **username**: Unique username (alphanumeric only)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    - **role**: User role ("admin" or "trader")
    
    Returns the created user information
    """
    try:
        return await user_service.create_user(db, user_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Create user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=UserListResponse, summary="List Users")
async def list_users(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
    role: Optional[str] = Query(default=None, description="Filter by role (admin/trader)"),
    active_only: bool = Query(default=True, description="Show only active users"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> UserListResponse:
    """
    List all users with filtering options (Admin only)
    
    Supports pagination and filtering by role and active status
    """
    try:
        users = await user_service.get_users(
            db=db, 
            skip=skip, 
            limit=limit,
            role_filter=role,
            active_only=active_only
        )
        
        # Get total count for pagination
        from backend.models.user import User
        query = db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        if role:
            query = query.filter(User.role == role)
        total = query.count()
        
        return UserListResponse(
            users=users,
            total=total,
            skip=skip,
            limit=limit
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"List users endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=UserStatsResponse, summary="Get User Statistics")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> UserStatsResponse:
    """
    Get user statistics (Admin only)
    
    Returns counts of users by various categories
    """
    try:
        from backend.models.user import User
        
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        inactive_users = db.query(User).filter(User.is_active == False).count()
        admin_users = db.query(User).filter(User.role == "admin").count()
        trader_users = db.query(User).filter(User.role == "trader").count()
        
        return UserStatsResponse(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            admin_users=admin_users,
            trader_users=trader_users
        )
    except Exception as e:
        logger.error(f"User stats endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{user_id}", response_model=UserRead, summary="Get User by ID")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> UserRead:
    """
    Get user by ID (Admin only)
    
    Returns detailed user information
    """
    try:
        return await user_service.get_user_by_id(db, user_id)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{user_id}", response_model=UserRead, summary="Update User")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> UserRead:
    """
    Update user information (Admin only)
    
    Allows updating email, role, and active status
    """
    try:
        return await user_service.update_user(db, user_id, user_update)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Update user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{user_id}", response_model=APIResponse, summary="Deactivate User")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> APIResponse:
    """
    Soft delete user (deactivate) (Admin only)
    
    Sets user as inactive instead of permanent deletion
    """
    try:
        result = await user_service.soft_delete_user(db, user_id)
        return ResponseHandler.success(
            data=result,
            message="User deactivated successfully"
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{user_id}/activate", response_model=UserRead, summary="Activate User")
async def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)
) -> UserRead:
    """
    Activate user (Admin only)
    
    Reactivates a previously deactivated user
    """
    try:
        return await user_service.activate_user(db, user_id)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Activate user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/profile", response_model=UserRead, summary="Get My Profile")
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> UserRead:
    """
    Get current user's profile
    
    Any authenticated user can access their own profile
    """
    try:
        return await user_service.get_user_by_id(db, current_user["user_id"])
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get profile endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
