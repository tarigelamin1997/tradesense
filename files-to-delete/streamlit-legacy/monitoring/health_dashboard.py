
import streamlit as st
import psutil
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

class SystemHealthMonitor:
    def __init__(self):
        self.db_path = "backend/tradesense.db"
    
    def render_health_dashboard(self):
        st.title("🔍 TradeSense System Health Dashboard")
        
        # System metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_percent = psutil.cpu_percent(interval=1)
            st.metric("CPU Usage", f"{cpu_percent}%", delta=None)
        
        with col2:
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent}%", delta=None)
        
        with col3:
            disk = psutil.disk_usage('/')
            st.metric("Disk Usage", f"{disk.percent}%", delta=None)
        
        with col4:
            # Database size
            try:
                import os
                db_size = os.path.getsize(self.db_path) / (1024*1024)  # MB
                st.metric("Database Size", f"{db_size:.1f} MB", delta=None)
            except:
                st.metric("Database Size", "N/A", delta=None)
        
        # Performance metrics
        st.subheader("📊 Performance Metrics")
        
        # Database performance
        self._render_db_performance()
        
        # User activity
        self._render_user_activity()
        
        # Error tracking
        self._render_error_tracking()
    
    def _render_db_performance(self):
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Query performance stats
            queries = [
                ("Total Users", "SELECT COUNT(*) FROM users"),
                ("Total Trades", "SELECT COUNT(*) FROM trades"),
                ("Total Playbooks", "SELECT COUNT(*) FROM playbooks"),
                ("Active Sessions", "SELECT COUNT(*) FROM users WHERE last_login > datetime('now', '-1 hour')")
            ]
            
            metrics = []
            for name, query in queries:
                try:
                    result = pd.read_sql_query(query, conn)
                    metrics.append({"Metric": name, "Value": result.iloc[0, 0]})
                except Exception as e:
                    metrics.append({"Metric": name, "Value": f"Error: {str(e)}"})
            
            st.dataframe(pd.DataFrame(metrics), use_container_width=True)
            conn.close()
            
        except Exception as e:
            st.error(f"Database connection error: {str(e)}")
    
    def _render_user_activity(self):
        try:
            conn = sqlite3.connect(self.db_path)
            
            # User activity over time
            activity_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as trade_count
            FROM trades 
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            
            df = pd.read_sql_query(activity_query, conn)
            if not df.empty:
                fig = px.line(df, x='date', y='trade_count', title='Daily Trade Activity (Last 30 Days)')
                st.plotly_chart(fig, use_container_width=True)
            
            conn.close()
            
        except Exception as e:
            st.error(f"Activity tracking error: {str(e)}")
    
    def _render_error_tracking(self):
        st.subheader("⚠️ Error Tracking")
        
        try:
            # Read error logs
            log_files = [
                "backend/logs/tradesense_errors.log",
                "logs/errors.log"
            ]
            
            recent_errors = []
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()[-50:]  # Last 50 lines
                        recent_errors.extend(lines)
                except FileNotFoundError:
                    continue
            
            if recent_errors:
                st.text_area("Recent Errors", "\n".join(recent_errors[-10:]), height=200)
            else:
                st.success("No recent errors found!")
                
        except Exception as e:
            st.error(f"Error log reading failed: {str(e)}")

def main():
    monitor = SystemHealthMonitor()
    monitor.render_health_dashboard()

if __name__ == "__main__":
    main()
