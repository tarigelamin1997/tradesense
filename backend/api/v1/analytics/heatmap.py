from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from backend.services.analytics.heatmap import HeatmapAnalyticsService

router = APIRouter(tags=["heatmap-analytics"])

def get_heatmap_service(db: Session = Depends(get_db)) -> HeatmapAnalyticsService:
    return HeatmapAnalyticsService(db)

@router.get("/heatmap")
async def get_performance_heatmap(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user),
    service: HeatmapAnalyticsService = Depends(get_heatmap_service)
) -> Dict[str, Any]:
    """
    Get comprehensive performance heatmap data including:
    - Time-based heatmap (hour × weekday)
    - Symbol performance statistics  
    - Actionable insights and recommendations
    """
    try:
        heatmap_data = await service.generate_heatmap_data(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "data": heatmap_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Heatmap analysis failed: {str(e)}"
        )

@router.get("/heatmap/time")
async def get_time_heatmap_only(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user),
    service: HeatmapAnalyticsService = Depends(get_heatmap_service)
) -> Dict[str, Any]:
    """Get only time-based heatmap data for focused analysis"""
    try:
        heatmap_data = await service.generate_heatmap_data(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "data": {
                "time_heatmap": heatmap_data["time_heatmap"],
                "insights": heatmap_data["insights"]["time_insights"],
                "metadata": heatmap_data["metadata"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Time heatmap analysis failed: {str(e)}"
        )

@router.get("/heatmap/symbols")
async def get_symbol_performance_only(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: dict = Depends(get_current_user),
    service: HeatmapAnalyticsService = Depends(get_heatmap_service)
) -> Dict[str, Any]:
    """Get only symbol performance data for focused analysis"""
    try:
        heatmap_data = await service.generate_heatmap_data(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "data": {
                "symbol_stats": heatmap_data["symbol_stats"],
                "insights": heatmap_data["insights"]["symbol_insights"],
                "metadata": heatmap_data["metadata"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Symbol performance analysis failed: {str(e)}"
        )
