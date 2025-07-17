"""
Mobile push notifications and in-app messaging endpoints.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from core.db.session import get_db
from models.user import User
from api.mobile.base import (
    MobileResponse, MobilePaginatedResponse, MobilePaginationParams,
    get_pagination_params, create_paginated_response, RequireAuth,
    DeviceInfo, get_device_info
)
from core.cache import redis_client
from sqlalchemy import text
import json


router = APIRouter(prefix="/api/mobile/v1/notifications")


class NotificationType(str, Enum):
    """Types of notifications."""
    TRADE = "trade"
    ALERT = "alert"
    ACCOUNT = "account"
    SYSTEM = "system"
    MARKETING = "marketing"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MobileNotification(BaseModel):
    """Mobile notification model."""
    id: str
    type: NotificationType
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    timestamp: datetime
    read: bool = False
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    icon: Optional[str] = None


class NotificationPreferences(BaseModel):
    """User notification preferences."""
    trades: bool = True
    alerts: bool = True
    account: bool = True
    system: bool = True
    marketing: bool = False
    quiet_hours: Optional[Dict[str, Any]] = None
    channels: Dict[str, bool] = {
        "push": True,
        "email": True,
        "sms": False
    }


class UpdateNotificationRequest(BaseModel):
    """Update notification status."""
    notification_ids: List[str]
    action: str = Field(..., regex="^(read|unread|delete)$")


class RegisterPushTokenRequest(BaseModel):
    """Register/update push notification token."""
    token: str
    platform: str = Field(..., regex="^(ios|android)$")
    device_info: Optional[DeviceInfo] = None


class TestNotificationRequest(BaseModel):
    """Test notification request."""
    title: str = "Test Notification"
    body: str = "This is a test notification from TradeSense"
    type: NotificationType = NotificationType.SYSTEM


@router.get("/list")
async def list_notifications(
    type_filter: Optional[NotificationType] = None,
    unread_only: bool = False,
    pagination: MobilePaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get paginated list of notifications."""
    # Get from Redis first (recent notifications)
    redis_key = f"notifications:{current_user.id}"
    redis_notifications = await redis_client.lrange(redis_key, 0, -1)
    
    all_notifications = []
    
    # Parse Redis notifications
    for notif_data in redis_notifications:
        notif = json.loads(notif_data)
        if type_filter and notif.get('type') != type_filter:
            continue
        if unread_only and notif.get('read', False):
            continue
        all_notifications.append(notif)
    
    # Get from database (older notifications)
    query = """
        SELECT 
            id, type, title, body, priority, timestamp,
            read, data, action_url, icon
        FROM mobile_notifications
        WHERE user_id = :user_id
    """
    
    params = {"user_id": current_user.id}
    
    if type_filter:
        query += " AND type = :type_filter"
        params["type_filter"] = type_filter
    
    if unread_only:
        query += " AND read = FALSE"
    
    query += " ORDER BY timestamp DESC LIMIT 100"
    
    result = await db.execute(text(query), params)
    
    for row in result:
        all_notifications.append({
            "id": str(row.id),
            "type": row.type,
            "title": row.title,
            "body": row.body,
            "priority": row.priority,
            "timestamp": row.timestamp,
            "read": row.read,
            "data": row.data,
            "action_url": row.action_url,
            "icon": row.icon
        })
    
    # Sort by timestamp
    all_notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Apply pagination
    start = pagination.offset
    end = start + pagination.limit
    paginated = all_notifications[start:end]
    
    # Format notifications
    notifications = []
    for notif in paginated:
        notifications.append(MobileNotification(**notif))
    
    return create_paginated_response(
        items=[n.dict() for n in notifications],
        total=len(all_notifications),
        pagination=pagination
    )


@router.get("/unread-count", response_model=MobileResponse[Dict[str, int]])
async def get_unread_count(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, int]]:
    """Get unread notification counts by type."""
    # Count from Redis
    redis_key = f"notifications:{current_user.id}"
    redis_notifications = await redis_client.lrange(redis_key, 0, -1)
    
    counts = {
        "total": 0,
        "trade": 0,
        "alert": 0,
        "account": 0,
        "system": 0,
        "marketing": 0
    }
    
    for notif_data in redis_notifications:
        notif = json.loads(notif_data)
        if not notif.get('read', False):
            counts["total"] += 1
            notif_type = notif.get('type', 'system')
            counts[notif_type] = counts.get(notif_type, 0) + 1
    
    # Count from database
    result = await db.execute(
        text("""
            SELECT 
                type,
                COUNT(*) as count
            FROM mobile_notifications
            WHERE user_id = :user_id
            AND read = FALSE
            GROUP BY type
        """),
        {"user_id": current_user.id}
    )
    
    for row in result:
        counts[row.type] += row.count
        counts["total"] += row.count
    
    return MobileResponse(data=counts)


@router.put("/update", response_model=MobileResponse[Dict[str, str]])
async def update_notifications(
    request: UpdateNotificationRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update notification status (read/unread/delete)."""
    if request.action == "delete":
        # Delete from database
        await db.execute(
            text("""
                DELETE FROM mobile_notifications
                WHERE id = ANY(:ids)
                AND user_id = :user_id
            """),
            {
                "ids": request.notification_ids,
                "user_id": current_user.id
            }
        )
        
        # Remove from Redis
        redis_key = f"notifications:{current_user.id}"
        redis_notifications = await redis_client.lrange(redis_key, 0, -1)
        
        for i, notif_data in enumerate(redis_notifications):
            notif = json.loads(notif_data)
            if notif.get('id') in request.notification_ids:
                await redis_client.lrem(redis_key, 1, notif_data)
        
        message = f"Deleted {len(request.notification_ids)} notifications"
        
    else:
        # Update read status
        read_status = request.action == "read"
        
        # Update in database
        await db.execute(
            text("""
                UPDATE mobile_notifications
                SET read = :read_status,
                    read_at = CASE WHEN :read_status THEN NOW() ELSE NULL END
                WHERE id = ANY(:ids)
                AND user_id = :user_id
            """),
            {
                "read_status": read_status,
                "ids": request.notification_ids,
                "user_id": current_user.id
            }
        )
        
        # Update in Redis
        redis_key = f"notifications:{current_user.id}"
        redis_notifications = await redis_client.lrange(redis_key, 0, -1)
        
        for i, notif_data in enumerate(redis_notifications):
            notif = json.loads(notif_data)
            if notif.get('id') in request.notification_ids:
                notif['read'] = read_status
                if read_status:
                    notif['read_at'] = datetime.utcnow().isoformat()
                await redis_client.lset(redis_key, i, json.dumps(notif))
        
        message = f"Marked {len(request.notification_ids)} notifications as {request.action}"
    
    await db.commit()
    
    return MobileResponse(data={"message": message})


@router.get("/preferences", response_model=MobileResponse[NotificationPreferences])
async def get_notification_preferences(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[NotificationPreferences]:
    """Get user's notification preferences."""
    prefs = current_user.notification_preferences or {}
    
    # Ensure all fields have defaults
    preferences = NotificationPreferences(
        trades=prefs.get('trades', True),
        alerts=prefs.get('alerts', True),
        account=prefs.get('account', True),
        system=prefs.get('system', True),
        marketing=prefs.get('marketing', False),
        quiet_hours=prefs.get('quiet_hours'),
        channels=prefs.get('channels', {
            "push": True,
            "email": True,
            "sms": False
        })
    )
    
    return MobileResponse(data=preferences)


@router.put("/preferences", response_model=MobileResponse[Dict[str, str]])
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update notification preferences."""
    # Update user preferences
    await db.execute(
        text("""
            UPDATE users
            SET notification_preferences = :preferences
            WHERE id = :user_id
        """),
        {
            "preferences": json.dumps(preferences.dict()),
            "user_id": current_user.id
        }
    )
    
    await db.commit()
    
    return MobileResponse(data={"message": "Preferences updated successfully"})


@router.post("/register-token", response_model=MobileResponse[Dict[str, str]])
async def register_push_token(
    request: RegisterPushTokenRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Register or update push notification token."""
    # Get device ID from request or header
    device_info = request.device_info or get_device_info(request)
    
    if not device_info:
        raise HTTPException(400, "Device information required")
    
    # Update device with push token
    await db.execute(
        text("""
            UPDATE mobile_devices
            SET push_token = :token,
                push_platform = :platform,
                push_token_updated_at = NOW(),
                push_notifications_enabled = TRUE
            WHERE device_id = :device_id
            AND user_id = :user_id
        """),
        {
            "token": request.token,
            "platform": request.platform,
            "device_id": device_info.device_id,
            "user_id": current_user.id
        }
    )
    
    rows_updated = db.rowcount
    
    if rows_updated == 0:
        # Device not found, create it
        await db.execute(
            text("""
                INSERT INTO mobile_devices (
                    device_id, user_id, push_token, push_platform,
                    push_token_updated_at, push_notifications_enabled,
                    device_type, os_version, app_version
                ) VALUES (
                    :device_id, :user_id, :token, :platform,
                    NOW(), TRUE, :device_type, :os_version, :app_version
                )
            """),
            {
                "device_id": device_info.device_id,
                "user_id": current_user.id,
                "token": request.token,
                "platform": request.platform,
                "device_type": device_info.device_type,
                "os_version": device_info.os_version,
                "app_version": device_info.app_version
            }
        )
    
    await db.commit()
    
    # Send test notification
    await _send_push_notification(
        current_user.id,
        "Push Notifications Enabled",
        "You'll now receive TradeSense notifications on this device",
        NotificationType.SYSTEM,
        db
    )
    
    return MobileResponse(data={"message": "Push token registered successfully"})


@router.delete("/unregister-token", response_model=MobileResponse[Dict[str, str]])
async def unregister_push_token(
    device_id: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Unregister push notification token."""
    await db.execute(
        text("""
            UPDATE mobile_devices
            SET push_token = NULL,
                push_notifications_enabled = FALSE
            WHERE device_id = :device_id
            AND user_id = :user_id
        """),
        {
            "device_id": device_id,
            "user_id": current_user.id
        }
    )
    
    await db.commit()
    
    return MobileResponse(data={"message": "Push notifications disabled"})


@router.post("/test", response_model=MobileResponse[Dict[str, str]])
async def send_test_notification(
    request: TestNotificationRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Send a test notification to user's devices."""
    # Send notification
    sent_count = await _send_push_notification(
        current_user.id,
        request.title,
        request.body,
        request.type,
        db
    )
    
    return MobileResponse(
        data={
            "message": f"Test notification sent to {sent_count} device(s)"
        }
    )


# Helper functions
async def _send_push_notification(
    user_id: str,
    title: str,
    body: str,
    notification_type: NotificationType,
    db: AsyncSession,
    data: Optional[Dict[str, Any]] = None,
    priority: NotificationPriority = NotificationPriority.NORMAL
) -> int:
    """Send push notification to user's devices."""
    # Get user's active devices with push tokens
    result = await db.execute(
        text("""
            SELECT 
                device_id, push_token, push_platform
            FROM mobile_devices
            WHERE user_id = :user_id
            AND push_token IS NOT NULL
            AND push_notifications_enabled = TRUE
            AND is_active = TRUE
        """),
        {"user_id": user_id}
    )
    
    devices = list(result)
    sent_count = 0
    
    # Create notification record
    notification_id = await _create_notification_record(
        user_id, title, body, notification_type, priority, data, db
    )
    
    # Send to each device
    for device in devices:
        success = await _send_to_device(
            device.push_token,
            device.push_platform,
            title,
            body,
            data,
            priority
        )
        if success:
            sent_count += 1
    
    # Also store in Redis for in-app delivery
    notification_data = {
        "id": str(notification_id),
        "type": notification_type,
        "title": title,
        "body": body,
        "priority": priority,
        "timestamp": datetime.utcnow().isoformat(),
        "read": False,
        "data": data
    }
    
    redis_key = f"notifications:{user_id}"
    await redis_client.lpush(redis_key, json.dumps(notification_data))
    await redis_client.ltrim(redis_key, 0, 99)  # Keep last 100
    await redis_client.expire(redis_key, 604800)  # 7 days
    
    # Send through WebSocket if connected
    from websocket.manager import manager
    await manager.send_personal_message(
        json.dumps({
            "type": "notification",
            "data": notification_data
        }),
        user_id
    )
    
    return sent_count


async def _create_notification_record(
    user_id: str,
    title: str,
    body: str,
    notification_type: NotificationType,
    priority: NotificationPriority,
    data: Optional[Dict[str, Any]],
    db: AsyncSession
) -> str:
    """Create notification record in database."""
    result = await db.execute(
        text("""
            INSERT INTO mobile_notifications (
                user_id, type, title, body, priority, data
            ) VALUES (
                :user_id, :type, :title, :body, :priority, :data
            )
            RETURNING id
        """),
        {
            "user_id": user_id,
            "type": notification_type,
            "title": title,
            "body": body,
            "priority": priority,
            "data": json.dumps(data) if data else None
        }
    )
    
    await db.commit()
    return result.scalar()


async def _send_to_device(
    token: str,
    platform: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]],
    priority: NotificationPriority
) -> bool:
    """Send push notification to specific device."""
    # This would integrate with Firebase Cloud Messaging or Apple Push Notification Service
    # For now, we'll simulate success
    
    if platform == "ios":
        # Send via APNS
        # await apns_client.send(token, title, body, data)
        pass
    elif platform == "android":
        # Send via FCM
        # await fcm_client.send(token, title, body, data)
        pass
    
    return True


# Public notification service for other modules
class MobileNotificationService:
    """Service for sending mobile notifications."""
    
    @staticmethod
    async def notify_trade_opened(user_id: str, trade_data: Dict[str, Any], db: AsyncSession):
        """Notify user of opened trade."""
        symbol = trade_data.get('symbol', 'Unknown')
        trade_type = trade_data.get('type', 'trade').upper()
        shares = trade_data.get('shares', 0)
        price = trade_data.get('entry_price', 0)
        
        await _send_push_notification(
            user_id,
            f"Trade Opened: {symbol}",
            f"{trade_type} {shares} shares @ ${price:.2f}",
            NotificationType.TRADE,
            db,
            data=trade_data
        )
    
    @staticmethod
    async def notify_trade_closed(user_id: str, trade_data: Dict[str, Any], db: AsyncSession):
        """Notify user of closed trade."""
        symbol = trade_data.get('symbol', 'Unknown')
        pnl = trade_data.get('pnl', 0)
        pnl_sign = "+" if pnl >= 0 else ""
        
        await _send_push_notification(
            user_id,
            f"Trade Closed: {symbol}",
            f"P&L: {pnl_sign}${abs(pnl):.2f}",
            NotificationType.TRADE,
            db,
            data=trade_data,
            priority=NotificationPriority.HIGH if abs(pnl) > 1000 else NotificationPriority.NORMAL
        )
    
    @staticmethod
    async def notify_alert_triggered(user_id: str, alert_data: Dict[str, Any], db: AsyncSession):
        """Notify user of triggered alert."""
        await _send_push_notification(
            user_id,
            f"Alert: {alert_data.get('name', 'Trading Alert')}",
            alert_data.get('message', 'Your alert has been triggered'),
            NotificationType.ALERT,
            db,
            data=alert_data,
            priority=NotificationPriority.HIGH
        )


# Export service
mobile_notification_service = MobileNotificationService()