"""
WebSocket router for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import logging
import json
from jose import jwt, JWTError

from core.config import settings
from .manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_current_user_ws(websocket: WebSocket) -> Optional[int]:
    """Get current user from WebSocket connection"""
    # Try to get token from query params or headers
    token = websocket.query_params.get("token")
    if not token:
        # Try to get from first message
        return None
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id:
            return int(user_id)
    except JWTError:
        logger.error("Invalid JWT token in WebSocket connection")
    
    return None

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint"""
    user_id = None
    
    try:
        # Check for token in query params first (preferred method)
        token = websocket.query_params.get("token")
        if token:
            try:
                payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
                user_id = int(payload.get("sub"))
                if user_id:
                    # Accept and register connection
                    await websocket.accept()
                    await ws_manager.connect(websocket, user_id)
                    logger.info(f"WebSocket authenticated for user {user_id} via query param")
                else:
                    # Reject without accepting
                    await websocket.close(code=1008, reason="Invalid token")
                    return
            except JWTError:
                # Reject without accepting
                await websocket.close(code=1008, reason="Invalid token")
                return
        else:
            # If no query param token, accept and wait for auth message
            await websocket.accept()
            
            # Set a timeout for authentication
            import asyncio
            try:
                auth_message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Authentication timeout"
                })
                await websocket.close(code=1008, reason="Authentication timeout")
                return
                
            try:
                auth_data = json.loads(auth_message)
                if auth_data.get("type") == "auth" and auth_data.get("token"):
                    # Verify token
                    payload = jwt.decode(
                        auth_data["token"], 
                        settings.jwt_secret_key, 
                        algorithms=["HS256"]
                    )
                    user_id = int(payload.get("sub"))
                    
                    if user_id:
                        # Register connection
                        await ws_manager.connect(websocket, user_id)
                        logger.info(f"WebSocket authenticated for user {user_id} via message")
                        await websocket.send_json({
                            "type": "auth_success",
                            "message": "Authentication successful"
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid authentication"
                        })
                        await websocket.close(code=1008, reason="Invalid authentication")
                        return
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Authentication required"
                    })
                    await websocket.close(code=1008, reason="Authentication required")
                    return
                    
            except (json.JSONDecodeError, JWTError) as e:
                logger.error(f"WebSocket auth error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid authentication data"
                })
                await websocket.close(code=1008, reason="Invalid authentication data")
                return
        
        # Handle messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await ws_manager.handle_message(user_id, message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                
    except WebSocketDisconnect:
        if user_id:
            ws_manager.disconnect(user_id)
            logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_id:
            ws_manager.disconnect(user_id)

@router.websocket("/ws/public")
async def public_websocket_endpoint(websocket: WebSocket):
    """Public WebSocket endpoint for market data"""
    await websocket.accept()
    
    try:
        # Subscribe to public market data
        public_user_id = -1  # Special ID for public connections
        await ws_manager.connect(websocket, public_user_id)
        ws_manager.subscribe(public_user_id, "market_data")
        
        while True:
            # Just keep connection alive, market data will be pushed
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        ws_manager.disconnect(public_user_id)
        logger.info("Public WebSocket disconnected")