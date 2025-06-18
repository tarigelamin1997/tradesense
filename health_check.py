
import time
import psutil
import sqlite3
from typing import Dict, Any
from config import config

class HealthMonitor:
    """Application health monitoring."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'uptime': time.time() - self.start_time,
            'memory': self._get_memory_status(),
            'database': self._check_database_health(),
            'disk': self._get_disk_status(),
            'version': '1.0.0'
        }
    
    def _get_memory_status(self) -> Dict[str, Any]:
        """Get memory usage status."""
        memory = psutil.virtual_memory()
        return {
            'usage_percent': memory.percent,
            'available_gb': memory.available / (1024**3),
            'total_gb': memory.total / (1024**3),
            'status': 'critical' if memory.percent > 90 else 'warning' if memory.percent > 80 else 'healthy'
        }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and status."""
        try:
            conn = sqlite3.connect(config.DATABASE_URL.replace('sqlite:///', ''), timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return {'status': 'healthy', 'message': 'Database accessible'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database error: {str(e)}'}
    
    def _get_disk_status(self) -> Dict[str, Any]:
        """Get disk usage status."""
        disk = psutil.disk_usage('/')
        usage_percent = (disk.used / disk.total) * 100
        return {
            'usage_percent': usage_percent,
            'free_gb': disk.free / (1024**3),
            'total_gb': disk.total / (1024**3),
            'status': 'critical' if usage_percent > 90 else 'warning' if usage_percent > 80 else 'healthy'
        }

# Global health monitor
health_monitor = HealthMonitor()
