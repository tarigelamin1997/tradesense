"""
Authentication API Schemas

Pydantic models for authentication request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserRegistration(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    trading_experience: Optional[str] = Field(None, description="Trading experience level")
    preferred_markets: Optional[str] = Field(None, description="Preferred trading markets")
    timezone: Optional[str] = Field("UTC", description="User timezone")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @field_validator('trading_experience')
    @classmethod
    def validate_trading_experience(cls, v):
        if v and v not in ['beginner', 'intermediate', 'advanced', 'professional']:
            raise ValueError('Trading experience must be one of: beginner, intermediate, advanced, professional')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "trader@example.com",
                "username": "trader123",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "trading_experience": "intermediate",
                "preferred_markets": "stocks,forex",
                "timezone": "America/New_York"
            }
        }
    }

class UserLogin(BaseModel):
    """User login request schema"""
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, description="Username")
    password: str = Field(..., description="Password")

    @field_validator('password', mode='after')
    @classmethod
    def check_email_or_username(cls, v, info):
        email = info.data.get('email')
        username = info.data.get('username')
        if not email and not username:
            raise ValueError('Either email or username must be provided')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "trader@example.com",
                "username": "trader123",
                "password": "SecurePass123!"
            }
        }
    }

class UserResponse(BaseModel):
    """User response schema"""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    username: str = Field(..., description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    trading_experience: Optional[str] = Field(None, description="Trading experience level")
    preferred_markets: Optional[str] = Field(None, description="Preferred trading markets")
    timezone: str = Field(..., description="User timezone")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "user_123",
                "email": "trader@example.com",
                "username": "trader123",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": False,
                "trading_experience": "intermediate",
                "preferred_markets": "stocks,forex",
                "timezone": "America/New_York",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-01-15T09:30:00Z"
            }
        }
    }

class Token(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "user_123",
                    "email": "trader@example.com",
                    "username": "trader123",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "is_verified": False,
                    "trading_experience": "intermediate",
                    "preferred_markets": "stocks,forex",
                    "timezone": "America/New_York",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "last_login": "2024-01-15T09:30:00Z"
                }
            }
        }
    }

class UserUpdate(BaseModel):
    """User update request schema"""
    email: Optional[EmailStr] = Field(None, description="Email address")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    trading_experience: Optional[str] = Field(None, description="Trading experience level")
    preferred_markets: Optional[str] = Field(None, description="Preferred trading markets")
    timezone: Optional[str] = Field(None, description="User timezone")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @field_validator('trading_experience')
    @classmethod
    def validate_trading_experience(cls, v):
        if v and v not in ['beginner', 'intermediate', 'advanced', 'professional']:
            raise ValueError('Trading experience must be one of: beginner, intermediate, advanced, professional')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "trading_experience": "advanced",
                "preferred_markets": "stocks,options,forex",
                "timezone": "America/Chicago"
            }
        }
    }

class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="Email address for password reset")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "trader@example.com"
            }
        }
    }

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass123!"
            }
        }
    }

class ChangePassword(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass123!"
            }
        }
    }

class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str = Field(..., description="Response message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully"
            }
        }
    }
