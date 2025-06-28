#!/usr/bin/env python3
"""
Market Data API Router
Real-time market data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from backend.services.real_time_market_service import market_service, MarketQuote, MarketSentiment
from backend.api.deps import get_current_user
from backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market-data", tags=["market-data"])

@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    api_key: Optional[str] = Query(None, description="Optional API key for premium data sources"),
    current_user: User = Depends(get_current_user)
):
    """Get real-time quote for a symbol."""
    try:
        quote = await market_service.get_quote(symbol.upper(), api_key)

        if not quote:
            raise HTTPException(status_code=404, detail=f"Quote not found for symbol {symbol}")

        return {
            "symbol": quote.symbol,
            "price": quote.price,
            "change": quote.change,
            "change_percent": quote.change_percent,
            "volume": quote.volume,
            "timestamp": quote.timestamp.isoformat(),
            "source": quote.source.value
        }

    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quote")

@router.get("/quotes/batch")
async def get_batch_quotes(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    api_key: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get quotes for multiple symbols."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        quotes = []

        for symbol in symbol_list:
            quote = await market_service.get_quote(symbol, api_key)
            if quote:
                quotes.append({
                    "symbol": quote.symbol,
                    "price": quote.price,
                    "change": quote.change,
                    "change_percent": quote.change_percent,
                    "volume": quote.volume,
                    "timestamp": quote.timestamp.isoformat(),
                    "source": quote.source.value
                })

        return {"quotes": quotes}

    except Exception as e:
        logger.error(f"Error getting batch quotes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get batch quotes")

@router.get("/sentiment/{symbol}")
async def get_market_sentiment(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get market sentiment analysis for a symbol."""
    try:
        sentiment = await market_service.get_market_sentiment(symbol.upper())

        if not sentiment:
            raise HTTPException(status_code=404, detail=f"Sentiment data not available for {symbol}")

        return {
            "symbol": sentiment.symbol,
            "sentiment_score": sentiment.sentiment_score,
            "sentiment_label": (
                "Bullish" if sentiment.sentiment_score > 0.2 else
                "Bearish" if sentiment.sentiment_score < -0.2 else
                "Neutral"
            ),
            "news_count": sentiment.news_count,
            "volatility": sentiment.volatility,
            "rsi": sentiment.rsi,
            "ma_signal": sentiment.ma_signal,
            "timestamp": sentiment.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sentiment")

@router.get("/watchlist")
async def get_watchlist(
    current_user: User = Depends(get_current_user)
):
    """Get user's watchlist with current quotes."""
    try:
        quotes = await market_service.get_watchlist_quotes(current_user.id)

        return {
            "watchlist": [
                {
                    "symbol": quote.symbol,
                    "price": quote.price,
                    "change": quote.change,
                    "change_percent": quote.change_percent,
                    "volume": quote.volume,
                    "timestamp": quote.timestamp.isoformat(),
                    "source": quote.source.value
                }
                for quote in quotes
            ]
        }

    except Exception as e:
        logger.error(f"Error getting watchlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to get watchlist")

@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Add symbol to watchlist."""
    try:
        success = market_service.add_to_watchlist(current_user.id, symbol.upper())

        if not success:
            raise HTTPException(status_code=400, detail="Failed to add symbol to watchlist")

        return {"message": f"Added {symbol.upper()} to watchlist"}

    except Exception as e:
        logger.error(f"Error adding to watchlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add to watchlist")

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Remove symbol from watchlist."""
    try:
        success = market_service.remove_from_watchlist(current_user.id, symbol.upper())

        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove symbol from watchlist")

        return {"message": f"Removed {symbol.upper()} from watchlist"}

    except Exception as e:
        logger.error(f"Error removing from watchlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove from watchlist")

@router.get("/context/{symbol}")
async def get_market_context(
    symbol: str,
    timestamp: Optional[str] = Query(None, description="ISO timestamp for historical context"),
    current_user: User = Depends(get_current_user)
):
    """Get market context for a symbol at a specific time."""
    try:
        trade_time = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        context = await market_service.get_market_context_for_trade(symbol.upper(), trade_time)

        return {
            "symbol": symbol.upper(),
            "timestamp": trade_time.isoformat(),
            "context": context
        }

    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market context")

@router.get("/health")
async def market_data_health():
    """Health check for market data service."""
    try:
        # Test with a common symbol
        test_quote = await market_service.get_quote("AAPL")

        return {
            "status": "healthy" if test_quote else "degraded",
            "message": "Market data service is operational" if test_quote else "Some data sources may be unavailable",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Market data health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": "Market data service is experiencing issues",
            "timestamp": datetime.now().isoformat()
        }