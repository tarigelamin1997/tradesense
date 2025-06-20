import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from auth import AuthManager, require_auth
import psutil
import logging

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Internal admin dashboard for monitoring system health and usage."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()

    def render_dashboard(self):
        """Render the complete admin dashboard."""
        current_user = self.auth_manager.get_current_user()

        if not current_user or current_user.get('role') != 'admin':
            st.error("🚫 Admin access required")
            return

        st.title("🛠️ TradeSense Admin Dashboard")
        st.markdown("---")

        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 System Overview",
            "👥 User Management", 
            "🏢 Partner Management",
            "📈 Analytics",
            "⚙️ System Health"
        ])

        with tab1:
            self._render_system_overview()

        with tab2:
            self._render_user_management()

        with tab3:
            self._render_partner_management()

        with tab4:
            self._render_analytics_dashboard()

        with tab5:
            self._render_system_health()

    def _render_system_overview(self):
        """Render system overview metrics."""
        st.subheader("📊 System Overview")

        # Get basic stats
        stats = self._get_system_stats()

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Users", stats.get('total_users', 0))

        with col2:
            st.metric("Active Partners", stats.get('active_partners', 0))

        with col3:
            st.metric("Daily Active Users", stats.get('daily_active_users', 0))

        with col4:
            st.metric("System Uptime", self._get_system_uptime())

        # Usage trends
        st.subheader("📈 Usage Trends")
        usage_data = self._get_usage_trends()

        if not usage_data.empty:
            fig = px.line(usage_data, x='date', y='active_users', 
                         title="Daily Active Users")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No usage data available")

    def _render_user_management(self):
        """Render user management interface."""
        st.subheader("👥 User Management")

        # User search and filters
        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input("Search Users", placeholder="Username or email...")

        with col2:
            role_filter = st.selectbox("Filter by Role", ["All", "user", "admin", "partner"])

        with col3:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])

        # Get and display users
        users = self._get_users(search_term, role_filter, status_filter)

        if not users.empty:
            # Display users in a table with action buttons
            for idx, user in users.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

                    with col1:
                        st.write(f"**{user['username']}**")
                        st.write(user['email'])

                    with col2:
                        st.write(f"Role: {user['role']}")
                        st.write(f"Partner: {user['partner_id'] or 'None'}")

                    with col3:
                        status = "🟢 Active" if user['is_active'] else "🔴 Inactive"
                        st.write(status)

                    with col4:
                        if st.button("✏️ Edit", key=f"edit_user_{user['id']}"):
                            self._edit_user_modal(user)

                    with col5:
                        action = "Deactivate" if user['is_active'] else "Activate"
                        if st.button(f"🔄 {action}", key=f"toggle_user_{user['id']}"):
                            self._toggle_user_status(user['id'], not user['is_active'])
                            st.rerun()

                st.markdown("---")
        else:
            st.info("No users found")

    def _render_partner_management(self):
        """Render partner management interface."""
        st.subheader("🏢 Partner Management")

        # Add new partner
        with st.expander("➕ Add New Partner"):
            with st.form("add_partner"):
                partner_name = st.text_input("Partner Name")
                partner_type = st.selectbox("Partner Type", ["broker", "prop_firm", "trading_group"])
                revenue_share = st.slider("Revenue Share %", 0.0, 50.0, 10.0)

                if st.form_submit_button("Create Partner"):
                    settings = {"revenue_share": revenue_share}
                    result = self.auth_manager.create_partner(partner_name, partner_type, settings)

                    if result["success"]:
                        st.success(f"Partner created! API Key: {result['api_key']}")
                    else:
                        st.error("Failed to create partner")

        # Display existing partners
        partners = self._get_partners()

        if not partners.empty:
            st.dataframe(partners, use_container_width=True)
        else:
            st.info("No partners found")

    def _render_analytics_dashboard(self):
        """Render analytics dashboard."""
        st.subheader("📈 Platform Analytics")

        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())

        # Analytics data
        analytics_data = self._get_analytics_data(start_date, end_date)

        # Display charts
        if analytics_data:
            # User activity chart
            if 'user_activity' in analytics_data:
                fig = px.bar(analytics_data['user_activity'], 
                           x='date', y='count', 
                           title="User Activity Over Time")
                st.plotly_chart(fig, use_container_width=True)

            # Partner performance
            if 'partner_performance' in analytics_data:
                fig = px.pie(analytics_data['partner_performance'],
                           values='users', names='partner_name',
                           title="Users by Partner")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analytics data available for selected period")

    def _render_system_health(self):
        """Render system health monitoring."""
        st.subheader("⚙️ System Health")

        # System metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            cpu_usage = psutil.cpu_percent()
            st.metric("CPU Usage", f"{cpu_usage}%")

            # CPU usage chart
            if cpu_usage > 80:
                st.error("High CPU usage detected!")
            elif cpu_usage > 60:
                st.warning("Moderate CPU usage")
            else:
                st.success("CPU usage normal")

        with col2:
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            st.metric("Memory Usage", f"{memory_usage}%")

            if memory_usage > 80:
                st.error("High memory usage detected!")
            elif memory_usage > 60:
                st.warning("Moderate memory usage")
            else:
                st.success("Memory usage normal")

        with col3:
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            st.metric("Disk Usage", f"{disk_usage}%")

            if disk_usage > 80:
                st.error("High disk usage detected!")
            elif disk_usage > 60:
                st.warning("Moderate disk usage")
            else:
                st.success("Disk usage normal")

        # Database health
        st.subheader("🗄️ Database Health")
        db_stats = self._get_database_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Database Size", db_stats.get('size', 'Unknown'))
        with col2:
            st.metric("Table Count", db_stats.get('tables', 0))
        with col3:
            st.metric("Total Records", db_stats.get('records', 0))

        # Recent errors
        st.subheader("🚨 Recent Errors")
        recent_errors = self._get_recent_errors()

        if recent_errors:
            for error in recent_errors:
                st.error(f"**{error['timestamp']}**: {error['message']}")
        else:
            st.success("No recent errors!")

    def _get_system_stats(self) -> Dict:
        """Get basic system statistics."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Total users
            total_users = pd.read_sql_query("SELECT COUNT(*) as count FROM users", conn).iloc[0]['count']

            # Active partners
            active_partners = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM partners WHERE is_active = 1", conn
            ).iloc[0]['count']

            # Daily active users (last 24 hours)
            daily_active = pd.read_sql_query('''
                SELECT COUNT(DISTINCT user_id) as count 
                FROM user_sessions 
                WHERE created_at > datetime('now', '-1 day')
            ''', conn).iloc[0]['count']

            conn.close()

            return {
                'total_users': total_users,
                'active_partners': active_partners,
                'daily_active_users': daily_active
            }

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}

    def _get_system_uptime(self) -> str:
        """Get system uptime."""
        try:
            uptime_seconds = psutil.boot_time()
            uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            return f"{days}d {hours}h"
        except Exception:
            return "Unknown"

    def _get_usage_trends(self) -> pd.DataFrame:
        """Get usage trend data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(DISTINCT user_id) as active_users
                FROM user_sessions 
                WHERE created_at > datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            '''

            df = pd.read_sql_query(query, conn)
            conn.close()

            df['date'] = pd.to_datetime(df['date'])
            return df

        except Exception as e:
            logger.error(f"Error getting usage trends: {e}")
            return pd.DataFrame()

    def _get_users(self, search_term: str = "", role_filter: str = "All", status_filter: str = "All") -> pd.DataFrame:
        """Get users with filters."""
        try:
            conn = sqlite3.connect(self.db_path)

            query = "SELECT * FROM users WHERE 1=1"
            params = []

            if search_term:
                query += " AND (username LIKE ? OR email LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])

            if role_filter != "All":
                query += " AND role = ?"
                params.append(role_filter)

            if status_filter != "All":
                is_active = 1 if status_filter == "Active" else 0
                query += " AND is_active = ?"
                params.append(is_active)

            query += " ORDER BY created_at DESC"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            return df

        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return pd.DataFrame()

    def _get_partners(self) -> pd.DataFrame:
        """Get all partners."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM partners ORDER BY created_at DESC", conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error getting partners: {e}")
            return pd.DataFrame()

    def _get_analytics_data(self, start_date, end_date) -> Dict:
        """Get analytics data for date range."""
        try:
            conn = sqlite3.connect(self.db_path)

            # User activity
            user_activity = pd.read_sql_query('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM user_sessions 
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', conn, params=[start_date, end_date])

            # Partner performance
            partner_performance = pd.read_sql_query('''
                SELECT 
                    p.name as partner_name,
                    COUNT(u.id) as users
                FROM partners p
                LEFT JOIN users u ON p.id = u.partner_id
                WHERE p.is_active = 1
                GROUP BY p.id, p.name
            ''', conn)

            conn.close()

            return {
                'user_activity': user_activity,
                'partner_performance': partner_performance
            }

        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {}

    def _get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)

            # Get database size
            cursor = conn.cursor()
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            size_bytes = page_count * page_size
            size_mb = round(size_bytes / 1024 / 1024, 2)

            # Get table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Get total records (approximate)
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM partners")
            partner_count = cursor.fetchone()[0]
            total_records = user_count + partner_count

            conn.close()

            return {
                'size': f"{size_mb} MB",
                'tables': table_count,
                'records': total_records
            }

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def _get_recent_errors(self) -> List[Dict]:
        """Get recent error logs."""
        try:
            # Read from log file if it exists
            import os
            if os.path.exists('logs/errors.log'):
                with open('logs/errors.log', 'r') as f:
                    lines = f.readlines()[-10:]  # Last 10 errors
                    errors = []
                    for line in lines:
                        if 'ERROR' in line:
                            parts = line.split(' - ', 2)
                            if len(parts) >= 3:
                                errors.append({
                                    'timestamp': parts[0],
                                    'message': parts[2].strip()
                                })
                    return errors
            return []
        except Exception:
            return []

    def _toggle_user_status(self, user_id: int, is_active: bool):
        """Toggle user active status."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))
            conn.commit()
            conn.close()

            action = "activated" if is_active else "deactivated"
            st.success(f"User {action} successfully!")

        except Exception as e:
            logger.error(f"Error toggling user status: {e}")
            st.error("Failed to update user status")

def main():
    """Main admin dashboard entry point."""
    admin_dashboard = AdminDashboard()
    admin_dashboard.render_dashboard()

if __name__ == "__main__":
    main()