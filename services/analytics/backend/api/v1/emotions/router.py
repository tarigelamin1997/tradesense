from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from api.deps import get_current_user, get_db
from services.emotional_analytics import EmotionalAnalyticsService
from models.user import User
from pydantic import BaseModel, Field

router = APIRouter(tags=["emotions"])

class EmotionalTagsUpdate(BaseModel):
    trade_id: str
    emotional_tags: List[str] = Field(..., description="List of emotional states")
    reflection_notes: str = Field(..., max_length=2000, description="Reflection notes")
    emotional_score: int = Field(..., ge=1, le=10, description="Emotional control score")
    executed_plan: bool = Field(..., description="Did trader follow plan?")
    post_trade_mood: str = Field(..., max_length=50, description="Post-trade mood")

@router.get("/")
async def get_emotions_overview(
    current_user: User = Depends(get_current_user)
):
    """Get overview of emotion tracking features"""
    return {
        "status": "available",
        "features": [
            "Daily emotion tracking",
            "Trade emotion analysis", 
            "Emotional pattern detection",
            "Mood impact on performance"
        ],
        "endpoints": {
            "daily_tracking": "/api/v1/emotions/daily",
            "trade_emotions": "/api/v1/emotions/trades",
            "patterns": "/api/v1/emotions/patterns"
        }
    }

@router.get("/states")
async def get_emotional_states():
    """Get list of available emotional states"""
    return {
        "emotional_states": EmotionalAnalyticsService.EMOTIONAL_STATES,
        "mood_categories": EmotionalAnalyticsService.MOOD_CATEGORIES
    }

@router.post("/trades/{trade_id}/reflection")
async def update_trade_reflection(
    trade_id: str,
    reflection_data: EmotionalTagsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update trade with emotional reflection data"""
    from models.trade import Trade
    from datetime import datetime
    import json
    
    # Get trade
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    # Update emotional data
    trade.emotional_tags = json.dumps(reflection_data.emotional_tags)
    trade.reflection_notes = reflection_data.reflection_notes
    trade.emotional_score = reflection_data.emotional_score
    trade.executed_plan = reflection_data.executed_plan
    trade.post_trade_mood = reflection_data.post_trade_mood
    trade.reflection_timestamp = datetime.now()
    
    db.commit()
    db.refresh(trade)
    
    return {"message": "Reflection updated successfully", "trade_id": trade_id}

@router.get("/analytics/performance-correlation")
async def get_emotion_performance_correlation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get correlation between emotions and performance"""
    service = EmotionalAnalyticsService(db, current_user.id)
    return service.get_emotional_performance_correlation()

@router.get("/analytics/plan-execution")
async def get_plan_execution_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze performance when following vs breaking plan"""
    service = EmotionalAnalyticsService(db, current_user.id)
    return service.get_plan_execution_analysis()

@router.get("/analytics/trends")
async def get_emotional_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emotional trends over time"""
    service = EmotionalAnalyticsService(db, current_user.id)
    return service.get_emotional_trends_over_time(days)

@router.get("/insights")
async def get_emotional_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get actionable emotional insights"""
    service = EmotionalAnalyticsService(db, current_user.id)
    return {"insights": service.get_emotional_insights()}
