
import time
import functools
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
        
    def track_execution_time(self, operation_name: str):
        """Decorator to track execution time of functions"""
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000  # ms
                    self._record_metric(operation_name, execution_time)
                    return result
                except Exception as e:
                    self._record_error(operation_name)
                    logger.error(f"Error in {operation_name}: {str(e)}")
                    raise
                    
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000  # ms
                    self._record_metric(operation_name, execution_time)
                    return result
                except Exception as e:
                    self._record_error(operation_name)
                    logger.error(f"Error in {operation_name}: {str(e)}")
                    raise
                    
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record_metric(self, operation: str, value: float):
        """Record a performance metric"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append(value)
        
        # Keep only last 1000 measurements
        if len(self.metrics[operation]) > 1000:
            self.metrics[operation] = self.metrics[operation][-1000:]
    
    def _record_error(self, operation: str):
        """Record an error occurrence"""
        if operation not in self.error_counts:
            self.error_counts[operation] = 0
        self.error_counts[operation] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all performance metrics"""
        summary = {}
        
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    "avg_time_ms": sum(times) / len(times),
                    "min_time_ms": min(times),
                    "max_time_ms": max(times),
                    "total_calls": len(times),
                    "error_count": self.error_counts.get(operation, 0),
                    "error_rate": self.error_counts.get(operation, 0) / len(times) * 100
                }
        
        return summary
    
    def clear_metrics(self):
        """Clear all stored metrics"""
        self.metrics.clear()
        self.error_counts.clear()

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience decorator
def monitor_performance(operation_name: str):
    """Convenience decorator for performance monitoring"""
    return performance_monitor.track_execution_time(operation_name)
