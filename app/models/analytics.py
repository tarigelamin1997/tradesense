
"""
Analytics Models
Pydantic models for analytics data
"""

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, date

class PerformanceMetrics(BaseModel):
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_pnl: float
    best_trade: float
    worst_trade: float

class TradeAnalysis(BaseModel):
    trade_id: int
    symbol: str
    pnl: float
    duration_minutes: int
    risk_reward: float
    tags: List[str]

class EquityCurve(BaseModel):
    dates: List[date]
    equity_values: List[float]
    drawdown_values: List[float]

class StreakAnalysis(BaseModel):
    current_streak: int
    current_streak_type: str  # "winning" or "losing"
    max_winning_streak: int
    max_losing_streak: int
    avg_winning_streak: float
    avg_losing_streak: float

class RiskMetrics(BaseModel):
    value_at_risk: float
    expected_shortfall: float
    volatility: float
    beta: float
    correlation_to_market: float
    risk_score: int  # 1-10 scale
