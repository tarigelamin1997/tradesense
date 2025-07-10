"""
Strategy schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StrategyBase(BaseModel):
    """Base schema for strategies"""
    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(None, max_length=500, description="Strategy description")


class StrategyCreate(StrategyBase):
    """Schema for creating a new strategy"""
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Scalping v2",
                "description": "Quick scalping strategy focusing on 1-2 point moves"
            }
        }
    }


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Strategy name")
    description: Optional[str] = Field(None, max_length=500, description="Strategy description")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Scalping v3",
                "description": "Updated scalping strategy with better risk management"
            }
        }
    }


class StrategyRead(StrategyBase):
    """Schema for reading strategies"""
    id: str = Field(..., description="Strategy ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "strategy_123",
                "user_id": "user_456",
                "name": "News Playbook",
                "description": "Trading strategy for news events",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    }


class StrategyListResponse(BaseModel):
    """Response schema for strategy listing"""
    strategies: List[StrategyRead] = Field(..., description="List of strategies")
    total: int = Field(..., description="Total number of strategies")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "strategies": [
                    {
                        "id": "strategy_123",
                        "user_id": "user_456",
                        "name": "Momentum Play",
                        "description": "High momentum breakout strategy",
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1
            }
        }
    }


class StrategyAnalytics(BaseModel):
    """Strategy performance analytics"""
    strategy_name: str = Field(..., description="Strategy name")
    total_trades: int = Field(..., description="Total trades")
    win_rate: float = Field(..., description="Win rate percentage")
    total_pnl: float = Field(..., description="Total P&L")
    avg_pnl: float = Field(..., description="Average P&L per trade")
    profit_factor: float = Field(..., description="Profit factor")
    best_trade: float = Field(..., description="Best single trade")
    worst_trade: float = Field(..., description="Worst single trade")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "strategy_name": "Scalping v2",
                "total_trades": 45,
                "win_rate": 68.9,
                "total_pnl": 1250.75,
                "avg_pnl": 27.79,
                "profit_factor": 2.15,
                "best_trade": 125.50,
                "worst_trade": -85.25
            }
        }
    }


class TagAnalytics(BaseModel):
    """Tag performance analytics"""
    tag: str = Field(..., description="Tag name")
    total_trades: int = Field(..., description="Total trades with this tag")
    win_rate: float = Field(..., description="Win rate percentage")
    total_pnl: float = Field(..., description="Total P&L")
    avg_pnl: float = Field(..., description="Average P&L per trade")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "tag": "FOMO",
                "total_trades": 12,
                "win_rate": 25.0,
                "total_pnl": -245.50,
                "avg_pnl": -20.46
            }
        }
    }
