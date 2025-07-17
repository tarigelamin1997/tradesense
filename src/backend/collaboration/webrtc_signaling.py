"""
WebRTC signaling server for real-time collaboration.
Handles screen sharing, voice, and video calls.
"""

from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import uuid
from datetime import datetime
import asyncio


class WebRTCSignalingServer:
    """WebRTC signaling server for peer-to-peer connections."""
    
    def __init__(self):
        # workspace_id -> {user_id -> WebSocket}
        self.workspace_connections: Dict[str, Dict[str, WebSocket]] = {}
        
        # Active calls/shares
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Peer connections
        self.peer_connections: Dict[str, Set[str]] = {}
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        workspace_id: str,
        user_id: str,
        username: str
    ):
        """Handle new WebRTC connection."""
        await websocket.accept()
        
        # Register connection
        if workspace_id not in self.workspace_connections:
            self.workspace_connections[workspace_id] = {}
        
        self.workspace_connections[workspace_id][user_id] = websocket
        
        # Notify others of new peer
        await self._broadcast_to_workspace(
            workspace_id,
            {
                "type": "peer_joined",
                "peer_id": user_id,
                "username": username
            },
            exclude=user_id
        )
        
        # Send current peers to new user
        current_peers = [
            {"peer_id": pid, "username": f"User_{pid[:8]}"}
            for pid in self.workspace_connections[workspace_id].keys()
            if pid != user_id
        ]
        
        await websocket.send_json({
            "type": "current_peers",
            "peers": current_peers
        })
        
        try:
            while True:
                data = await websocket.receive_json()
                await self._handle_message(workspace_id, user_id, data)
                
        except WebSocketDisconnect:
            await self._handle_disconnect(workspace_id, user_id)
        except Exception as e:
            print(f"WebRTC error: {e}")
            await self._handle_disconnect(workspace_id, user_id)
    
    async def _handle_message(
        self,
        workspace_id: str,
        sender_id: str,
        message: Dict[str, Any]
    ):
        """Handle WebRTC signaling messages."""
        msg_type = message.get("type")
        target_id = message.get("target_id")
        
        if msg_type == "offer":
            # Forward offer to target peer
            await self._send_to_peer(
                workspace_id,
                target_id,
                {
                    "type": "offer",
                    "sender_id": sender_id,
                    "offer": message.get("offer")
                }
            )
            
            # Track peer connection
            self._add_peer_connection(sender_id, target_id)
        
        elif msg_type == "answer":
            # Forward answer to target peer
            await self._send_to_peer(
                workspace_id,
                target_id,
                {
                    "type": "answer",
                    "sender_id": sender_id,
                    "answer": message.get("answer")
                }
            )
        
        elif msg_type == "ice_candidate":
            # Forward ICE candidate to target peer
            await self._send_to_peer(
                workspace_id,
                target_id,
                {
                    "type": "ice_candidate",
                    "sender_id": sender_id,
                    "candidate": message.get("candidate")
                }
            )
        
        elif msg_type == "start_screen_share":
            # Notify all peers about screen share
            session_id = str(uuid.uuid4())
            self.active_sessions[session_id] = {
                "type": "screen_share",
                "workspace_id": workspace_id,
                "user_id": sender_id,
                "started_at": datetime.utcnow()
            }
            
            await self._broadcast_to_workspace(
                workspace_id,
                {
                    "type": "screen_share_started",
                    "session_id": session_id,
                    "user_id": sender_id
                },
                exclude=sender_id
            )
        
        elif msg_type == "stop_screen_share":
            # Find and stop screen share session
            for session_id, session in self.active_sessions.items():
                if (session["type"] == "screen_share" and
                    session["user_id"] == sender_id):
                    
                    del self.active_sessions[session_id]
                    
                    await self._broadcast_to_workspace(
                        workspace_id,
                        {
                            "type": "screen_share_stopped",
                            "session_id": session_id,
                            "user_id": sender_id
                        }
                    )
                    break
        
        elif msg_type == "start_voice_call":
            # Initiate voice call
            session_id = str(uuid.uuid4())
            participants = message.get("participants", [])
            
            self.active_sessions[session_id] = {
                "type": "voice_call",
                "workspace_id": workspace_id,
                "initiator": sender_id,
                "participants": participants,
                "started_at": datetime.utcnow()
            }
            
            # Notify participants
            for participant_id in participants:
                if participant_id != sender_id:
                    await self._send_to_peer(
                        workspace_id,
                        participant_id,
                        {
                            "type": "incoming_call",
                            "session_id": session_id,
                            "caller_id": sender_id,
                            "call_type": "voice"
                        }
                    )
        
        elif msg_type == "start_video_call":
            # Initiate video call
            session_id = str(uuid.uuid4())
            participants = message.get("participants", [])
            
            self.active_sessions[session_id] = {
                "type": "video_call",
                "workspace_id": workspace_id,
                "initiator": sender_id,
                "participants": participants,
                "started_at": datetime.utcnow()
            }
            
            # Notify participants
            for participant_id in participants:
                if participant_id != sender_id:
                    await self._send_to_peer(
                        workspace_id,
                        participant_id,
                        {
                            "type": "incoming_call",
                            "session_id": session_id,
                            "caller_id": sender_id,
                            "call_type": "video"
                        }
                    )
        
        elif msg_type == "accept_call":
            # Handle call acceptance
            session_id = message.get("session_id")
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Notify all participants
                for participant_id in session["participants"]:
                    if participant_id != sender_id:
                        await self._send_to_peer(
                            workspace_id,
                            participant_id,
                            {
                                "type": "call_accepted",
                                "session_id": session_id,
                                "user_id": sender_id
                            }
                        )
        
        elif msg_type == "reject_call" or msg_type == "end_call":
            # Handle call rejection/ending
            session_id = message.get("session_id")
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Notify all participants
                for participant_id in session["participants"]:
                    if participant_id != sender_id:
                        await self._send_to_peer(
                            workspace_id,
                            participant_id,
                            {
                                "type": "call_ended",
                                "session_id": session_id,
                                "ended_by": sender_id
                            }
                        )
                
                # Remove session
                del self.active_sessions[session_id]
        
        elif msg_type == "mute_audio" or msg_type == "unmute_audio":
            # Handle audio mute/unmute
            session_id = message.get("session_id")
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Notify other participants
                for participant_id in session["participants"]:
                    if participant_id != sender_id:
                        await self._send_to_peer(
                            workspace_id,
                            participant_id,
                            {
                                "type": msg_type,
                                "session_id": session_id,
                                "user_id": sender_id
                            }
                        )
        
        elif msg_type == "mute_video" or msg_type == "unmute_video":
            # Handle video mute/unmute
            session_id = message.get("session_id")
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Notify other participants
                for participant_id in session["participants"]:
                    if participant_id != sender_id:
                        await self._send_to_peer(
                            workspace_id,
                            participant_id,
                            {
                                "type": msg_type,
                                "session_id": session_id,
                                "user_id": sender_id
                            }
                        )
    
    async def _handle_disconnect(self, workspace_id: str, user_id: str):
        """Handle peer disconnection."""
        # Remove from connections
        if (workspace_id in self.workspace_connections and
            user_id in self.workspace_connections[workspace_id]):
            
            del self.workspace_connections[workspace_id][user_id]
            
            # Clean up empty workspaces
            if not self.workspace_connections[workspace_id]:
                del self.workspace_connections[workspace_id]
            
            # Notify other peers
            await self._broadcast_to_workspace(
                workspace_id,
                {
                    "type": "peer_left",
                    "peer_id": user_id
                }
            )
            
            # End any active sessions for this user
            sessions_to_remove = []
            for session_id, session in self.active_sessions.items():
                if session.get("user_id") == user_id or user_id in session.get("participants", []):
                    sessions_to_remove.append(session_id)
                    
                    # Notify others if it's a call
                    if session["type"] in ["voice_call", "video_call"]:
                        for participant_id in session["participants"]:
                            if participant_id != user_id:
                                await self._send_to_peer(
                                    workspace_id,
                                    participant_id,
                                    {
                                        "type": "call_ended",
                                        "session_id": session_id,
                                        "reason": "peer_disconnected"
                                    }
                                )
            
            # Remove ended sessions
            for session_id in sessions_to_remove:
                del self.active_sessions[session_id]
            
            # Remove peer connections
            self._remove_peer_connections(user_id)
    
    async def _send_to_peer(
        self,
        workspace_id: str,
        peer_id: str,
        message: Dict[str, Any]
    ):
        """Send message to specific peer."""
        if (workspace_id in self.workspace_connections and
            peer_id in self.workspace_connections[workspace_id]):
            
            websocket = self.workspace_connections[workspace_id][peer_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Failed to send to peer {peer_id}: {e}")
                await self._handle_disconnect(workspace_id, peer_id)
    
    async def _broadcast_to_workspace(
        self,
        workspace_id: str,
        message: Dict[str, Any],
        exclude: Optional[str] = None
    ):
        """Broadcast message to all peers in workspace."""
        if workspace_id not in self.workspace_connections:
            return
        
        disconnected_peers = []
        
        for peer_id, websocket in self.workspace_connections[workspace_id].items():
            if peer_id != exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Failed to send to peer {peer_id}: {e}")
                    disconnected_peers.append(peer_id)
        
        # Handle disconnected peers
        for peer_id in disconnected_peers:
            await self._handle_disconnect(workspace_id, peer_id)
    
    def _add_peer_connection(self, peer1: str, peer2: str):
        """Track peer connection."""
        if peer1 not in self.peer_connections:
            self.peer_connections[peer1] = set()
        if peer2 not in self.peer_connections:
            self.peer_connections[peer2] = set()
        
        self.peer_connections[peer1].add(peer2)
        self.peer_connections[peer2].add(peer1)
    
    def _remove_peer_connections(self, peer_id: str):
        """Remove all connections for a peer."""
        if peer_id in self.peer_connections:
            # Remove from connected peers
            for connected_peer in self.peer_connections[peer_id]:
                if connected_peer in self.peer_connections:
                    self.peer_connections[connected_peer].discard(peer_id)
            
            # Remove peer's connections
            del self.peer_connections[peer_id]
    
    def get_active_sessions(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get active sessions for a workspace."""
        active = []
        for session_id, session in self.active_sessions.items():
            if session.get("workspace_id") == workspace_id:
                active.append({
                    "session_id": session_id,
                    "type": session["type"],
                    "participants": session.get("participants", []),
                    "started_at": session["started_at"].isoformat()
                })
        return active


# Global WebRTC signaling server instance
webrtc_server = WebRTCSignalingServer()
