
"""
User schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

# Re-export from models for API consistency
from backend.models.user import UserCreate, UserRead, UserUpdate


class UserListResponse(BaseModel):
    """Response schema for user listing"""
    users: List[UserRead] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "user_123",
                        "username": "trader1",
                        "email": "trader1@example.com",
                        "role": "trader",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }


class UserFilterParams(BaseModel):
    """Query parameters for user filtering"""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    role: Optional[str] = Field(default=None, description="Filter by role")
    active_only: bool = Field(default=True, description="Show only active users")
    
    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ["admin", "trader"]:
            raise ValueError('Role must be either "admin" or "trader"')
        return v


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")
    
    class Config:
        schema_extra = {
            "example": {
                "current_password": "oldpassword",
                "new_password": "newsecurepassword123"
            }
        }


class UserStatsResponse(BaseModel):
    """Response schema for user statistics"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    admin_users: int = Field(..., description="Number of admin users")
    trader_users: int = Field(..., description="Number of trader users")
    
    class Config:
        schema_extra = {
            "example": {
                "total_users": 150,
                "active_users": 142,
                "inactive_users": 8,
                "admin_users": 5,
                "trader_users": 145
            }
        }
