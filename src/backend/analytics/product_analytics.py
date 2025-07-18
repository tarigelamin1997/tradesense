"""
Product analytics for TradeSense.
Provides insights into product usage, feature adoption, and user behavior.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import asyncio

from sqlalchemy import text
from core.db.session import get_db
from core.cache import redis_client
from analytics.user_analytics import user_analytics, EventType


class ProductAnalytics:
    """Handles product-level analytics and insights."""
    
    async def get_product_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive product metrics."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        metrics = await asyncio.gather(
            self._get_user_metrics(start_date, end_date),
            self._get_engagement_metrics(start_date, end_date),
            self._get_feature_metrics(start_date, end_date),
            self._get_revenue_metrics(start_date, end_date),
            self._get_performance_metrics(start_date, end_date)
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "user_metrics": metrics[0],
            "engagement_metrics": metrics[1],
            "feature_metrics": metrics[2],
            "revenue_metrics": metrics[3],
            "performance_metrics": metrics[4]
        }
    
    async def _get_user_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get user-related metrics."""
        async with get_db() as db:
            # Total users
            total_users = await db.execute(
                text("SELECT COUNT(*) FROM users")
            )
            
            # New users
            new_users = await db.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE created_at BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            # Active users (DAU, WAU, MAU)
            dau = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT user_id)
                    FROM user_events
                    WHERE timestamp > NOW() - INTERVAL '1 day'
                """)
            )
            
            wau = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT user_id)
                    FROM user_events
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                """)
            )
            
            mau = await db.execute(
                text("""
                    SELECT COUNT(DISTINCT user_id)
                    FROM user_events
                    WHERE timestamp > NOW() - INTERVAL '30 days'
                """)
            )
            
            # User growth rate
            prev_period_users = await db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM users
                    WHERE created_at < :start_date
                """),
                {"start_date": start_date}
            )
            
            prev_count = prev_period_users.scalar() or 1
            growth_rate = ((total_users.scalar() - prev_count) / prev_count) * 100
            
            return {
                "total_users": total_users.scalar(),
                "new_users": new_users.scalar(),
                "daily_active_users": dau.scalar(),
                "weekly_active_users": wau.scalar(),
                "monthly_active_users": mau.scalar(),
                "growth_rate": round(growth_rate, 2),
                "dau_mau_ratio": round(dau.scalar() / max(mau.scalar(), 1), 3)
            }
    
    async def _get_engagement_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get engagement metrics."""
        async with get_db() as db:
            # Average session duration
            session_data = await db.execute(
                text("""
                    WITH session_durations AS (
                        SELECT 
                            session_id,
                            EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp))) as duration
                        FROM user_events
                        WHERE timestamp BETWEEN :start_date AND :end_date
                        GROUP BY session_id
                        HAVING COUNT(*) > 1
                    )
                    SELECT 
                        AVG(duration) as avg_duration,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration) as median_duration
                    FROM session_durations
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            session_stats = session_data.first()
            
            # Events per user
            events_per_user = await db.execute(
                text("""
                    SELECT 
                        AVG(event_count) as avg_events,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY event_count) as median_events
                    FROM (
                        SELECT user_id, COUNT(*) as event_count
                        FROM user_events
                        WHERE timestamp BETWEEN :start_date AND :end_date
                        GROUP BY user_id
                    ) user_events
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            event_stats = events_per_user.first()
            
            # Retention rates
            retention_7d = await db.execute(
                text("""
                    WITH new_users AS (
                        SELECT id as user_id
                        FROM users
                        WHERE created_at BETWEEN :start_date AND :start_date + INTERVAL '1 day'
                    )
                    SELECT 
                        COUNT(DISTINCT nu.user_id) as cohort_size,
                        COUNT(DISTINCT CASE 
                            WHEN e.timestamp > u.created_at + INTERVAL '7 days' 
                            THEN nu.user_id 
                        END) as retained_users
                    FROM new_users nu
                    JOIN users u ON nu.user_id = u.id
                    LEFT JOIN user_events e ON nu.user_id = e.user_id
                    AND e.timestamp BETWEEN u.created_at + INTERVAL '7 days' 
                        AND u.created_at + INTERVAL '8 days'
                """),
                {"start_date": start_date - timedelta(days=7)}
            )
            
            retention = retention_7d.first()
            retention_rate = (retention.retained_users / max(retention.cohort_size, 1)) * 100
            
            return {
                "avg_session_duration": round(session_stats.avg_duration or 0, 2),
                "median_session_duration": round(session_stats.median_duration or 0, 2),
                "avg_events_per_user": round(event_stats.avg_events or 0, 2),
                "median_events_per_user": round(event_stats.median_events or 0, 2),
                "retention_rate_7d": round(retention_rate, 2)
            }
    
    async def _get_feature_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get feature usage metrics."""
        async with get_db() as db:
            # Feature adoption
            feature_usage = await db.execute(
                text("""
                    SELECT 
                        event_type,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(*) as total_uses
                    FROM user_events
                    WHERE timestamp BETWEEN :start_date AND :end_date
                    AND event_type IN :feature_events
                    GROUP BY event_type
                    ORDER BY unique_users DESC
                """),
                {
                    "start_date": start_date,
                    "end_date": end_date,
                    "feature_events": (
                        EventType.ANALYTICS_VIEWED,
                        EventType.REPORT_GENERATED,
                        EventType.JOURNAL_ENTRY_CREATED,
                        EventType.PLAYBOOK_CREATED,
                        EventType.TRADE_IMPORTED
                    )
                }
            )
            
            features = {}
            for row in feature_usage:
                features[row.event_type] = {
                    "unique_users": row.unique_users,
                    "total_uses": row.total_uses,
                    "uses_per_user": round(row.total_uses / max(row.unique_users, 1), 2)
                }
            
            # Most used features
            top_features = await db.execute(
                text("""
                    SELECT 
                        properties->>'feature_name' as feature,
                        COUNT(DISTINCT user_id) as users,
                        COUNT(*) as uses
                    FROM user_events
                    WHERE timestamp BETWEEN :start_date AND :end_date
                    AND event_type = 'feature_discovered'
                    AND properties->>'feature_name' IS NOT NULL
                    GROUP BY properties->>'feature_name'
                    ORDER BY uses DESC
                    LIMIT 10
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            return {
                "feature_adoption": features,
                "top_features": [
                    {
                        "feature": row.feature,
                        "users": row.users,
                        "uses": row.uses
                    }
                    for row in top_features
                ]
            }
    
    async def _get_revenue_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get revenue-related metrics."""
        async with get_db() as db:
            # MRR (Monthly Recurring Revenue)
            mrr = await db.execute(
                text("""
                    SELECT 
                        SUM(CASE 
                            WHEN subscription_tier = 'pro' THEN 49.99
                            WHEN subscription_tier = 'premium' THEN 99.99
                            ELSE 0
                        END) as total_mrr
                    FROM users
                    WHERE subscription_status = 'active'
                """)
            )
            
            # New MRR
            new_mrr = await db.execute(
                text("""
                    SELECT 
                        SUM(CASE 
                            WHEN subscription_tier = 'pro' THEN 49.99
                            WHEN subscription_tier = 'premium' THEN 99.99
                            ELSE 0
                        END) as new_mrr
                    FROM users
                    WHERE subscription_status = 'active'
                    AND subscription_started_at BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            # Churn
            churned = await db.execute(
                text("""
                    SELECT COUNT(*) as churned_users
                    FROM user_events
                    WHERE event_type = 'subscription_cancelled'
                    AND timestamp BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            # ARPU (Average Revenue Per User)
            paying_users = await db.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE subscription_tier IN ('pro', 'premium')
                    AND subscription_status = 'active'
                """)
            )
            
            total_mrr = mrr.scalar() or 0
            paying_count = paying_users.scalar() or 1
            arpu = total_mrr / paying_count
            
            return {
                "monthly_recurring_revenue": round(total_mrr, 2),
                "new_mrr": round(new_mrr.scalar() or 0, 2),
                "churned_users": churned.scalar() or 0,
                "average_revenue_per_user": round(arpu, 2)
            }
    
    async def _get_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get performance metrics."""
        async with get_db() as db:
            # Page load times
            page_loads = await db.execute(
                text("""
                    SELECT 
                        AVG(CAST(properties->>'load_time' AS FLOAT)) as avg_load_time,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (
                            ORDER BY CAST(properties->>'load_time' AS FLOAT)
                        ) as p95_load_time
                    FROM user_events
                    WHERE event_type = 'page_view'
                    AND properties->>'load_time' IS NOT NULL
                    AND timestamp BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            load_stats = page_loads.first()
            
            # Error rate
            errors = await db.execute(
                text("""
                    SELECT 
                        COUNT(CASE WHEN event_type = 'error_occurred' THEN 1 END) as errors,
                        COUNT(*) as total_events
                    FROM user_events
                    WHERE timestamp BETWEEN :start_date AND :end_date
                """),
                {"start_date": start_date, "end_date": end_date}
            )
            
            error_stats = errors.first()
            error_rate = (error_stats.errors / max(error_stats.total_events, 1)) * 100
            
            return {
                "avg_page_load_time": round(load_stats.avg_load_time or 0, 3),
                "p95_page_load_time": round(load_stats.p95_load_time or 0, 3),
                "error_rate": round(error_rate, 4),
                "total_errors": error_stats.errors
            }
    
    async def get_user_flow_analysis(
        self,
        start_page: str,
        end_page: Optional[str] = None,
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """Analyze user flow through the application."""
        async with get_db() as db:
            # Get all paths starting from the start page
            paths = await db.execute(
                text("""
                    WITH user_paths AS (
                        SELECT 
                            user_id,
                            session_id,
                            page_url,
                            LAG(page_url) OVER (
                                PARTITION BY session_id 
                                ORDER BY timestamp
                            ) as prev_page,
                            LEAD(page_url) OVER (
                                PARTITION BY session_id 
                                ORDER BY timestamp
                            ) as next_page
                        FROM user_events
                        WHERE event_type = 'page_view'
                        AND timestamp > NOW() - INTERVAL '30 days'
                    )
                    SELECT 
                        prev_page,
                        page_url,
                        next_page,
                        COUNT(*) as transitions
                    FROM user_paths
                    WHERE prev_page = :start_page
                    OR page_url = :start_page
                    GROUP BY prev_page, page_url, next_page
                    ORDER BY transitions DESC
                    LIMIT 100
                """),
                {"start_page": start_page}
            )
            
            # Build flow graph
            flow_data = defaultdict(lambda: defaultdict(int))
            for row in paths:
                if row.prev_page and row.page_url:
                    flow_data[row.prev_page][row.page_url] += row.transitions
                if row.page_url and row.next_page:
                    flow_data[row.page_url][row.next_page] += row.transitions
            
            return {
                "start_page": start_page,
                "end_page": end_page,
                "flows": dict(flow_data),
                "total_sessions": sum(
                    sum(destinations.values()) 
                    for destinations in flow_data.values()
                )
            }
    
    async def get_conversion_metrics(
        self,
        conversion_events: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """Calculate conversion metrics between events."""
        async with get_db() as db:
            conversions = []
            
            for start_event, end_event in conversion_events:
                result = await db.execute(
                    text("""
                        WITH start_users AS (
                            SELECT DISTINCT user_id
                            FROM user_events
                            WHERE event_type = :start_event
                            AND timestamp > NOW() - INTERVAL '30 days'
                        ),
                        converted_users AS (
                            SELECT DISTINCT e.user_id
                            FROM user_events e
                            JOIN start_users s ON e.user_id = s.user_id
                            WHERE e.event_type = :end_event
                            AND e.timestamp > (
                                SELECT MIN(timestamp)
                                FROM user_events
                                WHERE user_id = e.user_id
                                AND event_type = :start_event
                            )
                        )
                        SELECT 
                            (SELECT COUNT(*) FROM start_users) as started,
                            (SELECT COUNT(*) FROM converted_users) as converted
                    """),
                    {
                        "start_event": start_event,
                        "end_event": end_event
                    }
                )
                
                stats = result.first()
                conversion_rate = (stats.converted / max(stats.started, 1)) * 100
                
                conversions.append({
                    "from": start_event,
                    "to": end_event,
                    "started": stats.started,
                    "converted": stats.converted,
                    "conversion_rate": round(conversion_rate, 2)
                })
            
            return {
                "conversions": conversions,
                "overall_conversion_rate": round(
                    sum(c["conversion_rate"] for c in conversions) / len(conversions),
                    2
                ) if conversions else 0
            }
    
    async def get_user_behavior_insights(self) -> Dict[str, Any]:
        """Get insights about user behavior patterns."""
        async with get_db() as db:
            # Peak usage times
            usage_by_hour = await db.execute(
                text("""
                    SELECT 
                        EXTRACT(HOUR FROM timestamp) as hour,
                        COUNT(*) as events,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM user_events
                    WHERE timestamp > NOW() - INTERVAL '7 days'
                    GROUP BY EXTRACT(HOUR FROM timestamp)
                    ORDER BY hour
                """)
            )
            
            peak_hours = [
                {
                    "hour": int(row.hour),
                    "events": row.events,
                    "users": row.unique_users
                }
                for row in usage_by_hour
            ]
            
            # Most common user paths
            common_paths = await db.execute(
                text("""
                    WITH event_sequences AS (
                        SELECT 
                            user_id,
                            session_id,
                            STRING_AGG(event_type, ' -> ' ORDER BY timestamp) as path
                        FROM (
                            SELECT *
                            FROM user_events
                            WHERE timestamp > NOW() - INTERVAL '7 days'
                            ORDER BY user_id, session_id, timestamp
                            LIMIT 10000
                        ) recent_events
                        GROUP BY user_id, session_id
                    )
                    SELECT 
                        path,
                        COUNT(*) as occurrences
                    FROM event_sequences
                    WHERE path LIKE '%->%->%'
                    GROUP BY path
                    ORDER BY occurrences DESC
                    LIMIT 20
                """)
            )
            
            # Feature discovery patterns
            discovery_patterns = await db.execute(
                text("""
                    SELECT 
                        properties->>'feature_name' as feature,
                        AVG(EXTRACT(EPOCH FROM (
                            timestamp - u.created_at
                        )) / 86400) as avg_days_to_discover
                    FROM user_events e
                    JOIN users u ON e.user_id = u.id
                    WHERE e.event_type = 'feature_discovered'
                    AND e.properties->>'feature_name' IS NOT NULL
                    GROUP BY properties->>'feature_name'
                    ORDER BY avg_days_to_discover
                """)
            )
            
            return {
                "peak_usage_hours": peak_hours,
                "common_user_paths": [
                    {
                        "path": row.path,
                        "occurrences": row.occurrences
                    }
                    for row in common_paths
                ],
                "feature_discovery": [
                    {
                        "feature": row.feature,
                        "avg_days_to_discover": round(row.avg_days_to_discover, 1)
                    }
                    for row in discovery_patterns
                ]
            }


# Helper functions for tracking specific events
async def track_trade_analytics(
    user_id: str,
    trade_id: str,
    action: str,
    trade_details: Dict[str, Any]
):
    """Track trade-related analytics."""
    event_type_map = {
        "create": EventType.TRADE_CREATED,
        "update": EventType.TRADE_UPDATED,
        "delete": EventType.TRADE_DELETED,
        "import": EventType.TRADE_IMPORTED
    }
    
    await user_analytics.track_event(
        user_id=user_id,
        event_type=event_type_map.get(action, EventType.TRADE_CREATED),
        properties={
            "trade_id": trade_id,
            "symbol": trade_details.get("symbol"),
            "trade_type": trade_details.get("trade_type"),
            "quantity": trade_details.get("quantity"),
            "value": trade_details.get("value"),
            "profit_loss": trade_details.get("profit_loss")
        }
    )


async def track_feature_usage(
    user_id: str,
    feature_name: str,
    properties: Optional[Dict[str, Any]] = None
):
    """Track feature usage."""
    await user_analytics.track_event(
        user_id=user_id,
        event_type=EventType.FEATURE_DISCOVERED,
        properties={
            "feature_name": feature_name,
            **(properties or {})
        }
    )


async def track_subscription_event(
    user_id: str,
    event: str,
    plan: str,
    price: float
):
    """Track subscription-related events."""
    event_type_map = {
        "started": EventType.SUBSCRIPTION_STARTED,
        "upgraded": EventType.SUBSCRIPTION_UPGRADED,
        "downgraded": EventType.SUBSCRIPTION_DOWNGRADED,
        "cancelled": EventType.SUBSCRIPTION_CANCELLED
    }
    
    await user_analytics.track_event(
        user_id=user_id,
        event_type=event_type_map.get(event, EventType.SUBSCRIPTION_STARTED),
        properties={
            "plan": plan,
            "price": price,
            "currency": "USD"
        }
    )


async def track_support_event(
    user_id: str,
    event: str,
    ticket_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None
):
    """Track support-related events."""
    await user_analytics.track_event(
        user_id=user_id,
        event_type=EventType.CUSTOM,
        properties={
            "event": f"support_{event}",
            "ticket_id": ticket_id,
            **(properties or {})
        }
    )


async def track_kb_event(
    user_id: str,
    event: str,
    article_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None
):
    """Track knowledge base related events."""
    await user_analytics.track_event(
        user_id=user_id,
        event_type=EventType.CUSTOM,
        properties={
            "event": f"kb_{event}",
            "article_id": article_id,
            **(properties or {})
        }
    )


# Initialize product analytics
product_analytics = ProductAnalytics()