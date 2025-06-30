from sqlalchemy import Column, String, DateTime, Text, JSON, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

Base = declarative_base()

# Export classes for proper importing
__all__ = ['MentalMapEntry', 'SessionReplay', 'MentalMapEntryCreate', 'MentalMapEntryResponse', 'SessionReplayCreate', 'SessionReplayResponse', 'MentalMap']

# Backward compatibility alias
MentalMap = MentalMapEntry

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

    # Relationships
    trade = relationship("Trade", back_populates="mental_entries")
    session = relationship("SessionReplay", back_populates="mental_entries")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_user_mood', 'user_id', 'mood'),
        Index('idx_session_time', 'session_id', 'timestamp'),
    )

class SessionReplay(Base):
    __tablename__ = "session_replays"

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

    # Relationships
    mental_entries = relationship("MentalMapEntry", back_populates="session")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_session_date', 'user_id', 'start_time'),
    )

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

    class Config:
        from_attributes = True

# Backward compatibility alias - must be after class definition
MentalMap = MentalMapEntry

class SessionReplayBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    session_name: Optional[str] = Field(None, max_length=100)
    market_conditions: Optional[str] = Field(None, max_length=200)
    session_notes: Optional[str] = Field(None, max_length=1000)

class SessionReplayCreate(SessionReplayBase):
    pass

class SessionReplayUpdate(BaseModel):
    end_time: Optional[datetime] = None
    session_name: Optional[str] = Field(None, max_length=100)
    market_conditions: Optional[str] = Field(None, max_length=200)
    session_notes: Optional[str] = Field(None, max_length=1000)

class SessionReplayResponse(SessionReplayBase):
    id: str
    user_id: str
    total_trades: str
    dominant_mood: Optional[str]
    rule_breaks: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True