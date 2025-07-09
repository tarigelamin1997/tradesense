
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass

    async def send_trade_update(self, trade_data: dict, user_id: str):
        """Send real-time trade updates"""
        message = {
            "type": "trade_update",
            "data": trade_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_personal_message(json.dumps(message), user_id)

    async def send_market_update(self, market_data: dict):
        """Broadcast market data to all connected users"""
        message = {
            "type": "market_update", 
            "data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(message))

    async def send_performance_alert(self, alert_data: dict, user_id: str):
        """Send performance alerts to specific user"""
        message = {
            "type": "performance_alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_personal_message(json.dumps(message), user_id)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await handle_websocket_message(message, user_id, websocket)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

async def handle_websocket_message(message: dict, user_id: str, websocket: WebSocket):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "ping":
        await websocket.send_text(json.dumps({"type": "pong"}))
    
    elif message_type == "subscribe_market_data":
        # Subscribe user to market data updates
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed", 
            "subscription": "market_data"
        }))
    
    elif message_type == "request_trade_summary":
        # Send current trade summary
        # This would integrate with your trade service
        try:
            # Import trade service to get real data
            from backend.api.v1.trades.service import TradeService
            from backend.core.db.session import get_db
            
            db = next(get_db())
            trade_service = TradeService(db)
            
            # Get user's trade summary (you'd need to pass user_id in the message)
            user_id = message.get("user_id")
            if user_id:
                summary = await trade_service.get_trade_summary(user_id)
            else:
                # Fallback to mock data
                summary = {
                    "total_trades": 150,
                    "win_rate": 65.5,
                    "profit_factor": 1.85,
                    "total_pnl": 12500.50,
                    "avg_trade_duration": "2.5 hours"
                }
            
            await websocket.send_text(json.dumps({
                "type": "trade_summary",
                "data": summary
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Failed to get trade summary: {str(e)}"
            }))
    
    elif message_type == "subscribe_trade_alerts":
        # Subscribe user to trade alerts
        user_id = message.get("user_id")
        if user_id:
            # Add user to trade alert subscribers
            manager.user_connections[user_id] = websocket
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "subscription": "trade_alerts"
            }))
    
    elif message_type == "request_market_data":
        # Send current market data for requested symbols
        symbols = message.get("symbols", [])
        if symbols:
            try:
                from backend.services.real_time_market_service import RealTimeMarketService
                
                market_service = RealTimeMarketService()
                market_data = {}
                
                for symbol in symbols:
                    data = await market_service.get_current_price(symbol)
                    if data:
                        market_data[symbol] = {
                            "price": data.price,
                            "change": data.change,
                            "change_percent": data.change_percent,
                            "volume": data.volume
                        }
                
                await websocket.send_text(json.dumps({
                    "type": "market_data",
                    "data": market_data
                }))
                
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Failed to get market data: {str(e)}"
                }))
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))
