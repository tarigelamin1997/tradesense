
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
        summary = {
            "total_trades": 150,  # Mock data
            "win_rate": 65.5,
            "profit_factor": 1.85
        }
        await websocket.send_text(json.dumps({
            "type": "trade_summary",
            "data": summary
        }))
