"""
Trading Alerts API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from core.db.session import get_db
from core.auth import get_current_user
from models.user import User
from alerts.alert_service import (
    alert_service, AlertConfig, AlertCondition, 
    AlertType, AlertChannel, AlertPriority, AlertStatus
)
from monitoring.metrics import feature_usage


router = APIRouter(prefix="/api/v1/alerts")


class CreateAlertRequest(BaseModel):
    """Request to create a new alert."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: AlertType
    conditions: List[AlertCondition]
    channels: List[AlertChannel]
    priority: AlertPriority = AlertPriority.MEDIUM
    
    # Optional fields
    symbols: Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    cooldown_minutes: int = Field(default=60, ge=1, le=1440)  # Max 24 hours
    max_triggers_per_day: Optional[int] = Field(None, ge=1, le=100)
    expires_at: Optional[datetime] = None
    notification_template: Optional[Dict[str, str]] = None
    webhook_url: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    
    @validator('channels')
    def validate_channels(cls, v):
        if not v:
            raise ValueError("At least one notification channel is required")
        return v
    
    @validator('conditions')
    def validate_conditions(cls, v):
        if not v:
            raise ValueError("At least one condition is required")
        return v


class UpdateAlertRequest(BaseModel):
    """Request to update an alert."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    conditions: Optional[List[AlertCondition]] = None
    channels: Optional[List[AlertChannel]] = None
    priority: Optional[AlertPriority] = None
    symbols: Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440)
    max_triggers_per_day: Optional[int] = Field(None, ge=1, le=100)
    expires_at: Optional[datetime] = None
    notification_template: Optional[Dict[str, str]] = None
    webhook_url: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    """Alert response model."""
    id: str
    name: str
    description: Optional[str]
    type: str
    conditions: List[Dict[str, Any]]
    channels: List[str]
    priority: str
    symbols: Optional[List[str]]
    strategies: Optional[List[str]]
    cooldown_minutes: int
    max_triggers_per_day: Optional[int]
    expires_at: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]
    trigger_count: int


class AlertHistoryResponse(BaseModel):
    """Alert history response model."""
    id: str
    alert_id: str
    alert_name: str
    alert_type: str
    triggered_at: datetime
    trigger_data: Dict[str, Any]
    channels_notified: List[str]
    notification_status: Dict[str, str]


@router.post("/create")
@feature_usage("alerts")
async def create_alert(
    request: CreateAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new trading alert."""
    config = AlertConfig(
        name=request.name,
        description=request.description,
        type=request.type,
        conditions=request.conditions,
        channels=request.channels,
        priority=request.priority,
        symbols=request.symbols,
        strategies=request.strategies,
        cooldown_minutes=request.cooldown_minutes,
        max_triggers_per_day=request.max_triggers_per_day,
        expires_at=request.expires_at,
        notification_template=request.notification_template,
        webhook_url=request.webhook_url,
        custom_data=request.custom_data
    )
    
    try:
        result = await alert_service.create_alert(current_user, config, db)
        return {
            "success": True,
            "alert": result,
            "message": "Alert created successfully"
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to create alert: {str(e)}")


@router.get("/list")
async def list_alerts(
    status: Optional[AlertStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """List all alerts for the current user."""
    alerts = await alert_service.get_user_alerts(current_user, db, status)
    
    return {
        "alerts": alerts,
        "total": len(alerts)
    }


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AlertResponse:
    """Get a specific alert."""
    alerts = await alert_service.get_user_alerts(current_user, db)
    
    for alert in alerts:
        if alert["id"] == alert_id:
            return AlertResponse(**alert)
    
    raise HTTPException(404, "Alert not found")


@router.put("/{alert_id}")
async def update_alert(
    alert_id: str,
    request: UpdateAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Update an existing alert."""
    updates = request.dict(exclude_unset=True)
    
    # Convert conditions to JSON if provided
    if 'conditions' in updates:
        updates['conditions'] = json.dumps([c.dict() for c in updates['conditions']])
    
    # Convert other fields to JSON if needed
    if 'notification_template' in updates and updates['notification_template']:
        updates['notification_template'] = json.dumps(updates['notification_template'])
    if 'custom_data' in updates and updates['custom_data']:
        updates['custom_data'] = json.dumps(updates['custom_data'])
    
    success = await alert_service.update_alert(current_user, alert_id, updates, db)
    
    if not success:
        raise HTTPException(404, "Alert not found")
    
    return {
        "success": True,
        "message": "Alert updated successfully"
    }


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Delete an alert."""
    success = await alert_service.delete_alert(current_user, alert_id, db)
    
    if not success:
        raise HTTPException(404, "Alert not found")
    
    return {
        "success": True,
        "message": "Alert deleted successfully"
    }


@router.post("/{alert_id}/toggle")
async def toggle_alert(
    alert_id: str,
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Enable or disable an alert."""
    success = await alert_service.toggle_alert(current_user, alert_id, enabled, db)
    
    if not success:
        raise HTTPException(404, "Alert not found")
    
    return {
        "success": True,
        "enabled": enabled,
        "message": f"Alert {'enabled' if enabled else 'disabled'} successfully"
    }


@router.get("/history/list")
async def get_alert_history(
    alert_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get alert trigger history."""
    history = await alert_service.get_alert_history(
        current_user, alert_id, db, limit
    )
    
    return {
        "history": history,
        "total": len(history)
    }


@router.get("/templates/list")
async def get_alert_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get available alert templates."""
    from sqlalchemy import text
    
    query = """
        SELECT 
            id, name, description, category, alert_type,
            default_conditions, default_channels, default_priority
        FROM alert_templates
        WHERE is_active = TRUE
    """
    
    params = {}
    if category:
        query += " AND category = :category"
        params["category"] = category
    
    query += " ORDER BY category, name"
    
    result = await db.execute(text(query), params)
    
    templates = []
    for row in result:
        templates.append({
            "id": str(row.id),
            "name": row.name,
            "description": row.description,
            "category": row.category,
            "type": row.alert_type,
            "default_conditions": json.loads(row.default_conditions),
            "default_channels": row.default_channels,
            "default_priority": row.default_priority
        })
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/templates/{template_id}/use")
async def create_alert_from_template(
    template_id: str,
    customization: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Create an alert from a template."""
    from sqlalchemy import text
    
    # Get template
    result = await db.execute(
        text("""
            SELECT * FROM alert_templates
            WHERE id = :template_id AND is_active = TRUE
        """),
        {"template_id": template_id}
    )
    
    template = result.first()
    if not template:
        raise HTTPException(404, "Template not found")
    
    # Build alert config from template
    conditions = json.loads(template.default_conditions)
    
    # Apply customizations to conditions
    if 'condition_values' in customization:
        for i, condition in enumerate(conditions):
            if str(i) in customization['condition_values']:
                condition['value'] = customization['condition_values'][str(i)]
    
    config = AlertConfig(
        name=customization.get('name', template.name),
        description=customization.get('description', template.description),
        type=template.alert_type,
        conditions=[AlertCondition(**c) for c in conditions],
        channels=customization.get('channels', template.default_channels),
        priority=customization.get('priority', template.default_priority),
        symbols=customization.get('symbols'),
        strategies=customization.get('strategies'),
        cooldown_minutes=customization.get('cooldown_minutes', 60),
        max_triggers_per_day=customization.get('max_triggers_per_day'),
        expires_at=customization.get('expires_at')
    )
    
    try:
        result = await alert_service.create_alert(current_user, config, db)
        return {
            "success": True,
            "alert": result,
            "message": "Alert created from template successfully"
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/stats/overview")
async def get_alert_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get alert statistics for the current user."""
    from sqlalchemy import text
    
    # Get user stats
    result = await db.execute(
        text("""
            SELECT 
                COUNT(DISTINCT a.id) as total_alerts,
                COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_alerts,
                COUNT(DISTINCT ah.id) as total_triggers,
                COUNT(DISTINCT CASE WHEN ah.triggered_at > NOW() - INTERVAL '24 hours' THEN ah.id END) as triggers_24h,
                COUNT(DISTINCT CASE WHEN ah.triggered_at > NOW() - INTERVAL '7 days' THEN ah.id END) as triggers_7d,
                MAX(ah.triggered_at) as last_trigger
            FROM trading_alerts a
            LEFT JOIN alert_history ah ON a.id = ah.alert_id
            WHERE a.user_id = :user_id
            AND a.status != 'deleted'
        """),
        {"user_id": current_user.id}
    )
    
    stats = result.first()
    
    # Get triggers by type
    type_result = await db.execute(
        text("""
            SELECT 
                a.alert_type,
                COUNT(ah.id) as trigger_count
            FROM trading_alerts a
            JOIN alert_history ah ON a.id = ah.alert_id
            WHERE a.user_id = :user_id
            AND ah.triggered_at > NOW() - INTERVAL '30 days'
            GROUP BY a.alert_type
            ORDER BY trigger_count DESC
        """),
        {"user_id": current_user.id}
    )
    
    triggers_by_type = [
        {"type": row.alert_type, "count": row.trigger_count}
        for row in type_result
    ]
    
    # Get alert limits based on subscription
    tier_limits = {
        'free': 5,
        'starter': 20,
        'pro': 50,
        'premium': 100
    }
    
    alert_limit = tier_limits.get(current_user.subscription_tier, 5)
    
    return {
        "stats": {
            "total_alerts": stats.total_alerts or 0,
            "active_alerts": stats.active_alerts or 0,
            "alert_limit": alert_limit,
            "alerts_remaining": max(0, alert_limit - (stats.active_alerts or 0)),
            "total_triggers": stats.total_triggers or 0,
            "triggers_24h": stats.triggers_24h or 0,
            "triggers_7d": stats.triggers_7d or 0,
            "last_trigger": stats.last_trigger
        },
        "triggers_by_type": triggers_by_type
    }


@router.put("/notification-preferences")
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Update user's notification preferences."""
    from sqlalchemy import text
    
    # Validate preferences
    valid_channels = ['email', 'sms', 'in_app', 'push']
    cleaned_prefs = {
        k: v for k, v in preferences.items() 
        if k in valid_channels and isinstance(v, bool)
    }
    
    # Add quiet hours if provided
    if 'quiet_hours' in preferences:
        cleaned_prefs['quiet_hours'] = preferences['quiet_hours']
    
    # Update user preferences
    await db.execute(
        text("""
            UPDATE users
            SET notification_preferences = :preferences
            WHERE id = :user_id
        """),
        {
            "user_id": current_user.id,
            "preferences": json.dumps(cleaned_prefs)
        }
    )
    
    await db.commit()
    
    return {
        "success": True,
        "preferences": cleaned_prefs,
        "message": "Notification preferences updated"
    }


@router.post("/test/{alert_id}")
async def test_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Test an alert by triggering it manually."""
    from sqlalchemy import text
    
    # Get alert
    result = await db.execute(
        text("""
            SELECT * FROM trading_alerts
            WHERE id = :alert_id AND user_id = :user_id
            AND status != 'deleted'
        """),
        {
            "alert_id": alert_id,
            "user_id": current_user.id
        }
    )
    
    alert = result.first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    
    # Create test trigger data
    test_data = {
        "test_mode": True,
        "triggered_by": "manual_test",
        "current_value": "TEST_VALUE",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Trigger the alert
    await alert_service._trigger_alert(alert, test_data, db)
    
    return {
        "success": True,
        "message": "Test alert sent successfully",
        "channels": alert.channels
    }


# Import json for JSON operations
import json


# Add feature usage decorator
from functools import wraps

def feature_usage(feature: str):
    """Track feature usage for alerts."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Track usage metric
            from monitoring.metrics import feature_usage as usage_metric
            user = kwargs.get('current_user')
            if user:
                usage_metric.labels(
                    feature=feature,
                    user_tier=user.subscription_tier
                ).inc()
            return await func(*args, **kwargs)
        return wrapper
    return decorator