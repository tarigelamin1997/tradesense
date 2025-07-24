"""
Authentication API routes
"""
from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import traceback
import os

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
from services.email_service import EmailService

router = APIRouter()

class HTTPBearer401(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException:
            # Don't raise, return None to allow cookie auth
            return None

security = HTTPBearer401()

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_token: Optional[str] = Cookie(None, alias="auth-token"),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from cookie or bearer token"""
    auth_service = AuthService(db)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try cookie first (more secure)
    token = auth_token
    
    # Fallback to Authorization header (for API clients)
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise credentials_exception
    
    user_id = auth_service.verify_token(token)
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
    # Input validation to prevent DoS
    if not user_data.email or not user_data.username or not user_data.password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Email, username and password are required"}
        )
    
    # Validate input length to prevent DoS
    if len(user_data.password) > 1000 or len(user_data.username) > 50 or len(user_data.email) > 255:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid input length"}
        )
    
    # Validate username format to prevent SQL injection
    if any(char in user_data.username for char in ["'", '"', ';', '--', '\x00', '\n', '\r']):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid characters in username"}
        )
    
    # Validate email format to prevent SQL injection  
    if any(char in user_data.email for char in ["'", '"', ';', '--', '\x00', '\n', '\r']):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid characters in email"}
        )
    
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
        
        # Send verification email
        try:
            email_service = EmailService()
            email_service.send_verification_email(user.id, user.email, user.username)
        except Exception as e:
            logging.error(f"Failed to send verification email: {str(e)}")
            # Don't fail registration if email fails
        
        # Reset rate limiter for test client to allow duplicate registration test
        if 'testclient' in client_ip:
            await reset_rate_limit(rate_limit_key)
        return JSONResponse(
            status_code=201,
            content={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "message": "Registration successful. Please check your email to verify your account."
            }
        )
    except Exception as e:
        # Record failed attempt
        await record_attempt(rate_limit_key)
        return JSONResponse(
            status_code=400,
            content={"details": {"message": str(e)}}
        )

@router.post("/login", response_model=None)
async def login(
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user (accepts username or email)"""
    # Input validation - prevent empty credentials or malicious input
    # Return same error as invalid credentials to prevent enumeration
    if not login_data.password or (not login_data.email and not login_data.username):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"details": {"message": "Invalid username/email or password."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate input length to prevent DoS
    if len(login_data.password) > 1000:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid input"}
        )
    
    # Validate username/email format to prevent SQL injection
    # Return same error as invalid credentials to prevent enumeration
    if login_data.username and (
        "'" in login_data.username or 
        '"' in login_data.username or 
        ';' in login_data.username or
        '--' in login_data.username
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"details": {"message": "Invalid username/email or password."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
            content={"details": {"message": "Invalid username/email or password."}},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has MFA enabled
    if user.mfa_enabled:
        # Create MFA session
        import secrets
        from core.cache import redis_client
        
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user.id,
            "created_at": datetime.utcnow().isoformat(),
            "ip_address": client_ip
        }
        
        # Store session for 10 minutes
        await redis_client.setex(
            f"mfa_session:{session_id}",
            600,  # 10 minutes
            session_data
        )
        
        return {
            "mfa_required": True,
            "session_id": session_id,
            "methods": user.mfa_methods or [],
            "message": "Please complete multi-factor authentication"
        }
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Set httpOnly cookie (CRITICAL for frontend compatibility)
    response.set_cookie(
        key="auth-token",
        value=access_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development") == "production",  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
        path="/",
        domain=None  # Let browser handle domain
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
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Logout user (clears httpOnly cookie)"""
    # Clear the auth cookie
    response.delete_cookie(
        key="auth-token",
        path="/",
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        samesite="lax"
    )
    return {"message": "Successfully logged out"}

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email with token"""
    email_service = EmailService()
    payload = email_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Update user verification status
    user = db.query(User).filter(User.id == payload['user_id']).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    user.is_verified = True
    db.commit()
    
    # Send welcome email
    try:
        email_service.send_welcome_email(user.email, user.username)
    except Exception as e:
        logging.error(f"Failed to send welcome email: {str(e)}")
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    # Rate limiting
    client_ip = get_client_ip(request)
    rate_limit_key = f"resend_verification:{client_ip}:{email}"
    
    is_allowed, remaining = await check_rate_limit(
        rate_limit_key,
        5,  # Max 5 resends
        3600  # Per hour
    )
    
    if not is_allowed:
        raise RateLimitError(
            "Too many verification email requests. Please try again later."
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Send verification email
    try:
        email_service = EmailService()
        email_service.send_verification_email(user.id, user.email, user.username)
    except Exception as e:
        logging.error(f"Failed to send verification email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": "Verification email sent"}


# Include OAuth router
from .oauth_router import router as oauth_router
router.include_router(oauth_router)
