from sqlalchemy import Column, String, DateTime, Float, Text, JSON, Index
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Import shared Base
from backend.core.db.session import Base

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    # Milestone details
    type = Column(String, nullable=False, index=True)  # 'journal_streak', 'consistency_rating', 'win_streak', etc.
    category = Column(String, nullable=False, index=True)  # 'journaling', 'performance', 'discipline', 'analytics'
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    # Achievement data
    achieved_at = Column(DateTime, nullable=False, default=func.now())
    value = Column(Float)  # The actual value achieved (e.g., streak length, percentage)
    target_value = Column(Float)  # The target that was met

    # Gamification
    xp_points = Column(Float, default=0)  # Experience points awarded
    badge_icon = Column(String)  # Icon identifier for the badge
    rarity = Column(String, default="common")  # common, rare, epic, legendary

    # Metadata
    milestone_metadata = Column(JSON)  # Additional context data

    created_at = Column(DateTime, default=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_type', 'user_id', 'type'),
        Index('idx_user_category', 'user_id', 'category'),
        Index('idx_milestone_user_achieved', 'user_id', 'achieved_at'),
        {"extend_existing": True}
    )

# Pydantic models for API
class MilestoneBase(BaseModel):
    type: str
    category: str
    title: str
    description: str
    value: Optional[float] = None
    target_value: Optional[float] = None
    xp_points: float = Field(default=0, ge=0)
    badge_icon: Optional[str] = None
    rarity: str = Field(default="common", pattern="^(common|rare|epic|legendary)$")
    milestone_metadata: Optional[Dict[str, Any]] = None

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneResponse(MilestoneBase):
    id: str
    user_id: str
    achieved_at: datetime
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class UserProgress(BaseModel):
    total_xp: float
    total_milestones: int
    level: int
    level_progress: float  # 0-100 percentage to next level
    xp_to_next_level: float
    recent_milestones: list[MilestoneResponse]
    category_progress: Dict[str, Dict[str, Any]]
    active_streaks: Dict[str, int]