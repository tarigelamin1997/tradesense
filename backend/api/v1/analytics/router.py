
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date

from backend.core.db.session import get_db
from backend.core.security import get_current_user
from .service import AnalyticsService
from .schemas import AnalyticsSummaryResponse, AnalyticsFilters, TimelineResponse

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive analytics summary for trading performance"""
    try:
        filters = AnalyticsFilters(
            start_date=start_date,
            end_date=end_date,
            strategy_filter=strategy_filter
        )
        
        summary = await service.get_analytics_summary(
            user_id=current_user["user_id"],
            filters=filters
        )
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics calculation failed: {str(e)}")

@router.get("/emotion-impact")
async def get_emotion_impact(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get emotional impact analysis on trading performance"""
    try:
        return await service.get_emotion_impact_analysis(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emotion analysis failed: {str(e)}")

@router.get("/strategy-performance")
async def get_strategy_performance(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed strategy performance breakdown"""
    try:
        return await service.get_strategy_performance_analysis(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy analysis failed: {str(e)}")

@router.get("/confidence-correlation")
async def get_confidence_correlation(
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get confidence score vs performance correlation"""
    try:
        return await service.get_confidence_performance_correlation(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confidence analysis failed: {str(e)}")

@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline_analysis(
    start_date: Optional[date] = Query(None, description="Timeline start date"),
    end_date: Optional[date] = Query(None, description="Timeline end date"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get timeline heatmap data with daily P&L and emotions"""
    try:
        return await service.get_timeline_analysis(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline analysis failed: {str(e)}")
