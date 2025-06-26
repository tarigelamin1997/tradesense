
"""
Market Context API endpoints for TradeSense
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from backend.services.market_context import market_context_service
from backend.core.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market-context", tags=["market-context"])

@router.get("/symbol/{symbol}")
async def get_market_context(
    symbol: str,
    trade_date: Optional[date] = Query(None, description="Trade date (YYYY-MM-DD)")
):
    """Get market context for a specific symbol and date"""
    try:
        if not trade_date:
            trade_date = datetime.now()
        else:
            trade_date = datetime.combine(trade_date, datetime.min.time())
            
        context = await market_context_service.get_market_context(symbol, trade_date)
        
        return success_response(
            data=context,
            message=f"Market context retrieved for {symbol}"
        )
        
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        return error_response(
            message="Failed to retrieve market context",
            details=str(e)
        )

@router.post("/tag-trade")
async def tag_trade_with_context(trade_data: Dict[str, Any]):
    """Add market context tags to a trade"""
    try:
        tagged_trade = await market_context_service.tag_trade_with_context(trade_data)
        
        return success_response(
            data=tagged_trade,
            message="Trade tagged with market context"
        )
        
    except Exception as e:
        logger.error(f"Error tagging trade: {e}")
        return error_response(
            message="Failed to tag trade with market context",
            details=str(e)
        )

@router.get("/conditions")
async def get_market_conditions():
    """Get available market condition types"""
    try:
        conditions = [
            {"value": "bullish", "label": "Bullish", "description": "Rising market trend"},
            {"value": "bearish", "label": "Bearish", "description": "Declining market trend"},
            {"value": "sideways", "label": "Sideways", "description": "Horizontal market trend"},
            {"value": "volatile", "label": "Volatile", "description": "High price volatility"},
            {"value": "low_volume", "label": "Low Volume", "description": "Below average trading volume"},
            {"value": "high_volume", "label": "High Volume", "description": "Above average trading volume"}
        ]
        
        return success_response(
            data=conditions,
            message="Market conditions retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting market conditions: {e}")
        return error_response(
            message="Failed to retrieve market conditions",
            details=str(e)
        )

@router.get("/sectors")
async def get_sector_performance():
    """Get sector performance data"""
    try:
        sectors = [
            {"name": "Technology", "performance": "outperforming", "change": "+2.3%"},
            {"name": "Healthcare", "performance": "neutral", "change": "+0.1%"},
            {"name": "Financial", "performance": "underperforming", "change": "-1.2%"},
            {"name": "Energy", "performance": "outperforming", "change": "+3.1%"},
            {"name": "Consumer", "performance": "neutral", "change": "+0.4%"}
        ]
        
        return success_response(
            data=sectors,
            message="Sector performance retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting sector performance: {e}")
        return error_response(
            message="Failed to retrieve sector performance", 
            details=str(e)
        )

@router.get("/events")
async def get_economic_events(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Get economic events for date range"""
    try:
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = start_date
            
        # Simulated economic events
        events = [
            {
                "date": start_date.isoformat(),
                "event": "CPI Release",
                "impact": "high",
                "description": "Consumer Price Index monthly data"
            },
            {
                "date": start_date.isoformat(),
                "event": "Non-Farm Payrolls",
                "impact": "high", 
                "description": "Monthly employment report"
            }
        ]
        
        return success_response(
            data=events,
            message="Economic events retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting economic events: {e}")
        return error_response(
            message="Failed to retrieve economic events",
            details=str(e)
        )
