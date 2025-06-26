
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from backend.models.playbook import PlaybookStatus

class PlaybookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    entry_criteria: str = Field(..., min_length=1)
    exit_criteria: str = Field(..., min_length=1)
    description: Optional[str] = None
    status: PlaybookStatus = PlaybookStatus.ACTIVE

class PlaybookCreate(PlaybookBase):
    pass

class PlaybookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    entry_criteria: Optional[str] = Field(None, min_length=1)
    exit_criteria: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    status: Optional[PlaybookStatus] = None

class PlaybookResponse(PlaybookBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PlaybookPerformance(BaseModel):
    playbook_id: UUID
    playbook_name: str
    trade_count: int
    total_pnl: float
    avg_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    avg_hold_time_minutes: Optional[float]
    profit_factor: Optional[float]
    
class PlaybookAnalytics(BaseModel):
    playbooks: List[PlaybookPerformance]
    summary: dict
