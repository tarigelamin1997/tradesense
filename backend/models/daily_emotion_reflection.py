from sqlalchemy import Column, String, Text, DateTime, Integer, JSON
from sqlalchemy.sql import func
from core.db.session import Base
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import uuid


class DailyEmotionReflection(Base):
    __tablename__ = "daily_emotion_reflections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD format
    
    # Emotion tracking
    pre_market_emotion = Column(String(50), nullable=True)
    post_market_emotion = Column(String(50), nullable=True)
    dominant_emotion = Column(String(50), nullable=True)
    emotion_intensity = Column(Integer, nullable=True)  # 1-10 scale
    
    # Reflection content
    what_went_well = Column(Text, nullable=True)
    what_to_improve = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    tomorrow_focus = Column(Text, nullable=True)
    
    # Market conditions and mindset
    market_conditions = Column(String(100), nullable=True)
    trading_mindset = Column(String(100), nullable=True)
    stress_level = Column(Integer, nullable=True)  # 1-10 scale
    
    # Goals and achievements
    daily_goals_met = Column(JSON, nullable=True)  # List of boolean flags
    major_wins = Column(Text, nullable=True)
    areas_for_growth = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

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

    model_config = {
        "from_attributes": True
    }
