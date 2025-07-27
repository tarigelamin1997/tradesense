from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

# Import shared Base
from core.db.session import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = ({"extend_existing": True},)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
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
    
    # Billing
    stripe_customer_id = Column(String, nullable=True, unique=True, index=True)

    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # portfolios = relationship("backend.models.portfolio.Portfolio", back_populates="user")
    # trades = relationship("backend.models.trade.Trade", back_populates="user")
    # playbooks = relationship("backend.models.playbook.Playbook", back_populates="user")
    # feature_requests = relationship("backend.models.feature_request.FeatureRequest", back_populates="user")
    subscription = relationship("models.billing.Subscription", back_populates="user", uselist=False)
    usage_records = relationship("models.billing.UsageRecord", back_populates="user")
    feedback_submissions = relationship("models.feedback.Feedback", back_populates="user")

    @property
    def is_admin(self):
        """Check if user is admin (you can modify this based on your role system)"""
        # For now, check if username is 'admin' or email contains 'admin'
        return self.username == 'admin' or 'admin' in self.email.lower()

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

# Pydantic models for API
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    role: str = Field(default="trader", description="User role")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ["admin", "trader"]:
            raise ValueError('Role must be either "admin" or "trader"')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "trader123",
                "email": "trader@example.com",
                "password": "securepassword123",
                "role": "trader"
            }
        }
    }

class UserRead(UserBase):
    id: str = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
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
    }

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Email address")
    role: Optional[str] = Field(None, description="User role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in ["admin", "trader"]:
            raise ValueError('Role must be either "admin" or "trader"')
        return v