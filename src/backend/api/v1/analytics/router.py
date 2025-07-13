from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import logging

from core.db.session import get_db
from api.deps import get_current_user
from core.exceptions import (
    TradeSenseException, NotFoundError, ValidationError, 
    DatabaseError, ExternalServiceError
)
from core.responses import (
    create_success_response, create_error_response, 
    AnalyticsResponse
)
from .service import AnalyticsService
from .schemas import AnalyticsSummaryResponse, AnalyticsFilters, TimelineResponse
from .edge_strength import get_edge_strength_analysis
from . import streaks, heatmap, playbook_comparison, performance

logger = logging.getLogger(__name__)

router = APIRouter()

# Include sub-routers
router.include_router(streaks.router, prefix="/streaks", tags=["streaks"])
router.include_router(heatmap.router, prefix="/heatmap", tags=["heatmap"])
router.include_router(playbook_comparison.router, prefix="/playbooks", tags=["playbook-comparison"])
router.include_router(performance.router, tags=["performance"])


@router.get("/health")
async def analytics_health():
    return {"status": "healthy", "service": "analytics"}

def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("/summary", response_model=AnalyticsResponse)
async def get_analytics_summary(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive analytics summary for trading performance"""
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date must be before end date")
        
        filters = AnalyticsFilters(
            start_date=start_date,
            end_date=end_date,
            strategy_filter=strategy_filter
        )

        summary = await service.get_analytics_summary(
            user_id=current_user.id,
            filters=filters
        )

        return create_success_response(
            data=summary.dict() if hasattr(summary, 'dict') else summary,
            message="Analytics summary retrieved successfully",
            request_id=request.headers.get("x-request-id")
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error in analytics summary: {e.message}")
        raise e
    except NotFoundError as e:
        logger.warning(f"Data not found for analytics summary: {e.message}")
        raise e
    except DatabaseError as e:
        logger.error(f"Database error in analytics summary: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in analytics summary: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Analytics calculation failed: {str(e)}")

@router.get("/emotion-impact", response_model=AnalyticsResponse)
async def get_emotion_impact(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get emotional impact analysis on trading performance"""
    try:
        data = await service.get_emotion_impact_analysis(current_user.id)
        return create_success_response(
            data=data,
            message="Emotion impact analysis completed",
            request_id=request.headers.get("x-request-id")
        )
    except NotFoundError as e:
        logger.warning(f"Data not found for emotion impact: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Error in emotion impact analysis: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Emotion analysis failed: {str(e)}")

@router.get("/strategy-performance", response_model=AnalyticsResponse)
async def get_strategy_performance(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get detailed strategy performance breakdown"""
    try:
        data = await service.get_strategy_performance_analysis(current_user.id)
        return create_success_response(
            data=data,
            message="Strategy performance analysis completed",
            request_id=request.headers.get("x-request-id")
        )
    except NotFoundError as e:
        logger.warning(f"Data not found for strategy performance: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Error in strategy performance analysis: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Strategy analysis failed: {str(e)}")

@router.get("/confidence-correlation", response_model=AnalyticsResponse)
async def get_confidence_correlation(
    request: Request,
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get confidence score vs performance correlation"""
    try:
        data = await service.get_confidence_performance_correlation(current_user.id)
        return create_success_response(
            data=data,
            message="Confidence correlation analysis completed",
            request_id=request.headers.get("x-request-id")
        )
    except NotFoundError as e:
        logger.warning(f"Data not found for confidence correlation: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Error in confidence correlation analysis: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Confidence analysis failed: {str(e)}")

@router.get("/timeline", response_model=AnalyticsResponse)
async def get_timeline_analysis(
    request: Request,
    start_date: Optional[date] = Query(None, description="Timeline start date"),
    end_date: Optional[date] = Query(None, description="Timeline end date"),
    current_user: dict = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get timeline heatmap data with daily P&L and emotions"""
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date must be before end date")
        
        data = await service.get_timeline_analysis(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        
        return create_success_response(
            data=data,
            message="Timeline analysis completed",
            request_id=request.headers.get("x-request-id")
        )
    except ValidationError as e:
        logger.warning(f"Validation error in timeline analysis: {e.message}")
        raise e
    except NotFoundError as e:
        logger.warning(f"Data not found for timeline analysis: {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Error in timeline analysis: {str(e)}", exc_info=True)
        raise ExternalServiceError(f"Timeline analysis failed: {str(e)}")