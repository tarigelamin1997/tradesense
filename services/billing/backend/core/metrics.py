"""
Metrics collection and monitoring for TradeSense

Provides Prometheus-compatible metrics for monitoring application health,
performance, and business metrics.
"""

import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from datetime import datetime
import psutil
import os

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary, Info,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback implementations
    class Counter:
        def __init__(self, *args, **kwargs):
            self.value = 0
        def inc(self, amount=1):
            self.value += amount
        def labels(self, **kwargs):
            return self
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            self.values = []
        def observe(self, value):
            self.values.append(value)
        def labels(self, **kwargs):
            return self
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            self.value = 0
        def set(self, value):
            self.value = value
        def inc(self, amount=1):
            self.value += amount
        def dec(self, amount=1):
            self.value -= amount
        def labels(self, **kwargs):
            return self

# Create registry
registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None

# HTTP Metrics
http_requests_total = Counter(
    'tradesense_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'tradesense_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

http_requests_in_progress = Gauge(
    'tradesense_http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'tradesense_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry
)

db_connections_active = Gauge(
    'tradesense_db_connections_active',
    'Number of active database connections',
    registry=registry
)

db_connections_idle = Gauge(
    'tradesense_db_connections_idle',
    'Number of idle database connections',
    registry=registry
)

# Cache Metrics
cache_hits_total = Counter(
    'tradesense_cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'tradesense_cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

cache_evictions_total = Counter(
    'tradesense_cache_evictions_total',
    'Total cache evictions',
    ['cache_type', 'reason'],
    registry=registry
)

# Business Metrics
trades_created_total = Counter(
    'tradesense_trades_created_total',
    'Total trades created',
    ['user_id', 'trade_type'],
    registry=registry
)

user_registrations_total = Counter(
    'tradesense_user_registrations_total',
    'Total user registrations',
    ['source'],
    registry=registry
)

analytics_queries_total = Counter(
    'tradesense_analytics_queries_total',
    'Total analytics queries',
    ['query_type', 'user_id'],
    registry=registry
)

# Authentication Metrics
auth_attempts_total = Counter(
    'tradesense_auth_attempts_total',
    'Total authentication attempts',
    ['method', 'success'],
    registry=registry
)

auth_tokens_issued_total = Counter(
    'tradesense_auth_tokens_issued_total',
    'Total authentication tokens issued',
    ['token_type'],
    registry=registry
)

# Rate Limiting Metrics
rate_limit_hits = Counter(
    'tradesense_rate_limit_hits_total',
    'Total rate limit checks',
    ['endpoint', 'method'],
    registry=registry
)

rate_limit_violations = Counter(
    'tradesense_rate_limit_violations_total',
    'Total rate limit violations',
    ['endpoint', 'method'],
    registry=registry
)

rate_limit_usage = Gauge(
    'tradesense_rate_limit_usage_percent',
    'Current rate limit usage percentage',
    ['user_id', 'tier', 'limit_type'],
    registry=registry
)

rate_limit_check_duration = Histogram(
    'tradesense_rate_limit_check_duration_seconds',
    'Time spent checking rate limits',
    ['strategy'],
    registry=registry
)

# System Metrics
system_cpu_usage_percent = Gauge(
    'tradesense_system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=registry
)

system_memory_usage_bytes = Gauge(
    'tradesense_system_memory_usage_bytes',
    'System memory usage in bytes',
    registry=registry
)

system_disk_usage_bytes = Gauge(
    'tradesense_system_disk_usage_bytes',
    'System disk usage in bytes',
    ['path'],
    registry=registry
)

# Application Info
app_info = Info(
    'tradesense_app',
    'Application information',
    registry=registry
) if PROMETHEUS_AVAILABLE else None

if app_info:
    app_info.info({
        'version': '2.0.0',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'service': 'tradesense-backend'
    })

class MetricsCollector:
    """Collect and expose metrics"""
    
    def __init__(self):
        self.custom_metrics: Dict[str, Any] = {}
    
    def collect_system_metrics(self) -> None:
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage_percent.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage_bytes.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            system_disk_usage_bytes.labels(path='/').set(disk.used)
            
        except Exception as e:
            # Log error but don't crash
            pass
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float) -> None:
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, table: str, duration: float) -> None:
        """Record database query metrics"""
        db_query_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_cache_hit(self, cache_type: str) -> None:
        """Record cache hit"""
        cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str) -> None:
        """Record cache miss"""
        cache_misses_total.labels(cache_type=cache_type).inc()
    
    def record_trade_created(self, user_id: str, trade_type: str) -> None:
        """Record trade creation"""
        trades_created_total.labels(
            user_id=user_id,
            trade_type=trade_type
        ).inc()
    
    def record_user_registration(self, source: str = 'web') -> None:
        """Record user registration"""
        user_registrations_total.labels(source=source).inc()
    
    def record_auth_attempt(self, method: str, success: bool) -> None:
        """Record authentication attempt"""
        auth_attempts_total.labels(
            method=method,
            success=str(success)
        ).inc()
    
    def set_db_pool_metrics(self, active: int, idle: int) -> None:
        """Set database connection pool metrics"""
        db_connections_active.set(active)
        db_connections_idle.set(idle)
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        if PROMETHEUS_AVAILABLE:
            # Collect system metrics before generating
            self.collect_system_metrics()
            return generate_latest(registry)
        else:
            # Return simple text format
            return b"# Metrics collection not available\n"

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Decorators for metric collection
def track_request_metrics(endpoint: str = None):
    """Decorator to track HTTP request metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            method = kwargs.get('request', args[0] if args else None)
            method_name = method.method if hasattr(method, 'method') else 'GET'
            endpoint_name = endpoint or func.__name__
            
            # Track in-progress requests
            http_requests_in_progress.labels(
                method=method_name,
                endpoint=endpoint_name
            ).inc()
            
            try:
                result = await func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_http_request(
                    method_name,
                    endpoint_name,
                    status,
                    duration
                )
                http_requests_in_progress.labels(
                    method=method_name,
                    endpoint=endpoint_name
                ).dec()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            method = kwargs.get('request', args[0] if args else None)
            method_name = method.method if hasattr(method, 'method') else 'GET'
            endpoint_name = endpoint or func.__name__
            
            http_requests_in_progress.labels(
                method=method_name,
                endpoint=endpoint_name
            ).inc()
            
            try:
                result = func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.record_http_request(
                    method_name,
                    endpoint_name,
                    status,
                    duration
                )
                http_requests_in_progress.labels(
                    method=method_name,
                    endpoint=endpoint_name
                ).dec()
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def track_db_metrics(operation: str, table: str):
    """Decorator to track database query metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record_db_query(operation, table, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record_db_query(operation, table, duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Custom metric creation helpers
def create_custom_counter(name: str, description: str, labels: List[str] = None) -> Counter:
    """Create a custom counter metric"""
    return Counter(
        f'tradesense_{name}',
        description,
        labels or [],
        registry=registry
    )

def create_custom_histogram(name: str, description: str, labels: List[str] = None, buckets: List[float] = None) -> Histogram:
    """Create a custom histogram metric"""
    return Histogram(
        f'tradesense_{name}',
        description,
        labels or [],
        buckets=buckets,
        registry=registry
    )

def create_custom_gauge(name: str, description: str, labels: List[str] = None) -> Gauge:
    """Create a custom gauge metric"""
    return Gauge(
        f'tradesense_{name}',
        description,
        labels or [],
        registry=registry
    )