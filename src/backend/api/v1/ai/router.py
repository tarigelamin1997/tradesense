"""
AI Intelligence API Router
Exposes AI-powered analytics, insights, and predictions
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db.session import get_db
from api.deps import get_current_user
from models.user import User
from models.trade import Trade
from services.trade_intelligence_engine import TradeIntelligenceEngine
from services.critique_engine import AITradeAnalyzer
from services.behavioral_analytics import BehavioralAnalyticsService
from services.edge_strength import EdgeStrengthAnalyzer
from services.pattern_detection import PatternDetectionService
from services.emotional_analytics import EmotionalAnalyticsService
from services.market_context import MarketContextService
from services.feature_flag_service import FeatureFlagService

from schemas.ai import (
    TradeScoreResponse,
    TradeCritiqueResponse,
    BehavioralInsightsResponse,
    EdgeStrengthResponse,
    PatternDetectionResponse,
    MarketContextResponse,
    EmotionalAnalyticsResponse,
    PreTradeAnalysisRequest,
    PreTradeAnalysisResponse,
    AIInsightsSummaryResponse,
    RecommendationsResponse,
    RiskAnalysisResponse
)

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])

# Initialize services
trade_intelligence = TradeIntelligenceEngine()
ai_analyzer = AITradeAnalyzer()
behavioral_service = BehavioralAnalyticsService()
edge_analyzer = EdgeStrengthAnalyzer()
pattern_service = PatternDetectionService()
emotional_service = EmotionalAnalyticsService()
market_service = MarketContextService()


@router.get("/trades/{trade_id}/score", response_model=TradeScoreResponse)
async def get_trade_score(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered trade quality score and analysis"""
    # Check feature flag
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    # Get trade
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Analyze trade
    analysis = trade_intelligence.analyze_trade_quality({
        'entry_price': trade.entry_price,
        'exit_price': trade.exit_price,
        'quantity': trade.quantity,
        'symbol': trade.symbol,
        'strategy': trade.strategy,
        'confidence_level': trade.confidence_level,
        'entry_date': trade.entry_date,
        'exit_date': trade.exit_date
    })
    
    return TradeScoreResponse(**analysis)


@router.post("/trades/score/bulk", response_model=Dict[str, TradeScoreResponse])
async def get_trade_scores_bulk(
    trade_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI scores for multiple trades"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    # Get trades
    trades = db.query(Trade).filter(
        Trade.id.in_(trade_ids),
        Trade.user_id == current_user.id
    ).all()
    
    results = {}
    for trade in trades:
        analysis = trade_intelligence.analyze_trade_quality({
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'quantity': trade.quantity,
            'symbol': trade.symbol,
            'strategy': trade.strategy,
            'confidence_level': trade.confidence_level,
            'entry_date': trade.entry_date,
            'exit_date': trade.exit_date
        })
        results[str(trade.id)] = TradeScoreResponse(**analysis)
    
    return results


@router.get("/behavioral/insights", response_model=BehavioralInsightsResponse)
async def get_behavioral_insights(
    timeframe: str = Query("month", regex="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get behavioral analytics and patterns"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    # Calculate date range
    end_date = datetime.now()
    if timeframe == "week":
        start_date = end_date - timedelta(days=7)
    elif timeframe == "month":
        start_date = end_date - timedelta(days=30)
    elif timeframe == "quarter":
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)
    
    insights = behavioral_service.analyze_trader_behavior(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )
    
    return BehavioralInsightsResponse(**insights)


@router.get("/patterns/detect", response_model=List[PatternDetectionResponse])
async def detect_patterns(
    timeframe: str = Query("month", regex="^(week|month|all)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect trading patterns using AI"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    patterns = pattern_service.detect_patterns(
        user_id=current_user.id,
        timeframe=timeframe,
        db=db
    )
    
    return [PatternDetectionResponse(**p) for p in patterns]


@router.get("/edge/strength", response_model=List[EdgeStrengthResponse])
async def get_edge_strength(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze edge strength by strategy"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    edge_analysis = edge_analyzer.analyze_all_strategies(
        user_id=current_user.id,
        db=db
    )
    
    return [EdgeStrengthResponse(**e) for e in edge_analysis]


@router.get("/edge/strategy/{strategy}", response_model=EdgeStrengthResponse)
async def get_edge_by_strategy(
    strategy: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get edge strength for specific strategy"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    edge = edge_analyzer.analyze_strategy(
        user_id=current_user.id,
        strategy=strategy,
        db=db
    )
    
    if not edge:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return EdgeStrengthResponse(**edge)


@router.get("/market/context", response_model=MarketContextResponse)
async def get_market_context(
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current market context and regime"""
    context = market_service.analyze_market_context(symbol)
    return MarketContextResponse(**context)


@router.get("/market/regime")
async def get_market_regime(
    current_user: User = Depends(get_current_user)
):
    """Get current market regime analysis"""
    regime = market_service.detect_market_regime()
    return regime


@router.get("/emotional/analytics", response_model=EmotionalAnalyticsResponse)
async def get_emotional_analytics(
    timeframe: str = Query("month", regex="^(week|month|quarter)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze emotional impact on trading"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    analytics = emotional_service.analyze_emotional_impact(
        user_id=current_user.id,
        timeframe=timeframe,
        db=db
    )
    
    return EmotionalAnalyticsResponse(**analytics)


@router.get("/emotional/impact")
async def get_emotional_impact(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed emotional impact analysis"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    impact = emotional_service.calculate_emotion_performance_impact(
        user_id=current_user.id,
        db=db
    )
    
    return impact


@router.post("/pre-trade/analyze", response_model=PreTradeAnalysisResponse)
async def analyze_pre_trade(
    trade: PreTradeAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a potential trade before execution"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    # Perform pre-trade analysis
    analysis = trade_intelligence.pre_trade_analysis(
        user_id=current_user.id,
        trade_data=trade.dict(),
        db=db
    )
    
    return PreTradeAnalysisResponse(**analysis)


@router.get("/insights/summary", response_model=AIInsightsSummaryResponse)
async def get_ai_insights_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive AI insights summary"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    # Get latest trade for scoring
    latest_trade = db.query(Trade).filter(
        Trade.user_id == current_user.id
    ).order_by(Trade.exit_date.desc()).first()
    
    if not latest_trade:
        raise HTTPException(status_code=404, detail="No trades found")
    
    # Gather all insights
    trade_score = trade_intelligence.analyze_trade_quality({
        'entry_price': latest_trade.entry_price,
        'exit_price': latest_trade.exit_price,
        'quantity': latest_trade.quantity,
        'symbol': latest_trade.symbol,
        'strategy': latest_trade.strategy,
        'confidence_level': latest_trade.confidence_level,
        'entry_date': latest_trade.entry_date,
        'exit_date': latest_trade.exit_date
    })
    
    critique = await ai_analyzer.analyze_trade(latest_trade)
    
    behavioral_insights = behavioral_service.analyze_trader_behavior(
        user_id=current_user.id,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        db=db
    )
    
    edge_strength = edge_analyzer.analyze_all_strategies(
        user_id=current_user.id,
        db=db
    )
    
    market_context = market_service.analyze_market_context(latest_trade.symbol)
    
    emotional_analytics = emotional_service.analyze_emotional_impact(
        user_id=current_user.id,
        timeframe="month",
        db=db
    )
    
    return AIInsightsSummaryResponse(
        trade_score=trade_score,
        critique={
            'summary': critique.summary,
            'suggestion': critique.suggestion,
            'confidence': critique.confidence,
            'tags': critique.tags,
            'technical_analysis': critique.technical_analysis,
            'psychological_analysis': critique.psychological_analysis,
            'risk_assessment': critique.risk_assessment
        },
        behavioral_insights=behavioral_insights,
        edge_strength=edge_strength,
        market_context=market_context,
        emotional_analytics=emotional_analytics
    )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered trading recommendations"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    recommendations = trade_intelligence.generate_personalized_recommendations(
        user_id=current_user.id,
        db=db
    )
    
    return RecommendationsResponse(**recommendations)


@router.get("/risk/analysis", response_model=RiskAnalysisResponse)
async def get_risk_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI-powered risk analysis"""
    if not FeatureFlagService.is_enabled("ai_trade_insights", current_user):
        raise HTTPException(status_code=403, detail="AI insights not available in your plan")
    
    risk_analysis = trade_intelligence.analyze_portfolio_risk(
        user_id=current_user.id,
        db=db
    )
    
    return RiskAnalysisResponse(**risk_analysis)