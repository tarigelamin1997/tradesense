
"""
WebSocket endpoints for real-time trading updates
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            
            # Get latest performance data
            performance_data = {
                "type": "performance_update",
                "data": {
                    "timestamp": "2024-01-01T12:00:00Z",
                    "daily_pnl": 1250.50,
                    "total_trades": 45
                }
            }
            
            await manager.send_personal_message(
                json.dumps(performance_data), 
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
