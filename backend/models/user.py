from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import typing

# Use TYPE_CHECKING to avoid circular imports
if typing.TYPE_CHECKING:
    from backend.models.portfolio import Portfolio

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_password_token = Column(String, nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Profile fields
    trading_experience = Column(String, nullable=True)  # beginner, intermediate, advanced
    preferred_markets = Column(Text, nullable=True)  # JSON string of market preferences
    timezone = Column(String, default="UTC")

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    playbooks = relationship("Playbook", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

# Pydantic models for API
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

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
        json_schema_extra = {
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
        json_schema_extra = {
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