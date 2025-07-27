"""
Alerting system for TradeSense.
Manages alert rules, evaluations, and notifications.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from core.config import settings
from core.db.session import get_db
from core.cache import redis_client
from services.email_service import email_service
from sqlalchemy import text


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    FIRING = "firing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Represents an alert instance."""
    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    details: Dict[str, Any]
    fired_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    runbook_url: Optional[str] = None


@dataclass
class AlertRule:
    """Defines an alert rule."""
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable
    message_template: str
    cooldown_minutes: int = 5
    tags: List[str] = field(default_factory=list)
    runbook_url: Optional[str] = None
    enabled: bool = True


class AlertingSystem:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.evaluation_interval = 60  # seconds
        self._running = False
        self._init_default_rules()
    
    def _init_default_rules(self):
        """Initialize default alert rules."""
        
        # High error rate alert
        self.add_rule(
            AlertRule(
                name="high_error_rate",
                description="API error rate exceeds threshold",
                severity=AlertSeverity.HIGH,
                condition=self._check_error_rate,
                message_template="API error rate is {error_rate:.2%} (threshold: {threshold:.2%})",
                cooldown_minutes=5,
                tags=["api", "errors"],
                runbook_url="https://docs.tradesense.com/runbook#high-error-rate"
            )
        )
        
        # Database connection pool alert
        self.add_rule(
            AlertRule(
                name="db_connection_pool_exhausted",
                description="Database connection pool is exhausted",
                severity=AlertSeverity.CRITICAL,
                condition=self._check_db_connections,
                message_template="Database connection pool usage: {used}/{total} connections",
                cooldown_minutes=3,
                tags=["database", "performance"],
                runbook_url="https://docs.tradesense.com/runbook#db-connections"
            )
        )
        
        # High memory usage alert
        self.add_rule(
            AlertRule(
                name="high_memory_usage",
                description="Application memory usage is high",
                severity=AlertSeverity.MEDIUM,
                condition=self._check_memory_usage,
                message_template="Memory usage is {memory_percent:.1f}% (threshold: {threshold}%)",
                cooldown_minutes=10,
                tags=["system", "performance"]
            )
        )
        
        # Payment failures alert
        self.add_rule(
            AlertRule(
                name="payment_failures",
                description="High rate of payment failures",
                severity=AlertSeverity.HIGH,
                condition=self._check_payment_failures,
                message_template="Payment failure rate: {failure_rate:.2%} in last {window} minutes",
                cooldown_minutes=15,
                tags=["payments", "business"],
                runbook_url="https://docs.tradesense.com/runbook#payment-failures"
            )
        )
        
        # Cache hit rate alert
        self.add_rule(
            AlertRule(
                name="low_cache_hit_rate",
                description="Cache hit rate is below threshold",
                severity=AlertSeverity.MEDIUM,
                condition=self._check_cache_hit_rate,
                message_template="Cache hit rate: {hit_rate:.2%} (threshold: {threshold:.2%})",
                cooldown_minutes=10,
                tags=["cache", "performance"]
            )
        )
        
        # User activity drop alert
        self.add_rule(
            AlertRule(
                name="user_activity_drop",
                description="Significant drop in user activity",
                severity=AlertSeverity.HIGH,
                condition=self._check_user_activity,
                message_template="User activity dropped by {drop_percent:.1f}% compared to {comparison_period}",
                cooldown_minutes=30,
                tags=["business", "users"]
            )
        )
        
        # SSL certificate expiry alert
        self.add_rule(
            AlertRule(
                name="ssl_certificate_expiry",
                description="SSL certificate expiring soon",
                severity=AlertSeverity.HIGH,
                condition=self._check_ssl_expiry,
                message_template="SSL certificate expires in {days_remaining} days",
                cooldown_minutes=1440,  # 24 hours
                tags=["security", "infrastructure"]
            )
        )
        
        # Disk space alert
        self.add_rule(
            AlertRule(
                name="low_disk_space",
                description="Disk space is running low",
                severity=AlertSeverity.HIGH,
                condition=self._check_disk_space,
                message_template="Disk usage: {disk_percent:.1f}% on {mount_point}",
                cooldown_minutes=30,
                tags=["system", "infrastructure"]
            )
        )
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule."""
        self.rules.pop(rule_name, None)
    
    async def start(self):
        """Start the alerting system."""
        self._running = True
        while self._running:
            try:
                await self.evaluate_rules()
                await asyncio.sleep(self.evaluation_interval)
            except Exception as e:
                print(f"Error in alerting system: {e}")
                await asyncio.sleep(self.evaluation_interval)
    
    async def stop(self):
        """Stop the alerting system."""
        self._running = False
    
    async def evaluate_rules(self):
        """Evaluate all enabled alert rules."""
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Check if rule is in cooldown
                if await self._is_in_cooldown(rule_name):
                    continue
                
                # Evaluate condition
                result = await rule.condition()
                
                if result.get("should_alert", False):
                    await self._fire_alert(rule, result)
                else:
                    await self._resolve_alert(rule_name)
                    
            except Exception as e:
                print(f"Error evaluating rule {rule_name}: {e}")
    
    async def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if a rule is in cooldown period."""
        last_fired = await redis_client.get(f"alert:cooldown:{rule_name}")
        if last_fired:
            return True
        return False
    
    async def _fire_alert(self, rule: AlertRule, result: Dict[str, Any]):
        """Fire an alert for a rule."""
        alert_id = f"{rule.name}:{datetime.utcnow().timestamp()}"
        
        # Format message
        message = rule.message_template.format(**result.get("data", {}))
        
        alert = Alert(
            id=alert_id,
            name=rule.name,
            severity=rule.severity,
            status=AlertStatus.FIRING,
            message=message,
            details=result.get("data", {}),
            fired_at=datetime.utcnow(),
            tags=rule.tags,
            runbook_url=rule.runbook_url
        )
        
        self.active_alerts[rule.name] = alert
        
        # Set cooldown
        await redis_client.setex(
            f"alert:cooldown:{rule.name}",
            rule.cooldown_minutes * 60,
            "1"
        )
        
        # Send notifications
        await self._send_notifications(alert)
        
        # Store alert in database
        await self._store_alert(alert)
    
    async def _resolve_alert(self, rule_name: str):
        """Resolve an active alert."""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            
            # Send resolution notification
            await self._send_resolution_notification(alert)
            
            # Update alert in database
            await self._update_alert(alert)
            
            # Remove from active alerts
            del self.active_alerts[rule_name]
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications."""
        # Send based on severity
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            await asyncio.gather(
                self._send_pagerduty(alert),
                self._send_slack(alert),
                self._send_email(alert)
            )
        else:
            await self._send_slack(alert)
    
    async def _send_pagerduty(self, alert: Alert):
        """Send alert to PagerDuty."""
        if not settings.PAGERDUTY_INTEGRATION_KEY:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "routing_key": settings.PAGERDUTY_INTEGRATION_KEY,
                    "event_action": "trigger",
                    "dedup_key": alert.name,
                    "payload": {
                        "summary": alert.message,
                        "severity": alert.severity,
                        "source": "tradesense",
                        "custom_details": alert.details
                    },
                    "links": [{"href": alert.runbook_url, "text": "Runbook"}] if alert.runbook_url else []
                }
                
                async with session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload
                ) as response:
                    if response.status != 202:
                        print(f"Failed to send PagerDuty alert: {await response.text()}")
                        
        except Exception as e:
            print(f"Error sending PagerDuty alert: {e}")
    
    async def _send_slack(self, alert: Alert):
        """Send alert to Slack."""
        if not settings.SLACK_WEBHOOK_URL:
            return
        
        try:
            color = {
                AlertSeverity.CRITICAL: "#FF0000",
                AlertSeverity.HIGH: "#FF8C00",
                AlertSeverity.MEDIUM: "#FFD700",
                AlertSeverity.LOW: "#00CED1",
                AlertSeverity.INFO: "#808080"
            }.get(alert.severity, "#808080")
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "attachments": [{
                        "color": color,
                        "title": f"[{alert.severity.upper()}] {alert.name}",
                        "text": alert.message,
                        "fields": [
                            {"title": k, "value": str(v), "short": True}
                            for k, v in alert.details.items()
                        ][:4],  # Limit to 4 fields
                        "footer": "TradeSense Alerting",
                        "ts": int(alert.fired_at.timestamp())
                    }]
                }
                
                if alert.runbook_url:
                    payload["attachments"][0]["actions"] = [{
                        "type": "button",
                        "text": "View Runbook",
                        "url": alert.runbook_url
                    }]
                
                async with session.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=payload
                ) as response:
                    if response.status != 200:
                        print(f"Failed to send Slack alert: {await response.text()}")
                        
        except Exception as e:
            print(f"Error sending Slack alert: {e}")
    
    async def _send_email(self, alert: Alert):
        """Send alert via email."""
        try:
            recipients = settings.ALERT_EMAIL_RECIPIENTS
            if not recipients:
                return
            
            subject = f"[{alert.severity.upper()}] TradeSense Alert: {alert.name}"
            
            html_content = f"""
            <html>
                <body>
                    <h2>TradeSense Alert</h2>
                    <p><strong>Alert:</strong> {alert.name}</p>
                    <p><strong>Severity:</strong> {alert.severity.upper()}</p>
                    <p><strong>Message:</strong> {alert.message}</p>
                    <p><strong>Time:</strong> {alert.fired_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    
                    <h3>Details:</h3>
                    <ul>
                        {''.join(f'<li><strong>{k}:</strong> {v}</li>' for k, v in alert.details.items())}
                    </ul>
                    
                    {f'<p><a href="{alert.runbook_url}">View Runbook</a></p>' if alert.runbook_url else ''}
                </body>
            </html>
            """
            
            await email_service.send_email(
                to=recipients,
                subject=subject,
                html_content=html_content
            )
            
        except Exception as e:
            print(f"Error sending email alert: {e}")
    
    async def _send_resolution_notification(self, alert: Alert):
        """Send notification when alert is resolved."""
        if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            # Send PagerDuty resolution
            if settings.PAGERDUTY_INTEGRATION_KEY:
                await self._send_pagerduty_resolution(alert)
            
            # Send Slack resolution
            await self._send_slack_resolution(alert)
    
    async def _send_pagerduty_resolution(self, alert: Alert):
        """Send resolution to PagerDuty."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "routing_key": settings.PAGERDUTY_INTEGRATION_KEY,
                    "event_action": "resolve",
                    "dedup_key": alert.name
                }
                
                await session.post(
                    "https://events.pagerduty.com/v2/enqueue",
                    json=payload
                )
                
        except Exception as e:
            print(f"Error sending PagerDuty resolution: {e}")
    
    async def _send_slack_resolution(self, alert: Alert):
        """Send resolution notification to Slack."""
        if not settings.SLACK_WEBHOOK_URL:
            return
        
        try:
            duration = alert.resolved_at - alert.fired_at
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "attachments": [{
                        "color": "#00FF00",
                        "title": f"[RESOLVED] {alert.name}",
                        "text": f"Alert resolved after {duration.total_seconds() / 60:.1f} minutes",
                        "footer": "TradeSense Alerting",
                        "ts": int(alert.resolved_at.timestamp())
                    }]
                }
                
                await session.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=payload
                )
                
        except Exception as e:
            print(f"Error sending Slack resolution: {e}")
    
    async def _store_alert(self, alert: Alert):
        """Store alert in database."""
        try:
            async with get_db() as db:
                await db.execute(
                    text("""
                        INSERT INTO alerts (
                            id, name, severity, status, message,
                            details, fired_at, tags, runbook_url
                        ) VALUES (
                            :id, :name, :severity, :status, :message,
                            :details, :fired_at, :tags, :runbook_url
                        )
                    """),
                    {
                        "id": alert.id,
                        "name": alert.name,
                        "severity": alert.severity,
                        "status": alert.status,
                        "message": alert.message,
                        "details": json.dumps(alert.details),
                        "fired_at": alert.fired_at,
                        "tags": alert.tags,
                        "runbook_url": alert.runbook_url
                    }
                )
                await db.commit()
                
        except Exception as e:
            print(f"Error storing alert: {e}")
    
    async def _update_alert(self, alert: Alert):
        """Update alert in database."""
        try:
            async with get_db() as db:
                await db.execute(
                    text("""
                        UPDATE alerts
                        SET status = :status,
                            resolved_at = :resolved_at,
                            acknowledged_at = :acknowledged_at,
                            acknowledged_by = :acknowledged_by
                        WHERE id = :id
                    """),
                    {
                        "id": alert.id,
                        "status": alert.status,
                        "resolved_at": alert.resolved_at,
                        "acknowledged_at": alert.acknowledged_at,
                        "acknowledged_by": alert.acknowledged_by
                    }
                )
                await db.commit()
                
        except Exception as e:
            print(f"Error updating alert: {e}")
    
    # Alert condition methods
    async def _check_error_rate(self) -> Dict[str, Any]:
        """Check API error rate."""
        # This would typically query Prometheus or internal metrics
        # For now, returning mock data
        error_rate = 0.02  # 2% error rate
        threshold = 0.05   # 5% threshold
        
        return {
            "should_alert": error_rate > threshold,
            "data": {
                "error_rate": error_rate,
                "threshold": threshold
            }
        }
    
    async def _check_db_connections(self) -> Dict[str, Any]:
        """Check database connection pool usage."""
        try:
            async with get_db() as db:
                result = await db.execute(
                    text("SELECT count(*) FROM pg_stat_activity")
                )
                active_connections = result.scalar()
                
                max_connections = 100  # This should come from config
                usage_percent = (active_connections / max_connections) * 100
                
                return {
                    "should_alert": usage_percent > 90,
                    "data": {
                        "used": active_connections,
                        "total": max_connections,
                        "usage_percent": usage_percent
                    }
                }
        except Exception:
            return {"should_alert": False, "data": {}}
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check application memory usage."""
        import psutil
        
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        threshold = 85
        
        return {
            "should_alert": memory_percent > threshold,
            "data": {
                "memory_percent": memory_percent,
                "threshold": threshold,
                "used_gb": memory.used / (1024 ** 3),
                "total_gb": memory.total / (1024 ** 3)
            }
        }
    
    async def _check_payment_failures(self) -> Dict[str, Any]:
        """Check payment failure rate."""
        try:
            window_minutes = 15
            
            async with get_db() as db:
                result = await db.execute(
                    text("""
                        SELECT 
                            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                            COUNT(*) as total
                        FROM payments
                        WHERE created_at > NOW() - INTERVAL :window
                    """),
                    {"window": f"{window_minutes} minutes"}
                )
                
                row = result.first()
                if row and row.total > 0:
                    failure_rate = row.failed / row.total
                    
                    return {
                        "should_alert": failure_rate > 0.1,  # 10% threshold
                        "data": {
                            "failure_rate": failure_rate,
                            "failed_count": row.failed,
                            "total_count": row.total,
                            "window": window_minutes
                        }
                    }
                    
        except Exception:
            pass
        
        return {"should_alert": False, "data": {}}
    
    async def _check_cache_hit_rate(self) -> Dict[str, Any]:
        """Check Redis cache hit rate."""
        try:
            info = await redis_client.info("stats")
            
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            
            if total > 0:
                hit_rate = hits / total
                threshold = 0.8  # 80% threshold
                
                return {
                    "should_alert": hit_rate < threshold,
                    "data": {
                        "hit_rate": hit_rate,
                        "threshold": threshold,
                        "hits": hits,
                        "misses": misses
                    }
                }
                
        except Exception:
            pass
        
        return {"should_alert": False, "data": {}}
    
    async def _check_user_activity(self) -> Dict[str, Any]:
        """Check for drops in user activity."""
        try:
            async with get_db() as db:
                # Compare last hour vs same hour yesterday
                result = await db.execute(
                    text("""
                        WITH current_activity AS (
                            SELECT COUNT(DISTINCT user_id) as count
                            FROM user_sessions
                            WHERE last_activity > NOW() - INTERVAL '1 hour'
                        ),
                        yesterday_activity AS (
                            SELECT COUNT(DISTINCT user_id) as count
                            FROM user_sessions
                            WHERE last_activity BETWEEN 
                                NOW() - INTERVAL '25 hours' 
                                AND NOW() - INTERVAL '24 hours'
                        )
                        SELECT c.count as current, y.count as yesterday
                        FROM current_activity c, yesterday_activity y
                    """)
                )
                
                row = result.first()
                if row and row.yesterday > 0:
                    drop_percent = ((row.yesterday - row.current) / row.yesterday) * 100
                    
                    return {
                        "should_alert": drop_percent > 30,  # 30% drop threshold
                        "data": {
                            "drop_percent": drop_percent,
                            "current_users": row.current,
                            "yesterday_users": row.yesterday,
                            "comparison_period": "same hour yesterday"
                        }
                    }
                    
        except Exception:
            pass
        
        return {"should_alert": False, "data": {}}
    
    async def _check_ssl_expiry(self) -> Dict[str, Any]:
        """Check SSL certificate expiry."""
        # This would typically check the actual certificate
        # For now, returning mock data
        days_remaining = 25
        
        return {
            "should_alert": days_remaining < 30,
            "data": {
                "days_remaining": days_remaining,
                "expiry_date": (datetime.utcnow() + timedelta(days=days_remaining)).isoformat()
            }
        }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        import psutil
        
        # Check root partition
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        return {
            "should_alert": disk_percent > 85,
            "data": {
                "disk_percent": disk_percent,
                "mount_point": "/",
                "free_gb": disk.free / (1024 ** 3),
                "total_gb": disk.total / (1024 ** 3)
            }
        }


# Initialize alerting system
alerting_system = AlertingSystem()