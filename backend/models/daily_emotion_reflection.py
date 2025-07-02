
from sqlalchemy import Column, String, Integer, DateTime, Text, Date, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
import uuid

Base = declarative_base()

class DailyEmotionReflection(Base):
    __tablename__ = "daily_emotion_reflections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Date for the reflection
    reflection_date = Column(Date, nullable=False, index=True)
    
    # Emotional data
    mood_score = Column(Integer)  # -5 to +5 scale
    summary = Column(Text)
    dominant_emotion = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'reflection_date'),
    )

# Pydantic models for API
class DailyEmotionReflectionBase(BaseModel):
    reflection_date: date
    mood_score: Optional[int] = Field(None, ge=-5, le=5, description="Mood scale from -5 (terrible) to +5 (excellent)")
    summary: Optional[str] = Field(None, max_length=1000, description="Daily reflection summary")
    dominant_emotion: Optional[str] = Field(None, max_length=50)

class DailyEmotionReflectionCreate(DailyEmotionReflectionBase):
    pass

class DailyEmotionReflectionUpdate(BaseModel):
    mood_score: Optional[int] = Field(None, ge=-5, le=5)
    summary: Optional[str] = Field(None, max_length=1000)
    dominant_emotion: Optional[str] = Field(None, max_length=50)

class DailyEmotionReflectionResponse(DailyEmotionReflectionBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
