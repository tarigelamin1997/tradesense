from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Index, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
import uuid
from core.db.session import Base

class TradeReview(Base):
    __tablename__ = "trade_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trade_id = Column(String, ForeignKey('trades.id'), nullable=False, unique=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Review metrics
    quality_score = Column(Integer, nullable=False)  # 1-5 rating
    mistakes = Column(JSON)  # List of mistake tags
    mood = Column(String, index=True)  # Emotional state during trade
    lesson_learned = Column(Text)  # Key takeaway
    execution_vs_plan = Column(Integer)  # How well did execution match the plan (1-5)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # trade = relationship("backend.models.trade.Trade", back_populates="review")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_quality', 'user_id', 'quality_score'),
        Index('idx_user_mood_review', 'user_id', 'mood'),
        Index('idx_review_date', 'user_id', 'created_at'),
        {"extend_existing": True}
    )

# Pydantic schemas
class TradeReviewCreate(BaseModel):
    quality_score: int = Field(..., ge=1, le=5, description="Trade quality rating 1-5")
    mistakes: List[str] = Field(default_factory=list, description="List of mistake tags")
    mood: Optional[str] = Field(None, description="Emotional state during trade")
    lesson_learned: Optional[str] = Field(None, max_length=1000, description="Key lesson learned")
    execution_vs_plan: Optional[int] = Field(None, ge=1, le=5, description="Execution vs plan rating")

    @field_validator('mistakes')
    @classmethod
    def validate_mistakes(cls, v):
        valid_mistakes = {
            'early_entry', 'late_entry', 'no_confirmation', 'wrong_size', 
            'missed_stop', 'early_exit', 'late_exit', 'revenge_trade',
            'overtrading', 'fomo', 'hesitation', 'greed', 'fear',
            'poor_timing', 'ignored_plan', 'emotional_decision'
        }
        for mistake in v:
            if mistake not in valid_mistakes:
                raise ValueError(f"Invalid mistake tag: {mistake}")
        return v

    @field_validator('mood')
    @classmethod
    def validate_mood(cls, v):
        if v is None:
            return v
        valid_moods = {
            'calm', 'confident', 'focused', 'anxious', 'impulsive', 
            'frustrated', 'greedy', 'fearful', 'rushed', 'patient'
        }
        if v not in valid_moods:
            raise ValueError(f"Invalid mood: {v}")
        return v

class TradeReviewUpdate(BaseModel):
    quality_score: Optional[int] = Field(None, ge=1, le=5)
    mistakes: Optional[List[str]] = None
    mood: Optional[str] = None
    lesson_learned: Optional[str] = Field(None, max_length=1000)
    execution_vs_plan: Optional[int] = Field(None, ge=1, le=5)

class TradeReviewResponse(BaseModel):
    id: str
    trade_id: str
    quality_score: int
    mistakes: List[str]
    mood: Optional[str]
    lesson_learned: Optional[str]
    execution_vs_plan: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class ReviewPatternAnalysis(BaseModel):
    total_reviews: int
    avg_quality_score: float
    most_common_mistakes: List[dict]  # [{"mistake": "early_entry", "count": 5, "percentage": 25.0}]
    mood_performance: List[dict]  # [{"mood": "anxious", "avg_quality": 2.1, "count": 8}]
    quality_trend: List[dict]  # [{"date": "2024-01-01", "avg_quality": 3.2}]
    improvement_areas: List[str]  # Areas needing most improvement
    strengths: List[str]  # Areas of consistent good performance
    
class ReviewInsights(BaseModel):
    patterns: ReviewPatternAnalysis
    recommendations: List[str]
    warnings: List[str]  # Repeated mistakes or concerning patterns
    achievements: List[str]  # Recent improvements
