from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Optional
from datetime import datetime
import json
import asyncio
from backend.services.real_time_market_service import market_service, MarketData, MarketSentiment
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.services.real_time_feeds import market_feed
from backend.services.market_data_service import MarketDataService

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_subscriptions: Dict[str, List[str]] = {}  # user_id -> symbols

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_subscriptions[user_id] = []

    def disconnect(self, websocket: WebSocket, user_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id in self.user_subscriptions:
            del self.user_subscriptions[user_id]

    async def send_to_user(self, user_id: str, data: dict):
        # Find websocket for user and send data
        # Simplified implementation
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except:
                pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.get("/current-price/{symbol}")
async def get_current_price(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get current market price for symbol"""
    price = market_service.get_current_price(symbol)
    if price is None:
        # Trigger a fetch if not in cache
        await market_service._fetch_market_data_batch()
        price = market_service.get_current_price(symbol)

    return {
        "symbol": symbol,
        "price": price,
        "timestamp": datetime.now().isoformat(),
        "market_open": market_service._is_market_hours()
    }

@router.get("/sentiment/{symbol}")
async def get_market_sentiment(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> MarketSentiment:
    """Get current market sentiment for symbol"""
    sentiment = await market_service.fetch_market_sentiment(symbol)
    return sentiment

@router.get("/trade-context/{symbol}")
async def get_trade_context(
    symbol: str,
    entry_time: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get market context for trade analysis"""
    if entry_time:
        entry_dt = datetime.fromisoformat(entry_time)
    else:
        entry_dt = datetime.now()

    context = await market_service.get_trade_context(symbol, entry_dt)
    return context

@router.post("/subscribe/{symbol}")
async def subscribe_to_symbol(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Subscribe to real-time updates for a symbol"""

    async def user_callback(data: MarketData):
        await manager.send_to_user(current_user.id, {
            "type": "market_update",
            "symbol": data.symbol,
            "price": data.price,
            "volume": data.volume,
            "change_percent": data.change_percent,
            "timestamp": data.timestamp.isoformat()
        })

    market_service.subscribe_to_symbol(symbol, user_callback)

    return {
        "message": f"Subscribed to {symbol}",
        "symbol": symbol,
        "user_id": current_user.id
    }

@router.delete("/unsubscribe/{symbol}")
async def unsubscribe_from_symbol(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Unsubscribe from symbol updates"""
    # Note: In production, track callbacks per user
    return {
        "message": f"Unsubscribed from {symbol}",
        "symbol": symbol
    }

@router.get("/market-status")
async def get_market_status(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """Get current market status"""
    return {
        "market_open": market_service._is_market_hours(),
        "session_type": market_service._get_market_session(),
        "timestamp": datetime.now().isoformat(),
        "active_symbols": list(market_service.active_subscriptions.keys()),
        "total_subscriptions": len(market_service.active_subscriptions)
    }

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time market data"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("action") == "subscribe":
                symbol = message.get("symbol")
                if symbol:
                    # Subscribe to symbol for this user
                    async def ws_callback(market_data: MarketData):
                        await websocket.send_text(json.dumps({
                            "type": "market_update",
                            "symbol": market_data.symbol,
                            "price": market_data.price,
                            "volume": market_data.volume,
                            "timestamp": market_data.timestamp.isoformat()
                        }))

                    market_service.subscribe_to_symbol(symbol, ws_callback)
                    manager.user_subscriptions[user_id].append(symbol)

            elif message.get("action") == "unsubscribe":
                symbol = message.get("symbol")
                if symbol and symbol in manager.user_subscriptions.get(user_id, []):
                    manager.user_subscriptions[user_id].remove(symbol)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@router.get("/symbols/trending")
async def get_trending_symbols(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    """Get trending symbols based on activity"""
    # Mock data for trending symbols
    trending = [
        {"symbol": "AAPL", "volume": 25000000, "change_percent": 2.1},
        {"symbol": "TSLA", "volume": 18000000, "change_percent": -1.5},
        {"symbol": "MSFT", "volume": 15000000, "change_percent": 0.8},
        {"symbol": "NVDA", "volume": 22000000, "change_percent": 3.2},
        {"symbol": "AMD", "volume": 12000000, "change_percent": 1.9},
        {"symbol": "GOOGL", "volume": 8000000, "change_percent": -0.3},
        {"symbol": "AMZN", "volume": 11000000, "change_percent": 1.1},
        {"symbol": "META", "volume": 9000000, "change_percent": 2.7},
        {"symbol": "SPY", "volume": 45000000, "change_percent": 0.6},
        {"symbol": "QQQ", "volume": 35000000, "change_percent": 1.2}
    ]

    return trending[:limit]

@router.websocket("/ws/market-data")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get('type') == 'subscribe':
                symbol = message_data.get('symbol')

                # Subscribe to market feed for this symbol
                async def market_callback(update):
                    await manager.send_personal_message(
                        json.dumps(update), websocket
                    )

                market_feed.subscribe_to_symbol(symbol, market_callback)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/symbols/{symbol}/live")
async def get_live_data(symbol: str):
    """Get current live market data for a symbol"""
    service = MarketDataService()
    return await service.get_live_quote(symbol)

@router.get("/market-hours")
async def get_market_hours():
    """Get current market hours and status"""
    service = MarketDataService()
    return await service.get_market_status()

@router.get("/trending")
async def get_trending_symbols():
    """Get trending/most active symbols"""
    service = MarketDataService()
    return await service.get_trending_symbols()