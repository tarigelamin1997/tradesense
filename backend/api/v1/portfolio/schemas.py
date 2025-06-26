
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    initial_balance: float = Field(default=10000.0, gt=0)

class PortfolioResponse(BaseModel):
    id: str
    name: str
    initial_balance: float
    current_balance: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    win_rate: float
    is_default: bool
    created_at: str
    return_percentage: float

class EquityDataPoint(BaseModel):
    date: str
    balance: float
    daily_pnl: float
    total_pnl: float
    trade_count: int

class EquityMetrics(BaseModel):
    sharpe_ratio: float
    max_drawdown: float
    total_return: float

class EquityCurveResponse(BaseModel):
    success: bool
    equity_curve: List[EquityDataPoint]
    metrics: EquityMetrics
