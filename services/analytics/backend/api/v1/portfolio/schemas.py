from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PortfolioCreate(BaseModel):
    name: str
    initial_balance: float = 10000.0

class PortfolioResponse(BaseModel):
    id: str
    user_id: str
    name: str
    initial_balance: float
    current_balance: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class EquityCurveResponse(BaseModel):
    timestamp: datetime
    balance: float
    daily_pnl: float
    total_pnl: float
    trade_count: int

    model_config = {
        "from_attributes": True
    }

class TradeSimulation(BaseModel):
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    strategy: Optional[str] = None
    notes: Optional[str] = None

class PositionResponse(BaseModel):
    symbol: str
    quantity: float
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float
    total_pnl: float
    allocation_pct: float
    asset_class: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }

class AllocationResponse(BaseModel):
    category: str
    value: float
    percentage: float
    count: int
    
    model_config = {
        "from_attributes": True
    }

class PerformanceResponse(BaseModel):
    date: datetime
    portfolio_value: float
    daily_return: float
    cumulative_return: float
    trades_count: int
    win_rate: float
    
    model_config = {
        "from_attributes": True
    }
