"""
Tag schemas for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class TagBase(BaseModel):
    """Base schema for tag operations"""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        v = v.strip().lower()
        if not v:
            raise ValueError('Tag name cannot be empty')
        return v


class TagCreate(TagBase):
    """Schema for creating new tags"""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "breakout",
                "description": "Breakout trading pattern",
                "color": "#FF5733"
            }
        }
    }


class TagUpdate(BaseModel):
    """Schema for updating existing tags"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            v = v.strip().lower()
            if not v:
                raise ValueError('Tag name cannot be empty')
        return v


class TagResponse(TagBase):
    """Schema for tag responses"""
    id: str = Field(..., description="Tag ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    trade_count: Optional[int] = Field(None, description="Number of trades with this tag")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "tag_123",
                "user_id": "user_456",
                "name": "breakout",
                "description": "Breakout trading pattern",
                "color": "#FF5733",
                "created_at": "2024-01-15T14:30:00Z",
                "updated_at": "2024-01-15T14:30:00Z",
                "trade_count": 25
            }
        }
    }


class TagListResponse(BaseModel):
    """Schema for paginated tag list responses"""
    tags: List[TagResponse] = Field(..., description="List of tags")
    total_count: int = Field(..., description="Total number of tags")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more pages")
