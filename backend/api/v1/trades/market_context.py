"""
Market Context API endpoints for trade context and market analysis
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from backend.core.db.session import get_db
from backend.core.security import get_current_user
from backend.services.market_context import market_context_service

router = APIRouter(prefix="/market-context", tags=["market-context"])

@router.get("/symbol/{symbol}")
async def get_market_context(
    symbol: str,
    trade_date: Optional[str] = Query(None, description="Trade date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get market context for a specific symbol and date"""
    try:
        # Parse trade date or use current date
        if trade_date:
            date_obj = datetime.fromisoformat(trade_date)
        else:
            date_obj = datetime.now()

        # Get market context
        context = await market_context_service.get_market_context(symbol, date_obj)

        return {
            "status": "success",
            "data": context
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market context: {e}")

@router.post("/tag-trade")
async def tag_trade_with_context(
    trade_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Tag a trade with market context"""
    try:
        # Add market context to trade
        enhanced_trade = await market_context_service.tag_trade_with_context(trade_data)

        return {
            "status": "success",
            "data": enhanced_trade
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to tag trade: {e}")

@router.get("/conditions")
async def get_market_conditions(
    current_user: dict = Depends(get_current_user)
):
    """Get available market conditions"""
    try:
        from backend.services.market_context import MarketCondition

        conditions = [
            {
                "value": condition.value,
                "label": condition.value.replace("_", " ").title(),
                "description": f"Market showing {condition.value.replace('_', ' ')} characteristics"
            }
            for condition in MarketCondition
        ]

        return {
            "status": "success",
            "data": conditions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conditions: {e}")

@router.get("/sectors")
async def get_sector_performance(
    current_user: dict = Depends(get_current_user)
):
    """Get sector performance data"""
    try:
        # Mock sector data - would integrate with real sector APIs
        sectors = [
            {"name": "Technology", "performance": "outperforming", "change": "+2.3%"},
            {"name": "Healthcare", "performance": "neutral", "change": "+0.1%"},
            {"name": "Financial", "performance": "underperforming", "change": "-1.2%"},
            {"name": "Energy", "performance": "outperforming", "change": "+3.1%"},
            {"name": "Consumer", "performance": "neutral", "change": "+0.5%"}
        ]

        return {
            "status": "success",
            "data": sectors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sector data: {e}")

@router.get("/events")
async def get_economic_events(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user)
):
    """Get economic events for date range"""
    try:
        # Parse dates
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now()

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()

        # Mock economic events - would integrate with economic calendar APIs
        events = [
            {
                "date": start_dt.isoformat(),
                "event": "Non-Farm Payrolls",
                "impact": "high",
                "description": "Monthly employment report"
            },
            {
                "date": start_dt.isoformat(),
                "event": "CPI Release",
                "impact": "high",
                "description": "Consumer Price Index inflation data"
            }
        ]

        return {
            "status": "success",
            "data": events
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {e}")