"""
Trade schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TradeDirection(str, Enum):
    """Trade direction enumeration"""
    LONG = "long"
    SHORT = "short"


class TradeStatus(str, Enum):
    """Trade status enumeration"""
    OPEN = "open"
    CLOSED = "closed"


class TradeCreateRequest(BaseModel):
    """Trade creation request schema"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    direction: TradeDirection = Field(..., description="Trade direction")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    entry_price: float = Field(..., gt=0, description="Entry price")
    entry_time: datetime = Field(..., description="Entry timestamp")
    strategy_tag: Optional[str] = Field(None, max_length=50, description="Strategy identifier")
    confidence_score: Optional[int] = Field(None, ge=1, le=10, description="Confidence score (1-10)")
    notes: Optional[str] = Field(None, max_length=1000, description="Trade notes")
    tags: Optional[List[str]] = Field(None, description="Trade tags (e.g., 'FOMO', 'breakout')")
    strategy_tag: Optional[str] = Field(None, max_length=100, description="Strategy identifier")
    tag_ids: Optional[List[str]] = Field(None, description="Tag IDs to assign to trade")
    strategy_id: Optional[str] = Field(None, max_length=100, description="Strategy ID reference")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "ES",
                "direction": "long",
                "quantity": 1.0,
                "entry_price": 4500.25,
                "entry_time": "2024-01-15T10:30:00Z",
                "strategy_tag": "Scalping v2",
                "confidence_score": 8,
                "notes": "Strong bullish momentum",
                "tags": ["breakout", "high-volume"]
            }
        }


class TradeUpdateRequest(BaseModel):
    """Trade update request schema"""
    exit_price: Optional[float] = Field(None, gt=0, description="Exit price")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    notes: Optional[str] = Field(None, max_length=1000, description="Updated trade notes")
    tags: Optional[List[str]] = Field(None, description="Trade tags")
    tag_ids: Optional[List[str]] = Field(None, description="Tag IDs to assign to trade")
    strategy_tag: Optional[str] = Field(None, max_length=100, description="Strategy identifier")
    strategy_id: Optional[str] = Field(None, max_length=100, description="Strategy ID reference")

    @validator('exit_time')
    def validate_exit_time(cls, v, values):
        # Note: In a real scenario, we'd validate against entry_time from database
        return v

    class Config:
        schema_extra = {
            "example": {
                "exit_price": 4525.75,
                "exit_time": "2024-01-15T14:45:00Z",
                "notes": "Target reached, good profit",
                "tags": ["profitable", "quick"],
                "strategy_tag": "Scalping v2"
            }
        }


class TradeResponse(BaseModel):
    """Schema for trade responses"""
    id: str = Field(..., description="Trade ID")
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    direction: TradeDirection = Field(..., description="Trade direction")
    quantity: float = Field(..., description="Trade quantity")
    entry_price: float = Field(..., description="Entry price")
    exit_price: Optional[float] = Field(None, description="Exit price")
    entry_time: datetime = Field(..., description="Entry timestamp")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    pnl: Optional[float] = Field(None, description="Profit/Loss")
    commission: Optional[float] = Field(None, description="Commission fees")
    net_pnl: Optional[float] = Field(None, description="Net Profit/Loss")
    strategy_tag: Optional[str] = Field(None, description="Strategy identifier")
    confidence_score: Optional[int] = Field(None, description="Confidence level 1-10")
    notes: Optional[str] = Field(None, description="Trade notes")
    tags: Optional[List[str]] = Field(None, description="Legacy string tags")
    strategy_tag: Optional[str] = Field(None, description="Strategy identifier")
    status: TradeStatus = Field(..., description="Trade status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "trade_001",
                "user_id": "user_123",
                "symbol": "ES",
                "direction": "long",
                "quantity": 1.0,
                "entry_price": 4500.25,
                "exit_price": 4525.75,
                "entry_time": "2024-01-15T10:30:00Z",
                "exit_time": "2024-01-15T14:45:00Z",
                "pnl": 1275.0,
                "commission": 5.0,
                "net_pnl": 1270.0,
                "strategy_tag": "momentum",
                "confidence_score": 8,
                "notes": "Strong bullish momentum",
                "status": "closed",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T14:45:00Z"
            }
        }


class TradeQueryParams(BaseModel):
    """Query parameters for filtering trades"""
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    strategy_tag: Optional[str] = Field(None, description="Filter by strategy")
    tags: Optional[List[str]] = Field(None, description="Filter by legacy tags")
    tag_ids: Optional[List[str]] = Field(None, description="Filter by tag IDs")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    status: Optional[TradeStatus] = Field(None, description="Filter by status")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=1000, description="Items per page")


class AnalyticsRequest(BaseModel):
    """Analytics calculation request"""
    data: List[Dict[str, Any]] = Field(..., description="Trade data for analysis")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")

    class Config:
        schema_extra = {
            "example": {
                "data": [
                    {"symbol": "ES", "pnl": 1250.0, "entry_time": "2024-01-15T10:30:00Z"},
                    {"symbol": "NQ", "pnl": -500.0, "entry_time": "2024-01-16T11:15:00Z"}
                ],
                "analysis_type": "comprehensive"
            }
        }

class PaginatedResponse(BaseModel):
    """Enhanced pagination response"""
    items: List[Any]
    total_count: int
    current_page: int
    per_page: int
    total_pages: int
    has_previous: bool
    has_next: bool

    @validator('total_pages', pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        total_count = values.get('total_count', 0)
        per_page = values.get('per_page', 50)
        return max(1, (total_count + per_page - 1) // per_page)

    @validator('has_previous', pre=True, always=True)
    def calculate_has_previous(cls, v, values):
        return values.get('current_page', 1) > 1

    @validator('has_next', pre=True, always=True)
    def calculate_has_next(cls, v, values):
        current_page = values.get('current_page', 1)
        total_pages = values.get('total_pages', 1)
        return current_page < total_pages

class AnalyticsFilters(BaseModel):
    """Analytics filters"""
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    strategy_tag: Optional[str] = Field(None, description="Filter by strategy")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    confidence_score_min: Optional[int] = Field(None, ge=1, le=10)
    confidence_score_max: Optional[int] = Field(None, ge=1, le=10)
    min_pnl: Optional[float] = Field(None, description="Minimum PnL")
    max_pnl: Optional[float] = Field(None, description="Maximum PnL")

class TradeIngestRequest(BaseModel):
    """Schema for API trade ingestion"""
    entry_time: datetime = Field(..., description="Entry timestamp")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    position: TradeDirection = Field(..., description="Trade position (long/short)")
    size: float = Field(..., gt=0, description="Position size")
    entry_price: float = Field(..., gt=0, description="Entry price")
    exit_price: Optional[float] = Field(None, gt=0, description="Exit price")
    tags: Optional[List[str]] = Field(None, description="Trade tags")
    strategy: Optional[str] = Field(None, max_length=100, description="Strategy name")
    notes: Optional[str] = Field(None, max_length=1000, description="Trade notes")

    @validator('exit_time')
    def validate_exit_time(cls, v, values):
        if v and 'entry_time' in values and v <= values['entry_time']:
            raise ValueError('Exit time must be after entry time')
        return v

    class Config:
        schema_extra = {
            "example": {
                "entry_time": "2024-12-18T09:00:00Z",
                "exit_time": "2024-12-18T09:45:00Z",
                "symbol": "NQ",
                "position": "long",
                "size": 2,
                "entry_price": 16000,
                "exit_price": 16040,
                "tags": ["breakout", "morning session"],
                "strategy": "momentum",
                "notes": "Strong breakout pattern"
            }
        }


class TradeIngestResponse(BaseModel):
    """Response for trade ingestion"""
    status: str = Field(..., description="Status of the operation")
    trade_id: str = Field(..., description="ID of the created trade")
    message: str = Field(..., description="Success message")

    class Config:
        schema_extra = {
            "example": {
                "status": "ok",
                "trade_id": "trade_12345",
                "message": "Trade ingested successfully"
            }
        }


class AnalyticsResponse(BaseModel):
    """Enhanced analytics response model"""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl_per_trade: float
    best_trade: float
    worst_trade: float
    profit_factor: float

    # Advanced metrics
    avg_confidence_score: Optional[float] = None
    confidence_distribution: Dict[str, int] = {}

    # Breakdowns
    strategy_performance: Dict[str, Dict[str, Any]] = {}
    tag_performance: Dict[str, Dict[str, Any]] = {}
    monthly_pnl: Dict[str, float] = {}
    daily_pnl: Dict[str, float] = {}

    # Time-based metrics
    avg_trade_duration: Optional[float] = None
    trades_by_day_of_week: Dict[str, int] = {}

    # Behavioral metrics (NEW)
    behavioral_metrics: Dict[str, Any] = {}

    # Applied filters (for reference)
    filters_applied: Optional[AnalyticsFilters] = None