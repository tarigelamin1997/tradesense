
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
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from backend.api.deps import get_current_user, get_db
from backend.services.real_time_market_service import market_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/subscribe/{symbol}")
async def subscribe_to_symbol(
    symbol: str,
    provider: str = "yahoo_finance",
    user_id: str = Depends(get_current_user)
):
    """Subscribe to real-time market data for a symbol"""
    try:
        success = await market_service.subscribe_to_symbol(symbol.upper(), provider)
        if success:
            return {
                "success": True,
                "message": f"Subscribed to {symbol.upper()} on {provider}",
                "symbol": symbol.upper(),
                "provider": provider
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to subscribe to {symbol}")
    except Exception as e:
        logger.error(f"Error subscribing to {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unsubscribe/{symbol}")
async def unsubscribe_from_symbol(
    symbol: str,
    user_id: str = Depends(get_current_user)
):
    """Unsubscribe from real-time market data for a symbol"""
    try:
        success = await market_service.unsubscribe_from_symbol(symbol.upper())
        return {
            "success": success,
            "message": f"Unsubscribed from {symbol.upper()}" if success else f"Not subscribed to {symbol.upper()}",
            "symbol": symbol.upper()
        }
    except Exception as e:
        logger.error(f"Error unsubscribing from {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{symbol}")
async def get_market_data(
    symbol: str,
    user_id: str = Depends(get_current_user)
):
    """Get current market data for a symbol"""
    try:
        data = market_service.get_market_data(symbol.upper())
        if data:
            return {
                "success": True,
                "symbol": symbol.upper(),
                "data": data["data"],
                "timestamp": data["timestamp"].isoformat(),
                "provider": data["provider"]
            }
        else:
            # Try to subscribe and get data
            await market_service.subscribe_to_symbol(symbol.upper())
            return {
                "success": False,
                "message": f"No data available for {symbol.upper()}. Subscription initiated.",
                "symbol": symbol.upper()
            }
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscriptions")
async def get_active_subscriptions(user_id: str = Depends(get_current_user)):
    """Get all active market data subscriptions"""
    try:
        subscriptions = market_service.get_all_subscriptions()
        return {
            "success": True,
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        }
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/{symbol}")
async def get_market_context(
    symbol: str,
    trade_time: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Get market context for a symbol at a specific time"""
    try:
        # Parse trade time if provided
        if trade_time:
            try:
                parsed_time = datetime.fromisoformat(trade_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid trade_time format. Use ISO format.")
        else:
            parsed_time = datetime.now()
        
        context = await market_service.get_market_context_for_trade(symbol.upper(), parsed_time)
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "context": context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market context for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-trade-timing")
async def analyze_trade_timing(
    trade_data: Dict,
    user_id: str = Depends(get_current_user)
):
    """Analyze trade timing against market conditions"""
    try:
        symbol = trade_data.get("symbol", "").upper()
        entry_time = trade_data.get("entry_time")
        
        if not symbol or not entry_time:
            raise HTTPException(status_code=400, detail="Symbol and entry_time are required")
        
        # Parse entry time
        try:
            parsed_entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid entry_time format")
        
        # Get market context
        context = await market_service.get_market_context_for_trade(symbol, parsed_entry_time)
        
        # Analyze timing
        analysis = {
            "symbol": symbol,
            "entry_time": entry_time,
            "market_context": context,
            "timing_analysis": {
                "market_volatility": context.get("volatility_indicator", "UNKNOWN"),
                "market_trend": context.get("market_trend", "UNKNOWN"),
                "timing_score": _calculate_timing_score(context),
                "recommendations": _get_timing_recommendations(context)
            }
        }
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trade timing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_timing_score(context: Dict) -> int:
    """Calculate a timing score from 1-10 based on market context"""
    try:
        score = 5  # Base score
        
        # Adjust based on volatility
        volatility = context.get("volatility_indicator", "UNKNOWN")
        if volatility == "LOW":
            score += 1
        elif volatility == "HIGH":
            score -= 1
        
        # Adjust based on market state
        market_state = context.get("market_state", "UNKNOWN")
        if market_state == "REGULAR":
            score += 1
        elif market_state in ["PRE", "POST"]:
            score -= 1
        
        # Adjust based on support/resistance
        support_resistance = context.get("support_resistance", {})
        if support_resistance:
            distance_to_support = support_resistance.get("distance_to_support", 0)
            distance_to_resistance = support_resistance.get("distance_to_resistance", 0)
            
            # Good timing if near support for long or near resistance for short
            if 0 < distance_to_support < 2:  # Within 2% of support
                score += 1
            if 0 < distance_to_resistance < 2:  # Within 2% of resistance
                score += 1
        
        return max(1, min(10, score))
    except:
        return 5

def _get_timing_recommendations(context: Dict) -> List[str]:
    """Get timing recommendations based on market context"""
    recommendations = []
    
    try:
        volatility = context.get("volatility_indicator", "UNKNOWN")
        if volatility == "HIGH":
            recommendations.append("High volatility detected - consider smaller position sizes")
        elif volatility == "LOW":
            recommendations.append("Low volatility environment - good for range-bound strategies")
        
        market_state = context.get("market_state", "UNKNOWN")
        if market_state in ["PRE", "POST"]:
            recommendations.append("Trading during extended hours - be aware of lower liquidity")
        
        trend = context.get("market_trend", "UNKNOWN")
        if trend == "BULLISH":
            recommendations.append("Bullish trend detected - favor long positions")
        elif trend == "BEARISH":
            recommendations.append("Bearish trend detected - favor short positions")
        
        support_resistance = context.get("support_resistance", {})
        if support_resistance:
            distance_to_support = support_resistance.get("distance_to_support", 0)
            distance_to_resistance = support_resistance.get("distance_to_resistance", 0)
            
            if distance_to_support < 2:
                recommendations.append("Near support level - good long entry opportunity")
            if distance_to_resistance < 2:
                recommendations.append("Near resistance level - consider profit taking or short entry")
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
    
    if not recommendations:
        recommendations.append("Market conditions are neutral - stick to your trading plan")
    
    return recommendations
