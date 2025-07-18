from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import pandas as pd
import io

from api.deps import get_current_user, get_db
from models.user import User
from models.trade import Trade
from .schemas import PortfolioResponse, PositionResponse, AllocationResponse, PerformanceResponse
from .service import PortfolioService

router = APIRouter(tags=["portfolio"])

@router.get("", response_model=PortfolioResponse)
async def get_portfolio(
    timeframe: str = Query("30d", description="Timeframe: 7d, 30d, 90d, 1y, all"),
    asset_class: Optional[str] = Query(None, description="Filter by asset class"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio overview with positions and performance"""
    service = PortfolioService(db)
    return service.get_portfolio(
        user_id=current_user.id,
        timeframe=timeframe,
        asset_class=asset_class
    )

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    asset_class: Optional[str] = Query(None),
    sort_by: str = Query("value", description="Sort by: value, pnl, allocation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current positions"""
    service = PortfolioService(db)
    return service.get_positions(
        user_id=current_user.id,
        asset_class=asset_class,
        sort_by=sort_by
    )

@router.get("/performance", response_model=List[PerformanceResponse])
async def get_performance(
    timeframe: str = Query("30d"),
    interval: str = Query("daily", description="Interval: daily, weekly, monthly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio performance over time"""
    service = PortfolioService(db)
    return service.get_performance(
        user_id=current_user.id,
        timeframe=timeframe,
        interval=interval
    )

@router.get("/allocations", response_model=List[AllocationResponse])
async def get_allocations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset allocation breakdown"""
    service = PortfolioService(db)
    return service.get_allocations(user_id=current_user.id)

@router.get("/export")
async def export_portfolio(
    format: str = Query("csv", description="Export format: csv, excel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export portfolio data"""
    service = PortfolioService(db)
    positions = service.get_positions(user_id=current_user.id)
    
    # Convert to DataFrame
    df = pd.DataFrame([p.dict() for p in positions])
    
    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv"
    else:  # excel
        output = io.BytesIO()
        df.to_excel(output, index=False)
        content = output.getvalue()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"portfolio_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/risk-metrics")
async def get_risk_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio risk metrics"""
    service = PortfolioService(db)
    return service.calculate_risk_metrics(user_id=current_user.id)