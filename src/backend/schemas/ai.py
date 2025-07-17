"""
AI Intelligence Schemas
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class TradeScoreResponse(BaseModel):
    overall_score: float = Field(..., ge=0, le=100)
    execution_score: float = Field(..., ge=0, le=100)
    timing_score: float = Field(..., ge=0, le=100)
    strategy_score: float = Field(..., ge=0, le=100)
    risk_reward_ratio: float
    pnl: float
    pnl_percentage: float
    insights: List[str]
    recommendations: List[str]
    market_context: Dict[str, Any]


class TradeCritiqueResponse(BaseModel):
    summary: str
    suggestion: str
    confidence: int = Field(..., ge=1, le=10)
    tags: List[str]
    technical_analysis: str
    psychological_analysis: str
    risk_assessment: str


class PatternDetection(BaseModel):
    pattern_type: str
    frequency: int
    impact_on_pnl: float
    description: str
    examples: List[str]
    recommendations: str


class StreakAnalysis(BaseModel):
    current_streak: int
    streak_type: str = Field(..., pattern="^(winning|losing|neutral)$")
    best_streak: int
    worst_streak: int
    average_streak_length: float


class BehavioralInsightsResponse(BaseModel):
    emotional_state: str
    consistency_rating: float
    discipline_score: float
    risk_profile: str
    patterns_detected: List[PatternDetection]
    improvement_areas: List[str]
    streaks: StreakAnalysis


class EdgeStrengthResponse(BaseModel):
    strategy: str
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    kelly_criterion: float
    sample_size: int
    confidence_level: float
    market_conditions: List[str]


class PatternDetectionResponse(BaseModel):
    pattern_type: str
    frequency: int
    impact_on_pnl: float
    description: str
    examples: List[str]
    recommendations: str


class MarketContextResponse(BaseModel):
    regime: str = Field(..., pattern="^(bull|bear|sideways)$")
    volatility: str = Field(..., pattern="^(low|medium|high)$")
    trend_strength: float
    support_levels: List[float]
    resistance_levels: List[float]
    recommendation: str


class EmotionMetric(BaseModel):
    emotion: str
    frequency: float
    impact: float


class EmotionalAnalyticsResponse(BaseModel):
    dominant_emotions: List[EmotionMetric]
    emotional_consistency: float
    best_performing_emotion: str
    worst_performing_emotion: str
    recommendations: List[str]


class PatternMatch(BaseModel):
    pattern: str
    similarity: float
    historical_outcome: str


class PreTradeAnalysisRequest(BaseModel):
    symbol: str
    side: str = Field(..., pattern="^(long|short)$")
    entry_price: float
    quantity: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: Optional[str] = None
    confidence_level: Optional[int] = Field(None, ge=1, le=10)


class PreTradeAnalysisResponse(BaseModel):
    should_take_trade: bool
    confidence_score: float
    risk_score: float
    pattern_matches: List[PatternMatch]
    market_alignment: bool
    psychological_readiness: float
    suggested_position_size: float
    warnings: List[str]


class AIInsightsSummaryResponse(BaseModel):
    trade_score: TradeScoreResponse
    critique: TradeCritiqueResponse
    behavioral_insights: BehavioralInsightsResponse
    edge_strength: List[EdgeStrengthResponse]
    market_context: MarketContextResponse
    emotional_analytics: EmotionalAnalyticsResponse


class RecommendationsResponse(BaseModel):
    immediate: List[str]
    weekly: List[str]
    improvement_plan: List[str]


class RiskAnalysisResponse(BaseModel):
    current_risk_score: float
    var_95: float
    var_99: float
    max_drawdown_predicted: float
    position_sizing_recommendation: float
    warnings: List[str]