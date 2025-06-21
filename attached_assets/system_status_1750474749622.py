
import streamlit as st
import psutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List
from logging_manager import logger_instance
import os

class SystemStatusMonitor:
    """Monitor and display system status information."""
    
    def __init__(self):
        self.db_path = "tradesense.db"
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('.')
            
            # Database size
            db_size = 0
            if os.path.exists(self.db_path):
                db_size = os.path.getsize(self.db_path) / 1024 / 1024  # MB
            
            # Log file sizes
            log_size = 0
            if os.path.exists('logs/tradesense.log'):
                log_size = os.path.getsize('logs/tradesense.log') / 1024 / 1024  # MB
            
            return {
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
                'db_size_mb': db_size,
                'log_size_mb': log_size
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_error_summary(self, hours: int = 24) -> Dict:
        """Get error summary for the specified time period."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Error counts by level
            cursor.execute('''
                SELECT level, COUNT(*) as count
                FROM system_logs
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY level
            '''.format(hours))
            
            error_counts = dict(cursor.fetchall())
            
            # Recent critical errors
            cursor.execute('''
                SELECT message, timestamp
                FROM system_logs
                WHERE level = 'CRITICAL' 
                AND timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                LIMIT 5
            '''.format(hours))
            
            critical_errors = cursor.fetchall()
            
            # Active error patterns
            cursor.execute('''
                SELECT COUNT(*) FROM error_patterns
                WHERE status = 'active' AND occurrence_count >= 3
            ''')
            
            active_patterns = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'error_counts': error_counts,
                'critical_errors': critical_errors,
                'active_patterns': active_patterns,
                'total_errors': sum(error_counts.values())
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_user_activity_stats(self, hours: int = 24) -> Dict:
        """Get user activity statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Active users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM user_actions
                WHERE timestamp > datetime('now', '-{} hours')
            '''.format(hours))
            
            active_users = cursor.fetchone()[0]
            
            # Total actions
            cursor.execute('''
                SELECT COUNT(*) FROM user_actions
                WHERE timestamp > datetime('now', '-{} hours')
            '''.format(hours))
            
            total_actions = cursor.fetchone()[0]
            
            # Top actions
            cursor.execute('''
                SELECT action_type, COUNT(*) as count
                FROM user_actions
                WHERE timestamp > datetime('now', '-{} hours')
                GROUP BY action_type
                ORDER BY count DESC
                LIMIT 5
            '''.format(hours))
            
            top_actions = cursor.fetchall()
            
            conn.close()
            
            return {
                'active_users': active_users,
                'total_actions': total_actions,
                'top_actions': dict(top_actions)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def render_status_widget(self):
        """Render a compact system status widget."""
        col1, col2, col3 = st.columns(3)
        
        # System metrics
        metrics = self.get_system_metrics()
        if 'error' not in metrics:
            with col1:
                st.metric(
                    "Memory Usage", 
                    f"{metrics['memory_percent']:.1f}%",
                    delta=f"{metrics['memory_used_gb']:.1f}GB used"
                )
                
                if metrics['memory_percent'] > 80:
                    st.error("⚠️ High memory usage")
                elif metrics['memory_percent'] > 60:
                    st.warning("⚠️ Memory usage elevated")
        
        # Error summary
        error_summary = self.get_error_summary(hours=24)
        if 'error' not in error_summary:
            with col2:
                total_errors = error_summary['total_errors']
                critical_count = error_summary['error_counts'].get('CRITICAL', 0)
                
                if total_errors == 0:
                    st.success("✅ No Errors (24h)")
                elif critical_count > 0:
                    st.error(f"🚨 {total_errors} Errors ({critical_count} Critical)")
                else:
                    st.warning(f"⚠️ {total_errors} Errors (24h)")
        
        # User activity
        activity = self.get_user_activity_stats(hours=24)
        if 'error' not in activity:
            with col3:
                st.metric(
                    "Active Users (24h)",
                    activity['active_users'],
                    delta=f"{activity['total_actions']} actions"
                )
    
    def render_detailed_status(self):
        """Render detailed system status information."""
        st.subheader("🔍 Detailed System Status")
        
        tab1, tab2, tab3, tab4 = st.tabs(["System Resources", "Error Analysis", "User Activity", "Database Health"])
        
        with tab1:
            metrics = self.get_system_metrics()
            
            if 'error' in metrics:
                st.error(f"Failed to get system metrics: {metrics['error']}")
            else:
                # Memory
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Memory Usage")
                    st.metric("RAM Usage", f"{metrics['memory_percent']:.1f}%")
                    st.progress(metrics['memory_percent'] / 100)
                    st.caption(f"{metrics['memory_used_gb']:.2f}GB / {metrics['memory_total_gb']:.2f}GB")
                
                with col2:
                    st.subheader("Storage Usage")
                    st.metric("Disk Usage", f"{metrics['disk_percent']:.1f}%")
                    st.progress(metrics['disk_percent'] / 100)
                    st.caption(f"{metrics['disk_used_gb']:.2f}GB / {metrics['disk_total_gb']:.2f}GB")
                
                # File sizes
                st.subheader("File Sizes")
                col3, col4 = st.columns(2)
                with col3:
                    st.metric("Database Size", f"{metrics['db_size_mb']:.2f}MB")
                with col4:
                    st.metric("Log Files", f"{metrics['log_size_mb']:.2f}MB")
        
        with tab2:
            error_summary = self.get_error_summary(hours=48)
            
            if 'error' in error_summary:
                st.error(f"Failed to get error summary: {error_summary['error']}")
            else:
                # Error counts
                if error_summary['error_counts']:
                    st.subheader("Error Distribution (48h)")
                    for level, count in error_summary['error_counts'].items():
                        color = "🔥" if level == 'CRITICAL' else "❌" if level == 'ERROR' else "⚠️"
                        st.write(f"{color} **{level}**: {count}")
                else:
                    st.success("✅ No errors in the last 48 hours")
                
                # Critical errors
                if error_summary['critical_errors']:
                    st.subheader("Recent Critical Errors")
                    for message, timestamp in error_summary['critical_errors']:
                        st.error(f"**{timestamp}**: {message}")
                
                # Error patterns
                if error_summary['active_patterns'] > 0:
                    st.warning(f"⚠️ **{error_summary['active_patterns']} active error patterns** detected")
                    st.write("Recurring issues that need attention")
                else:
                    st.success("✅ No recurring error patterns detected")
        
        with tab3:
            activity = self.get_user_activity_stats(hours=48)
            
            if 'error' in activity:
                st.error(f"Failed to get activity stats: {activity['error']}")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Active Users (48h)", activity['active_users'])
                    st.metric("Total Actions", activity['total_actions'])
                
                with col2:
                    if activity['top_actions']:
                        st.subheader("Top User Actions")
                        for action, count in activity['top_actions'].items():
                            st.write(f"• **{action}**: {count}")
                    else:
                        st.info("No user activity recorded")
        
        with tab4:
            # Database health checks
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Table sizes
                tables = ['system_logs', 'user_actions', 'sync_logs', 'error_patterns']
                st.subheader("Database Tables")
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        st.write(f"**{table}**: {count:,} records")
                    except Exception as e:
                        st.error(f"**{table}**: Error - {str(e)}")
                
                # Recent activity
                cursor.execute('''
                    SELECT COUNT(*) FROM system_logs 
                    WHERE timestamp > datetime('now', '-1 hour')
                ''')
                recent_logs = cursor.fetchone()[0]
                
                st.subheader("Database Activity")
                st.metric("Log Entries (Last Hour)", recent_logs)
                
                if recent_logs > 1000:
                    st.warning("⚠️ High logging activity - consider log rotation")
                elif recent_logs > 0:
                    st.success("✅ Normal logging activity")
                else:
                    st.info("ℹ️ No recent log activity")
                
                conn.close()
                
            except Exception as e:
                st.error(f"Database health check failed: {str(e)}")

# Global instance
system_monitor = SystemStatusMonitor()
