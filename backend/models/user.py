from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="trader", index=True)  # "admin" or "trader"
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_role_active', 'role', 'is_active'),
        Index('idx_user_email_active', 'email', 'is_active'),
    )

    # Relationships
    trades = relationship("Trade", back_populates="user")
    playbooks = relationship("Playbook", back_populates="user")

# Pydantic models for API
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(default="trader", description="User role")

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v

    @validator('role')
    def validate_role(cls, v):
        if v not in ["admin", "trader"]:
            raise ValueError('Role must be either "admin" or "trader"')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password")

    class Config:
        schema_extra = {
            "example": {
                "username": "trader123",
                "email": "trader@example.com",
                "password": "securepassword123",
                "role": "trader"
            }
        }

class UserRead(UserBase):
    id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "user_123",
                "username": "trader123",
                "email": "trader@example.com",
                "role": "trader",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email address")
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")

    @validator('role')
    def validate_role(cls, v):
        if v is not None and v not in ["admin", "trader"]:
            raise ValueError('Role must be either "admin" or "trader"')
        return v