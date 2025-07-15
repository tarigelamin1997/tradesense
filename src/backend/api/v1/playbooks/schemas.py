from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class PlaybookCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    entry_criteria: str = Field(..., min_length=1)
    exit_criteria: str = Field(..., min_length=1)
    description: Optional[str] = None

class PlaybookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    entry_criteria: Optional[str] = Field(None, min_length=1)
    exit_criteria: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    status: Optional[str] = None

class PlaybookResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    entry_criteria: str
    exit_criteria: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

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
