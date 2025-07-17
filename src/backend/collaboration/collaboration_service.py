"""
Real-time collaboration service for TradeSense.
Handles teams, workspaces, and shared resources.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid
import json
from enum import Enum

from core.db.session import get_db
from models.user import User
from core.cache import redis_client
from websocket.manager import manager as websocket_manager


class TeamRole(str, Enum):
    """Team member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ResourceType(str, Enum):
    """Types of shareable resources."""
    PORTFOLIO = "portfolio"
    STRATEGY = "strategy"
    WATCHLIST = "watchlist"
    TRADE_LOG = "trade_log"
    ANALYTICS = "analytics"
    JOURNAL = "journal"


class PermissionLevel(str, Enum):
    """Permission levels for resources."""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    DELETE = "delete"


class CollaborationService:
    """Service for managing collaboration features."""
    
    def __init__(self):
        self.active_sessions: Dict[str, Set[str]] = {}  # workspace_id -> set of user_ids
        self.user_workspaces: Dict[str, str] = {}  # user_id -> current_workspace_id
    
    async def create_team(self, owner: User, name: str, description: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a new team."""
        team_id = str(uuid.uuid4())
        
        # Create team
        await db.execute(
            text("""
                INSERT INTO teams (id, name, description, owner_id, created_at)
                VALUES (:id, :name, :description, :owner_id, NOW())
            """),
            {
                "id": team_id,
                "name": name,
                "description": description,
                "owner_id": owner.id
            }
        )
        
        # Add owner as team member
        await db.execute(
            text("""
                INSERT INTO team_members (team_id, user_id, role, joined_at)
                VALUES (:team_id, :user_id, :role, NOW())
            """),
            {
                "team_id": team_id,
                "user_id": owner.id,
                "role": TeamRole.OWNER
            }
        )
        
        # Create default workspace
        workspace_id = await self.create_workspace(
            team_id, 
            f"{name} Workspace",
            "Default team workspace",
            owner.id,
            db
        )
        
        await db.commit()
        
        return {
            "id": team_id,
            "name": name,
            "description": description,
            "workspace_id": workspace_id,
            "owner_id": str(owner.id)
        }
    
    async def invite_member(
        self, 
        team_id: str, 
        inviter: User, 
        email: str, 
        role: TeamRole,
        db: AsyncSession
    ) -> str:
        """Invite a user to join the team."""
        # Check if inviter has permission
        inviter_role = await self._get_user_role(team_id, inviter.id, db)
        if inviter_role not in [TeamRole.OWNER, TeamRole.ADMIN]:
            raise PermissionError("Only owners and admins can invite members")
        
        # Create invitation
        invite_id = str(uuid.uuid4())
        invite_token = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO team_invitations (
                    id, team_id, email, role, token, 
                    invited_by, expires_at, created_at
                )
                VALUES (
                    :id, :team_id, :email, :role, :token,
                    :invited_by, :expires_at, NOW()
                )
            """),
            {
                "id": invite_id,
                "team_id": team_id,
                "email": email,
                "role": role,
                "token": invite_token,
                "invited_by": inviter.id,
                "expires_at": datetime.utcnow() + timedelta(days=7)
            }
        )
        
        await db.commit()
        
        # Send invitation email
        await self._send_invitation_email(email, team_id, invite_token)
        
        return invite_id
    
    async def create_workspace(
        self,
        team_id: str,
        name: str,
        description: str,
        creator_id: str,
        db: AsyncSession
    ) -> str:
        """Create a new workspace within a team."""
        workspace_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO workspaces (
                    id, team_id, name, description, 
                    created_by, created_at
                )
                VALUES (
                    :id, :team_id, :name, :description,
                    :created_by, NOW()
                )
            """),
            {
                "id": workspace_id,
                "team_id": team_id,
                "name": name,
                "description": description,
                "created_by": creator_id
            }
        )
        
        return workspace_id
    
    async def share_resource(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str,
        workspace_id: str,
        permissions: List[PermissionLevel],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Share a resource with a workspace."""
        # Verify ownership
        if not await self._verify_resource_ownership(user.id, resource_type, resource_id, db):
            raise PermissionError("You don't have permission to share this resource")
        
        # Create share record
        share_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO shared_resources (
                    id, workspace_id, resource_type, resource_id,
                    shared_by, permissions, created_at
                )
                VALUES (
                    :id, :workspace_id, :resource_type, :resource_id,
                    :shared_by, :permissions, NOW()
                )
            """),
            {
                "id": share_id,
                "workspace_id": workspace_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "shared_by": user.id,
                "permissions": json.dumps(permissions)
            }
        )
        
        await db.commit()
        
        # Notify workspace members
        await self._notify_workspace(
            workspace_id,
            "resource_shared",
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "shared_by": user.username
            }
        )
        
        return {
            "share_id": share_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "workspace_id": workspace_id
        }
    
    async def join_workspace(
        self,
        user: User,
        workspace_id: str,
        db: AsyncSession
    ):
        """User joins a workspace for real-time collaboration."""
        # Verify access
        if not await self._has_workspace_access(user.id, workspace_id, db):
            raise PermissionError("Access denied to workspace")
        
        # Add to active sessions
        if workspace_id not in self.active_sessions:
            self.active_sessions[workspace_id] = set()
        
        self.active_sessions[workspace_id].add(str(user.id))
        self.user_workspaces[str(user.id)] = workspace_id
        
        # Get workspace info
        workspace_info = await self._get_workspace_info(workspace_id, db)
        
        # Notify other users
        await self._notify_workspace(
            workspace_id,
            "user_joined",
            {
                "user_id": str(user.id),
                "username": user.username,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=str(user.id)
        )
        
        # Send workspace state to joining user
        await websocket_manager.send_personal_message(
            json.dumps({
                "type": "workspace_state",
                "workspace": workspace_info,
                "active_users": list(self.active_sessions.get(workspace_id, set())),
                "shared_resources": await self._get_shared_resources(workspace_id, db)
            }),
            str(user.id)
        )
    
    async def leave_workspace(self, user_id: str):
        """User leaves current workspace."""
        workspace_id = self.user_workspaces.get(user_id)
        if not workspace_id:
            return
        
        # Remove from active sessions
        if workspace_id in self.active_sessions:
            self.active_sessions[workspace_id].discard(user_id)
            if not self.active_sessions[workspace_id]:
                del self.active_sessions[workspace_id]
        
        del self.user_workspaces[user_id]
        
        # Notify others
        await self._notify_workspace(
            workspace_id,
            "user_left",
            {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def broadcast_cursor(
        self,
        user: User,
        resource_id: str,
        position: Dict[str, Any]
    ):
        """Broadcast cursor position for collaborative editing."""
        workspace_id = self.user_workspaces.get(str(user.id))
        if not workspace_id:
            return
        
        await self._notify_workspace(
            workspace_id,
            "cursor_update",
            {
                "user_id": str(user.id),
                "username": user.username,
                "resource_id": resource_id,
                "position": position,
                "color": self._get_user_color(str(user.id))
            },
            exclude_user=str(user.id)
        )
    
    async def broadcast_selection(
        self,
        user: User,
        resource_id: str,
        selection: Dict[str, Any]
    ):
        """Broadcast selection for collaborative viewing."""
        workspace_id = self.user_workspaces.get(str(user.id))
        if not workspace_id:
            return
        
        await self._notify_workspace(
            workspace_id,
            "selection_update",
            {
                "user_id": str(user.id),
                "username": user.username,
                "resource_id": resource_id,
                "selection": selection,
                "color": self._get_user_color(str(user.id))
            },
            exclude_user=str(user.id)
        )
    
    async def sync_change(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str,
        change_type: str,
        change_data: Dict[str, Any],
        db: AsyncSession
    ):
        """Synchronize a change across all workspace members."""
        workspace_id = self.user_workspaces.get(str(user.id))
        if not workspace_id:
            return
        
        # Verify permission
        permissions = await self._get_resource_permissions(
            workspace_id,
            resource_type,
            resource_id,
            db
        )
        
        if PermissionLevel.EDIT not in permissions:
            raise PermissionError("No edit permission for this resource")
        
        # Create change record
        change_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO collaboration_changes (
                    id, workspace_id, resource_type, resource_id,
                    user_id, change_type, change_data, created_at
                )
                VALUES (
                    :id, :workspace_id, :resource_type, :resource_id,
                    :user_id, :change_type, :change_data, NOW()
                )
            """),
            {
                "id": change_id,
                "workspace_id": workspace_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user.id,
                "change_type": change_type,
                "change_data": json.dumps(change_data)
            }
        )
        
        # Broadcast change
        await self._notify_workspace(
            workspace_id,
            "resource_changed",
            {
                "change_id": change_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "change_type": change_type,
                "change_data": change_data,
                "user_id": str(user.id),
                "username": user.username,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=str(user.id)
        )
    
    async def add_comment(
        self,
        user: User,
        resource_type: ResourceType,
        resource_id: str,
        comment_text: str,
        parent_id: Optional[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Add a comment to a shared resource."""
        workspace_id = self.user_workspaces.get(str(user.id))
        if not workspace_id:
            raise ValueError("Not in a workspace")
        
        # Verify permission
        permissions = await self._get_resource_permissions(
            workspace_id,
            resource_type,
            resource_id,
            db
        )
        
        if PermissionLevel.COMMENT not in permissions and PermissionLevel.EDIT not in permissions:
            raise PermissionError("No comment permission for this resource")
        
        # Create comment
        comment_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO resource_comments (
                    id, workspace_id, resource_type, resource_id,
                    user_id, comment_text, parent_id, created_at
                )
                VALUES (
                    :id, :workspace_id, :resource_type, :resource_id,
                    :user_id, :comment_text, :parent_id, NOW()
                )
            """),
            {
                "id": comment_id,
                "workspace_id": workspace_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user.id,
                "comment_text": comment_text,
                "parent_id": parent_id
            }
        )
        
        await db.commit()
        
        # Notify workspace
        await self._notify_workspace(
            workspace_id,
            "comment_added",
            {
                "comment_id": comment_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": str(user.id),
                "username": user.username,
                "comment_text": comment_text,
                "parent_id": parent_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "id": comment_id,
            "comment_text": comment_text,
            "user_id": str(user.id),
            "username": user.username,
            "created_at": datetime.utcnow()
        }
    
    async def start_screen_share(
        self,
        user: User,
        stream_id: str
    ):
        """Start screen sharing in workspace."""
        workspace_id = self.user_workspaces.get(str(user.id))
        if not workspace_id:
            return
        
        # Store in Redis
        await redis_client.setex(
            f"screen_share:{workspace_id}",
            3600,  # 1 hour expiry
            json.dumps({
                "user_id": str(user.id),
                "username": user.username,
                "stream_id": stream_id,
                "started_at": datetime.utcnow().isoformat()
            })
        )
        
        # Notify workspace
        await self._notify_workspace(
            workspace_id,
            "screen_share_started",
            {
                "user_id": str(user.id),
                "username": user.username,
                "stream_id": stream_id
            },
            exclude_user=str(user.id)
        )
    
    async def stop_screen_share(self, user: User):
        """Stop screen sharing."""
        workspace_id = self.user_workspaces.get(str(user.id))
        if not workspace_id:
            return
        
        # Remove from Redis
        await redis_client.delete(f"screen_share:{workspace_id}")
        
        # Notify workspace
        await self._notify_workspace(
            workspace_id,
            "screen_share_stopped",
            {
                "user_id": str(user.id),
                "username": user.username
            }
        )
    
    # Helper methods
    async def _get_user_role(self, team_id: str, user_id: str, db: AsyncSession) -> Optional[TeamRole]:
        """Get user's role in team."""
        result = await db.execute(
            text("""
                SELECT role FROM team_members
                WHERE team_id = :team_id AND user_id = :user_id
            """),
            {"team_id": team_id, "user_id": user_id}
        )
        row = result.first()
        return TeamRole(row.role) if row else None
    
    async def _verify_resource_ownership(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str,
        db: AsyncSession
    ) -> bool:
        """Verify user owns the resource."""
        # This would check the specific resource table based on type
        # For now, simplified check
        return True
    
    async def _has_workspace_access(self, user_id: str, workspace_id: str, db: AsyncSession) -> bool:
        """Check if user has access to workspace."""
        result = await db.execute(
            text("""
                SELECT 1 FROM team_members tm
                JOIN workspaces w ON tm.team_id = w.team_id
                WHERE w.id = :workspace_id AND tm.user_id = :user_id
            """),
            {"workspace_id": workspace_id, "user_id": user_id}
        )
        return result.scalar() is not None
    
    async def _get_workspace_info(self, workspace_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Get workspace information."""
        result = await db.execute(
            text("""
                SELECT w.*, t.name as team_name
                FROM workspaces w
                JOIN teams t ON w.team_id = t.id
                WHERE w.id = :workspace_id
            """),
            {"workspace_id": workspace_id}
        )
        row = result.first()
        
        if not row:
            return {}
        
        return {
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "team_name": row.team_name,
            "created_at": row.created_at
        }
    
    async def _get_shared_resources(self, workspace_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get resources shared in workspace."""
        result = await db.execute(
            text("""
                SELECT sr.*, u.username as shared_by_username
                FROM shared_resources sr
                JOIN users u ON sr.shared_by = u.id
                WHERE sr.workspace_id = :workspace_id
                ORDER BY sr.created_at DESC
            """),
            {"workspace_id": workspace_id}
        )
        
        resources = []
        for row in result:
            resources.append({
                "id": row.id,
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "shared_by": row.shared_by_username,
                "permissions": json.loads(row.permissions),
                "created_at": row.created_at.isoformat()
            })
        
        return resources
    
    async def _get_resource_permissions(
        self,
        workspace_id: str,
        resource_type: ResourceType,
        resource_id: str,
        db: AsyncSession
    ) -> List[PermissionLevel]:
        """Get permissions for a resource in workspace."""
        result = await db.execute(
            text("""
                SELECT permissions FROM shared_resources
                WHERE workspace_id = :workspace_id
                AND resource_type = :resource_type
                AND resource_id = :resource_id
            """),
            {
                "workspace_id": workspace_id,
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )
        row = result.first()
        
        if not row:
            return []
        
        return [PermissionLevel(p) for p in json.loads(row.permissions)]
    
    async def _notify_workspace(
        self,
        workspace_id: str,
        event_type: str,
        data: Dict[str, Any],
        exclude_user: Optional[str] = None
    ):
        """Send notification to all workspace members."""
        users = self.active_sessions.get(workspace_id, set())
        
        message = json.dumps({
            "type": f"collaboration.{event_type}",
            "workspace_id": workspace_id,
            "data": data
        })
        
        for user_id in users:
            if user_id != exclude_user:
                await websocket_manager.send_personal_message(message, user_id)
    
    def _get_user_color(self, user_id: str) -> str:
        """Get consistent color for user."""
        # Generate color from user ID
        colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
            "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
        ]
        index = int(user_id.split('-')[0], 16) % len(colors)
        return colors[index]
    
    async def _send_invitation_email(self, email: str, team_id: str, token: str):
        """Send team invitation email."""
        # This would integrate with email service
        pass


# Global collaboration service instance
collaboration_service = CollaborationService()
