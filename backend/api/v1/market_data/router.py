
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.services.market_data_service import market_data_service

router = APIRouter()

@router.post("/enrich-trades")
async def enrich_user_trades(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enrich user's trades with market context data"""
    try:
        enriched_count = await market_data_service.enrich_trades_with_market_context(
            current_user.id
        )
        
        return {
            "success": True,
            "enriched_trades": enriched_count,
            "message": f"Successfully enriched {enriched_count} trades with market context"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enrich trades: {str(e)}"
        )

@router.get("/conditions/{symbol}")
async def get_current_market_conditions(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get current market conditions for a symbol"""
    try:
        from datetime import datetime
        conditions = await market_data_service.get_market_conditions(
            symbol, 
            datetime.now()
        )
        
        return {
            "symbol": symbol,
            "conditions": conditions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market conditions: {str(e)}"
        )

@router.get("/analytics/by-conditions")
async def get_performance_by_market_conditions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trading performance analytics grouped by market conditions"""
    try:
        from backend.models.trade import Trade
        from sqlalchemy import func
        
        # Query trades with market context
        trades = db.query(Trade).filter(
            Trade.user_id == current_user.id,
            Trade.market_context.isnot(None)
        ).all()
        
        # Group by market conditions
        condition_analytics = {}
        
        for trade in trades:
            if not trade.market_context:
                continue
                
            conditions_key = f"{trade.market_context.get('volatility', 'unknown')}_" \
                           f"{trade.market_context.get('trend', 'unknown')}_" \
                           f"{trade.market_context.get('volume', 'unknown')}"
            
            if conditions_key not in condition_analytics:
                condition_analytics[conditions_key] = {
                    "trades": 0,
                    "wins": 0,
                    "total_pnl": 0,
                    "conditions": trade.market_context
                }
            
            condition_analytics[conditions_key]["trades"] += 1
            if trade.pnl > 0:
                condition_analytics[conditions_key]["wins"] += 1
            condition_analytics[conditions_key]["total_pnl"] += trade.pnl
        
        # Calculate win rates and average P&L
        for key, analytics in condition_analytics.items():
            analytics["win_rate"] = (analytics["wins"] / analytics["trades"]) * 100 if analytics["trades"] > 0 else 0
            analytics["avg_pnl"] = analytics["total_pnl"] / analytics["trades"] if analytics["trades"] > 0 else 0
        
        return {
            "success": True,
            "analytics": condition_analytics,
            "total_analyzed_trades": len(trades)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze performance by conditions: {str(e)}"
        )
"""
Market Data API Router
Provides real-time market data endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from backend.services.real_time_market_service import real_time_market_service
from backend.api.deps import get_current_user

router = APIRouter()

@router.get("/quote/{symbol}")
async def get_live_quote(
    symbol: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get live quote for a symbol"""
    try:
        quote = await real_time_market_service.get_live_quote(symbol.upper())
        return {"success": True, "data": quote}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{symbol}")
async def get_market_sentiment(
    symbol: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get market sentiment for a symbol"""
    try:
        sentiment = await real_time_market_service.get_market_sentiment(symbol.upper())
        return {"success": True, "data": sentiment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regime")
async def get_market_regime(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current market regime"""
    try:
        regime = await real_time_market_service.get_market_regime()
        return {"success": True, "data": regime}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-trade")
async def enhance_trade_with_context(
    trade_data: Dict[str, Any],
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Enhance trade data with real-time market context"""
    try:
        enhanced_trade = await real_time_market_service.enhance_trade_with_market_context(trade_data)
        return {"success": True, "data": enhanced_trade}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/watchlist")
async def get_watchlist_quotes(
    symbols: str,  # Comma-separated symbols
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get quotes for multiple symbols"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        quotes = []
        
        for symbol in symbol_list:
            quote = await real_time_market_service.get_live_quote(symbol)
            quotes.append(quote)
        
        return {"success": True, "data": quotes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
