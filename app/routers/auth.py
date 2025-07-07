
"""
Authentication Router
Handles user registration, login, and token management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from app.services.auth_service import AuthService
from app.models.user import UserCreate, UserLogin, UserResponse, Token

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

@router.post("/register", response_model=dict)
async def register_user(request: RegisterRequest):
    """Register a new user"""
    try:
        if request.password != request.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Passwords do not match"
            )
        
        user = await auth_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        
        logger.info(f"User registered: {request.username}")
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user.id
        }
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login_user(request: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        token = await auth_service.authenticate_user(
            username=request.username,
            password=request.password
        )
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        logger.info(f"User logged in: {request.username}")
        return token
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user profile"""
    try:
        user = await auth_service.get_user_from_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        logger.error(f"Get user failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and invalidate token"""
    try:
        await auth_service.invalidate_token(credentials.credentials)
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {"success": True, "message": "Logged out"}  # Always success for logout

@router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh JWT token"""
    try:
        new_token = await auth_service.refresh_token(credentials.credentials)
        return new_token
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")
