
import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import time
from logging_manager import log_critical, log_warning, LogCategory
from notification_system import create_system_alert, NotificationType, NotificationPriority

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class SystemHealthMonitor:
    """Monitor system health and trigger alerts."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.health_checks: Dict[str, HealthCheck] = {}
        self.monitoring_active = False
        self.alert_thresholds = {
            'sync_success_rate': 90.0,  # %
            'error_rate': 1.0,  # %
            'memory_usage': 80.0,  # %
            'disk_usage': 85.0,  # %
            'avg_response_time': 5.0,  # seconds
            'active_users_drop': 50.0  # % drop
        }
    
    def start_monitoring(self):
        """Start background health monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        self.monitoring_active = False
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self.run_health_checks()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                log_critical(f"Health monitoring loop failed: {str(e)}", 
                           category=LogCategory.SYSTEM_ERROR)
    
    def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks and return results."""
        checks = {}
        
        try:
            # Sync success rate check
            checks['sync_success'] = self.check_sync_success_rate()
            
            # Error rate check
            checks['error_rate'] = self.check_error_rate()
            
            # System resource checks
            checks['memory_usage'] = self.check_memory_usage()
            checks['disk_usage'] = self.check_disk_usage()
            
            # Database health
            checks['database_health'] = self.check_database_health()
            
            # User activity check
            checks['user_activity'] = self.check_user_activity()
            
            # Partner health check
            checks['partner_health'] = self.check_partner_health()
            
        except Exception as e:
            log_critical(f"Health check execution failed: {str(e)}",
                        category=LogCategory.SYSTEM_ERROR)
        
        self.health_checks.update(checks)
        
        # Process alerts
        self.process_health_alerts(checks)
        
        return checks
    
    def check_sync_success_rate(self) -> HealthCheck:
        """Check sync success rate in last hour."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful
                FROM sync_logs 
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result[0] == 0:
                return HealthCheck(
                    name="Sync Success Rate",
                    status=HealthStatus.UNKNOWN,
                    message="No sync operations in the last hour"
                )
            
            success_rate = (result[1] / result[0]) * 100
            threshold = self.alert_thresholds['sync_success_rate']
            
            if success_rate >= threshold:
                status = HealthStatus.HEALTHY
                message = f"Sync success rate is healthy: {success_rate:.1f}%"
            elif success_rate >= threshold - 10:
                status = HealthStatus.WARNING
                message = f"Sync success rate is declining: {success_rate:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Sync success rate is critically low: {success_rate:.1f}%"
            
            return HealthCheck(
                name="Sync Success Rate",
                status=status,
                message=message,
                value=success_rate,
                threshold=threshold
            )
            
        except Exception as e:
            return HealthCheck(
                name="Sync Success Rate",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check sync success rate: {str(e)}"
            )
    
    def check_error_rate(self) -> HealthCheck:
        """Check error rate in last hour."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total actions and errors
            cursor.execute('''
                SELECT COUNT(*) FROM user_actions 
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            total_actions = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM system_logs 
                WHERE level IN ('ERROR', 'CRITICAL') 
                AND timestamp > datetime('now', '-1 hour')
            ''')
            total_errors = cursor.fetchone()[0]
            
            conn.close()
            
            if total_actions == 0:
                return HealthCheck(
                    name="Error Rate",
                    status=HealthStatus.UNKNOWN,
                    message="No user activity in the last hour"
                )
            
            error_rate = (total_errors / total_actions) * 100
            threshold = self.alert_thresholds['error_rate']
            
            if error_rate <= threshold:
                status = HealthStatus.HEALTHY
                message = f"Error rate is normal: {error_rate:.2f}%"
            elif error_rate <= threshold * 2:
                status = HealthStatus.WARNING
                message = f"Error rate is elevated: {error_rate:.2f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Error rate is critically high: {error_rate:.2f}%"
            
            return HealthCheck(
                name="Error Rate",
                status=status,
                message=message,
                value=error_rate,
                threshold=threshold
            )
            
        except Exception as e:
            return HealthCheck(
                name="Error Rate",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check error rate: {str(e)}"
            )
    
    def check_memory_usage(self) -> HealthCheck:
        """Check system memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            threshold = self.alert_thresholds['memory_usage']
            
            if usage_percent <= threshold:
                status = HealthStatus.HEALTHY
                message = f"Memory usage is normal: {usage_percent:.1f}%"
            elif usage_percent <= threshold + 10:
                status = HealthStatus.WARNING
                message = f"Memory usage is high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Memory usage is critically high: {usage_percent:.1f}%"
            
            return HealthCheck(
                name="Memory Usage",
                status=status,
                message=message,
                value=usage_percent,
                threshold=threshold
            )
            
        except Exception as e:
            return HealthCheck(
                name="Memory Usage",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check memory usage: {str(e)}"
            )
    
    def check_disk_usage(self) -> HealthCheck:
        """Check disk usage."""
        try:
            import psutil
            disk = psutil.disk_usage('.')
            usage_percent = (disk.used / disk.total) * 100
            threshold = self.alert_thresholds['disk_usage']
            
            if usage_percent <= threshold:
                status = HealthStatus.HEALTHY
                message = f"Disk usage is normal: {usage_percent:.1f}%"
            elif usage_percent <= threshold + 5:
                status = HealthStatus.WARNING
                message = f"Disk usage is high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Disk usage is critically high: {usage_percent:.1f}%"
            
            return HealthCheck(
                name="Disk Usage",
                status=status,
                message=message,
                value=usage_percent,
                threshold=threshold
            )
            
        except Exception as e:
            return HealthCheck(
                name="Disk Usage",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk usage: {str(e)}"
            )
    
    def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple query to check connectivity
            cursor.execute('SELECT 1')
            cursor.fetchone()
            
            # Check for locked database
            cursor.execute('PRAGMA quick_check')
            result = cursor.fetchone()
            
            conn.close()
            
            response_time = time.time() - start_time
            
            if result[0] == 'ok' and response_time < 1.0:
                status = HealthStatus.HEALTHY
                message = f"Database is healthy (response: {response_time:.3f}s)"
            elif result[0] == 'ok' and response_time < 5.0:
                status = HealthStatus.WARNING
                message = f"Database is slow (response: {response_time:.3f}s)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Database issues detected (response: {response_time:.3f}s)"
            
            return HealthCheck(
                name="Database Health",
                status=status,
                message=message,
                value=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="Database Health",
                status=HealthStatus.CRITICAL,
                message=f"Database connectivity failed: {str(e)}"
            )
    
    def check_user_activity(self) -> HealthCheck:
        """Check for unusual drops in user activity."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compare current hour vs previous hour
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM user_actions 
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            current_hour = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM user_actions 
                WHERE timestamp BETWEEN datetime('now', '-2 hours') 
                AND datetime('now', '-1 hour')
            ''')
            previous_hour = cursor.fetchone()[0]
            
            conn.close()
            
            if previous_hour == 0:
                return HealthCheck(
                    name="User Activity",
                    status=HealthStatus.UNKNOWN,
                    message="Insufficient data to compare user activity"
                )
            
            drop_percent = ((previous_hour - current_hour) / previous_hour) * 100
            threshold = self.alert_thresholds['active_users_drop']
            
            if drop_percent <= threshold:
                status = HealthStatus.HEALTHY
                message = f"User activity is normal ({current_hour} vs {previous_hour} users)"
            elif drop_percent <= threshold + 20:
                status = HealthStatus.WARNING
                message = f"User activity decreased by {drop_percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Significant drop in user activity: {drop_percent:.1f}%"
            
            return HealthCheck(
                name="User Activity",
                status=status,
                message=message,
                value=drop_percent
            )
            
        except Exception as e:
            return HealthCheck(
                name="User Activity",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check user activity: {str(e)}"
            )
    
    def check_partner_health(self) -> HealthCheck:
        """Check partner sync and activity health."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for partners with recent failed syncs
            cursor.execute('''
                SELECT 
                    partner_id,
                    COUNT(*) as failed_syncs
                FROM sync_logs 
                WHERE status = 'failed' 
                AND timestamp > datetime('now', '-1 hour')
                AND partner_id IS NOT NULL
                GROUP BY partner_id
                HAVING failed_syncs >= 3
            ''')
            
            failing_partners = cursor.fetchall()
            
            # Check overall partner sync success
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful
                FROM sync_logs 
                WHERE timestamp > datetime('now', '-1 hour')
                AND partner_id IS NOT NULL
            ''')
            
            partner_sync_stats = cursor.fetchone()
            conn.close()
            
            if len(failing_partners) == 0:
                status = HealthStatus.HEALTHY
                message = "All partners have healthy sync operations"
            elif len(failing_partners) <= 2:
                status = HealthStatus.WARNING
                message = f"{len(failing_partners)} partner(s) experiencing sync issues"
            else:
                status = HealthStatus.CRITICAL
                message = f"{len(failing_partners)} partners have critical sync failures"
            
            return HealthCheck(
                name="Partner Health",
                status=status,
                message=message,
                value=len(failing_partners)
            )
            
        except Exception as e:
            return HealthCheck(
                name="Partner Health",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check partner health: {str(e)}"
            )
    
    def process_health_alerts(self, checks: Dict[str, HealthCheck]):
        """Process health check results and send alerts if needed."""
        for check_name, check in checks.items():
            if check.status == HealthStatus.CRITICAL:
                # Send critical alert
                create_system_alert(
                    title=f"🚨 Critical: {check.name}",
                    message=check.message,
                    notification_type=NotificationType.ERROR,
                    priority=NotificationPriority.CRITICAL
                )
                
                # Log critical issue
                log_critical(f"Health check failed: {check.name} - {check.message}",
                           details={'check_name': check_name, 'value': check.value},
                           category=LogCategory.SYSTEM_ERROR)
            
            elif check.status == HealthStatus.WARNING:
                # Send warning alert
                create_system_alert(
                    title=f"⚠️ Warning: {check.name}",
                    message=check.message,
                    notification_type=NotificationType.WARNING,
                    priority=NotificationPriority.HIGH
                )
                
                # Log warning
                log_warning(f"Health check warning: {check.name} - {check.message}",
                          details={'check_name': check_name, 'value': check.value},
                          category=LogCategory.SYSTEM_ERROR)
    
    def get_overall_health_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.health_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.health_checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.HEALTHY in statuses:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def render_health_widget(self):
        """Render a compact health status widget."""
        overall_status = self.get_overall_health_status()
        
        status_config = {
            HealthStatus.HEALTHY: {"icon": "✅", "color": "success", "text": "All Systems Healthy"},
            HealthStatus.WARNING: {"icon": "⚠️", "color": "warning", "text": "Some Issues Detected"},
            HealthStatus.CRITICAL: {"icon": "🚨", "color": "error", "text": "Critical Issues"},
            HealthStatus.UNKNOWN: {"icon": "❓", "color": "info", "text": "Status Unknown"}
        }
        
        config = status_config[overall_status]
        
        if overall_status == HealthStatus.HEALTHY:
            st.success(f"{config['icon']} {config['text']}")
        elif overall_status == HealthStatus.WARNING:
            st.warning(f"{config['icon']} {config['text']}")
        elif overall_status == HealthStatus.CRITICAL:
            st.error(f"{config['icon']} {config['text']}")
        else:
            st.info(f"{config['icon']} {config['text']}")
        
        # Show critical issues
        critical_checks = [check for check in self.health_checks.values() 
                          if check.status == HealthStatus.CRITICAL]
        
        if critical_checks:
            with st.expander(f"🚨 {len(critical_checks)} Critical Issue(s)"):
                for check in critical_checks:
                    st.error(f"**{check.name}**: {check.message}")

# Global health monitor
health_monitor = SystemHealthMonitor()

def start_health_monitoring():
    """Start the health monitoring system."""
    health_monitor.start_monitoring()

def get_system_health_status():
    """Get current system health status."""
    return health_monitor.run_health_checks()
import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import threading
import time
from logging_manager import log_critical, log_warning, LogCategory
from notification_system import create_system_alert, NotificationType, NotificationPriority

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class SystemHealthMonitor:
    """Monitor system health and trigger alerts."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.health_checks: Dict[str, HealthCheck] = {}
        self.monitoring_active = False
        self.alert_thresholds = {
            'sync_success_rate': 90.0,  # %
            'error_rate': 1.0,  # %
            'memory_usage': 80.0,  # %
            'disk_usage': 85.0,  # %
            'avg_response_time': 5.0,  # seconds
            'active_users_drop': 50.0  # % drop
        }
    
    def start_monitoring(self):
        """Start background health monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        self.monitoring_active = False
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self.run_health_checks()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                try:
                    log_critical(f"Health monitoring loop failed: {str(e)}", 
                               category=LogCategory.SYSTEM_ERROR)
                except:
                    pass  # Fail silently if logging not available
    
    def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all health checks and return results."""
        checks = {}
        
        try:
            # System resource checks
            checks['memory_usage'] = self.check_memory_usage()
            checks['disk_usage'] = self.check_disk_usage()
            
            # Database health
            checks['database_health'] = self.check_database_health()
            
        except Exception as e:
            try:
                log_critical(f"Health check execution failed: {str(e)}",
                            category=LogCategory.SYSTEM_ERROR)
            except:
                pass
        
        self.health_checks.update(checks)
        
        # Process alerts
        self.process_health_alerts(checks)
        
        return checks
    
    def check_memory_usage(self) -> HealthCheck:
        """Check system memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            threshold = self.alert_thresholds['memory_usage']
            
            if usage_percent <= threshold:
                status = HealthStatus.HEALTHY
                message = f"Memory usage is normal: {usage_percent:.1f}%"
            elif usage_percent <= threshold + 10:
                status = HealthStatus.WARNING
                message = f"Memory usage is high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Memory usage is critically high: {usage_percent:.1f}%"
            
            return HealthCheck(
                name="Memory Usage",
                status=status,
                message=message,
                value=usage_percent,
                threshold=threshold
            )
            
        except Exception as e:
            return HealthCheck(
                name="Memory Usage",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check memory usage: {str(e)}"
            )
    
    def check_disk_usage(self) -> HealthCheck:
        """Check disk usage."""
        try:
            import psutil
            disk = psutil.disk_usage('.')
            usage_percent = (disk.used / disk.total) * 100
            threshold = self.alert_thresholds['disk_usage']
            
            if usage_percent <= threshold:
                status = HealthStatus.HEALTHY
                message = f"Disk usage is normal: {usage_percent:.1f}%"
            elif usage_percent <= threshold + 5:
                status = HealthStatus.WARNING
                message = f"Disk usage is high: {usage_percent:.1f}%"
            else:
                status = HealthStatus.CRITICAL
                message = f"Disk usage is critically high: {usage_percent:.1f}%"
            
            return HealthCheck(
                name="Disk Usage",
                status=status,
                message=message,
                value=usage_percent,
                threshold=threshold
            )
            
        except Exception as e:
            return HealthCheck(
                name="Disk Usage",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk usage: {str(e)}"
            )
    
    def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Simple query to check connectivity
            cursor.execute('SELECT 1')
            cursor.fetchone()
            
            # Check for locked database
            cursor.execute('PRAGMA quick_check')
            result = cursor.fetchone()
            
            conn.close()
            
            response_time = time.time() - start_time
            
            if result[0] == 'ok' and response_time < 1.0:
                status = HealthStatus.HEALTHY
                message = f"Database is healthy (response: {response_time:.3f}s)"
            elif result[0] == 'ok' and response_time < 5.0:
                status = HealthStatus.WARNING
                message = f"Database is slow (response: {response_time:.3f}s)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Database issues detected (response: {response_time:.3f}s)"
            
            return HealthCheck(
                name="Database Health",
                status=status,
                message=message,
                value=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="Database Health",
                status=HealthStatus.CRITICAL,
                message=f"Database connectivity failed: {str(e)}"
            )
    
    def process_health_alerts(self, checks: Dict[str, HealthCheck]):
        """Process health check results and send alerts if needed."""
        for check_name, check in checks.items():
            if check.status == HealthStatus.CRITICAL:
                # Create critical alert
                try:
                    create_system_alert(
                        title=f"🚨 Critical: {check.name}",
                        message=check.message,
                        notification_type=NotificationType.ERROR,
                        priority=NotificationPriority.CRITICAL
                    )
                    
                    # Log critical issue
                    log_critical(f"Health check failed: {check.name} - {check.message}",
                               details={'check_name': check_name, 'value': check.value},
                               category=LogCategory.SYSTEM_ERROR)
                except:
                    pass  # Fail silently if notification system not available
            
            elif check.status == HealthStatus.WARNING:
                # Create warning alert
                try:
                    create_system_alert(
                        title=f"⚠️ Warning: {check.name}",
                        message=check.message,
                        notification_type=NotificationType.WARNING,
                        priority=NotificationPriority.HIGH
                    )
                    
                    # Log warning
                    log_warning(f"Health check warning: {check.name} - {check.message}",
                              details={'check_name': check_name, 'value': check.value},
                              category=LogCategory.SYSTEM_ERROR)
                except:
                    pass
    
    def get_overall_health_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.health_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self.health_checks.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            return HealthStatus.WARNING
        elif HealthStatus.HEALTHY in statuses:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def render_status_widget(self):
        """Render a compact health status widget."""
        overall_status = self.get_overall_health_status()
        
        status_config = {
            HealthStatus.HEALTHY: {"icon": "✅", "color": "success", "text": "All Systems Healthy"},
            HealthStatus.WARNING: {"icon": "⚠️", "color": "warning", "text": "Some Issues Detected"},
            HealthStatus.CRITICAL: {"icon": "🚨", "color": "error", "text": "Critical Issues"},
            HealthStatus.UNKNOWN: {"icon": "❓", "color": "info", "text": "Status Unknown"}
        }
        
        config = status_config[overall_status]
        
        if overall_status == HealthStatus.HEALTHY:
            st.success(f"{config['icon']} {config['text']}")
        elif overall_status == HealthStatus.WARNING:
            st.warning(f"{config['icon']} {config['text']}")
        elif overall_status == HealthStatus.CRITICAL:
            st.error(f"{config['icon']} {config['text']}")
        else:
            st.info(f"{config['icon']} {config['text']}")

# Global health monitor
system_monitor = SystemHealthMonitor()

def start_health_monitoring():
    """Start the health monitoring system."""
    system_monitor.start_monitoring()

def get_system_health_status():
    """Get current system health status."""
    return system_monitor.run_health_checks()
