"""
Structured logging configuration for TradeSense

Provides JSON-formatted logs for better observability and log aggregation.
Includes request ID tracking, user context, and performance metrics.
"""

import logging
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
import traceback
from pythonjsonlogger import jsonlogger

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add context from context variables
        log_record['request_id'] = request_id_var.get()
        log_record['user_id'] = user_id_var.get()
        log_record['correlation_id'] = correlation_id_var.get()
        
        # Add source location
        log_record['source'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName,
            'module': record.module
        }
        
        # Add environment info
        log_record['environment'] = {
            'service': 'tradesense-backend',
            'version': '2.0.0',
            'deployment': 'production'
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stacktrace': traceback.format_exception(*record.exc_info)
            }

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timings: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation"""
        self.timings[operation] = time.time()
    
    def end_timer(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """End timing and log the duration"""
        if operation not in self.timings:
            return
        
        duration = time.time() - self.timings[operation]
        del self.timings[operation]
        
        log_data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'performance_metric': True
        }
        
        if metadata:
            log_data.update(metadata)
        
        self.logger.info(f"Operation completed: {operation}", extra=log_data)

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_authentication_attempt(self, username: str, success: bool, ip_address: str, metadata: Optional[Dict[str, Any]] = None):
        """Log authentication attempts"""
        log_data = {
            'event_type': 'authentication',
            'username': username,
            'success': success,
            'ip_address': ip_address,
            'security_event': True
        }
        
        if metadata:
            log_data.update(metadata)
        
        if success:
            self.logger.info(f"Authentication successful for {username}", extra=log_data)
        else:
            self.logger.warning(f"Authentication failed for {username}", extra=log_data)
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, ip_address: str):
        """Log authorization failures"""
        self.logger.warning(
            f"Authorization denied: user {user_id} attempted {action} on {resource}",
            extra={
                'event_type': 'authorization_failure',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'ip_address': ip_address,
                'security_event': True
            }
        )
    
    def log_suspicious_activity(self, description: str, metadata: Dict[str, Any]):
        """Log suspicious activities"""
        self.logger.warning(
            f"Suspicious activity detected: {description}",
            extra={
                'event_type': 'suspicious_activity',
                'security_event': True,
                **metadata
            }
        )

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (logs to stdout if not provided)
    """
    # Create formatters
    json_formatter = StructuredFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5
        )
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup
    root_logger.info(
        "Logging initialized",
        extra={
            'log_level': log_level,
            'handlers': ['console'] + (['file'] if log_file else [])
        }
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)

def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger instance"""
    return PerformanceLogger(get_logger(name))

def get_security_logger(name: str) -> SecurityLogger:
    """Get a security logger instance"""
    return SecurityLogger(get_logger(name))

# Utility functions for context management
def set_request_context(request_id: str, user_id: Optional[str] = None, correlation_id: Optional[str] = None) -> None:
    """Set request context for logging"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if correlation_id:
        correlation_id_var.set(correlation_id)

def clear_request_context() -> None:
    """Clear request context"""
    request_id_var.set(None)
    user_id_var.set(None)
    correlation_id_var.set(None)

# Log aggregation helpers
class LogAggregator:
    """Aggregate logs for batch processing"""
    
    def __init__(self, logger: logging.Logger, batch_size: int = 100, flush_interval: float = 5.0):
        self.logger = logger
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer: List[Dict[str, Any]] = []
        self.last_flush = time.time()
    
    def add(self, level: str, message: str, **kwargs) -> None:
        """Add a log entry to the buffer"""
        self.buffer.append({
            'level': level,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **kwargs
        })
        
        if len(self.buffer) >= self.batch_size or (time.time() - self.last_flush) > self.flush_interval:
            self.flush()
    
    def flush(self) -> None:
        """Flush buffered logs"""
        if not self.buffer:
            return
        
        self.logger.info(
            f"Batch log: {len(self.buffer)} entries",
            extra={'batch_logs': self.buffer}
        )
        
        self.buffer.clear()
        self.last_flush = time.time()