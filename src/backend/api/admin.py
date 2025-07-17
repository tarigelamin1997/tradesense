"""
Admin API endpoints for TradeSense.
Provides user management, system administration, and support tools.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy import text, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user, require_admin
from core.db.session import get_db
from models.user import User
from services.email_service import email_service
from analytics import user_analytics, track_feature_usage

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    subscription_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    notes: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    subscription_tier: str = "free"
    role: str = "user"
    send_welcome_email: bool = True


class BulkAction(BaseModel):
    user_ids: List[str]
    action: str
    params: Optional[Dict[str, Any]] = None


class SupportTicketResponse(BaseModel):
    ticket_id: str
    response: str
    status: str = "resolved"


@router.get("/dashboard/stats")
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive admin dashboard statistics."""
    try:
        # User statistics
        user_stats = await db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as new_users_24h,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as new_users_7d,
                    COUNT(CASE WHEN subscription_tier != 'free' THEN 1 END) as paid_users,
                    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_users,
                    COUNT(CASE WHEN last_login > NOW() - INTERVAL '24 hours' THEN 1 END) as active_24h,
                    COUNT(CASE WHEN last_login > NOW() - INTERVAL '7 days' THEN 1 END) as active_7d
                FROM users
            """)
        )
        user_data = user_stats.first()
        
        # Subscription breakdown
        subscription_stats = await db.execute(
            text("""
                SELECT 
                    subscription_tier,
                    COUNT(*) as count,
                    SUM(CASE 
                        WHEN subscription_tier = 'pro' THEN 49.99
                        WHEN subscription_tier = 'premium' THEN 99.99
                        ELSE 0
                    END) as mrr
                FROM users
                WHERE subscription_status = 'active'
                GROUP BY subscription_tier
            """)
        )
        
        subscription_breakdown = {}
        total_mrr = 0
        for row in subscription_stats:
            subscription_breakdown[row.subscription_tier] = {
                "count": row.count,
                "mrr": float(row.mrr or 0)
            }
            total_mrr += float(row.mrr or 0)
        
        # Trade statistics
        trade_stats = await db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as trades_24h,
                    COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as trades_7d,
                    COUNT(DISTINCT user_id) as users_with_trades
                FROM trades
            """)
        )
        trade_data = trade_stats.first()
        
        # System health
        system_health = await db.execute(
            text("""
                SELECT 
                    (SELECT COUNT(*) FROM api_requests WHERE created_at > NOW() - INTERVAL '1 hour') as api_requests_1h,
                    (SELECT AVG(response_time_ms) FROM api_requests WHERE created_at > NOW() - INTERVAL '1 hour') as avg_response_time,
                    (SELECT COUNT(*) FROM api_requests WHERE status_code >= 500 AND created_at > NOW() - INTERVAL '1 hour') as errors_1h,
                    pg_database_size(current_database()) as database_size
            """)
        )
        health_data = system_health.first()
        
        # Recent activity
        recent_signups = await db.execute(
            text("""
                SELECT id, email, full_name, created_at, subscription_tier
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            """)
        )
        
        recent_issues = await db.execute(
            text("""
                SELECT 
                    'error' as type,
                    timestamp,
                    message,
                    context->>'user_id' as user_id
                FROM application_logs
                WHERE level = 'ERROR'
                AND timestamp > NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
        )
        
        # Track admin dashboard view
        await track_feature_usage(
            str(current_user.id),
            "admin_dashboard_viewed"
        )
        
        return {
            "users": {
                "total": user_data.total_users,
                "new_24h": user_data.new_users_24h,
                "new_7d": user_data.new_users_7d,
                "paid": user_data.paid_users,
                "inactive": user_data.inactive_users,
                "active_24h": user_data.active_24h,
                "active_7d": user_data.active_7d
            },
            "subscriptions": {
                "breakdown": subscription_breakdown,
                "total_mrr": round(total_mrr, 2)
            },
            "trades": {
                "total": trade_data.total_trades,
                "trades_24h": trade_data.trades_24h,
                "trades_7d": trade_data.trades_7d,
                "users_with_trades": trade_data.users_with_trades
            },
            "system": {
                "api_requests_1h": health_data.api_requests_1h,
                "avg_response_time_ms": round(health_data.avg_response_time or 0, 2),
                "errors_1h": health_data.errors_1h,
                "database_size_mb": round(health_data.database_size / (1024 * 1024), 2)
            },
            "recent_signups": [
                {
                    "id": str(row.id),
                    "email": row.email,
                    "full_name": row.full_name,
                    "created_at": row.created_at.isoformat(),
                    "subscription_tier": row.subscription_tier
                }
                for row in recent_signups
            ],
            "recent_issues": [
                {
                    "type": row.type,
                    "timestamp": row.timestamp.isoformat(),
                    "message": row.message,
                    "user_id": row.user_id
                }
                for row in recent_issues
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    subscription_tier: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sort_by: str = Query("created_at", enum=["created_at", "last_login", "email"]),
    sort_order: str = Query("desc", enum=["asc", "desc"]),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users with filtering and pagination."""
    try:
        # Build query
        query = "SELECT * FROM users WHERE 1=1"
        params = {"skip": skip, "limit": limit}
        
        if search:
            query += " AND (email ILIKE :search OR full_name ILIKE :search)"
            params["search"] = f"%{search}%"
        
        if subscription_tier:
            query += " AND subscription_tier = :tier"
            params["tier"] = subscription_tier
        
        if status == "active":
            query += " AND is_active = true"
        elif status == "inactive":
            query += " AND is_active = false"
        elif status == "paid":
            query += " AND subscription_tier != 'free'"
        
        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total_result = await db.execute(text(count_query), params)
        total = total_result.scalar()
        
        # Add sorting and pagination
        query += f" ORDER BY {sort_by} {sort_order.upper()} LIMIT :limit OFFSET :skip"
        
        # Execute query
        result = await db.execute(text(query), params)
        
        users = []
        for row in result:
            users.append({
                "id": str(row.id),
                "email": row.email,
                "full_name": row.full_name,
                "subscription_tier": row.subscription_tier,
                "subscription_status": row.subscription_status,
                "is_active": row.is_active,
                "role": row.role,
                "created_at": row.created_at.isoformat(),
                "last_login": row.last_login.isoformat() if row.last_login else None,
                "trade_count": await _get_user_trade_count(db, row.id)
            })
        
        return {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific user."""
    try:
        # Get user info
        user_result = await db.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        user = user_result.first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user statistics
        stats = await user_analytics.get_user_stats(user_id)
        
        # Get recent activity
        recent_activity = await db.execute(
            text("""
                SELECT event_type, timestamp, properties
                FROM user_events
                WHERE user_id = :user_id
                ORDER BY timestamp DESC
                LIMIT 20
            """),
            {"user_id": user_id}
        )
        
        # Get subscription history
        subscription_history = await db.execute(
            text("""
                SELECT *
                FROM subscription_changes
                WHERE user_id = :user_id
                ORDER BY changed_at DESC
            """),
            {"user_id": user_id}
        )
        
        # Get payment history
        payment_history = await db.execute(
            text("""
                SELECT 
                    id, amount, currency, status,
                    created_at, description
                FROM payments
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {"user_id": user_id}
        )
        
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "subscription_tier": user.subscription_tier,
                "subscription_status": user.subscription_status,
                "subscription_started_at": user.subscription_started_at.isoformat() if user.subscription_started_at else None,
                "is_active": user.is_active,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "notes": user.notes
            },
            "statistics": stats,
            "recent_activity": [
                {
                    "event_type": row.event_type,
                    "timestamp": row.timestamp.isoformat(),
                    "properties": json.loads(row.properties) if row.properties else {}
                }
                for row in recent_activity
            ],
            "subscription_history": [
                {
                    "old_tier": row.old_tier,
                    "new_tier": row.new_tier,
                    "changed_at": row.changed_at.isoformat(),
                    "reason": row.reason
                }
                for row in subscription_history
            ] if subscription_history else [],
            "payment_history": [
                {
                    "id": str(row.id),
                    "amount": float(row.amount),
                    "currency": row.currency,
                    "status": row.status,
                    "created_at": row.created_at.isoformat(),
                    "description": row.description
                }
                for row in payment_history
            ] if payment_history else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user information."""
    try:
        # Build update query
        update_fields = []
        params = {"user_id": user_id}
        
        if user_update.email is not None:
            update_fields.append("email = :email")
            params["email"] = user_update.email
        
        if user_update.full_name is not None:
            update_fields.append("full_name = :full_name")
            params["full_name"] = user_update.full_name
        
        if user_update.subscription_tier is not None:
            update_fields.append("subscription_tier = :tier")
            params["tier"] = user_update.subscription_tier
        
        if user_update.subscription_status is not None:
            update_fields.append("subscription_status = :status")
            params["status"] = user_update.subscription_status
        
        if user_update.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = user_update.is_active
        
        if user_update.role is not None:
            update_fields.append("role = :role")
            params["role"] = user_update.role
        
        if user_update.notes is not None:
            update_fields.append("notes = :notes")
            params["notes"] = user_update.notes
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Execute update
        query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE id = :user_id
            RETURNING id
        """
        
        result = await db.execute(text(query), params)
        if not result.first():
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.commit()
        
        # Log admin action
        await _log_admin_action(
            db,
            admin_id=str(current_user.id),
            action="update_user",
            target_user_id=user_id,
            details=user_update.dict(exclude_unset=True)
        )
        
        return {"message": "User updated successfully", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    try:
        from services.auth_service import auth_service
        
        # Check if user exists
        existing = await db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user_data.email}
        )
        if existing.first():
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        hashed_password = auth_service.get_password_hash(user_data.password)
        
        result = await db.execute(
            text("""
                INSERT INTO users (
                    email, full_name, hashed_password,
                    subscription_tier, role, is_active
                ) VALUES (
                    :email, :full_name, :password,
                    :tier, :role, true
                ) RETURNING id
            """),
            {
                "email": user_data.email,
                "full_name": user_data.full_name,
                "password": hashed_password,
                "tier": user_data.subscription_tier,
                "role": user_data.role
            }
        )
        
        new_user_id = result.scalar()
        await db.commit()
        
        # Send welcome email if requested
        if user_data.send_welcome_email:
            await email_service.send_welcome_email(
                user_data.email,
                user_data.full_name
            )
        
        # Log admin action
        await _log_admin_action(
            db,
            admin_id=str(current_user.id),
            action="create_user",
            target_user_id=str(new_user_id),
            details={"email": user_data.email}
        )
        
        return {
            "message": "User created successfully",
            "user_id": str(new_user_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (soft delete)."""
    try:
        # Prevent self-deletion
        if user_id == str(current_user.id):
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Soft delete (deactivate)
        result = await db.execute(
            text("""
                UPDATE users 
                SET is_active = false, 
                    deleted_at = NOW(),
                    email = CONCAT(email, '_deleted_', EXTRACT(EPOCH FROM NOW()))
                WHERE id = :user_id
                RETURNING id
            """),
            {"user_id": user_id}
        )
        
        if not result.first():
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.commit()
        
        # Log admin action
        await _log_admin_action(
            db,
            admin_id=str(current_user.id),
            action="delete_user",
            target_user_id=user_id
        )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/bulk-action")
async def bulk_user_action(
    action: BulkAction,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk actions on multiple users."""
    try:
        affected_users = 0
        
        if action.action == "activate":
            result = await db.execute(
                text("""
                    UPDATE users 
                    SET is_active = true 
                    WHERE id = ANY(:user_ids)
                """),
                {"user_ids": action.user_ids}
            )
            affected_users = result.rowcount
            
        elif action.action == "deactivate":
            result = await db.execute(
                text("""
                    UPDATE users 
                    SET is_active = false 
                    WHERE id = ANY(:user_ids)
                """),
                {"user_ids": action.user_ids}
            )
            affected_users = result.rowcount
            
        elif action.action == "change_tier":
            new_tier = action.params.get("tier")
            if not new_tier:
                raise HTTPException(status_code=400, detail="Tier not specified")
            
            result = await db.execute(
                text("""
                    UPDATE users 
                    SET subscription_tier = :tier 
                    WHERE id = ANY(:user_ids)
                """),
                {"user_ids": action.user_ids, "tier": new_tier}
            )
            affected_users = result.rowcount
            
        elif action.action == "send_email":
            # Queue bulk email
            for user_id in action.user_ids:
                # This would queue email tasks
                pass
            affected_users = len(action.user_ids)
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
        
        await db.commit()
        
        # Log admin action
        await _log_admin_action(
            db,
            admin_id=str(current_user.id),
            action=f"bulk_{action.action}",
            details={
                "user_count": len(action.user_ids),
                "params": action.params
            }
        )
        
        return {
            "message": f"Bulk action completed",
            "affected_users": affected_users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/impersonate")
async def impersonate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Generate a temporary token to impersonate a user (for support)."""
    try:
        from services.auth_service import auth_service
        
        # Get target user
        user_result = await db.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        target_user = user_result.first()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Generate temporary token with impersonation flag
        token_data = {
            "sub": target_user.email,
            "user_id": str(target_user.id),
            "impersonated_by": str(current_user.id),
            "exp": datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        }
        
        token = auth_service.create_access_token(token_data)
        
        # Log admin action
        await _log_admin_action(
            db,
            admin_id=str(current_user.id),
            action="impersonate_user",
            target_user_id=user_id
        )
        
        return {
            "token": token,
            "expires_in": 3600,
            "user": {
                "id": str(target_user.id),
                "email": target_user.email,
                "full_name": target_user.full_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-log")
async def get_admin_activity_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin activity log."""
    try:
        query = """
            SELECT 
                al.*,
                u.email as admin_email,
                u.full_name as admin_name
            FROM admin_activity_log al
            JOIN users u ON al.admin_id = u.id
            WHERE 1=1
        """
        params = {"skip": skip, "limit": limit}
        
        if admin_id:
            query += " AND al.admin_id = :admin_id"
            params["admin_id"] = admin_id
        
        if action:
            query += " AND al.action = :action"
            params["action"] = action
        
        query += " ORDER BY al.created_at DESC LIMIT :limit OFFSET :skip"
        
        result = await db.execute(text(query), params)
        
        activities = []
        for row in result:
            activities.append({
                "id": row.id,
                "admin_id": str(row.admin_id),
                "admin_email": row.admin_email,
                "admin_name": row.admin_name,
                "action": row.action,
                "target_user_id": str(row.target_user_id) if row.target_user_id else None,
                "details": json.loads(row.details) if row.details else {},
                "ip_address": row.ip_address,
                "created_at": row.created_at.isoformat()
            })
        
        return {
            "activities": activities,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
async def _get_user_trade_count(db: AsyncSession, user_id: str) -> int:
    """Get trade count for a user."""
    result = await db.execute(
        text("SELECT COUNT(*) FROM trades WHERE user_id = :user_id"),
        {"user_id": user_id}
    )
    return result.scalar() or 0


async def _log_admin_action(
    db: AsyncSession,
    admin_id: str,
    action: str,
    target_user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log admin action for audit trail."""
    await db.execute(
        text("""
            INSERT INTO admin_activity_log (
                admin_id, action, target_user_id, details, ip_address
            ) VALUES (
                :admin_id, :action, :target_user_id, :details, :ip
            )
        """),
        {
            "admin_id": admin_id,
            "action": action,
            "target_user_id": target_user_id,
            "details": json.dumps(details) if details else None,
            "ip": "127.0.0.1"  # This should come from request
        }
    )