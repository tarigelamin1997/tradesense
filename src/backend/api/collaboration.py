"""
Collaboration API endpoints.
Handles team management, workspaces, and real-time collaboration.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from core.db.session import get_db
from core.auth import get_current_user
from models.user import User
from src.backend.collaboration.collaboration_service import (
    collaboration_service, TeamRole, ResourceType, PermissionLevel
)
from sqlalchemy import text
import json


router = APIRouter(prefix="/api/v1/collaboration")


# Request/Response Models
class CreateTeamRequest(BaseModel):
    """Create team request."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)


class InviteMemberRequest(BaseModel):
    """Invite team member request."""
    email: EmailStr
    role: TeamRole = TeamRole.MEMBER


class CreateWorkspaceRequest(BaseModel):
    """Create workspace request."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., max_length=500)


class ShareResourceRequest(BaseModel):
    """Share resource request."""
    resource_type: ResourceType
    resource_id: str
    workspace_id: str
    permissions: List[PermissionLevel] = [PermissionLevel.VIEW]


class UpdateResourceRequest(BaseModel):
    """Update shared resource request."""
    change_type: str
    change_data: Dict[str, Any]


class AddCommentRequest(BaseModel):
    """Add comment request."""
    comment_text: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[str] = None


class TeamResponse(BaseModel):
    """Team response model."""
    id: str
    name: str
    description: str
    owner_id: str
    member_count: int
    created_at: datetime


class WorkspaceResponse(BaseModel):
    """Workspace response model."""
    id: str
    team_id: str
    name: str
    description: str
    active_users: int
    shared_resources: int
    created_at: datetime


# Team Management Endpoints
@router.post("/teams", response_model=Dict[str, Any])
async def create_team(
    request: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new team."""
    try:
        team = await collaboration_service.create_team(
            current_user,
            request.name,
            request.description,
            db
        )
        return team
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TeamResponse]:
    """Get user's teams."""
    result = await db.execute(
        text("""
            SELECT 
                t.*,
                COUNT(DISTINCT tm.user_id) as member_count
            FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE t.id IN (
                SELECT team_id FROM team_members WHERE user_id = :user_id
            )
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """),
        {"user_id": current_user.id}
    )
    
    teams = []
    for row in result:
        teams.append(TeamResponse(
            id=str(row.id),
            name=row.name,
            description=row.description,
            owner_id=str(row.owner_id),
            member_count=row.member_count,
            created_at=row.created_at
        ))
    
    return teams


@router.get("/teams/{team_id}/members")
async def get_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get team members."""
    # Verify user is team member
    member_check = await db.execute(
        text("""
            SELECT 1 FROM team_members
            WHERE team_id = :team_id AND user_id = :user_id
        """),
        {"team_id": team_id, "user_id": current_user.id}
    )
    
    if not member_check.scalar():
        raise HTTPException(403, "Not a team member")
    
    # Get members
    result = await db.execute(
        text("""
            SELECT 
                u.id, u.username, u.email, u.full_name, u.avatar_url,
                tm.role, tm.joined_at
            FROM team_members tm
            JOIN users u ON tm.user_id = u.id
            WHERE tm.team_id = :team_id
            ORDER BY tm.joined_at
        """),
        {"team_id": team_id}
    )
    
    members = []
    for row in result:
        members.append({
            "id": str(row.id),
            "username": row.username,
            "email": row.email,
            "full_name": row.full_name,
            "avatar_url": row.avatar_url,
            "role": row.role,
            "joined_at": row.joined_at
        })
    
    return members


@router.post("/teams/{team_id}/invite")
async def invite_member(
    team_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Invite a member to team."""
    try:
        invite_id = await collaboration_service.invite_member(
            team_id,
            current_user,
            request.email,
            request.role,
            db
        )
        return {"invite_id": invite_id, "message": "Invitation sent"}
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


# Workspace Management Endpoints
@router.post("/teams/{team_id}/workspaces", response_model=Dict[str, str])
async def create_workspace(
    team_id: str,
    request: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Create a new workspace."""
    # Verify user is team member
    member_check = await db.execute(
        text("""
            SELECT role FROM team_members
            WHERE team_id = :team_id AND user_id = :user_id
        """),
        {"team_id": team_id, "user_id": current_user.id}
    )
    
    member = member_check.first()
    if not member or member.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(403, "Only owners and admins can create workspaces")
    
    workspace_id = await collaboration_service.create_workspace(
        team_id,
        request.name,
        request.description,
        str(current_user.id),
        db
    )
    
    await db.commit()
    
    return {"workspace_id": workspace_id}


@router.get("/teams/{team_id}/workspaces", response_model=List[WorkspaceResponse])
async def get_workspaces(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[WorkspaceResponse]:
    """Get team workspaces."""
    # Verify user is team member
    member_check = await db.execute(
        text("""
            SELECT 1 FROM team_members
            WHERE team_id = :team_id AND user_id = :user_id
        """),
        {"team_id": team_id, "user_id": current_user.id}
    )
    
    if not member_check.scalar():
        raise HTTPException(403, "Not a team member")
    
    # Get workspaces
    result = await db.execute(
        text("""
            SELECT 
                w.*,
                COUNT(DISTINCT sr.id) as shared_resources
            FROM workspaces w
            LEFT JOIN shared_resources sr ON w.id = sr.workspace_id
            WHERE w.team_id = :team_id
            GROUP BY w.id
            ORDER BY w.created_at DESC
        """),
        {"team_id": team_id}
    )
    
    workspaces = []
    for row in result:
        # Get active user count
        active_users = len(collaboration_service.active_sessions.get(str(row.id), set()))
        
        workspaces.append(WorkspaceResponse(
            id=str(row.id),
            team_id=str(row.team_id),
            name=row.name,
            description=row.description,
            active_users=active_users,
            shared_resources=row.shared_resources,
            created_at=row.created_at
        ))
    
    return workspaces


# Resource Sharing Endpoints
@router.post("/share", response_model=Dict[str, Any])
async def share_resource(
    request: ShareResourceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Share a resource with a workspace."""
    try:
        share_info = await collaboration_service.share_resource(
            current_user,
            request.resource_type,
            request.resource_id,
            request.workspace_id,
            request.permissions,
            db
        )
        return share_info
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/workspaces/{workspace_id}/resources")
async def get_shared_resources(
    workspace_id: str,
    resource_type: Optional[ResourceType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get resources shared in workspace."""
    # Verify access
    access_check = await db.execute(
        text("""
            SELECT 1 FROM team_members tm
            JOIN workspaces w ON tm.team_id = w.team_id
            WHERE w.id = :workspace_id AND tm.user_id = :user_id
        """),
        {"workspace_id": workspace_id, "user_id": current_user.id}
    )
    
    if not access_check.scalar():
        raise HTTPException(403, "No access to workspace")
    
    # Get resources
    query = """
        SELECT 
            sr.*,
            u.username as shared_by_username,
            u.avatar_url as shared_by_avatar
        FROM shared_resources sr
        JOIN users u ON sr.shared_by = u.id
        WHERE sr.workspace_id = :workspace_id
    """
    
    params = {"workspace_id": workspace_id}
    
    if resource_type:
        query += " AND sr.resource_type = :resource_type"
        params["resource_type"] = resource_type
    
    query += " ORDER BY sr.created_at DESC"
    
    result = await db.execute(text(query), params)
    
    resources = []
    for row in result:
        # Get resource details based on type
        resource_details = await _get_resource_details(
            row.resource_type,
            row.resource_id,
            db
        )
        
        resources.append({
            "id": str(row.id),
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "resource_details": resource_details,
            "permissions": json.loads(row.permissions),
            "shared_by": {
                "id": str(row.shared_by),
                "username": row.shared_by_username,
                "avatar_url": row.shared_by_avatar
            },
            "created_at": row.created_at
        })
    
    return resources


@router.put("/resources/{resource_type}/{resource_id}")
async def update_shared_resource(
    resource_type: ResourceType,
    resource_id: str,
    request: UpdateResourceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Update a shared resource."""
    try:
        await collaboration_service.sync_change(
            current_user,
            resource_type,
            resource_id,
            request.change_type,
            request.change_data,
            db
        )
        await db.commit()
        return {"message": "Resource updated"}
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except Exception as e:
        raise HTTPException(400, str(e))


# Comments Endpoints
@router.post("/resources/{resource_type}/{resource_id}/comments")
async def add_comment(
    resource_type: ResourceType,
    resource_id: str,
    request: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Add comment to shared resource."""
    try:
        comment = await collaboration_service.add_comment(
            current_user,
            resource_type,
            resource_id,
            request.comment_text,
            request.parent_id,
            db
        )
        return comment
    except ValueError as e:
        raise HTTPException(400, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))


@router.get("/resources/{resource_type}/{resource_id}/comments")
async def get_comments(
    resource_type: ResourceType,
    resource_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get comments for shared resource."""
    # Get user's current workspace
    workspace_id = collaboration_service.user_workspaces.get(str(current_user.id))
    if not workspace_id:
        raise HTTPException(400, "Not in a workspace")
    
    # Get comments
    result = await db.execute(
        text("""
            SELECT 
                rc.*,
                u.username,
                u.avatar_url,
                COUNT(replies.id) as reply_count
            FROM resource_comments rc
            JOIN users u ON rc.user_id = u.id
            LEFT JOIN resource_comments replies ON rc.id = replies.parent_id
            WHERE rc.workspace_id = :workspace_id
            AND rc.resource_type = :resource_type
            AND rc.resource_id = :resource_id
            AND rc.parent_id IS NULL
            GROUP BY rc.id, u.username, u.avatar_url
            ORDER BY rc.created_at DESC
        """),
        {
            "workspace_id": workspace_id,
            "resource_type": resource_type,
            "resource_id": resource_id
        }
    )
    
    comments = []
    for row in result:
        # Get replies if any
        replies = []
        if row.reply_count > 0:
            reply_result = await db.execute(
                text("""
                    SELECT 
                        rc.*,
                        u.username,
                        u.avatar_url
                    FROM resource_comments rc
                    JOIN users u ON rc.user_id = u.id
                    WHERE rc.parent_id = :parent_id
                    ORDER BY rc.created_at
                """),
                {"parent_id": row.id}
            )
            
            for reply_row in reply_result:
                replies.append({
                    "id": str(reply_row.id),
                    "comment_text": reply_row.comment_text,
                    "user": {
                        "id": str(reply_row.user_id),
                        "username": reply_row.username,
                        "avatar_url": reply_row.avatar_url
                    },
                    "created_at": reply_row.created_at
                })
        
        comments.append({
            "id": str(row.id),
            "comment_text": row.comment_text,
            "user": {
                "id": str(row.user_id),
                "username": row.username,
                "avatar_url": row.avatar_url
            },
            "created_at": row.created_at,
            "replies": replies
        })
    
    return comments


# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/{workspace_id}")
async def collaboration_websocket(
    websocket: WebSocket,
    workspace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time collaboration."""
    await websocket.accept()
    
    # Get user from token
    try:
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        from core.auth import decode_access_token
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Get user
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        # Join workspace
        await collaboration_service.join_workspace(user, workspace_id, db)
        
        try:
            while True:
                # Receive messages
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "cursor_move":
                    await collaboration_service.broadcast_cursor(
                        user,
                        data.get("resource_id"),
                        data.get("position")
                    )
                
                elif message_type == "selection_change":
                    await collaboration_service.broadcast_selection(
                        user,
                        data.get("resource_id"),
                        data.get("selection")
                    )
                
                elif message_type == "start_screen_share":
                    await collaboration_service.start_screen_share(
                        user,
                        data.get("stream_id")
                    )
                
                elif message_type == "stop_screen_share":
                    await collaboration_service.stop_screen_share(user)
                
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            pass
        finally:
            # Leave workspace
            await collaboration_service.leave_workspace(str(user.id))
            
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


# WebRTC signaling endpoint
@router.websocket("/webrtc/{workspace_id}")
async def webrtc_websocket(
    websocket: WebSocket,
    workspace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebRTC signaling endpoint for screen sharing and calls."""
    # Get user from token
    try:
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        from core.auth import decode_access_token
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return
        
        # Get user
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        # Handle WebRTC signaling
        from src.backend.collaboration.webrtc_signaling import webrtc_server
        await webrtc_server.handle_connection(
            websocket,
            workspace_id,
            str(user.id),
            user.username
        )
        
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


# Helper function
async def _get_resource_details(
    resource_type: ResourceType,
    resource_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Get details for a specific resource."""
    if resource_type == ResourceType.PORTFOLIO:
        result = await db.execute(
            text("""
                SELECT name, description
                FROM portfolios
                WHERE id = :id
            """),
            {"id": resource_id}
        )
        row = result.first()
        if row:
            return {"name": row.name, "description": row.description}
    
    elif resource_type == ResourceType.STRATEGY:
        result = await db.execute(
            text("""
                SELECT name, description
                FROM strategies
                WHERE id = :id
            """),
            {"id": resource_id}
        )
        row = result.first()
        if row:
            return {"name": row.name, "description": row.description}
    
    elif resource_type == ResourceType.WATCHLIST:
        result = await db.execute(
            text("""
                SELECT COUNT(*) as symbol_count
                FROM watchlist
                WHERE user_id = (
                    SELECT user_id FROM watchlist WHERE id = :id LIMIT 1
                )
            """),
            {"id": resource_id}
        )
        row = result.first()
        if row:
            return {"symbol_count": row.symbol_count}
    
    return {}
