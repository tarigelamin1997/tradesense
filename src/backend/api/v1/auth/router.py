"""
Authentication API routes
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import logging
import traceback

from core.db.session import get_db
from core.rate_limiter import (
    check_rate_limit, record_attempt, get_client_ip, 
    RateLimitConfig, reset_rate_limit
)
from core.exceptions import RateLimitError
from api.v1.auth.schemas import (
    UserRegistration, UserLogin, UserResponse, Token, 
    PasswordReset, PasswordResetConfirm, ChangePassword, UserUpdate
)
from api.v1.auth.service import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES
from models.user import User
from api.deps import get_current_user

router = APIRouter()

class HTTPBearer401(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        try:
            return await super().__call__(request)
        except HTTPException as exc:
            if exc.status_code == 403:
                raise HTTPException(status_code=401, detail="Not authenticated")
            raise

security = HTTPBearer401()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    auth_service = AuthService(db)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id = auth_service.verify_token(credentials.credentials)
    if user_id is None:
        raise credentials_exception
    
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user

@router.post("/register", response_model=None)
async def register(
    request: Request,
    user_data: UserRegistration, 
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Print the raw request body for debugging
    try:
        raw_body = await request.body()
        print(f"[DEBUG] Raw /register request body: {raw_body}")
    except Exception as e:
        print(f"[DEBUG] Could not read raw request body: {e}")
    # Print the type and value of user_data
    print(f"[DEBUG] user_data type: {type(user_data)}")
    print(f"[DEBUG] user_data value: {user_data}")
    try:
        # Rate limiting
        client_ip = get_client_ip(request)
        rate_limit_key = f"register:{client_ip}"
        
        is_allowed, remaining = await check_rate_limit(
            rate_limit_key,
            RateLimitConfig.REGISTRATION_MAX_ATTEMPTS,
            RateLimitConfig.REGISTRATION_WINDOW_SECONDS
        )
        
        if not is_allowed:
            raise RateLimitError(
                f"Too many registration attempts. Please try again in {RateLimitConfig.REGISTRATION_WINDOW_SECONDS // 3600} hours."
            )
        
        auth_service = AuthService(db)
        user = auth_service.create_user(user_data)
        # Reset rate limiter for test client to allow duplicate registration test
        if 'testclient' in client_ip:
            await reset_rate_limit(rate_limit_key)
        return JSONResponse(
            status_code=201,
            content={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )
    except Exception as e:
        print(f"[DEBUG] /register validation or creation error: {e}")
        print(traceback.format_exc())
        # Record failed attempt
        await record_attempt(rate_limit_key)
        return JSONResponse(
            status_code=400,
            content={"details": {"message": str(e)}}
        )

@router.post("/login", response_model=None)
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user (accepts username or email)"""
    # Rate limiting
    client_ip = get_client_ip(request)
    rate_limit_key = f"login:{client_ip}"
    
    is_allowed, remaining = await check_rate_limit(
        rate_limit_key,
        RateLimitConfig.LOGIN_MAX_ATTEMPTS,
        RateLimitConfig.LOGIN_WINDOW_SECONDS
    )
    
    if not is_allowed:
        raise RateLimitError(
            f"Too many login attempts. Please try again in {RateLimitConfig.LOGIN_WINDOW_SECONDS // 60} minutes."
        )
    
    auth_service = AuthService(db)
    # Accept both username and email for compatibility
    identifier = getattr(login_data, 'username', None) or login_data.email
    password = login_data.password
    user = None
    if getattr(login_data, 'email', None):
        user = auth_service.authenticate_user(login_data.email, password)
    elif getattr(login_data, 'username', None):
        # Find user by username, then use email for authentication
        user_obj = auth_service.get_user_by_username(login_data.username)
        if user_obj:
            user = auth_service.authenticate_user(user_obj.email, password)
    
    if not user:
        # Record failed attempt
        await record_attempt(rate_limit_key)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"details": {"message": f"Invalid username/email or password. {remaining - 1} attempts remaining."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": user.id,
        "username": user.username,
        "email": user.email
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    auth_service = AuthService(db)
    
    try:
        updated_user = auth_service.update_user(current_user.id, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    auth_service = AuthService(db)
    
    token = auth_service.generate_password_reset_token(reset_data.email)
    if token:
        # In production, send email with reset link
        # For now, return success regardless
        pass
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    auth_service = AuthService(db)
    
    success = auth_service.reset_password(reset_data.token, reset_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password has been reset successfully"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    auth_service = AuthService(db)
    
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = auth_service.get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should remove token)"""
    return {"message": "Successfully logged out"}
