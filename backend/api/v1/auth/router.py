
"""
Authentication router - handles all auth endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from backend.api.v1.auth.schemas import (
    LoginRequest, 
    RegisterRequest, 
    TokenResponse, 
    UserResponse
)
from backend.api.v1.auth.service import AuthService
from backend.core.security import get_current_active_user
from backend.core.response import ResponseHandler, APIResponse
from backend.core.exceptions import TradeSenseException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/login", response_model=TokenResponse, summary="User Login")
async def login(login_data: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return access token
    
    - **username**: User's username
    - **password**: User's password
    
    Returns JWT token and user information
    """
    try:
        return await auth_service.authenticate_user(login_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/register", response_model=APIResponse, summary="User Registration")
async def register(register_data: RegisterRequest) -> APIResponse:
    """
    Register a new user account
    
    - **username**: Desired username (alphanumeric only)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    
    Returns registration confirmation
    """
    try:
        result = await auth_service.register_user(register_data)
        return ResponseHandler.success(
            data=result,
            message="User registered successfully"
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Registration endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=UserResponse, summary="Get Current User")
async def get_current_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current authenticated user's profile
    
    Requires valid JWT token in Authorization header
    """
    try:
        return await auth_service.get_current_user_profile(current_user)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get current user endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=TokenResponse, summary="Refresh Token")
async def refresh_token(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TokenResponse:
    """
    Refresh JWT access token
    
    Returns new token with extended expiration
    """
    try:
        return await auth_service.refresh_token(current_user)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Token refresh endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout", response_model=APIResponse, summary="User Logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Logout user (client-side token invalidation)
    
    Note: JWT tokens are stateless, so logout is handled client-side
    """
    try:
        logger.info(f"User {current_user['username']} logged out")
        return ResponseHandler.success(
            message="Logged out successfully"
        )
    except Exception as e:
        logger.error(f"Logout endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
