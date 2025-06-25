
"""
Authentication schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "trader123",
                "password": "securepassword"
            }
        }


class RegisterRequest(BaseModel):
    """Registration request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "username": "newtrader",
                "email": "trader@example.com",
                "password": "securepassword123"
            }
        }


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: "UserResponse" = Field(..., description="User information")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 2592000,
                "user": {
                    "user_id": "123",
                    "username": "trader123",
                    "email": "trader@example.com",
                    "role": "user",
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
        }


class UserResponse(BaseModel):
    """User response schema"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(default="user", description="User role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123",
                "username": "trader123",
                "email": "trader@example.com",
                "role": "user",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-15T10:30:00Z"
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword",
                "new_password": "newsecurepassword123"
            }
        }


# Forward reference resolution
TokenResponse.model_rebuild()
