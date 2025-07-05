from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# Import shared Base
from backend.core.db.session import Base

# Export classes for proper importing
__all__ = ['MentalMapEntry', 'SessionReplay', 'MentalMapEntryCreate', 'MentalMapEntryResponse', 'SessionReplayCreate', 'SessionReplayResponse', 'MentalMap']

# Backward compatibility alias
#MentalMap = MentalMapEntry

class MentalMapEntry(Base):
    __tablename__ = "mental_map_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    trade_id = Column(String, ForeignKey('trades.id'), nullable=True, index=True)
    session_id = Column(String, ForeignKey('session_replays.id'), nullable=True, index=True)

    # Timing
    timestamp = Column(DateTime, nullable=False, index=True)

    # Mental state data
    note = Column(Text, nullable=False)
    mood = Column(String, nullable=False)  # calm, anxious, revenge, euphoric, fearful, overconfident
    confidence_score = Column(String)  # 1-10 scale

    # Rule tracking
    checklist_flags = Column(JSON)  # ["broke entry rule", "overconfidence", "fomo"]

    # Visual context
    screenshot_url = Column(String)
    chart_context = Column(Text)  # Market conditions, setup description

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # trade = relationship("backend.models.trade.Trade", back_populates="mental_entries")
    # session = relationship("backend.models.mental_map.SessionReplay", back_populates="mental_entries")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_user_mood', 'user_id', 'mood'),
        Index('idx_session_time', 'session_id', 'timestamp'),
        {"extend_existing": True}
    )

class SessionReplay(Base):
    __tablename__ = "session_replays"
    __table_args__ = (
        Index('idx_user_session_date', 'user_id', 'start_time'),
        {"extend_existing": True}
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    # Session timing
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, index=True)

    # Session metadata
    session_name = Column(String)  # "Morning ES Scalping", "FOMC Day"
    market_conditions = Column(String)  # "High volatility", "Range-bound"
    session_notes = Column(Text)

    # Session summary (computed)
    total_trades = Column(String, default="0")
    dominant_mood = Column(String)
    rule_breaks = Column(JSON)  # Summary of rule violations

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships - temporarily disabled to resolve SQLAlchemy conflicts
    # mental_entries = relationship("backend.models.mental_map.MentalMapEntry", back_populates="session")

# Pydantic models for API
class MentalMapEntryBase(BaseModel):
    trade_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime
    note: str = Field(..., min_length=1, max_length=2000)
    mood: str = Field(..., pattern="^(calm|anxious|revenge|euphoric|fearful|overconfident|focused|frustrated|confident|uncertain)$")
    confidence_score: Optional[str] = Field(None, pattern="^[1-9]|10$")
    checklist_flags: Optional[List[str]] = Field(default_factory=list)
    screenshot_url: Optional[str] = None
    chart_context: Optional[str] = Field(None, max_length=500)

class MentalMapEntryCreate(MentalMapEntryBase):
    pass

class MentalMapEntryUpdate(BaseModel):
    note: Optional[str] = Field(None, min_length=1, max_length=2000)
    mood: Optional[str] = Field(None, pattern="^(calm|anxious|revenge|euphoric|fearful|overconfident|focused|frustrated|confident|uncertain)$")
    confidence_score: Optional[str] = Field(None, pattern="^[1-9]|10$")
    checklist_flags: Optional[List[str]] = None
    screenshot_url: Optional[str] = None
    chart_context: Optional[str] = Field(None, max_length=500)

class MentalMapEntryResponse(MentalMapEntryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

# ✅ Backward compatibility alias - defined AFTER both classes exist
MentalMap = MentalMapEntry

# SessionReplay Pydantic models
class SessionReplayBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    session_name: Optional[str] = Field(None, max_length=200)
    market_conditions: Optional[str] = Field(None, max_length=200)
    session_notes: Optional[str] = Field(None, max_length=2000)

class SessionReplayCreate(SessionReplayBase):
    pass

class SessionReplayUpdate(BaseModel):
    end_time: Optional[datetime] = None
    session_name: Optional[str] = Field(None, max_length=200)
    market_conditions: Optional[str] = Field(None, max_length=200)
    session_notes: Optional[str] = Field(None, max_length=2000)
    dominant_mood: Optional[str] = None
    rule_breaks: Optional[List[str]] = None

class SessionReplayResponse(SessionReplayBase):
    id: str
    user_id: str
    total_trades: str
    dominant_mood: Optional[str] = None
    rule_breaks: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }