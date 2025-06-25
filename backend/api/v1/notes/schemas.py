"""
Trade Note schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JournalEntryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Entry title")
    content: str = Field(..., min_length=1, description="Entry content")
    mood: Optional[str] = Field(None, max_length=50, description="Trader's mood")

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    mood: Optional[str] = Field(None, max_length=50)

class JournalEntryResponse(JournalEntryBase):
    id: str
    trade_id: Optional[str]
    user_id: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# For including in trade responses
class TradeWithJournalResponse(BaseModel):
    id: str
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    pnl: Optional[float]
    strategy_tag: Optional[str]
    notes: Optional[str]
    journal_entries: List[JournalEntryResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True