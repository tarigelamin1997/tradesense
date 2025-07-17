"""
Automated Trading Alerts Service for TradeSense.
Handles alert creation, evaluation, and notification delivery.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import json
from enum import Enum
from pydantic import BaseModel, Field, validator
import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.user import User
from services.email_service import email_service
from src.backend.monitoring.metrics import alert_metrics
from core.cache import redis_client


class AlertType(str, Enum):
    """Types of trading alerts."""
    # Price-based alerts
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE_PERCENT = "price_change_percent"
    
    # Performance alerts
    DAILY_PNL = "daily_pnl"
    WEEKLY_PNL = "weekly_pnl"
    WIN_RATE = "win_rate"
    LOSS_STREAK = "loss_streak"
    WIN_STREAK = "win_streak"
    
    # Risk alerts
    DRAWDOWN = "drawdown"
    POSITION_SIZE = "position_size"
    EXPOSURE_LIMIT = "exposure_limit"
    
    # Pattern alerts
    PATTERN_DETECTED = "pattern_detected"
    STRATEGY_SIGNAL = "strategy_signal"
    
    # Market alerts
    VOLUME_SPIKE = "volume_spike"
    VOLATILITY = "volatility"
    NEWS_SENTIMENT = "news_sentiment"
    
    # Account alerts
    MARGIN_CALL = "margin_call"
    ACCOUNT_BALANCE = "account_balance"
    TRADE_EXECUTION = "trade_execution"


class AlertChannel(str, Enum):
    """Notification channels for alerts."""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    PUSH = "push"  # Mobile push notifications


class AlertPriority(str, Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    SNOOZED = "snoozed"
    DISABLED = "disabled"
    EXPIRED = "expired"


class AlertCondition(BaseModel):
    """Defines the condition for triggering an alert."""
    field: str
    operator: str  # gt, lt, eq, gte, lte, contains, regex
    value: Union[str, float, int, bool]
    time_window: Optional[int] = None  # Minutes to evaluate over
    
    @validator('operator')
    def validate_operator(cls, v):
        valid_operators = ['gt', 'lt', 'eq', 'gte', 'lte', 'contains', 'regex', 'change_percent']
        if v not in valid_operators:
            raise ValueError(f"Invalid operator. Must be one of: {valid_operators}")
        return v


class AlertConfig(BaseModel):
    """Configuration for an alert."""
    name: str
    description: Optional[str] = None
    type: AlertType
    conditions: List[AlertCondition]
    channels: List[AlertChannel]
    priority: AlertPriority = AlertPriority.MEDIUM
    
    # Symbols/strategies to monitor
    symbols: Optional[List[str]] = None
    strategies: Optional[List[str]] = None
    
    # Alert behavior
    cooldown_minutes: int = 60  # Minimum time between triggers
    max_triggers_per_day: Optional[int] = None
    expires_at: Optional[datetime] = None
    
    # Notification settings
    notification_template: Optional[Dict[str, str]] = None
    webhook_url: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None


class AlertService:
    """Manages automated trading alerts."""
    
    def __init__(self):
        self.evaluation_interval = 60  # seconds
        self._running = False
        self._market_data_cache = {}
        self._alert_cache = {}
        
        # Initialize notification clients
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            from twilio.rest import Client
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
    
    async def create_alert(
        self,
        user: User,
        config: AlertConfig,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new alert."""
        # Validate user has permission
        if not await self._check_alert_limit(user, db):
            raise ValueError("Alert limit reached for your subscription tier")
        
        # Create alert in database
        result = await db.execute(
            text("""
                INSERT INTO trading_alerts (
                    user_id, name, description, alert_type,
                    conditions, channels, priority, symbols,
                    strategies, cooldown_minutes, max_triggers_per_day,
                    expires_at, notification_template, webhook_url,
                    custom_data, status
                ) VALUES (
                    :user_id, :name, :description, :alert_type,
                    :conditions, :channels, :priority, :symbols,
                    :strategies, :cooldown_minutes, :max_triggers_per_day,
                    :expires_at, :notification_template, :webhook_url,
                    :custom_data, :status
                )
                RETURNING id, created_at
            """),
            {
                "user_id": user.id,
                "name": config.name,
                "description": config.description,
                "alert_type": config.type,
                "conditions": json.dumps([c.dict() for c in config.conditions]),
                "channels": config.channels,
                "priority": config.priority,
                "symbols": config.symbols,
                "strategies": config.strategies,
                "cooldown_minutes": config.cooldown_minutes,
                "max_triggers_per_day": config.max_triggers_per_day,
                "expires_at": config.expires_at,
                "notification_template": json.dumps(config.notification_template) if config.notification_template else None,
                "webhook_url": config.webhook_url,
                "custom_data": json.dumps(config.custom_data) if config.custom_data else None,
                "status": AlertStatus.ACTIVE
            }
        )
        
        alert_data = result.first()
        await db.commit()
        
        # Track metric
        alert_metrics.alerts_created.labels(
            alert_type=config.type,
            priority=config.priority
        ).inc()
        
        return {
            "id": str(alert_data.id),
            "name": config.name,
            "type": config.type,
            "status": AlertStatus.ACTIVE,
            "created_at": alert_data.created_at
        }
    
    async def update_alert(
        self,
        user: User,
        alert_id: str,
        updates: Dict[str, Any],
        db: AsyncSession
    ) -> bool:
        """Update an existing alert."""
        # Verify ownership
        result = await db.execute(
            text("""
                UPDATE trading_alerts
                SET updated_at = NOW(),
                    name = COALESCE(:name, name),
                    description = COALESCE(:description, description),
                    conditions = COALESCE(:conditions, conditions),
                    channels = COALESCE(:channels, channels),
                    priority = COALESCE(:priority, priority),
                    symbols = COALESCE(:symbols, symbols),
                    strategies = COALESCE(:strategies, strategies),
                    cooldown_minutes = COALESCE(:cooldown_minutes, cooldown_minutes),
                    max_triggers_per_day = COALESCE(:max_triggers_per_day, max_triggers_per_day),
                    expires_at = COALESCE(:expires_at, expires_at),
                    notification_template = COALESCE(:notification_template, notification_template),
                    webhook_url = COALESCE(:webhook_url, webhook_url),
                    custom_data = COALESCE(:custom_data, custom_data)
                WHERE id = :alert_id AND user_id = :user_id
            """),
            {
                "alert_id": alert_id,
                "user_id": user.id,
                **updates
            }
        )
        
        if result.rowcount > 0:
            await db.commit()
            return True
        
        return False
    
    async def delete_alert(
        self,
        user: User,
        alert_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete an alert."""
        result = await db.execute(
            text("""
                UPDATE trading_alerts
                SET status = 'deleted',
                    deleted_at = NOW()
                WHERE id = :alert_id AND user_id = :user_id
            """),
            {
                "alert_id": alert_id,
                "user_id": user.id
            }
        )
        
        if result.rowcount > 0:
            await db.commit()
            
            # Track metric
            alert_metrics.alerts_deleted.inc()
            
            return True
        
        return False
    
    async def toggle_alert(
        self,
        user: User,
        alert_id: str,
        enabled: bool,
        db: AsyncSession
    ) -> bool:
        """Enable or disable an alert."""
        status = AlertStatus.ACTIVE if enabled else AlertStatus.DISABLED
        
        result = await db.execute(
            text("""
                UPDATE trading_alerts
                SET status = :status,
                    updated_at = NOW()
                WHERE id = :alert_id AND user_id = :user_id
            """),
            {
                "alert_id": alert_id,
                "user_id": user.id,
                "status": status
            }
        )
        
        if result.rowcount > 0:
            await db.commit()
            return True
        
        return False
    
    async def get_user_alerts(
        self,
        user: User,
        db: AsyncSession,
        status: Optional[AlertStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get all alerts for a user."""
        query = """
            SELECT 
                id, name, description, alert_type, conditions,
                channels, priority, symbols, strategies,
                cooldown_minutes, max_triggers_per_day,
                expires_at, status, created_at, updated_at,
                last_triggered_at, trigger_count
            FROM trading_alerts
            WHERE user_id = :user_id
            AND status != 'deleted'
        """
        
        params = {"user_id": user.id}
        
        if status:
            query += " AND status = :status"
            params["status"] = status
        
        query += " ORDER BY created_at DESC"
        
        result = await db.execute(text(query), params)
        
        alerts = []
        for row in result:
            alerts.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "type": row.alert_type,
                "conditions": json.loads(row.conditions) if row.conditions else [],
                "channels": row.channels,
                "priority": row.priority,
                "symbols": row.symbols,
                "strategies": row.strategies,
                "cooldown_minutes": row.cooldown_minutes,
                "max_triggers_per_day": row.max_triggers_per_day,
                "expires_at": row.expires_at,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "last_triggered_at": row.last_triggered_at,
                "trigger_count": row.trigger_count
            })
        
        return alerts
    
    async def get_alert_history(
        self,
        user: User,
        alert_id: Optional[str],
        db: AsyncSession,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get alert trigger history."""
        query = """
            SELECT 
                ah.id, ah.alert_id, ah.triggered_at,
                ah.trigger_data, ah.channels_notified,
                ah.notification_status, a.name as alert_name,
                a.alert_type
            FROM alert_history ah
            JOIN trading_alerts a ON ah.alert_id = a.id
            WHERE a.user_id = :user_id
        """
        
        params = {"user_id": user.id}
        
        if alert_id:
            query += " AND ah.alert_id = :alert_id"
            params["alert_id"] = alert_id
        
        query += " ORDER BY ah.triggered_at DESC LIMIT :limit"
        params["limit"] = limit
        
        result = await db.execute(text(query), params)
        
        history = []
        for row in result:
            history.append({
                "id": str(row.id),
                "alert_id": str(row.alert_id),
                "alert_name": row.alert_name,
                "alert_type": row.alert_type,
                "triggered_at": row.triggered_at,
                "trigger_data": json.loads(row.trigger_data) if row.trigger_data else {},
                "channels_notified": row.channels_notified,
                "notification_status": row.notification_status
            })
        
        return history
    
    async def evaluate_alerts(self, db: AsyncSession):
        """Evaluate all active alerts."""
        # Get active alerts
        result = await db.execute(
            text("""
                SELECT 
                    a.*, u.email, u.phone_number, u.notification_preferences
                FROM trading_alerts a
                JOIN users u ON a.user_id = u.id
                WHERE a.status = 'active'
                AND (a.expires_at IS NULL OR a.expires_at > NOW())
                AND (
                    a.last_triggered_at IS NULL 
                    OR a.last_triggered_at < NOW() - INTERVAL '1 minute' * a.cooldown_minutes
                )
            """)
        )
        
        for alert_row in result:
            try:
                await self._evaluate_single_alert(alert_row, db)
            except Exception as e:
                print(f"Error evaluating alert {alert_row.id}: {e}")
                
                # Track error
                alert_metrics.alert_errors.labels(
                    alert_type=alert_row.alert_type,
                    error_type=type(e).__name__
                ).inc()
    
    async def _evaluate_single_alert(self, alert_row, db: AsyncSession):
        """Evaluate a single alert."""
        conditions = json.loads(alert_row.conditions)
        alert_type = alert_row.alert_type
        
        # Get relevant data based on alert type
        trigger_data = await self._get_alert_data(
            alert_row.user_id,
            alert_type,
            alert_row.symbols,
            alert_row.strategies,
            db
        )
        
        # Check if all conditions are met
        triggered = await self._check_conditions(conditions, trigger_data)
        
        if triggered:
            # Check daily trigger limit
            if alert_row.max_triggers_per_day:
                today_triggers = await self._get_today_triggers(alert_row.id, db)
                if today_triggers >= alert_row.max_triggers_per_day:
                    return
            
            # Trigger the alert
            await self._trigger_alert(alert_row, trigger_data, db)
    
    async def _check_conditions(
        self,
        conditions: List[Dict],
        data: Dict[str, Any]
    ) -> bool:
        """Check if all alert conditions are met."""
        for condition in conditions:
            field_value = data.get(condition['field'])
            if field_value is None:
                return False
            
            operator = condition['operator']
            target_value = condition['value']
            
            # Evaluate condition based on operator
            if operator == 'gt' and not (field_value > target_value):
                return False
            elif operator == 'lt' and not (field_value < target_value):
                return False
            elif operator == 'eq' and not (field_value == target_value):
                return False
            elif operator == 'gte' and not (field_value >= target_value):
                return False
            elif operator == 'lte' and not (field_value <= target_value):
                return False
            elif operator == 'contains' and target_value not in str(field_value):
                return False
            elif operator == 'change_percent':
                # Special handling for percentage change
                if 'previous_value' in data:
                    prev = data['previous_value']
                    if prev != 0:
                        change = ((field_value - prev) / prev) * 100
                        if not (change > target_value):
                            return False
                    else:
                        return False
                else:
                    return False
        
        return True
    
    async def _trigger_alert(self, alert_row, trigger_data: Dict, db: AsyncSession):
        """Trigger an alert and send notifications."""
        # Record trigger
        result = await db.execute(
            text("""
                INSERT INTO alert_history (
                    alert_id, user_id, triggered_at,
                    trigger_data, channels_notified
                ) VALUES (
                    :alert_id, :user_id, NOW(),
                    :trigger_data, :channels
                )
                RETURNING id
            """),
            {
                "alert_id": alert_row.id,
                "user_id": alert_row.user_id,
                "trigger_data": json.dumps(trigger_data),
                "channels": alert_row.channels
            }
        )
        
        history_id = result.scalar()
        
        # Update alert last triggered
        await db.execute(
            text("""
                UPDATE trading_alerts
                SET last_triggered_at = NOW(),
                    trigger_count = trigger_count + 1
                WHERE id = :alert_id
            """),
            {"alert_id": alert_row.id}
        )
        
        await db.commit()
        
        # Send notifications
        notification_status = {}
        for channel in alert_row.channels:
            try:
                success = await self._send_notification(
                    channel,
                    alert_row,
                    trigger_data
                )
                notification_status[channel] = "success" if success else "failed"
            except Exception as e:
                notification_status[channel] = f"error: {str(e)}"
        
        # Update notification status
        await db.execute(
            text("""
                UPDATE alert_history
                SET notification_status = :status
                WHERE id = :id
            """),
            {
                "id": history_id,
                "status": json.dumps(notification_status)
            }
        )
        await db.commit()
        
        # Track metrics
        alert_metrics.alerts_triggered.labels(
            alert_type=alert_row.alert_type,
            priority=alert_row.priority
        ).inc()
        
        for channel, status in notification_status.items():
            alert_metrics.notifications_sent.labels(
                channel=channel,
                status="success" if status == "success" else "failed"
            ).inc()
    
    async def _send_notification(
        self,
        channel: str,
        alert_row,
        trigger_data: Dict
    ) -> bool:
        """Send notification through specified channel."""
        if channel == AlertChannel.EMAIL:
            return await self._send_email_notification(alert_row, trigger_data)
        elif channel == AlertChannel.SMS:
            return await self._send_sms_notification(alert_row, trigger_data)
        elif channel == AlertChannel.IN_APP:
            return await self._send_in_app_notification(alert_row, trigger_data)
        elif channel == AlertChannel.WEBHOOK:
            return await self._send_webhook_notification(alert_row, trigger_data)
        else:
            return False
    
    async def _send_email_notification(self, alert_row, trigger_data: Dict) -> bool:
        """Send email notification."""
        template = alert_row.notification_template
        if template and isinstance(template, str):
            template = json.loads(template)
        
        subject = template.get('email_subject') if template else None
        if not subject:
            subject = f"TradeSense Alert: {alert_row.name}"
        
        # Build email body
        body = f"""
        <h2>Trading Alert Triggered</h2>
        <p><strong>Alert:</strong> {alert_row.name}</p>
        <p><strong>Type:</strong> {alert_row.alert_type}</p>
        <p><strong>Priority:</strong> {alert_row.priority}</p>
        
        <h3>Trigger Details</h3>
        <ul>
        """
        
        for key, value in trigger_data.items():
            if not key.startswith('_'):  # Skip internal fields
                body += f"<li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>"
        
        body += """
        </ul>
        
        <p>Manage your alerts in the <a href="https://tradesense.com/alerts">TradeSense Dashboard</a></p>
        """
        
        try:
            await email_service.send_email(
                to_email=alert_row.email,
                subject=subject,
                body=body,
                is_html=True
            )
            return True
        except Exception as e:
            print(f"Email notification error: {e}")
            return False
    
    async def _send_sms_notification(self, alert_row, trigger_data: Dict) -> bool:
        """Send SMS notification."""
        if not self.twilio_client or not alert_row.phone_number:
            return False
        
        template = alert_row.notification_template
        if template and isinstance(template, str):
            template = json.loads(template)
        
        message = template.get('sms_message') if template else None
        if not message:
            # Default message
            value_str = ""
            if 'current_value' in trigger_data:
                value_str = f" Value: {trigger_data['current_value']}"
            
            message = f"TradeSense Alert: {alert_row.name} triggered.{value_str}"
        
        try:
            self.twilio_client.messages.create(
                body=message[:160],  # SMS length limit
                from_=settings.TWILIO_PHONE_NUMBER,
                to=alert_row.phone_number
            )
            return True
        except Exception as e:
            print(f"SMS notification error: {e}")
            return False
    
    async def _send_in_app_notification(self, alert_row, trigger_data: Dict) -> bool:
        """Send in-app notification."""
        notification = {
            "user_id": alert_row.user_id,
            "type": "alert",
            "title": f"Alert: {alert_row.name}",
            "message": f"Your {alert_row.alert_type} alert has been triggered",
            "data": {
                "alert_id": str(alert_row.id),
                "alert_type": alert_row.alert_type,
                "trigger_data": trigger_data
            },
            "priority": alert_row.priority,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis for real-time delivery
        await redis_client.lpush(
            f"notifications:{alert_row.user_id}",
            json.dumps(notification)
        )
        
        # Expire after 7 days
        await redis_client.expire(f"notifications:{alert_row.user_id}", 604800)
        
        # Send through WebSocket if connected
        from src.backend.websocket.manager import manager
        await manager.send_personal_message(
            json.dumps({
                "type": "notification",
                "data": notification
            }),
            alert_row.user_id
        )
        
        return True
    
    async def _send_webhook_notification(self, alert_row, trigger_data: Dict) -> bool:
        """Send webhook notification."""
        if not alert_row.webhook_url:
            return False
        
        payload = {
            "alert_id": str(alert_row.id),
            "alert_name": alert_row.name,
            "alert_type": alert_row.alert_type,
            "priority": alert_row.priority,
            "triggered_at": datetime.utcnow().isoformat(),
            "trigger_data": trigger_data,
            "custom_data": json.loads(alert_row.custom_data) if alert_row.custom_data else {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    alert_row.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Webhook notification error: {e}")
            return False
    
    async def _get_alert_data(
        self,
        user_id: str,
        alert_type: str,
        symbols: Optional[List[str]],
        strategies: Optional[List[str]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get data relevant to the alert type."""
        data = {}
        
        if alert_type == AlertType.DAILY_PNL:
            # Get today's P&L
            result = await db.execute(
                text("""
                    SELECT SUM(pnl) as daily_pnl
                    FROM trades
                    WHERE user_id = :user_id
                    AND DATE(exit_time) = CURRENT_DATE
                    AND status = 'closed'
                """),
                {"user_id": user_id}
            )
            row = result.first()
            data['current_value'] = float(row.daily_pnl or 0)
            
        elif alert_type == AlertType.WIN_RATE:
            # Calculate current win rate
            result = await db.execute(
                text("""
                    SELECT 
                        COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                        COUNT(*) as total
                    FROM trades
                    WHERE user_id = :user_id
                    AND status = 'closed'
                    AND exit_time > NOW() - INTERVAL '30 days'
                """),
                {"user_id": user_id}
            )
            row = result.first()
            if row.total > 0:
                data['current_value'] = (row.wins / row.total) * 100
            else:
                data['current_value'] = 0
                
        elif alert_type == AlertType.LOSS_STREAK:
            # Count consecutive losses
            result = await db.execute(
                text("""
                    WITH consecutive_trades AS (
                        SELECT 
                            pnl,
                            ROW_NUMBER() OVER (ORDER BY exit_time DESC) as rn,
                            ROW_NUMBER() OVER (PARTITION BY CASE WHEN pnl < 0 THEN 1 ELSE 0 END ORDER BY exit_time DESC) as grp
                        FROM trades
                        WHERE user_id = :user_id
                        AND status = 'closed'
                        ORDER BY exit_time DESC
                    )
                    SELECT COUNT(*) as streak
                    FROM consecutive_trades
                    WHERE pnl < 0
                    AND rn = grp
                """),
                {"user_id": user_id}
            )
            row = result.first()
            data['current_value'] = row.streak or 0
            
        elif alert_type == AlertType.DRAWDOWN:
            # Calculate current drawdown
            result = await db.execute(
                text("""
                    WITH equity_curve AS (
                        SELECT 
                            SUM(pnl) OVER (ORDER BY exit_time) as cumulative_pnl
                        FROM trades
                        WHERE user_id = :user_id
                        AND status = 'closed'
                        ORDER BY exit_time
                    )
                    SELECT 
                        MAX(cumulative_pnl) as peak,
                        MIN(cumulative_pnl) as trough
                    FROM equity_curve
                """),
                {"user_id": user_id}
            )
            row = result.first()
            if row.peak and row.peak > 0:
                drawdown = ((row.peak - (row.trough or 0)) / row.peak) * 100
                data['current_value'] = drawdown
            else:
                data['current_value'] = 0
        
        # Add symbol/strategy specific data if needed
        if symbols:
            data['symbols'] = symbols
        if strategies:
            data['strategies'] = strategies
            
        data['timestamp'] = datetime.utcnow().isoformat()
        
        return data
    
    async def _check_alert_limit(self, user: User, db: AsyncSession) -> bool:
        """Check if user has reached alert limit."""
        # Get user's subscription tier limits
        tier_limits = {
            'free': 5,
            'starter': 20,
            'pro': 50,
            'premium': 100
        }
        
        limit = tier_limits.get(user.subscription_tier, 5)
        
        # Count active alerts
        result = await db.execute(
            text("""
                SELECT COUNT(*) as alert_count
                FROM trading_alerts
                WHERE user_id = :user_id
                AND status IN ('active', 'disabled')
            """),
            {"user_id": user.id}
        )
        
        count = result.scalar()
        return count < limit
    
    async def _get_today_triggers(self, alert_id: str, db: AsyncSession) -> int:
        """Get number of times alert triggered today."""
        result = await db.execute(
            text("""
                SELECT COUNT(*) as trigger_count
                FROM alert_history
                WHERE alert_id = :alert_id
                AND DATE(triggered_at) = CURRENT_DATE
            """),
            {"alert_id": alert_id}
        )
        
        return result.scalar() or 0
    
    async def start(self):
        """Start the alert evaluation loop."""
        self._running = True
        while self._running:
            try:
                async with get_db() as db:
                    await self.evaluate_alerts(db)
                    
                await asyncio.sleep(self.evaluation_interval)
                
            except Exception as e:
                print(f"Alert service error: {e}")
                await asyncio.sleep(self.evaluation_interval)
    
    async def stop(self):
        """Stop the alert evaluation loop."""
        self._running = False


# Alert metrics
class AlertMetrics:
    def __init__(self):
        from prometheus_client import Counter, Gauge, Histogram
        
        self.alerts_created = Counter(
            'tradesense_alerts_created_total',
            'Total number of alerts created',
            ['alert_type', 'priority']
        )
        
        self.alerts_triggered = Counter(
            'tradesense_alerts_triggered_total',
            'Total number of alerts triggered',
            ['alert_type', 'priority']
        )
        
        self.alerts_deleted = Counter(
            'tradesense_alerts_deleted_total',
            'Total number of alerts deleted'
        )
        
        self.notifications_sent = Counter(
            'tradesense_alert_notifications_sent_total',
            'Total number of alert notifications sent',
            ['channel', 'status']
        )
        
        self.alert_errors = Counter(
            'tradesense_alert_errors_total',
            'Total number of alert evaluation errors',
            ['alert_type', 'error_type']
        )
        
        self.active_alerts = Gauge(
            'tradesense_active_alerts',
            'Number of active alerts',
            ['alert_type']
        )
        
        self.alert_evaluation_duration = Histogram(
            'tradesense_alert_evaluation_duration_seconds',
            'Time spent evaluating alerts',
            buckets=(0.01, 0.05, 0.1, 0.5, 1, 2.5, 5, 10)
        )

alert_metrics = AlertMetrics()

# Initialize service
alert_service = AlertService()