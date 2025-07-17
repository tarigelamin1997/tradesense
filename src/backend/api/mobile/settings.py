"""
Mobile settings and preferences endpoints.
Manages user preferences, app settings, and account configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum

from core.db.session import get_db
from models.user import User
from api.mobile.base import (
    MobileResponse, RequireAuth, DeviceInfo, get_device_info
)
from services.auth_service import AuthService
from sqlalchemy import text
import json


router = APIRouter(prefix="/api/mobile/v1/settings")


class Theme(str, Enum):
    """App theme options."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ChartType(str, Enum):
    """Default chart type."""
    LINE = "line"
    CANDLESTICK = "candlestick"
    BAR = "bar"
    AREA = "area"


class AppSettings(BaseModel):
    """Mobile app settings."""
    theme: Theme = Theme.AUTO
    language: str = "en"
    currency: str = "USD"
    timezone: str = "America/New_York"
    
    # Display preferences
    show_portfolio_value: bool = True
    default_chart_type: ChartType = ChartType.CANDLESTICK
    default_chart_interval: str = "1d"
    
    # Trading preferences
    confirm_trades: bool = True
    default_order_type: str = "market"
    quick_trade_amounts: List[float] = [100, 500, 1000, 5000]
    
    # Data & sync
    auto_sync: bool = True
    sync_interval_minutes: int = 5
    offline_mode_enabled: bool = False
    cache_charts: bool = True
    
    # Privacy
    hide_balances: bool = False
    require_auth_on_open: bool = False
    biometric_enabled: bool = True
    

class NotificationSettings(BaseModel):
    """Notification preferences."""
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    
    # Notification types
    trade_executions: bool = True
    trade_alerts: bool = True
    price_alerts: bool = True
    account_alerts: bool = True
    news_alerts: bool = False
    marketing: bool = False
    
    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    quiet_hours_timezone: str = "America/New_York"
    
    # Alert thresholds
    portfolio_change_threshold: float = 5.0  # Percent
    position_change_threshold: float = 10.0  # Percent
    

class SecuritySettings(BaseModel):
    """Security and privacy settings."""
    two_factor_enabled: bool
    biometric_enabled: bool
    pin_enabled: bool
    auto_lock_minutes: int = 5
    hide_sensitive_info: bool = False
    
    # Session settings
    remember_device_days: int = 30
    require_password_for_trades: bool = False
    
    # Data privacy
    share_analytics: bool = True
    share_crash_reports: bool = True
    

class ProfileUpdate(BaseModel):
    """Profile update request."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    

class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    

class LinkedAccount(BaseModel):
    """Linked brokerage account."""
    id: str
    broker: str
    account_number: str
    account_type: str
    is_primary: bool
    last_sync: Optional[datetime]
    status: str
    

class DataExportRequest(BaseModel):
    """Data export request."""
    include_trades: bool = True
    include_analytics: bool = True
    include_journal: bool = True
    format: str = Field("csv", regex="^(csv|json|pdf)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


@router.get("/app", response_model=MobileResponse[AppSettings])
async def get_app_settings(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[AppSettings]:
    """Get app settings."""
    # Get user's app settings
    settings = current_user.mobile_settings or {}
    
    # Merge with defaults
    app_settings = AppSettings(
        theme=settings.get('theme', Theme.AUTO),
        language=settings.get('language', 'en'),
        currency=settings.get('currency', 'USD'),
        timezone=settings.get('timezone', 'America/New_York'),
        show_portfolio_value=settings.get('show_portfolio_value', True),
        default_chart_type=settings.get('default_chart_type', ChartType.CANDLESTICK),
        default_chart_interval=settings.get('default_chart_interval', '1d'),
        confirm_trades=settings.get('confirm_trades', True),
        default_order_type=settings.get('default_order_type', 'market'),
        quick_trade_amounts=settings.get('quick_trade_amounts', [100, 500, 1000, 5000]),
        auto_sync=settings.get('auto_sync', True),
        sync_interval_minutes=settings.get('sync_interval_minutes', 5),
        offline_mode_enabled=settings.get('offline_mode_enabled', False),
        cache_charts=settings.get('cache_charts', True),
        hide_balances=settings.get('hide_balances', False),
        require_auth_on_open=settings.get('require_auth_on_open', False),
        biometric_enabled=settings.get('biometric_enabled', True)
    )
    
    return MobileResponse(data=app_settings)


@router.put("/app", response_model=MobileResponse[Dict[str, str]])
async def update_app_settings(
    settings: AppSettings,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update app settings."""
    # Update user's mobile settings
    await db.execute(
        text("""
            UPDATE users
            SET mobile_settings = :settings,
                updated_at = NOW()
            WHERE id = :user_id
        """),
        {
            "settings": json.dumps(settings.dict()),
            "user_id": current_user.id
        }
    )
    
    await db.commit()
    
    # Clear cache for user
    from core.cache import redis_client
    await redis_client.delete(f"user_settings:{current_user.id}")
    
    return MobileResponse(data={"message": "Settings updated successfully"})


@router.get("/notifications", response_model=MobileResponse[NotificationSettings])
async def get_notification_settings(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[NotificationSettings]:
    """Get notification settings."""
    prefs = current_user.notification_preferences or {}
    
    notification_settings = NotificationSettings(
        push_enabled=prefs.get('push_enabled', True),
        email_enabled=prefs.get('email_enabled', True),
        sms_enabled=prefs.get('sms_enabled', False),
        trade_executions=prefs.get('trade_executions', True),
        trade_alerts=prefs.get('trade_alerts', True),
        price_alerts=prefs.get('price_alerts', True),
        account_alerts=prefs.get('account_alerts', True),
        news_alerts=prefs.get('news_alerts', False),
        marketing=prefs.get('marketing', False),
        quiet_hours_enabled=prefs.get('quiet_hours_enabled', False),
        quiet_hours_start=prefs.get('quiet_hours_start', '22:00'),
        quiet_hours_end=prefs.get('quiet_hours_end', '08:00'),
        quiet_hours_timezone=prefs.get('quiet_hours_timezone', 'America/New_York'),
        portfolio_change_threshold=prefs.get('portfolio_change_threshold', 5.0),
        position_change_threshold=prefs.get('position_change_threshold', 10.0)
    )
    
    return MobileResponse(data=notification_settings)


@router.put("/notifications", response_model=MobileResponse[Dict[str, str]])
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update notification settings."""
    await db.execute(
        text("""
            UPDATE users
            SET notification_preferences = :preferences,
                updated_at = NOW()
            WHERE id = :user_id
        """),
        {
            "preferences": json.dumps(settings.dict()),
            "user_id": current_user.id
        }
    )
    
    await db.commit()
    
    return MobileResponse(data={"message": "Notification settings updated"})


@router.get("/security", response_model=MobileResponse[SecuritySettings])
async def get_security_settings(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[SecuritySettings]:
    """Get security settings."""
    # Check if 2FA is enabled
    two_factor_enabled = bool(current_user.mfa_secret)
    
    # Check if biometric is enabled for any device
    biometric_result = await db.execute(
        text("""
            SELECT COUNT(*) > 0 as has_biometric
            FROM mobile_biometric_keys
            WHERE user_id = :user_id
        """),
        {"user_id": current_user.id}
    )
    biometric_enabled = biometric_result.scalar()
    
    # Get security preferences
    security_prefs = current_user.security_preferences or {}
    
    security_settings = SecuritySettings(
        two_factor_enabled=two_factor_enabled,
        biometric_enabled=biometric_enabled,
        pin_enabled=security_prefs.get('pin_enabled', False),
        auto_lock_minutes=security_prefs.get('auto_lock_minutes', 5),
        hide_sensitive_info=security_prefs.get('hide_sensitive_info', False),
        remember_device_days=security_prefs.get('remember_device_days', 30),
        require_password_for_trades=security_prefs.get('require_password_for_trades', False),
        share_analytics=security_prefs.get('share_analytics', True),
        share_crash_reports=security_prefs.get('share_crash_reports', True)
    )
    
    return MobileResponse(data=security_settings)


@router.put("/security", response_model=MobileResponse[Dict[str, str]])
async def update_security_settings(
    settings: SecuritySettings,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update security settings."""
    # Don't allow direct updates to 2FA/biometric status via this endpoint
    security_prefs = {
        'pin_enabled': settings.pin_enabled,
        'auto_lock_minutes': settings.auto_lock_minutes,
        'hide_sensitive_info': settings.hide_sensitive_info,
        'remember_device_days': settings.remember_device_days,
        'require_password_for_trades': settings.require_password_for_trades,
        'share_analytics': settings.share_analytics,
        'share_crash_reports': settings.share_crash_reports
    }
    
    await db.execute(
        text("""
            UPDATE users
            SET security_preferences = :preferences,
                updated_at = NOW()
            WHERE id = :user_id
        """),
        {
            "preferences": json.dumps(security_prefs),
            "user_id": current_user.id
        }
    )
    
    await db.commit()
    
    return MobileResponse(data={"message": "Security settings updated"})


@router.get("/profile", response_model=MobileResponse[Dict[str, Any]])
async def get_profile(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, Any]]:
    """Get user profile."""
    # Get account age
    account_age_days = (datetime.utcnow() - current_user.created_at).days
    
    # Get trading stats
    stats_result = await db.execute(
        text("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(DISTINCT symbol) as symbols_traded,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
        """),
        {"user_id": current_user.id}
    )
    stats = stats_result.first()
    
    profile = {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "bio": current_user.bio,
        "avatar_url": current_user.avatar_url,
        "joined_date": current_user.created_at,
        "account_age_days": account_age_days,
        "subscription_tier": current_user.subscription_tier,
        "subscription_status": current_user.subscription_status,
        "stats": {
            "total_trades": stats.total_trades,
            "symbols_traded": stats.symbols_traded,
            "win_rate": round(stats.winning_trades / stats.total_trades * 100, 1) if stats.total_trades > 0 else 0
        }
    }
    
    return MobileResponse(data=profile)


@router.put("/profile", response_model=MobileResponse[Dict[str, str]])
async def update_profile(
    update: ProfileUpdate,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update user profile."""
    updates = []
    params = {"user_id": current_user.id}
    
    if update.full_name is not None:
        updates.append("full_name = :full_name")
        params["full_name"] = update.full_name
    
    if update.phone is not None:
        updates.append("phone = :phone")
        params["phone"] = update.phone
    
    if update.bio is not None:
        updates.append("bio = :bio")
        params["bio"] = update.bio
    
    if update.avatar_url is not None:
        updates.append("avatar_url = :avatar_url")
        params["avatar_url"] = update.avatar_url
    
    if updates:
        updates.append("updated_at = NOW()")
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = :user_id"
        await db.execute(text(query), params)
        await db.commit()
    
    return MobileResponse(data={"message": "Profile updated successfully"})


@router.put("/password", response_model=MobileResponse[Dict[str, str]])
async def change_password(
    request: PasswordChange,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Change user password."""
    auth_service = AuthService(db)
    
    # Verify current password
    from api.deps import verify_password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")
    
    # Update password
    from api.deps import get_password_hash
    hashed_password = get_password_hash(request.new_password)
    
    await db.execute(
        text("""
            UPDATE users
            SET hashed_password = :password,
                password_changed_at = NOW(),
                updated_at = NOW()
            WHERE id = :user_id
        """),
        {
            "password": hashed_password,
            "user_id": current_user.id
        }
    )
    
    # Revoke all refresh tokens to force re-login
    await db.execute(
        text("""
            UPDATE mobile_refresh_tokens
            SET revoked = TRUE,
                revoked_at = NOW()
            WHERE user_id = :user_id
            AND revoked = FALSE
        """),
        {"user_id": current_user.id}
    )
    
    await db.commit()
    
    return MobileResponse(data={"message": "Password changed successfully"})


@router.get("/devices", response_model=MobileResponse[List[Dict[str, Any]]])
async def get_devices(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[Dict[str, Any]]]:
    """Get list of registered devices."""
    result = await db.execute(
        text("""
            SELECT 
                device_id,
                device_type,
                os_version,
                app_version,
                last_active_at,
                is_active,
                push_notifications_enabled,
                created_at,
                CASE 
                    WHEN EXISTS(
                        SELECT 1 FROM mobile_biometric_keys 
                        WHERE device_id = md.device_id
                    ) THEN TRUE ELSE FALSE 
                END as has_biometric
            FROM mobile_devices md
            WHERE user_id = :user_id
            ORDER BY last_active_at DESC
        """),
        {"user_id": current_user.id}
    )
    
    devices = []
    for row in result:
        devices.append({
            "device_id": row.device_id,
            "device_type": row.device_type,
            "os_version": row.os_version,
            "app_version": row.app_version,
            "last_active": row.last_active_at,
            "is_active": row.is_active,
            "push_enabled": row.push_notifications_enabled,
            "biometric_enabled": row.has_biometric,
            "registered_date": row.created_at
        })
    
    return MobileResponse(data=devices)


@router.delete("/devices/{device_id}", response_model=MobileResponse[Dict[str, str]])
async def remove_device(
    device_id: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Remove a device."""
    # Check if it's the current device
    # Don't allow removing the device making the request
    
    # Remove device and related data
    await db.execute(
        text("""
            DELETE FROM mobile_devices
            WHERE device_id = :device_id
            AND user_id = :user_id
        """),
        {
            "device_id": device_id,
            "user_id": current_user.id
        }
    )
    
    # Remove biometric keys
    await db.execute(
        text("""
            DELETE FROM mobile_biometric_keys
            WHERE device_id = :device_id
            AND user_id = :user_id
        """),
        {
            "device_id": device_id,
            "user_id": current_user.id
        }
    )
    
    # Revoke refresh tokens
    await db.execute(
        text("""
            UPDATE mobile_refresh_tokens
            SET revoked = TRUE,
                revoked_at = NOW()
            WHERE device_id = :device_id
            AND user_id = :user_id
        """),
        {
            "device_id": device_id,
            "user_id": current_user.id
        }
    )
    
    await db.commit()
    
    return MobileResponse(data={"message": "Device removed successfully"})


@router.get("/linked-accounts", response_model=MobileResponse[List[LinkedAccount]])
async def get_linked_accounts(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[LinkedAccount]]:
    """Get linked brokerage accounts."""
    result = await db.execute(
        text("""
            SELECT 
                id, broker_name, account_number, account_type,
                is_primary, last_sync_at, status, created_at
            FROM linked_accounts
            WHERE user_id = :user_id
            ORDER BY is_primary DESC, created_at
        """),
        {"user_id": current_user.id}
    )
    
    accounts = []
    for row in result:
        accounts.append(LinkedAccount(
            id=str(row.id),
            broker=row.broker_name,
            account_number=row.account_number[-4:],  # Only show last 4 digits
            account_type=row.account_type,
            is_primary=row.is_primary,
            last_sync=row.last_sync_at,
            status=row.status
        ))
    
    return MobileResponse(data=accounts)


@router.post("/export", response_model=MobileResponse[Dict[str, str]])
async def export_data(
    request: DataExportRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Request data export."""
    # Create export job
    result = await db.execute(
        text("""
            INSERT INTO data_export_jobs (
                user_id, format, options, status
            ) VALUES (
                :user_id, :format, :options, 'pending'
            )
            RETURNING id
        """),
        {
            "user_id": current_user.id,
            "format": request.format,
            "options": json.dumps(request.dict())
        }
    )
    
    job_id = result.scalar()
    await db.commit()
    
    # Queue export job
    from core.celery_app import celery_app
    celery_app.send_task(
        "app.tasks.export_user_data",
        args=[str(job_id), current_user.id, request.dict()]
    )
    
    return MobileResponse(
        data={
            "job_id": str(job_id),
            "message": "Export requested. You'll receive an email when ready."
        }
    )


@router.delete("/account", response_model=MobileResponse[Dict[str, str]])
async def delete_account(
    password: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Delete user account (soft delete)."""
    # Verify password
    from api.deps import verify_password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(400, "Incorrect password")
    
    # Soft delete account
    await db.execute(
        text("""
            UPDATE users
            SET is_active = FALSE,
                deleted_at = NOW(),
                email = CONCAT(email, '_deleted_', EXTRACT(EPOCH FROM NOW())),
                username = CONCAT(username, '_deleted_', EXTRACT(EPOCH FROM NOW()))
            WHERE id = :user_id
        """),
        {"user_id": current_user.id}
    )
    
    # Cancel subscriptions
    await db.execute(
        text("""
            UPDATE subscriptions
            SET status = 'cancelled',
                cancelled_at = NOW()
            WHERE user_id = :user_id
            AND status = 'active'
        """),
        {"user_id": current_user.id}
    )
    
    # Revoke all tokens
    await db.execute(
        text("""
            UPDATE mobile_refresh_tokens
            SET revoked = TRUE,
                revoked_at = NOW()
            WHERE user_id = :user_id
        """),
        {"user_id": current_user.id}
    )
    
    await db.commit()
    
    return MobileResponse(
        data={"message": "Account deleted successfully"}
    )


@router.get("/help", response_model=MobileResponse[Dict[str, Any]])
async def get_help_resources(
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, Any]]:
    """Get help resources and support information."""
    return MobileResponse(
        data={
            "support_email": "support@tradesense.app",
            "faq_url": "https://tradesense.app/faq",
            "docs_url": "https://docs.tradesense.app",
            "video_tutorials": [
                {
                    "title": "Getting Started",
                    "url": "https://tradesense.app/tutorials/getting-started",
                    "duration": "5:23"
                },
                {
                    "title": "Analyzing Your Trades",
                    "url": "https://tradesense.app/tutorials/analytics",
                    "duration": "8:45"
                },
                {
                    "title": "Setting Up Alerts",
                    "url": "https://tradesense.app/tutorials/alerts",
                    "duration": "4:12"
                }
            ],
            "contact_methods": {
                "email": True,
                "chat": True,
                "phone": False
            },
            "business_hours": "Mon-Fri 9AM-6PM EST"
        }
    )
