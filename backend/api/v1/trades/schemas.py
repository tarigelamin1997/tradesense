
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
    direction: TradeDirection = Field(..., description="Trade direction (long/short)")
    quantity: float = Field(..., gt=0, description="Trade quantity")
    entry_price: float = Field(..., gt=0, description="Entry price")
    entry_time: datetime = Field(..., description="Entry timestamp")
    strategy_tag: Optional[str] = Field(None, max_length=50, description="Strategy identifier")
    confidence_score: Optional[int] = Field(None, ge=1, le=10, description="Confidence score (1-10)")
    notes: Optional[str] = Field(None, max_length=1000, description="Trade notes")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "ES",
                "direction": "long",
                "quantity": 1.0,
                "entry_price": 4500.25,
                "entry_time": "2024-01-15T10:30:00Z",
                "strategy_tag": "momentum",
                "confidence_score": 8,
                "notes": "Strong bullish momentum"
            }
        }


class TradeUpdateRequest(BaseModel):
    """Trade update request schema"""
    exit_price: Optional[float] = Field(None, gt=0, description="Exit price")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    notes: Optional[str] = Field(None, max_length=1000, description="Updated trade notes")
    tags: Optional[str] = Field(None, max_length=200, description="Trade tags")
    
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
                "tags": "profitable,quick"
            }
        }


class TradeResponse(BaseModel):
    """Trade response schema"""
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
    commission: Optional[float] = Field(None, description="Commission paid")
    net_pnl: Optional[float] = Field(None, description="Net P&L after commission")
    strategy_tag: Optional[str] = Field(None, description="Strategy identifier")
    confidence_score: Optional[int] = Field(None, description="Confidence score")
    notes: Optional[str] = Field(None, description="Trade notes")
    status: TradeStatus = Field(..., description="Trade status")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record update timestamp")
    
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
    """Trade query parameters"""
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    strategy_tag: Optional[str] = Field(None, description="Filter by strategy")
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


class AnalyticsResponse(BaseModel):
    """Analytics response schema"""
    total_trades: int = Field(..., description="Total number of trades")
    winning_trades: int = Field(..., description="Number of winning trades")
    losing_trades: int = Field(..., description="Number of losing trades")
    win_rate: float = Field(..., description="Win rate percentage")
    total_pnl: float = Field(..., description="Total profit/loss")
    profit_factor: float = Field(..., description="Profit factor")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    expectancy: float = Field(..., description="Expected value per trade")
    equity_curve: List[float] = Field(..., description="Cumulative P&L curve")
    symbol_breakdown: List[Dict[str, Any]] = Field(..., description="Performance by symbol")
    
    class Config:
        schema_extra = {
            "example": {
                "total_trades": 100,
                "winning_trades": 65,
                "losing_trades": 35,
                "win_rate": 65.0,
                "total_pnl": 12500.0,
                "profit_factor": 1.85,
                "max_drawdown": 2500.0,
                "sharpe_ratio": 1.45,
                "expectancy": 125.0,
                "equity_curve": [0, 500, 750, 1250, 1000, 1500],
                "symbol_breakdown": [
                    {"symbol": "ES", "trades": 50, "pnl": 8000.0, "win_rate": 70.0},
                    {"symbol": "NQ", "trades": 30, "pnl": 3500.0, "win_rate": 60.0}
                ]
            }
        }
