"""
Error tracking and monitoring for TradeSense

Integrates with Sentry for production error tracking and provides
fallback local error logging for development.
"""

import os
import sys
import traceback
import logging
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime
import json
from contextlib import contextmanager

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

from core.logging_config import get_logger

logger = get_logger(__name__)

class ErrorTracker:
    """Central error tracking system"""
    
    def __init__(self):
        self.initialized = False
        self.local_errors: List[Dict[str, Any]] = []
        self.error_counts: Dict[str, int] = {}
        self.sentry_dsn = os.getenv('SENTRY_DSN')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        if self.sentry_dsn and SENTRY_AVAILABLE:
            self._initialize_sentry()
        else:
            logger.warning("Sentry not configured, using local error tracking")
    
    def _initialize_sentry(self) -> None:
        """Initialize Sentry error tracking"""
        try:
            # Configure Sentry integrations
            integrations = [
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ]
            
            # Add Redis integration if available
            try:
                integrations.append(RedisIntegration())
            except:
                pass
            
            # Initialize Sentry
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=integrations,
                environment=self.environment,
                traces_sample_rate=0.1,  # 10% of transactions
                profiles_sample_rate=0.1,  # 10% profiling
                attach_stacktrace=True,
                send_default_pii=False,  # Don't send PII
                before_send=self._before_send,
                before_send_transaction=self._before_send_transaction,
                release=f"tradesense@2.0.0"
            )
            
            self.initialized = True
            logger.info("Sentry error tracking initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.initialized = False
    
    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process event before sending to Sentry"""
        # Filter out sensitive data
        if 'request' in event and 'data' in event['request']:
            self._sanitize_data(event['request']['data'])
        
        # Add custom context
        event['contexts']['tradesense'] = {
            'version': '2.0.0',
            'environment': self.environment
        }
        
        return event
    
    def _before_send_transaction(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process transaction before sending to Sentry"""
        # Filter out health check endpoints
        if event.get('transaction', '').endswith('/health'):
            return None
        
        return event
    
    def _sanitize_data(self, data: Any) -> None:
        """Remove sensitive data from error reports"""
        if isinstance(data, dict):
            sensitive_keys = ['password', 'token', 'secret', 'api_key', 'credit_card', 'ssn']
            for key in list(data.keys()):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    data[key] = '[REDACTED]'
                elif isinstance(data[key], (dict, list)):
                    self._sanitize_data(data[key])
        elif isinstance(data, list):
            for item in data:
                self._sanitize_data(item)
    
    def capture_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """Capture an exception with context"""
        error_id = self._generate_error_id()
        
        # Create error record
        error_record = {
            'id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'stacktrace': traceback.format_exc(),
            'context': context or {}
        }
        
        # Send to Sentry if available
        if self.initialized and SENTRY_AVAILABLE:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                
                error_id = sentry_sdk.capture_exception(error)
        else:
            # Store locally
            self.local_errors.append(error_record)
            if len(self.local_errors) > 1000:  # Keep last 1000 errors
                self.local_errors = self.local_errors[-1000:]
        
        # Update error counts
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log the error
        logger.error(
            f"Exception captured: {error_type}",
            extra={
                'error_id': error_id,
                'error_type': error_type,
                'error_message': str(error),
                'context': context
            }
        )
        
        return error_id
    
    def capture_message(self, message: str, level: str = 'info', context: Optional[Dict[str, Any]] = None) -> None:
        """Capture a message with context"""
        if self.initialized and SENTRY_AVAILABLE:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_context(key, value)
                
                sentry_sdk.capture_message(message, level)
        else:
            logger.log(
                getattr(logging, level.upper()),
                message,
                extra={'context': context}
            )
    
    def set_user_context(self, user_id: str, email: Optional[str] = None, username: Optional[str] = None) -> None:
        """Set user context for error tracking"""
        if self.initialized and SENTRY_AVAILABLE:
            sentry_sdk.set_user({
                'id': user_id,
                'email': email,
                'username': username
            })
    
    def set_tag(self, key: str, value: str) -> None:
        """Set a tag for error categorization"""
        if self.initialized and SENTRY_AVAILABLE:
            sentry_sdk.set_tag(key, value)
    
    def add_breadcrumb(self, message: str, category: str = 'custom', level: str = 'info', data: Optional[Dict[str, Any]] = None) -> None:
        """Add a breadcrumb for error context"""
        if self.initialized and SENTRY_AVAILABLE:
            sentry_sdk.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data
            )
    
    @contextmanager
    def transaction(self, name: str, op: str = 'task'):
        """Create a performance transaction"""
        if self.initialized and SENTRY_AVAILABLE:
            with sentry_sdk.start_transaction(op=op, name=name) as transaction:
                yield transaction
        else:
            yield None
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': self.error_counts,
            'recent_errors': len(self.local_errors),
            'sentry_enabled': self.initialized
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors from local storage"""
        return self.local_errors[-limit:]
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID"""
        import uuid
        return str(uuid.uuid4())

# Global error tracker instance
error_tracker = ErrorTracker()

# Decorators for error tracking
def track_errors(operation: str = None):
    """Decorator to automatically track errors in functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_name = operation or f"{func.__module__}.{func.__name__}"
            
            try:
                # Add breadcrumb
                error_tracker.add_breadcrumb(
                    f"Starting {operation_name}",
                    category='operation',
                    level='info'
                )
                
                result = await func(*args, **kwargs)
                
                # Add success breadcrumb
                error_tracker.add_breadcrumb(
                    f"Completed {operation_name}",
                    category='operation',
                    level='info'
                )
                
                return result
                
            except Exception as e:
                # Capture exception with context
                context = {
                    'operation': operation_name,
                    'args': str(args)[:200],  # Limit size
                    'kwargs': str(kwargs)[:200]
                }
                
                error_id = error_tracker.capture_exception(e, context)
                
                # Re-raise with error ID
                if hasattr(e, 'error_id'):
                    e.error_id = error_id
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_name = operation or f"{func.__module__}.{func.__name__}"
            
            try:
                error_tracker.add_breadcrumb(
                    f"Starting {operation_name}",
                    category='operation',
                    level='info'
                )
                
                result = func(*args, **kwargs)
                
                error_tracker.add_breadcrumb(
                    f"Completed {operation_name}",
                    category='operation',
                    level='info'
                )
                
                return result
                
            except Exception as e:
                context = {
                    'operation': operation_name,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }
                
                error_id = error_tracker.capture_exception(e, context)
                
                if hasattr(e, 'error_id'):
                    e.error_id = error_id
                
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Error analysis utilities
class ErrorAnalyzer:
    """Analyze error patterns and trends"""
    
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
    
    def get_error_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get error trends over time"""
        recent_errors = self.error_tracker.get_recent_errors(limit=1000)
        
        # Group by hour
        hourly_counts = {}
        error_types = {}
        
        for error in recent_errors:
            timestamp = datetime.fromisoformat(error['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
            
            error_type = error['type']
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(timestamp)
        
        # Calculate trends
        trends = {
            'hourly_counts': hourly_counts,
            'top_errors': sorted(
                [(k, len(v)) for k, v in error_types.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'total_errors': len(recent_errors)
        }
        
        return trends
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary"""
        stats = self.error_tracker.get_error_stats()
        trends = self.get_error_trends()
        
        return {
            'stats': stats,
            'trends': trends,
            'health': self._calculate_error_health(stats, trends)
        }
    
    def _calculate_error_health(self, stats: Dict[str, Any], trends: Dict[str, Any]) -> str:
        """Calculate overall error health status"""
        total_errors = stats['total_errors']
        
        if total_errors == 0:
            return 'healthy'
        elif total_errors < 10:
            return 'good'
        elif total_errors < 50:
            return 'warning'
        else:
            return 'critical'

# Global error analyzer instance
error_analyzer = ErrorAnalyzer(error_tracker)