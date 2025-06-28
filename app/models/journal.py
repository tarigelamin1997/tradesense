
"""
Journal Models
Pydantic models for journaling features
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class JournalEntryBase(BaseModel):
    title: str
    content: str
    trade_id: Optional[int] = None
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    confidence: Optional[int] = None

class JournalEntry(JournalEntryBase):
    id: int
    user_id: int
    created_at: datetime

class TradeNote(BaseModel):
    id: int
    trade_id: int
    content: str
    created_at: datetime

class Reflection(BaseModel):
    id: int
    user_id: int
    period: str
    content: str
    key_learnings: List[str]
    goals_for_next_period: List[str]
    created_at: datetime
