"""
Enhanced monitoring and observability for TradeSense

Provides correlation IDs, distributed tracing, and enhanced metrics
for better debugging and performance monitoring.
"""

import time
import uuid
import json
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
import asyncio
from contextvars import ContextVar
import os

from core.logging_config import get_logger, get_performance_logger, request_id_var
from core.metrics import metrics_collector, rate_limit_check_duration, rate_limit_usage
from core.error_tracking import error_tracker
from core.cache import cache_manager

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)

# Context variables for distributed tracing
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar('span_id', default=None)
parent_span_id_var: ContextVar[Optional[str]] = ContextVar('parent_span_id', default=None)


class DistributedTracer:
    """Distributed tracing support for microservices"""
    
    def __init__(self):
        self.active_spans: Dict[str, Dict[str, Any]] = {}
        self.completed_spans: List[Dict[str, Any]] = []
        self.max_completed_spans = 1000
    
    def start_trace(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        # Set context
        trace_id_var.set(trace_id)
        span_id_var.set(span_id)
        parent_span_id_var.set(None)
        
        # Create span
        span = {
            'trace_id': trace_id,
            'span_id': span_id,
            'parent_span_id': None,
            'operation': operation,
            'start_time': time.time(),
            'metadata': metadata or {},
            'events': []
        }
        
        self.active_spans[span_id] = span
        
        logger.info(
            f"Started trace: {operation}",
            extra={
                'trace_id': trace_id,
                'span_id': span_id,
                'distributed_trace': True
            }
        )
        
        return trace_id
    
    def start_span(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new span within current trace"""
        trace_id = trace_id_var.get()
        parent_span_id = span_id_var.get()
        span_id = str(uuid.uuid4())
        
        if not trace_id:
            # No active trace, start a new one
            return self.start_trace(operation, metadata)
        
        # Set new span context
        span_id_var.set(span_id)
        parent_span_id_var.set(parent_span_id)
        
        # Create span
        span = {
            'trace_id': trace_id,
            'span_id': span_id,
            'parent_span_id': parent_span_id,
            'operation': operation,
            'start_time': time.time(),
            'metadata': metadata or {},
            'events': []
        }
        
        self.active_spans[span_id] = span
        
        return span_id
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to the current span"""
        span_id = span_id_var.get()
        if span_id and span_id in self.active_spans:
            event = {
                'name': name,
                'timestamp': time.time(),
                'attributes': attributes or {}
            }
            self.active_spans[span_id]['events'].append(event)
    
    def end_span(self, span_id: Optional[str] = None, status: str = 'ok', error: Optional[Exception] = None):
        """End a span"""
        if not span_id:
            span_id = span_id_var.get()
        
        if not span_id or span_id not in self.active_spans:
            return
        
        span = self.active_spans.pop(span_id)
        span['end_time'] = time.time()
        span['duration_ms'] = (span['end_time'] - span['start_time']) * 1000
        span['status'] = status
        
        if error:
            span['error'] = {
                'type': type(error).__name__,
                'message': str(error)
            }
        
        # Store completed span
        self.completed_spans.append(span)
        if len(self.completed_spans) > self.max_completed_spans:
            self.completed_spans = self.completed_spans[-self.max_completed_spans:]
        
        # Log span completion
        logger.info(
            f"Completed span: {span['operation']}",
            extra={
                'trace_id': span['trace_id'],
                'span_id': span['span_id'],
                'duration_ms': span['duration_ms'],
                'status': status,
                'distributed_trace': True
            }
        )
        
        # Record metrics
        perf_logger.end_timer(f"span:{span['operation']}", {
            'trace_id': span['trace_id'],
            'status': status
        })
    
    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all spans for a trace"""
        spans = [
            span for span in self.completed_spans
            if span['trace_id'] == trace_id
        ]
        return sorted(spans, key=lambda x: x['start_time'])
    
    def get_active_traces(self) -> List[Dict[str, Any]]:
        """Get all active traces"""
        traces = {}
        for span in self.active_spans.values():
            trace_id = span['trace_id']
            if trace_id not in traces:
                traces[trace_id] = {
                    'trace_id': trace_id,
                    'start_time': span['start_time'],
                    'spans': []
                }
            traces[trace_id]['spans'].append(span)
        
        return list(traces.values())


# Global tracer instance
tracer = DistributedTracer()


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}
    
    def register_check(self, name: str, check_func: Callable, critical: bool = False):
        """Register a health check"""
        self.checks[name] = {
            'func': check_func,
            'critical': critical
        }
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = 'healthy'
        
        for name, check_info in self.checks.items():
            try:
                start_time = time.time()
                
                # Run check
                if asyncio.iscoroutinefunction(check_info['func']):
                    result = await check_info['func']()
                else:
                    result = check_info['func']()
                
                duration = time.time() - start_time
                
                # Store result
                results[name] = {
                    'status': result.get('status', 'healthy'),
                    'message': result.get('message', 'OK'),
                    'duration_ms': round(duration * 1000, 2),
                    'critical': check_info['critical'],
                    'details': result.get('details', {}),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Update overall status
                if result.get('status') == 'unhealthy' and check_info['critical']:
                    overall_status = 'unhealthy'
                elif result.get('status') == 'degraded' and overall_status != 'unhealthy':
                    overall_status = 'degraded'
                
            except Exception as e:
                results[name] = {
                    'status': 'unhealthy',
                    'message': f'Check failed: {str(e)}',
                    'critical': check_info['critical'],
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if check_info['critical']:
                    overall_status = 'unhealthy'
        
        self.last_results = results
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': results
        }
    
    def get_last_results(self) -> Dict[str, Any]:
        """Get last health check results"""
        return self.last_results


# Global health checker
health_checker = HealthChecker()


# Standard health checks
async def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    from core.db.session import SessionLocal
    
    try:
        start_time = time.time()
        db = SessionLocal()
        
        # Test connection
        result = db.execute("SELECT 1").scalar()
        
        # Get pool stats
        pool = db.bind.pool
        
        duration = time.time() - start_time
        
        return {
            'status': 'healthy' if result == 1 else 'unhealthy',
            'message': 'Database is responsive',
            'details': {
                'response_time_ms': round(duration * 1000, 2),
                'pool_size': pool.size() if pool else 0,
                'checked_out': pool.checked_out() if pool else 0,
                'overflow': pool.overflow() if pool else 0
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        }
    finally:
        if 'db' in locals():
            db.close()


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and performance"""
    if not cache_manager._redis_client:
        return {
            'status': 'degraded',
            'message': 'Redis not configured'
        }
    
    try:
        start_time = time.time()
        
        # Test connection
        cache_manager._redis_client.ping()
        
        # Get info
        info = cache_manager._redis_client.info()
        
        duration = time.time() - start_time
        
        return {
            'status': 'healthy',
            'message': 'Redis is responsive',
            'details': {
                'response_time_ms': round(duration * 1000, 2),
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'uptime_days': info.get('uptime_in_days')
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Redis error: {str(e)}'
        }


async def check_disk_space() -> Dict[str, Any]:
    """Check available disk space"""
    import psutil
    
    try:
        disk = psutil.disk_usage('/')
        percent_used = disk.percent
        
        if percent_used > 90:
            status = 'unhealthy'
            message = 'Critical disk space'
        elif percent_used > 80:
            status = 'degraded'
            message = 'Low disk space'
        else:
            status = 'healthy'
            message = 'Adequate disk space'
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent_used': percent_used
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Disk check error: {str(e)}'
        }


async def check_memory_usage() -> Dict[str, Any]:
    """Check memory usage"""
    import psutil
    
    try:
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        if percent_used > 90:
            status = 'unhealthy'
            message = 'Critical memory usage'
        elif percent_used > 80:
            status = 'degraded'
            message = 'High memory usage'
        else:
            status = 'healthy'
            message = 'Normal memory usage'
        
        return {
            'status': status,
            'message': message,
            'details': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent_used': percent_used
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Memory check error: {str(e)}'
        }


# Register standard health checks
health_checker.register_check('database', check_database_health, critical=True)
health_checker.register_check('redis', check_redis_health, critical=False)
health_checker.register_check('disk_space', check_disk_space, critical=False)
health_checker.register_check('memory', check_memory_usage, critical=False)


# Monitoring decorators
def monitor_performance(operation: str = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_name = operation or f"{func.__module__}.{func.__name__}"
            
            # Start span
            span_id = tracer.start_span(operation_name)
            perf_logger.start_timer(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                tracer.end_span(span_id, status='ok')
                return result
            except Exception as e:
                tracer.end_span(span_id, status='error', error=e)
                raise
            finally:
                perf_logger.end_timer(operation_name)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_name = operation or f"{func.__module__}.{func.__name__}"
            
            span_id = tracer.start_span(operation_name)
            perf_logger.start_timer(operation_name)
            
            try:
                result = func(*args, **kwargs)
                tracer.end_span(span_id, status='ok')
                return result
            except Exception as e:
                tracer.end_span(span_id, status='error', error=e)
                raise
            finally:
                perf_logger.end_timer(operation_name)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def monitor_rate_limit(endpoint: str, limit_type: str = "api"):
    """Decorator to monitor rate limit usage"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Get request context
                request = None
                for arg in args:
                    if hasattr(arg, 'client'):
                        request = arg
                        break
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Record rate limit check duration
                duration = time.time() - start_time
                rate_limit_check_duration.labels(strategy=limit_type).observe(duration)
                
                # Record usage if available
                if hasattr(result, 'headers') and 'X-RateLimit-Remaining' in result.headers:
                    remaining = int(result.headers['X-RateLimit-Remaining'])
                    limit = int(result.headers.get('X-RateLimit-Limit', 100))
                    usage_percent = ((limit - remaining) / limit) * 100
                    
                    user_id = 'anonymous'
                    if request and hasattr(request.state, 'user'):
                        user_id = str(request.state.user.id)
                    
                    rate_limit_usage.labels(
                        user_id=user_id,
                        tier='default',
                        limit_type=limit_type
                    ).set(usage_percent)
                
                return result
                
            except Exception as e:
                raise
        
        return async_wrapper
    
    return decorator


# Business metrics tracking
class BusinessMetrics:
    """Track business-specific metrics"""
    
    def __init__(self):
        self.daily_metrics: Dict[str, Dict[str, Any]] = {}
    
    def track_trade(self, user_id: str, trade_type: str, amount: float, profit_loss: float):
        """Track trade metrics"""
        metrics_collector.record_trade_created(user_id, trade_type)
        
        # Store daily aggregates
        today = datetime.utcnow().date().isoformat()
        if today not in self.daily_metrics:
            self.daily_metrics[today] = {
                'trades': 0,
                'volume': 0,
                'profit_loss': 0,
                'users': set()
            }
        
        self.daily_metrics[today]['trades'] += 1
        self.daily_metrics[today]['volume'] += amount
        self.daily_metrics[today]['profit_loss'] += profit_loss
        self.daily_metrics[today]['users'].add(user_id)
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily business metrics summary"""
        if not date:
            date = datetime.utcnow().date().isoformat()
        
        if date not in self.daily_metrics:
            return {
                'date': date,
                'trades': 0,
                'volume': 0,
                'profit_loss': 0,
                'active_users': 0
            }
        
        metrics = self.daily_metrics[date]
        return {
            'date': date,
            'trades': metrics['trades'],
            'volume': metrics['volume'],
            'profit_loss': metrics['profit_loss'],
            'active_users': len(metrics['users'])
        }


# Global business metrics
business_metrics = BusinessMetrics()


# Monitoring API response
def create_monitoring_response() -> Dict[str, Any]:
    """Create comprehensive monitoring response"""
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'health': health_checker.get_last_results(),
        'metrics': {
            'system': metrics_collector.get_metrics().decode('utf-8'),
            'errors': error_tracker.get_error_stats(),
            'cache': cache_manager.get_stats(),
            'business': business_metrics.get_daily_summary()
        },
        'traces': {
            'active': len(tracer.active_spans),
            'recent': len(tracer.completed_spans)
        }
    }