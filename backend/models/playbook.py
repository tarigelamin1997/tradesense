
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import uuid

Base = declarative_base()

class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Playbook details
    name = Column(String, nullable=False)
    entry_criteria = Column(Text, nullable=False)
    exit_criteria = Column(Text, nullable=False)
    description = Column(Text)
    
    # Status and metadata
    status = Column(String, default="active")  # active, archived
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Performance tracking (calculated fields)
    total_trades = Column(String, default="0")
    win_rate = Column(String, default="0.0")
    avg_pnl = Column(String, default="0.0")
    total_pnl = Column(String, default="0.0")
    
    # Relationships
    trades = relationship("Trade", back_populates="playbook")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_user_playbook', 'user_id', 'name'),
    )

# Pydantic models for API
class PlaybookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    entry_criteria: str = Field(..., min_length=1, max_length=2000)
    exit_criteria: str = Field(..., min_length=1, max_length=2000)
    description: Optional[str] = Field(None, max_length=1000)
    status: Literal["active", "archived"] = Field(default="active")

class PlaybookCreate(PlaybookBase):
    pass

class PlaybookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    entry_criteria: Optional[str] = Field(None, min_length=1, max_length=2000)
    exit_criteria: Optional[str] = Field(None, min_length=1, max_length=2000)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[Literal["active", "archived"]] = None

class PlaybookResponse(PlaybookBase):
    id: str
    user_id: str
    total_trades: str
    win_rate: str
    avg_pnl: str
    total_pnl: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlaybookAnalytics(BaseModel):
    id: str
    name: str
    total_trades: int
    win_rate: float
    avg_pnl: float
    total_pnl: float
    avg_hold_time_minutes: Optional[float]
    best_win: Optional[float]
    worst_loss: Optional[float]
    consecutive_wins: int
    consecutive_losses: int
    recommendation: str  # "focus_more", "reduce_size", "cut_play", "keep_current"
    performance_trend: str  # "improving", "declining", "stable"
