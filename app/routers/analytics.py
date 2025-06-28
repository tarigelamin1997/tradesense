
"""
Analytics Router
Handles trade analytics, performance metrics, and data visualization endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import pandas as pd
import logging

from app.services.analytics_service import AnalyticsService
from app.services.auth_service import get_current_user
from app.models.analytics import (
    PerformanceMetrics, TradeAnalysis, EquityCurve, 
    StreakAnalysis, RiskMetrics
)

router = APIRouter()
analytics_service = AnalyticsService()
logger = logging.getLogger(__name__)

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data(user=Depends(get_current_user)):
    """Get main dashboard analytics data"""
    try:
        dashboard_data = await analytics_service.get_dashboard_metrics(user.id)
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard data failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard data")

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    symbol: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Get detailed performance metrics"""
    try:
        metrics = await analytics_service.calculate_performance_metrics(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            symbol=symbol
        )
        return metrics
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate metrics")

@router.get("/equity-curve")
async def get_equity_curve(
    period: str = "daily",
    user=Depends(get_current_user)
):
    """Get equity curve data for charting"""
    try:
        curve_data = await analytics_service.generate_equity_curve(
            user_id=user.id,
            period=period
        )
        return {
            "success": True,
            "data": curve_data,
            "period": period
        }
    except Exception as e:
        logger.error(f"Equity curve failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate equity curve")

@router.get("/streaks", response_model=StreakAnalysis)
async def get_streak_analysis(user=Depends(get_current_user)):
    """Get winning/losing streak analysis"""
    try:
        streaks = await analytics_service.analyze_streaks(user.id)
        return streaks
    except Exception as e:
        logger.error(f"Streak analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze streaks")

@router.get("/risk-metrics", response_model=RiskMetrics)
async def get_risk_metrics(user=Depends(get_current_user)):
    """Get risk assessment and metrics"""
    try:
        risk_data = await analytics_service.calculate_risk_metrics(user.id)
        return risk_data
    except Exception as e:
        logger.error(f"Risk metrics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate risk metrics")

@router.post("/upload-trades")
async def upload_trade_data(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Upload and process trade data from CSV/Excel"""
    try:
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Invalid file format")
        
        # Read file content
        content = await file.read()
        
        # Process the uploaded data
        result = await analytics_service.process_trade_upload(
            user_id=user.id,
            file_content=content,
            filename=file.filename
        )
        
        logger.info(f"Trade data uploaded for user {user.id}: {file.filename}")
        return {
            "success": True,
            "message": f"Processed {result['trades_count']} trades",
            "summary": result
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/heatmap")
async def get_performance_heatmap(
    metric: str = "pnl",
    groupby: str = "symbol",
    user=Depends(get_current_user)
):
    """Get performance heatmap data"""
    try:
        heatmap_data = await analytics_service.generate_heatmap(
            user_id=user.id,
            metric=metric,
            groupby=groupby
        )
        return {
            "success": True,
            "data": heatmap_data,
            "metric": metric,
            "groupby": groupby
        }
    except Exception as e:
        logger.error(f"Heatmap failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")

@router.get("/trades")
async def get_trades(
    limit: int = 100,
    offset: int = 0,
    symbol: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user=Depends(get_current_user)
):
    """Get paginated trade data with filters"""
    try:
        trades = await analytics_service.get_trades(
            user_id=user.id,
            limit=limit,
            offset=offset,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "success": True,
            "trades": trades,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(trades) == limit
            }
        }
    except Exception as e:
        logger.error(f"Get trades failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trades")
