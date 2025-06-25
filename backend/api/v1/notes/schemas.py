
"""
Trade Note schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class TradeNoteBase(BaseModel):
    """Base schema for trade notes"""
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(..., min_length=1, description="Note content")
    mood: Optional[str] = Field(None, max_length=50, description="Emotional state/mood")
    trade_id: Optional[str] = Field(None, description="Associated trade ID (optional)")
    
    @validator('mood')
    def validate_mood(cls, v):
        if v is not None:
            allowed_moods = [
                "confident", "anxious", "neutral", "excited", "frustrated", 
                "focused", "distracted", "calm", "stressed", "optimistic", "pessimistic"
            ]
            if v.lower() not in allowed_moods:
                # Allow custom moods but validate they're reasonable
                if len(v) > 50 or not v.replace(' ', '').replace('-', '').isalpha():
                    raise ValueError(f'Mood must be a valid emotional state')
        return v


class TradeNoteCreate(TradeNoteBase):
    """Schema for creating a new trade note"""
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Morning Trading Session",
                "content": "Entered ES long at 4150 based on RSI divergence. Felt confident about the setup but should have waited for better confirmation. Market was choppy early on.",
                "mood": "confident",
                "trade_id": "trade_123"
            }
        }


class TradeNoteUpdate(BaseModel):
    """Schema for updating a trade note"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Note title")
    content: Optional[str] = Field(None, min_length=1, description="Note content")
    mood: Optional[str] = Field(None, max_length=50, description="Emotional state/mood")
    
    @validator('mood')
    def validate_mood(cls, v):
        if v is not None:
            allowed_moods = [
                "confident", "anxious", "neutral", "excited", "frustrated", 
                "focused", "distracted", "calm", "stressed", "optimistic", "pessimistic"
            ]
            if v.lower() not in allowed_moods:
                if len(v) > 50 or not v.replace(' ', '').replace('-', '').isalpha():
                    raise ValueError(f'Mood must be a valid emotional state')
        return v


class TradeNoteRead(TradeNoteBase):
    """Schema for reading trade notes"""
    id: str = Field(..., description="Note ID")
    user_id: str = Field(..., description="User ID")
    timestamp: datetime = Field(..., description="Note timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "note_123",
                "user_id": "user_456",
                "trade_id": "trade_789",
                "title": "Post-Trade Analysis",
                "content": "This trade went well because I stuck to my plan and didn't let emotions interfere.",
                "mood": "satisfied",
                "timestamp": "2024-01-15T14:30:00Z",
                "created_at": "2024-01-15T14:30:00Z",
                "updated_at": "2024-01-15T14:30:00Z"
            }
        }


class TradeNoteListResponse(BaseModel):
    """Response schema for note listing"""
    notes: List[TradeNoteRead] = Field(..., description="List of notes")
    total: int = Field(..., description="Total number of notes")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    
    class Config:
        schema_extra = {
            "example": {
                "notes": [
                    {
                        "id": "note_123",
                        "user_id": "user_456",
                        "trade_id": "trade_789",
                        "title": "Good Trade Today",
                        "content": "Followed my strategy perfectly",
                        "mood": "confident",
                        "timestamp": "2024-01-15T14:30:00Z",
                        "created_at": "2024-01-15T14:30:00Z",
                        "updated_at": "2024-01-15T14:30:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 100
            }
        }


class MoodStatsResponse(BaseModel):
    """Response schema for mood statistics"""
    mood_distribution: dict = Field(..., description="Distribution of moods")
    most_common_mood: str = Field(..., description="Most frequently recorded mood")
    total_notes: int = Field(..., description="Total number of notes")
    
    class Config:
        schema_extra = {
            "example": {
                "mood_distribution": {
                    "confident": 15,
                    "anxious": 8,
                    "neutral": 12,
                    "frustrated": 5
                },
                "most_common_mood": "confident",
                "total_notes": 40
            }
        }
