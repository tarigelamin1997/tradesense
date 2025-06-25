
"""
Trade Note model for storing trader journal entries and trade context
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class TradeNote(Base):
    __tablename__ = "trade_notes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    trade_id = Column(String, nullable=True, index=True)  # Optional - can be standalone journal entry
    
    # Note content
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String(50), nullable=True)  # e.g., "confident", "anxious", "neutral"
    
    # Emotion tracking fields
    emotion = Column(String(50), nullable=True)  # Calm, Excited, Anxious, Fearful, Angry, etc.
    confidence_score = Column(Integer, nullable=True)  # 1-10 scale
    mental_triggers = Column(Text, nullable=True)  # JSON array of triggers like FOMO, Revenge, etc.
    
    # Timestamps
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_note_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_note_user_trade', 'user_id', 'trade_id'),
        Index('idx_note_mood', 'mood'),
    )
