from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from backend.api.v1.users.schemas import (
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
import logging

from backend.api.deps import get_current_user
from backend.api.v1.users.schemas import (
    UserProfileResponse,
    UserProfileUpdate,
    TradingStatsResponse,
    Achievement,
    UserResponse
)
from backend.models.user import User, UserCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


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
        user_service = UserService(db)
        return await user_service.create_user(user_data)
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
        user_service = UserService(db)
        users = await user_service.get_users(
            db=db,
            skip=skip,
            limit=limit,
            role_filter=role,
            active_only=active_only
        )

        # Get total count for pagination
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
        user_service = UserService(db)
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
        user_service = UserService(db)
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
        user_service = UserService(db)
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
        user_service = UserService(db)
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
        user_service = UserService(db)
        return await user_service.activate_user(db, user_id)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Activate user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's complete profile with stats and achievements"""
    service = UserService(db)
    profile = service.get_user_profile(current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get any user's profile (public stats only if not own profile)"""
    service = UserService(db)
    profile = service.get_user_profile(user_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # If not viewing own profile, filter to public stats only
    if user_id != current_user.id and not profile["customization"]["show_public_stats"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profile is private"
        )

    return profile


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    service = UserService(db)
    success = service.update_user_profile(current_user.id, profile_update)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile"
        )

    # Return updated user info
    updated_user = db.query(User).filter(User.id == current_user.id).first()
    return updated_user


@router.get("/stats", response_model=TradingStatsResponse)
async def get_trading_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's trading statistics"""
    service = UserService(db)
    stats = service.get_trading_stats(current_user.id)
    return stats


@router.get("/achievements", response_model=List[Achievement])
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's achievements"""
    service = UserService(db)
    stats = service.get_trading_stats(current_user.id)
    achievements = service.get_user_achievements(current_user.id, stats)
    return achievements


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user's basic info"""
    return current_user