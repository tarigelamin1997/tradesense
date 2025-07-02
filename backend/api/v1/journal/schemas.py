
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class JournalEntryBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    trade_id: Optional[UUID] = None
    tags: Optional[list[str]] = []

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    tags: Optional[list[str]] = None

class JournalEntryResponse(JournalEntryBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
