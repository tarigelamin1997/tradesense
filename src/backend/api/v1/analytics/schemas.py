
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class AnalyticsFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    strategy_filter: Optional[str] = None

class StrategyStats(BaseModel):
    name: str
    total_trades: int
    win_rate: float
    avg_return: float
    total_pnl: float
    profit_factor: float
    best_trade: float
    worst_trade: float

class EmotionImpact(BaseModel):
    emotion: str
    trade_count: int
    win_rate: float
    net_pnl: float
    avg_pnl: float
    impact_score: float  # Negative = harmful, Positive = helpful

class TriggerAnalysis(BaseModel):
    trigger: str
    usage_count: int
    win_rate: float
    net_result: float
    avg_impact: float
    frequency_rank: int

class ConfidenceAnalysis(BaseModel):
    confidence_level: int
    trade_count: int
    win_rate: float
    avg_pnl: float
    avg_return: float

class EmotionalLeak(BaseModel):
    category: str  # emotion, trigger, or pattern
    name: str
    cost: float
    frequency: int
    description: str
    severity: str  # low, medium, high, critical

class DailyTimelineData(BaseModel):
    date: date
    pnl: float
    trade_count: int
    dominant_emotion: Optional[str]
    emotion_emoji: Optional[str]
    trades: List[Dict[str, Any]]
    mood_score: Optional[int]
    reflection_summary: Optional[str]

class TimelineResponse(BaseModel):
    timeline_data: Dict[str, DailyTimelineData]  # date string -> data
    date_range: Dict[str, date]  # start_date, end_date
    total_days: int
    trading_days: int
    best_day: Optional[DailyTimelineData]
    worst_day: Optional[DailyTimelineData]
    emotional_patterns: Dict[str, Any]

class AnalyticsSummaryResponse(BaseModel):
    # Core Performance
    total_trades: int
    total_pnl: float
    overall_win_rate: float
    
    # Strategy Analysis
    strategy_stats: List[StrategyStats]
    best_strategy: Optional[str]
    worst_strategy: Optional[str]
    
    # Emotional Intelligence
    emotion_impact: List[EmotionImpact]
    trigger_analysis: List[TriggerAnalysis]
    confidence_analysis: List[ConfidenceAnalysis]
    
    # Key Insights
    emotional_leaks: List[EmotionalLeak]
    top_emotional_cost: float
    most_profitable_emotion: Optional[str]
    most_costly_emotion: Optional[str]
    
    # Behavioral Patterns
    overconfidence_bias: float
    hesitation_cost: float
    fomo_impact: float
    revenge_trading_cost: float
    
    # Performance Trends
    confidence_vs_performance_correlation: float
    emotional_consistency_score: float
    
    # Summary Metrics
    generated_at: datetime
    period_analyzed: str
