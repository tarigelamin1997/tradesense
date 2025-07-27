from fastapi import Depends, HTTPException, status, Cookie, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.db.session import get_db
from models.user import User
from typing import Dict, Any, Optional
import jwt
from core.config import settings

# Make auto_error=False to allow cookie auth fallback
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(
    request: Request,
    token_from_header: Optional[str] = Depends(oauth2_scheme),
    token_from_cookie: Optional[str] = Cookie(None, alias="auth-token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from cookie or bearer token
    Prefers cookie (more secure) but falls back to header for API compatibility
    """
    # Try cookie first (frontend uses this)
    token = token_from_cookie
    
    # Fallback to Authorization header (mobile/API clients)
    if not token and token_from_header:
        token = token_from_header
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        
        # Get user ID from token payload (support both 'sub' and 'user_id')
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        # Fetch user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

get_current_active_user = get_current_user


def get_admin_user(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure current user is an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Alias for backward compatibility
require_admin = get_admin_user


async def get_current_user_ws(websocket, token: str, db: Session) -> User:
    """
    Get current user from WebSocket connection
    """
    try:
        payload = verify_token(token)
        if not payload:
            await websocket.close(code=1008)
            return None
        
        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            await websocket.close(code=1008)
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=1008)
            return None
        
        return user
    except Exception:
        await websocket.close(code=1008)
        return None
