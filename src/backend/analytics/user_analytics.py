"""
User analytics and tracking system for TradeSense.
Captures user behavior, feature usage, and engagement metrics.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.cache import redis_client
from app.core.config import settings
from app.models.user import User


class EventType(str, Enum):
    # Page Views
    PAGE_VIEW = "page_view"
    
    # User Actions
    SIGN_UP = "sign_up"
    LOGIN = "login"
    LOGOUT = "logout"
    
    # Trade Events
    TRADE_CREATED = "trade_created"
    TRADE_UPDATED = "trade_updated"
    TRADE_DELETED = "trade_deleted"
    TRADE_IMPORTED = "trade_imported"
    
    # Feature Usage
    ANALYTICS_VIEWED = "analytics_viewed"
    REPORT_GENERATED = "report_generated"
    JOURNAL_ENTRY_CREATED = "journal_entry_created"
    PLAYBOOK_CREATED = "playbook_created"
    
    # Subscription Events
    SUBSCRIPTION_STARTED = "subscription_started"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    # Engagement Events
    FEATURE_DISCOVERED = "feature_discovered"
    TUTORIAL_COMPLETED = "tutorial_completed"
    HELP_ACCESSED = "help_accessed"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    
    # Error Events
    ERROR_OCCURRED = "error_occurred"
    FEATURE_FAILED = "feature_failed"


@dataclass
class UserEvent:
    """Represents a user analytics event."""
    event_id: str
    user_id: str
    session_id: str
    event_type: EventType
    timestamp: datetime
    properties: Dict[str, Any] = field(default_factory=dict)
    page_url: Optional[str] = None
    referrer_url: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "properties": self.properties,
            "page_url": self.page_url,
            "referrer_url": self.referrer_url,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address
        }


class UserAnalytics:
    """Handles user analytics and tracking."""
    
    def __init__(self):
        self.batch_size = 100
        self.flush_interval = 10  # seconds
        self._event_buffer = []
        self._last_flush = datetime.utcnow()
    
    async def track_event(
        self,
        user_id: str,
        event_type: EventType,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        page_url: Optional[str] = None,
        referrer_url: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Track a user event."""
        event = UserEvent(
            event_id=str(uuid4()),
            user_id=user_id,
            session_id=session_id or self._get_session_id(user_id),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            properties=properties or {},
            page_url=page_url,
            referrer_url=referrer_url,
            user_agent=user_agent,
            ip_address=self._hash_ip(ip_address) if ip_address else None
        )
        
        # Add to buffer
        self._event_buffer.append(event)
        
        # Store in Redis for real-time processing
        await self._store_realtime_event(event)
        
        # Flush if needed
        if len(self._event_buffer) >= self.batch_size or \
           (datetime.utcnow() - self._last_flush).seconds > self.flush_interval:
            await self.flush_events()
        
        return event.event_id
    
    async def flush_events(self):
        """Flush buffered events to database."""
        if not self._event_buffer:
            return
        
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()
        self._last_flush = datetime.utcnow()
        
        try:
            async with get_db() as db:
                # Batch insert events
                await db.execute(
                    text("""
                        INSERT INTO user_events (
                            event_id, user_id, session_id, event_type,
                            timestamp, properties, page_url, referrer_url,
                            user_agent, ip_address_hash
                        ) VALUES (
                            :event_id, :user_id, :session_id, :event_type,
                            :timestamp, :properties, :page_url, :referrer_url,
                            :user_agent, :ip_address
                        )
                    """),
                    [
                        {
                            "event_id": event.event_id,
                            "user_id": event.user_id,
                            "session_id": event.session_id,
                            "event_type": event.event_type,
                            "timestamp": event.timestamp,
                            "properties": json.dumps(event.properties),
                            "page_url": event.page_url,
                            "referrer_url": event.referrer_url,
                            "user_agent": event.user_agent,
                            "ip_address": event.ip_address
                        }
                        for event in events_to_flush
                    ]
                )
                await db.commit()
                
                # Update user engagement metrics
                for event in events_to_flush:
                    await self._update_user_engagement(event)
                    
        except Exception as e:
            print(f"Error flushing analytics events: {e}")
            # Re-add events to buffer for retry
            self._event_buffer.extend(events_to_flush)
    
    async def _store_realtime_event(self, event: UserEvent):
        """Store event in Redis for real-time processing."""
        try:
            # Add to recent events list
            await redis_client.lpush(
                f"analytics:events:recent",
                json.dumps(event.to_dict())
            )
            
            # Trim to keep only recent events
            await redis_client.ltrim("analytics:events:recent", 0, 999)
            
            # Update real-time counters
            await redis_client.hincrby(
                f"analytics:counters:{datetime.utcnow().strftime('%Y%m%d')}",
                event.event_type,
                1
            )
            
            # Update user activity
            await redis_client.zadd(
                "analytics:active_users",
                {event.user_id: datetime.utcnow().timestamp()}
            )
            
        except Exception as e:
            print(f"Error storing real-time event: {e}")
    
    async def _update_user_engagement(self, event: UserEvent):
        """Update user engagement metrics."""
        try:
            # Update last activity
            await redis_client.hset(
                f"user:engagement:{event.user_id}",
                mapping={
                    "last_activity": event.timestamp.isoformat(),
                    "last_event_type": event.event_type
                }
            )
            
            # Increment event count
            await redis_client.hincrby(
                f"user:engagement:{event.user_id}",
                f"event_count:{event.event_type}",
                1
            )
            
            # Update session activity
            await redis_client.zadd(
                f"session:activity:{event.session_id}",
                {event.event_type: event.timestamp.timestamp()}
            )
            
        except Exception as e:
            print(f"Error updating user engagement: {e}")
    
    def _get_session_id(self, user_id: str) -> str:
        """Generate or retrieve session ID."""
        # In a real implementation, this would use session management
        return f"session_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"
    
    def _hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy."""
        return hashlib.sha256(
            f"{ip_address}{settings.SECRET_KEY}".encode()
        ).hexdigest()[:16]
    
    async def get_user_journey(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get user's journey/event timeline."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with get_db() as db:
            result = await db.execute(
                text("""
                    SELECT 
                        event_id, event_type, timestamp,
                        properties, page_url, referrer_url
                    FROM user_events
                    WHERE user_id = :user_id
                    AND timestamp BETWEEN :start_date AND :end_date
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """),
                {
                    "user_id": user_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            events = []
            for row in result:
                events.append({
                    "event_id": row.event_id,
                    "event_type": row.event_type,
                    "timestamp": row.timestamp.isoformat(),
                    "properties": json.loads(row.properties) if row.properties else {},
                    "page_url": row.page_url,
                    "referrer_url": row.referrer_url
                })
            
            return events
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        async with get_db() as db:
            # Basic stats
            stats_result = await db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(DISTINCT DATE(timestamp)) as active_days,
                        MIN(timestamp) as first_activity,
                        MAX(timestamp) as last_activity,
                        COUNT(DISTINCT session_id) as total_sessions
                    FROM user_events
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            
            stats = stats_result.first()
            
            # Event breakdown
            event_breakdown = await db.execute(
                text("""
                    SELECT 
                        event_type,
                        COUNT(*) as count
                    FROM user_events
                    WHERE user_id = :user_id
                    GROUP BY event_type
                """),
                {"user_id": user_id}
            )
            
            event_counts = {
                row.event_type: row.count
                for row in event_breakdown
            }
            
            # Feature usage
            feature_usage = await db.execute(
                text("""
                    SELECT 
                        properties->>'feature_name' as feature,
                        COUNT(*) as usage_count,
                        MAX(timestamp) as last_used
                    FROM user_events
                    WHERE user_id = :user_id
                    AND event_type = 'feature_used'
                    AND properties->>'feature_name' IS NOT NULL
                    GROUP BY properties->>'feature_name'
                """),
                {"user_id": user_id}
            )
            
            return {
                "total_events": stats.total_events,
                "active_days": stats.active_days,
                "first_activity": stats.first_activity.isoformat() if stats.first_activity else None,
                "last_activity": stats.last_activity.isoformat() if stats.last_activity else None,
                "total_sessions": stats.total_sessions,
                "event_breakdown": event_counts,
                "feature_usage": [
                    {
                        "feature": row.feature,
                        "usage_count": row.usage_count,
                        "last_used": row.last_used.isoformat()
                    }
                    for row in feature_usage
                ]
            }
    
    async def get_cohort_analysis(
        self,
        cohort_type: str = "signup_month",
        metric: str = "retention"
    ) -> Dict[str, Any]:
        """Perform cohort analysis."""
        async with get_db() as db:
            if cohort_type == "signup_month" and metric == "retention":
                result = await db.execute(
                    text("""
                        WITH cohorts AS (
                            SELECT 
                                user_id,
                                DATE_TRUNC('month', created_at) as cohort_month
                            FROM users
                        ),
                        activities AS (
                            SELECT 
                                e.user_id,
                                c.cohort_month,
                                DATE_TRUNC('month', e.timestamp) as activity_month
                            FROM user_events e
                            JOIN cohorts c ON e.user_id = c.user_id
                            GROUP BY e.user_id, c.cohort_month, DATE_TRUNC('month', e.timestamp)
                        )
                        SELECT 
                            cohort_month,
                            activity_month,
                            COUNT(DISTINCT user_id) as active_users
                        FROM activities
                        GROUP BY cohort_month, activity_month
                        ORDER BY cohort_month, activity_month
                    """)
                )
                
                cohort_data = {}
                for row in result:
                    cohort = row.cohort_month.strftime('%Y-%m')
                    month = row.activity_month.strftime('%Y-%m')
                    
                    if cohort not in cohort_data:
                        cohort_data[cohort] = {}
                    
                    cohort_data[cohort][month] = row.active_users
                
                return {
                    "cohort_type": cohort_type,
                    "metric": metric,
                    "data": cohort_data
                }
    
    async def get_funnel_analysis(
        self,
        funnel_steps: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Analyze conversion funnel."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        async with get_db() as db:
            funnel_data = []
            
            for i, step in enumerate(funnel_steps):
                if i == 0:
                    # First step - all users who performed this event
                    result = await db.execute(
                        text("""
                            SELECT COUNT(DISTINCT user_id) as users
                            FROM user_events
                            WHERE event_type = :event_type
                            AND timestamp BETWEEN :start_date AND :end_date
                        """),
                        {
                            "event_type": step,
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    )
                else:
                    # Subsequent steps - users who performed all previous steps
                    prev_steps = funnel_steps[:i+1]
                    result = await db.execute(
                        text(f"""
                            WITH step_users AS (
                                SELECT user_id, event_type
                                FROM user_events
                                WHERE event_type IN :event_types
                                AND timestamp BETWEEN :start_date AND :end_date
                                GROUP BY user_id, event_type
                            )
                            SELECT COUNT(DISTINCT user_id) as users
                            FROM step_users
                            WHERE user_id IN (
                                SELECT user_id
                                FROM step_users
                                GROUP BY user_id
                                HAVING COUNT(DISTINCT event_type) = :step_count
                            )
                        """),
                        {
                            "event_types": tuple(prev_steps),
                            "start_date": start_date,
                            "end_date": end_date,
                            "step_count": len(prev_steps)
                        }
                    )
                
                users = result.scalar() or 0
                funnel_data.append({
                    "step": step,
                    "users": users,
                    "conversion_rate": users / funnel_data[0]["users"] if funnel_data else 1.0
                })
            
            return {
                "funnel_steps": funnel_steps,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "data": funnel_data
            }
    
    async def get_user_segments(self) -> Dict[str, List[str]]:
        """Get user segments based on behavior."""
        async with get_db() as db:
            segments = {}
            
            # Power users (high activity)
            power_users = await db.execute(
                text("""
                    SELECT DISTINCT user_id
                    FROM user_events
                    WHERE timestamp > NOW() - INTERVAL '30 days'
                    GROUP BY user_id
                    HAVING COUNT(*) > 100
                """)
            )
            segments["power_users"] = [row.user_id for row in power_users]
            
            # At risk users (declining activity)
            at_risk = await db.execute(
                text("""
                    WITH user_activity AS (
                        SELECT 
                            user_id,
                            COUNT(CASE WHEN timestamp > NOW() - INTERVAL '7 days' THEN 1 END) as recent,
                            COUNT(CASE WHEN timestamp BETWEEN NOW() - INTERVAL '30 days' AND NOW() - INTERVAL '7 days' THEN 1 END) as previous
                        FROM user_events
                        GROUP BY user_id
                    )
                    SELECT user_id
                    FROM user_activity
                    WHERE previous > 10 AND recent < previous * 0.3
                """)
            )
            segments["at_risk"] = [row.user_id for row in at_risk]
            
            # New users
            new_users = await db.execute(
                text("""
                    SELECT id as user_id
                    FROM users
                    WHERE created_at > NOW() - INTERVAL '7 days'
                """)
            )
            segments["new_users"] = [row.user_id for row in new_users]
            
            return segments
    
    async def track_feature_adoption(
        self,
        feature_name: str,
        user_id: str,
        adopted: bool = True
    ):
        """Track feature adoption."""
        await self.track_event(
            user_id=user_id,
            event_type=EventType.FEATURE_DISCOVERED,
            properties={
                "feature_name": feature_name,
                "adopted": adopted,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Analytics middleware for automatic page view tracking
class AnalyticsMiddleware:
    """Middleware to automatically track page views and API calls."""
    
    def __init__(self, app, analytics: UserAnalytics):
        self.app = app
        self.analytics = analytics
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            method = scope["method"]
            headers = dict(scope["headers"])
            
            # Extract user info from request
            # This would typically come from JWT or session
            user_id = None  # Extract from auth
            
            if user_id and method == "GET":
                # Track page view
                await self.analytics.track_event(
                    user_id=user_id,
                    event_type=EventType.PAGE_VIEW,
                    page_url=path,
                    referrer_url=headers.get(b"referer", b"").decode(),
                    user_agent=headers.get(b"user-agent", b"").decode()
                )
        
        await self.app(scope, receive, send)


# Initialize analytics
user_analytics = UserAnalytics()