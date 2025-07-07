
"""
Authentication Service
Handles JWT tokens, password hashing, and user management
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.settings import settings
from app.models.user import User, UserCreate, Token
from app.services.database_service import DatabaseService

security = HTTPBearer()
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.db = DatabaseService()
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    async def create_user(self, username: str, email: str, password: str) -> User:
        """Create new user with hashed password"""
        # Check if user exists
        existing_user = await self.db.get_user_by_username(username)
        if existing_user:
            raise ValueError("Username already exists")
        
        existing_email = await self.db.get_user_by_email(email)
        if existing_email:
            raise ValueError("Email already exists")
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password.decode('utf-8'),
            "created_at": datetime.now(),
            "is_active": True
        }
        
        user = await self.db.create_user(user_data)
        logger.info(f"User created: {username}")
        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[Token]:
        """Authenticate user and return JWT token"""
        user = await self.db.get_user_by_username(username)
        if not user:
            return None
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            return None
        
        # Generate JWT token
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )

    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def get_user_from_token(self, token: str) -> Optional[User]:
        """Decode JWT token and return user"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            
            user = await self.db.get_user_by_username(username)
            return user
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.JWTError:
            logger.warning("Invalid token")
            return None

    async def invalidate_token(self, token: str):
        """Add token to blacklist (implement if needed)"""
        # For now, tokens expire naturally
        # In production, implement token blacklisting
        pass

    async def refresh_token(self, token: str) -> Optional[Token]:
        """Refresh JWT token"""
        user = await self.get_user_from_token(token)
        if not user:
            return None
        
        # Generate new token
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    auth_service = AuthService()
    user = await auth_service.get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user

async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
