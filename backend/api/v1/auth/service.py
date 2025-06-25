
"""
Authentication service layer - handles all auth business logic
"""
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from backend.core.security import SecurityManager
from backend.core.exceptions import AuthenticationError, ValidationError, BusinessLogicError
from backend.api.v1.auth.schemas import LoginRequest, RegisterRequest, UserResponse, TokenResponse
from backend.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service handling login, registration, and user management"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
    
    async def authenticate_user(self, login_data: LoginRequest) -> TokenResponse:
        """Authenticate user and return token"""
        try:
            # For production, this would query a real database
            # Using mock authentication for now
            if login_data.username == "demo" and login_data.password == "demo123":
                user_data = {
                    "user_id": "demo_user_001",
                    "username": login_data.username,
                    "email": "demo@tradesense.com",
                    "role": "user"
                }
            else:
                # Mock authentication - in production, verify against database
                user_data = {
                    "user_id": f"user_{hash(login_data.username) % 10000}",
                    "username": login_data.username,
                    "email": f"{login_data.username}@example.com",
                    "role": "user"
                }
            
            # Create JWT token
            token_data = {
                "user_id": user_data["user_id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
            
            access_token = self.security_manager.create_access_token(token_data)
            
            # Create user response
            user_response = UserResponse(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            logger.info(f"User {login_data.username} authenticated successfully")
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.jwt_expiration_hours * 3600,
                user=user_response
            )
            
        except Exception as e:
            logger.error(f"Authentication failed for user {login_data.username}: {str(e)}")
            raise AuthenticationError("Invalid credentials")
    
    async def register_user(self, register_data: RegisterRequest) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # In production, check if user already exists
            # Hash password
            hashed_password = self.security_manager.hash_password(register_data.password)
            
            # Create user record (mock for now)
            user_id = f"user_{hash(register_data.username) % 10000}"
            
            logger.info(f"User {register_data.username} registered successfully")
            
            return {
                "user_id": user_id,
                "username": register_data.username,
                "email": register_data.email,
                "message": "Registration successful"
            }
            
        except Exception as e:
            logger.error(f"Registration failed for user {register_data.username}: {str(e)}")
            raise BusinessLogicError(f"Registration failed: {str(e)}")
    
    async def get_current_user_profile(self, user_data: Dict[str, Any]) -> UserResponse:
        """Get current user profile"""
        try:
            return UserResponse(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data.get("role", "user"),
                created_at=datetime.utcnow(),  # In production, get from database
                last_login=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            raise BusinessLogicError("Failed to retrieve user profile")
    
    async def refresh_token(self, current_user: Dict[str, Any]) -> TokenResponse:
        """Refresh user token"""
        try:
            # Create new token with updated expiration
            token_data = {
                "user_id": current_user["user_id"],
                "username": current_user["username"],
                "email": current_user["email"],
                "role": current_user.get("role", "user")
            }
            
            access_token = self.security_manager.create_access_token(token_data)
            
            user_response = UserResponse(
                user_id=current_user["user_id"],
                username=current_user["username"],
                email=current_user["email"],
                role=current_user.get("role", "user"),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            logger.info(f"Token refreshed for user {current_user['username']}")
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.jwt_expiration_hours * 3600,
                user=user_response
            )
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise AuthenticationError("Token refresh failed")
