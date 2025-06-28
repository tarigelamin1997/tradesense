from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

from backend.services.real_time_market_service import market_service, MarketData, MarketSentiment
from backend.api.deps import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/market-data", tags=["market-data"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(message)
            except:
                # Connection closed, clean up
                self.disconnect(self.user_connections[user_id], user_id)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

@router.get("/symbols/{symbol}/current")
async def get_current_market_data(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current market data for a symbol"""
    market_data = await market_service.get_current_price(symbol.upper())
    sentiment = await market_service.get_market_sentiment(symbol.upper())

    if not market_data:
        raise HTTPException(status_code=404, detail="Market data not available for symbol")

    return {
        "symbol": market_data.symbol,
        "price": market_data.price,
        "change": market_data.change,
        "change_percent": market_data.change_percent,
        "volume": market_data.volume,
        "bid": market_data.bid,
        "ask": market_data.ask,
        "high": market_data.high,
        "low": market_data.low,
        "timestamp": market_data.timestamp.isoformat(),
        "sentiment": {
            "score": sentiment.sentiment_score if sentiment else 0,
            "volatility": sentiment.volatility if sentiment else 0,
            "momentum": sentiment.momentum if sentiment else 0,
            "trend": sentiment.trend_direction if sentiment else "neutral"
        } if sentiment else None
    }

@router.get("/symbols/{symbol}/context")
async def get_trade_context(
    symbol: str,
    entry_price: float,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Analyze market context for a specific trade"""
    context = await market_service.analyze_trade_context(symbol.upper(), entry_price)
    return context

@router.get("/portfolio/context")
async def get_portfolio_context(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get real-time context for user's portfolio"""
    context = await market_service.get_portfolio_context(current_user.id)
    return context

@router.get("/watchlist")
async def get_watchlist_data(
    symbols: str,  # Comma-separated symbols
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get market data for a watchlist of symbols"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = []

    for symbol in symbol_list:
        market_data = await market_service.get_current_price(symbol)
        sentiment = await market_service.get_market_sentiment(symbol)

        if market_data:
            results.append({
                "symbol": symbol,
                "price": market_data.price,
                "change": market_data.change,
                "change_percent": market_data.change_percent,
                "volume": market_data.volume,
                "sentiment_score": sentiment.sentiment_score if sentiment else 0,
                "trend": sentiment.trend_direction if sentiment else "neutral"
            })

    return results

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time market data"""
    await manager.connect(websocket, user_id)

    # Subscribe to market updates
    async def market_update_callback(market_data: MarketData, sentiment: MarketSentiment):
        message = {
            "type": "market_update",
            "data": {
                "symbol": market_data.symbol,
                "price": market_data.price,
                "change": market_data.change,
                "change_percent": market_data.change_percent,
                "volume": market_data.volume,
                "timestamp": market_data.timestamp.isoformat(),
                "sentiment": {
                    "score": sentiment.sentiment_score,
                    "volatility": sentiment.volatility,
                    "momentum": sentiment.momentum,
                    "trend": sentiment.trend_direction
                }
            }
        }
        await manager.send_personal_message(json.dumps(message), user_id)

    try:
        while True:
            # Listen for client messages (symbol subscriptions)
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "subscribe":
                symbol = message["symbol"].upper()
                market_service.subscribe_to_symbol(symbol, market_update_callback)

                # Send current data immediately
                current_data = await market_service.get_current_price(symbol)
                current_sentiment = await market_service.get_market_sentiment(symbol)

                if current_data and current_sentiment:
                    await market_update_callback(current_data, current_sentiment)

            elif message["type"] == "unsubscribe":
                symbol = message["symbol"].upper()
                market_service.unsubscribe_from_symbol(symbol, market_update_callback)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)

@router.get("/market-hours")
async def get_market_hours() -> Dict[str, Any]:
    """Get current market hours and status"""
    now = datetime.now()

    # Simplified market hours (US Eastern Time)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    is_open = market_open <= now <= market_close and now.weekday() < 5

    return {
        "is_open": is_open,
        "market_open": market_open.isoformat(),
        "market_close": market_close.isoformat(),
        "current_time": now.isoformat(),
        "session": "regular" if is_open else "closed"
    }

# Initialize market service on startup
@router.on_event("startup")
async def startup_event():
    """Start the market data feed when the API starts"""
    asyncio.create_task(market_service.start_market_feed())