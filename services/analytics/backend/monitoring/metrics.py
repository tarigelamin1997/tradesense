"""
Application metrics collection for TradeSense.
Provides custom metrics beyond basic HTTP metrics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time
import psutil
import asyncio
from sqlalchemy import text

from core.db.session import get_db
from core.cache import redis_client


# Business Metrics
trades_created = Counter(
    'tradesense_trades_created_total',
    'Total number of trades created',
    ['user_tier', 'trade_type']
)

trades_value = Histogram(
    'tradesense_trades_value_dollars',
    'Trade value in dollars',
    ['symbol', 'trade_type'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]
)

active_users = Gauge(
    'tradesense_active_users',
    'Number of active users in the last period',
    ['period', 'tier']
)

subscription_revenue = Counter(
    'tradesense_subscription_revenue_total',
    'Total subscription revenue',
    ['plan', 'currency']
)

api_usage = Counter(
    'tradesense_api_usage_total',
    'API usage by endpoint and user tier',
    ['endpoint', 'method', 'user_tier']
)

# Performance Metrics
db_query_duration = Histogram(
    'tradesense_db_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5]
)

cache_operations = Counter(
    'tradesense_cache_operations_total',
    'Cache operations',
    ['operation', 'result']
)

background_task_duration = Histogram(
    'tradesense_background_task_duration_seconds',
    'Background task execution time',
    ['task_name', 'status']
)

# System Metrics
system_info = Info(
    'tradesense_system',
    'System information'
)

memory_usage = Gauge(
    'tradesense_memory_usage_bytes',
    'Memory usage in bytes',
    ['type']
)

cpu_usage = Gauge(
    'tradesense_cpu_usage_percent',
    'CPU usage percentage'
)

# User Behavior Metrics
user_sessions = Gauge(
    'tradesense_user_sessions_active',
    'Active user sessions'
)

feature_usage = Counter(
    'tradesense_feature_usage_total',
    'Feature usage tracking',
    ['feature', 'user_tier']
)

user_errors = Counter(
    'tradesense_user_errors_total',
    'User-facing errors',
    ['error_type', 'endpoint']
)


class MetricsCollector:
    """Collects and exposes application metrics."""
    
    def __init__(self):
        self.collection_interval = 60  # seconds
        self._running = False
        
    async def start(self):
        """Start the metrics collection loop."""
        self._running = True
        while self._running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def stop(self):
        """Stop the metrics collection loop."""
        self._running = False
    
    async def collect_metrics(self):
        """Collect all application metrics."""
        await asyncio.gather(
            self.collect_user_metrics(),
            self.collect_system_metrics(),
            self.collect_business_metrics(),
            self.collect_performance_metrics()
        )
    
    async def collect_user_metrics(self):
        """Collect user-related metrics."""
        try:
            # Active users by period
            for period, hours in [("1h", 1), ("24h", 24), ("7d", 168)]:
                async with get_db() as db:
                    since = datetime.utcnow() - timedelta(hours=hours)
                    
                    # By tier
                    result = await db.execute(
                        text("""
                            SELECT u.subscription_tier, COUNT(DISTINCT u.id)
                            FROM users u
                            JOIN user_sessions s ON u.id = s.user_id
                            WHERE s.last_activity > :since
                            GROUP BY u.subscription_tier
                        """),
                        {"since": since}
                    )
                    
                    for tier, count in result:
                        active_users.labels(period=period, tier=tier).set(count)
            
            # Active sessions
            session_count = await redis_client.scard("active_sessions")
            user_sessions.set(session_count or 0)
            
        except Exception as e:
            print(f"Error collecting user metrics: {e}")
    
    async def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage.labels(type="used").set(memory.used)
            memory_usage.labels(type="available").set(memory.available)
            memory_usage.labels(type="cached").set(memory.cached)
            
            # System info
            system_info.info({
                'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown',
                'python_version': '3.11',
                'cpu_count': str(psutil.cpu_count()),
                'total_memory': str(memory.total)
            })
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
    
    async def collect_business_metrics(self):
        """Collect business-related metrics."""
        try:
            async with get_db() as db:
                # Recent subscription revenue
                result = await db.execute(
                    text("""
                        SELECT subscription_tier, SUM(amount), currency
                        FROM payments
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                        AND status = 'completed'
                        GROUP BY subscription_tier, currency
                    """)
                )
                
                for tier, amount, currency in result:
                    subscription_revenue.labels(
                        plan=tier,
                        currency=currency
                    ).inc(float(amount))
                
        except Exception as e:
            print(f"Error collecting business metrics: {e}")
    
    async def collect_performance_metrics(self):
        """Collect performance metrics."""
        try:
            async with get_db() as db:
                # Database performance
                result = await db.execute(
                    text("""
                        SELECT 
                            schemaname,
                            tablename,
                            n_tup_ins + n_tup_upd + n_tup_del as total_ops
                        FROM pg_stat_user_tables
                        WHERE schemaname = 'public'
                        ORDER BY total_ops DESC
                        LIMIT 10
                    """)
                )
                
                # Cache hit rate
                cache_info = await redis_client.info("stats")
                if cache_info:
                    hits = cache_info.get("keyspace_hits", 0)
                    misses = cache_info.get("keyspace_misses", 0)
                    
                    cache_operations.labels(
                        operation="get",
                        result="hit"
                    ).inc(hits)
                    cache_operations.labels(
                        operation="get",
                        result="miss"
                    ).inc(misses)
                    
        except Exception as e:
            print(f"Error collecting performance metrics: {e}")


def track_feature_usage(feature: str):
    """Decorator to track feature usage."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user tier from request context
            user_tier = kwargs.get('current_user', {}).get('subscription_tier', 'free')
            feature_usage.labels(feature=feature, user_tier=user_tier).inc()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def track_db_query(query_type: str, table: str):
    """Decorator to track database query performance."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(
                    query_type=query_type,
                    table=table
                ).observe(duration)
            return result
        return wrapper
    return decorator


def track_background_task(task_name: str):
    """Decorator to track background task execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                background_task_duration.labels(
                    task_name=task_name,
                    status=status
                ).observe(duration)
            return result
        return wrapper
    return decorator


class MetricsMiddleware:
    """Middleware to track API usage metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            method = scope["method"]
            
            # Extract user tier from headers or session
            headers = dict(scope["headers"])
            user_tier = "anonymous"
            
            # Track API usage
            api_usage.labels(
                endpoint=path,
                method=method,
                user_tier=user_tier
            ).inc()
        
        await self.app(scope, receive, send)


# Backup metrics
class BackupMetrics:
    def __init__(self):
        self.backup_completed = Counter(
            'tradesense_backup_completed_total',
            'Total number of completed backups',
            ['backup_type', 'destination']
        )
        
        self.backup_failures = Counter(
            'tradesense_backup_failures_total',
            'Total number of failed backups',
            ['backup_type', 'reason']
        )
        
        self.backup_size_bytes = Histogram(
            'tradesense_backup_size_bytes',
            'Size of backups in bytes',
            ['backup_type'],
            buckets=(
                1024 * 1024,  # 1MB
                10 * 1024 * 1024,  # 10MB
                100 * 1024 * 1024,  # 100MB
                1024 * 1024 * 1024,  # 1GB
                10 * 1024 * 1024 * 1024  # 10GB
            )
        )
        
        self.backup_duration_seconds = Histogram(
            'tradesense_backup_duration_seconds',
            'Duration of backup operations',
            ['backup_type'],
            buckets=(30, 60, 300, 600, 1800, 3600)  # 30s to 1h
        )
        
        self.backups_deleted = Counter(
            'tradesense_backups_deleted_total',
            'Total number of backups deleted',
            ['location']
        )
        
        self.backup_verification_status = Counter(
            'tradesense_backup_verification_status',
            'Backup verification results',
            ['status']
        )
        
        self.active_backup_jobs = Gauge(
            'tradesense_active_backup_jobs',
            'Number of currently running backup jobs',
            ['backup_type']
        )

backup_metrics = BackupMetrics()

# Initialize metrics collector
metrics_collector = MetricsCollector()