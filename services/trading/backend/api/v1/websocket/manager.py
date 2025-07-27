"""
WebSocket connection manager for real-time updates
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, Optional
import json
import logging
from datetime import datetime
import asyncio
from jose import jwt, JWTError

from core.config import settings
from api.deps import get_current_user_ws

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Store connections by user_id
        self._connections: Dict[int, WebSocket] = {}
        # Store subscriptions by topic
        self._subscriptions: Dict[str, Set[int]] = {
            "trades": set(),
            "market_data": set(),
            "analytics": set(),
            "notifications": set()
        }
        # Background tasks
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self._connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Send initial connection message
        await self.send_to_user(user_id, {
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self._connections:
            del self._connections[user_id]
            # Remove from all subscriptions
            for topic_users in self._subscriptions.values():
                topic_users.discard(user_id)
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a message to a specific user"""
        if user_id in self._connections:
            try:
                await self._connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast a message to all users subscribed to a topic"""
        if topic in self._subscriptions:
            for user_id in self._subscriptions[topic].copy():
                await self.send_to_user(user_id, message)
    
    def subscribe(self, user_id: int, topic: str):
        """Subscribe a user to a topic"""
        if topic in self._subscriptions:
            self._subscriptions[topic].add(user_id)
            logger.info(f"User {user_id} subscribed to {topic}")
    
    def unsubscribe(self, user_id: int, topic: str):
        """Unsubscribe a user from a topic"""
        if topic in self._subscriptions:
            self._subscriptions[topic].discard(user_id)
            logger.info(f"User {user_id} unsubscribed from {topic}")
    
    async def handle_message(self, user_id: int, message: dict):
        """Handle incoming WebSocket messages"""
        msg_type = message.get("type")
        
        if msg_type == "ping":
            await self.send_to_user(user_id, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})
        
        elif msg_type == "subscribe":
            topic = message.get("topic")
            if topic and topic in self._subscriptions:
                self.subscribe(user_id, topic)
                await self.send_to_user(user_id, {
                    "type": "subscribed",
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        elif msg_type == "unsubscribe":
            topic = message.get("topic")
            if topic and topic in self._subscriptions:
                self.unsubscribe(user_id, topic)
                await self.send_to_user(user_id, {
                    "type": "unsubscribed",
                    "topic": topic,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        else:
            await self.send_to_user(user_id, {
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    # Methods for sending specific types of updates
    async def send_trade_update(self, user_id: int, trade_data: dict, action: str = "create"):
        """Send trade update to a specific user"""
        await self.send_to_user(user_id, {
            "type": "trade_update",
            "action": action,  # create, update, delete
            "trade": trade_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_market_data(self, market_data: dict):
        """Broadcast market data to all subscribed users"""
        await self.broadcast_to_topic("market_data", {
            "type": "market_update",
            "data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_analytics_update(self, user_id: int, analytics_data: dict):
        """Send analytics update to a specific user"""
        if user_id in self._subscriptions.get("analytics", set()):
            await self.send_to_user(user_id, {
                "type": "analytics_update",
                "data": analytics_data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def send_notification(self, user_id: int, notification: dict):
        """Send notification to a specific user"""
        await self.send_to_user(user_id, {
            "type": "notification",
            "notification": notification,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def start_market_data_stream(self):
        """Start streaming market data (mock implementation)"""
        while True:
            try:
                # In a real implementation, this would fetch from a market data provider
                await asyncio.sleep(5)  # Update every 5 seconds
                
                market_data = {
                    "SPY": {"price": 475.50, "change": 0.25, "volume": 85000000},
                    "QQQ": {"price": 410.25, "change": -0.15, "volume": 45000000},
                    "IWM": {"price": 198.75, "change": 0.45, "volume": 35000000}
                }
                
                await self.broadcast_market_data(market_data)
                
            except Exception as e:
                logger.error(f"Error in market data stream: {e}")
                await asyncio.sleep(30)  # Wait longer on error

# Global WebSocket manager instance
ws_manager = WebSocketManager()