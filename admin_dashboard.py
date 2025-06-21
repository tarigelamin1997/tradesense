import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import psutil
import os
from auth import AuthManager, require_auth
import logging

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Comprehensive admin dashboard for TradeSense."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()

    def render_dashboard(self):
        """Render the admin dashboard."""
        current_user = self.auth_manager.get_current_user()
        if not current_user or current_user.get('role') != 'admin':
            st.error("🚫 Admin access required")
            return

        st.title("🛠️ TradeSense Admin Dashboard")
        st.markdown("---")

        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "👥 Users", "🏢 Partners", "📈 Analytics", "⚙️ System"
        ])

        with tab1:
            self._render_overview()
        with tab2:
            self._render_user_management()
        with tab3:
            self._render_partner_management()
        with tab4:
            self._render_analytics_dashboard()
        with tab5:
            self._render_system_monitoring()

    def _render_overview(self):
        """Render overview metrics."""
        st.header("📊 System Overview")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_users = self._get_total_users()
            st.metric("Total Users", total_users)

        with col2:
            active_users = self._get_active_users()
            st.metric("Active Users (30d)", active_users)

        with col3:
            total_partners = self._get_total_partners()
            st.metric("Partners", total_partners)

        with col4:
            system_health = self._get_system_health()
            st.metric("System Health", f"{system_health}%")

        # Recent activity
        st.subheader("📈 Recent Activity")
        activity_data = self._get_recent_activity()
        if not activity_data.empty:
            fig = px.line(activity_data, x='date', y='users', title='Daily Active Users')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data available")

    def _render_user_management(self):
        """Render user management interface."""
        st.header("👥 User Management")

        # User search
        search_term = st.text_input("🔍 Search users", placeholder="Username or email")

        # User list
        users_df = self._get_users_dataframe(search_term)
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)

            # User actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📤 Export Users"):
                    csv = users_df.to_csv(index=False)
                    st.download_button("Download CSV", csv, "users.csv", "text/csv")

            with col2:
                if st.button("📧 Send Announcement"):
                    self._render_announcement_form()

            with col3:
                if st.button("🔧 Bulk Actions"):
                    self._render_bulk_actions()
        else:
            st.info("No users found")

    def _render_partner_management(self):
        """Render partner management interface."""
        st.header("🏢 Partner Management")

        # Create new partner
        with st.expander("➕ Create New Partner"):
            with st.form("new_partner_form"):
                partner_name = st.text_input("Partner Name")
                partner_type = st.selectbox("Partner Type", ["Enterprise", "Reseller", "Affiliate"])
                revenue_share = st.number_input("Revenue Share (%)", 0.0, 50.0, 10.0)

                if st.form_submit_button("Create Partner"):
                    result = self.auth_manager.create_partner(
                        partner_name, 
                        partner_type.lower(),
                        {"revenue_share": revenue_share}
                    )
                    if result["success"]:
                        st.success(f"Partner created! API Key: {result['api_key']}")
                    else:
                        st.error(result["message"])

        # Partners list
        partners_df = self._get_partners_dataframe()
        if not partners_df.empty:
            st.dataframe(partners_df, use_container_width=True)
        else:
            st.info("No partners found")

    def _render_analytics_dashboard(self):
        """Render analytics dashboard."""
        st.header("📈 Platform Analytics")

        # Usage metrics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Usage Metrics")
            usage_data = self._get_usage_metrics()
            if usage_data:
                fig = px.bar(
                    x=list(usage_data.keys()), 
                    y=list(usage_data.values()),
                    title="Feature Usage"
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("💰 Revenue Metrics")
            revenue_data = self._get_revenue_metrics()
            if revenue_data:
                fig = px.pie(
                    values=list(revenue_data.values()),
                    names=list(revenue_data.keys()),
                    title="Revenue by Source"
                )
                st.plotly_chart(fig, use_container_width=True)

    def _render_system_monitoring(self):
        """Render system monitoring dashboard."""
        st.header("⚙️ System Monitoring")

        # System resources
        col1, col2, col3 = st.columns(3)

        with col1:
            cpu_usage = psutil.cpu_percent()
            st.metric("CPU Usage", f"{cpu_usage}%")

        with col2:
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent}%")

        with col3:
            disk = psutil.disk_usage('/')
            st.metric("Disk Usage", f"{(disk.used/disk.total)*100:.1f}%")

        # Application health
        st.subheader("🏥 Application Health")
        health_checks = self._run_health_checks()

        for check, status in health_checks.items():
            if status:
                st.success(f"✅ {check}")
            else:
                st.error(f"❌ {check}")

        # Error logs
        st.subheader("📋 Recent Errors")
        error_logs = self._get_recent_errors()
        if error_logs:
            st.dataframe(error_logs, use_container_width=True)
        else:
            st.success("No recent errors")

    def _get_total_users(self) -> int:
        """Get total user count."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _get_active_users(self) -> int:
        """Get active user count (last 30 days)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE last_login > ?", 
                (thirty_days_ago,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _get_total_partners(self) -> int:
        """Get total partner count."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM partners")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _get_system_health(self) -> int:
        """Calculate system health score."""
        checks = self._run_health_checks()
        if not checks:
            return 0

        healthy = sum(1 for status in checks.values() if status)
        return int((healthy / len(checks)) * 100)

    def _get_recent_activity(self) -> pd.DataFrame:
        """Get recent activity data."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT DATE(last_login) as date, COUNT(DISTINCT id) as users
                FROM users 
                WHERE last_login > datetime('now', '-30 days')
                GROUP BY DATE(last_login)
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()

    def _get_users_dataframe(self, search_term: str = "") -> pd.DataFrame:
        """Get users dataframe with search."""
        try:
            conn = sqlite3.connect(self.db_path)

            if search_term:
                query = """
                    SELECT username, email, role, created_at, last_login, is_active
                    FROM users 
                    WHERE username LIKE ? OR email LIKE ?
                    ORDER BY created_at DESC
                """
                df = pd.read_sql_query(query, conn, params=[f"%{search_term}%", f"%{search_term}%"])
            else:
                query = """
                    SELECT username, email, role, created_at, last_login, is_active
                    FROM users 
                    ORDER BY created_at DESC
                """
                df = pd.read_sql_query(query, conn)

            conn.close()
            return df
        except:
            return pd.DataFrame()

    def _get_partners_dataframe(self) -> pd.DataFrame:
        """Get partners dataframe."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT name, type, created_at, is_active, billing_plan FROM partners ORDER BY created_at DESC"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()

    def _get_usage_metrics(self) -> Dict:
        """Get platform usage metrics."""
        # Placeholder - implement based on your analytics tracking
        return {
            "Data Uploads": 150,
            "Analytics Runs": 300,
            "Reports Generated": 80,
            "API Calls": 1200
        }

    def _get_revenue_metrics(self) -> Dict:
        """Get revenue metrics."""
        # Placeholder - implement based on your billing system
        return {
            "Subscriptions": 5000,
            "Partner Revenue": 2000,
            "Affiliate Commissions": 800
        }

    def _run_health_checks(self) -> Dict[str, bool]:
        """Run application health checks."""
        checks = {}

        # Database connectivity
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT 1")
            conn.close()
            checks["Database Connection"] = True
        except:
            checks["Database Connection"] = False

        # File system access
        try:
            test_file = "health_check.tmp"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            checks["File System"] = True
        except:
            checks["File System"] = False

        # Memory usage
        memory = psutil.virtual_memory()
        checks["Memory Available"] = memory.percent < 90

        # CPU usage
        cpu_usage = psutil.cpu_percent()
        checks["CPU Available"] = cpu_usage < 90

        return checks

    def _get_recent_errors(self) -> pd.DataFrame:
        """Get recent error logs."""
        try:
            log_file = "logs/tradesense_errors.log"
            if os.path.exists(log_file):
                # Read last 50 lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]

                errors = []
                for line in lines:
                    if "ERROR" in line:
                        parts = line.split(" - ", 3)
                        if len(parts) >= 3:
                            errors.append({
                                "timestamp": parts[0],
                                "level": "ERROR",
                                "message": parts[-1].strip()
                            })

                return pd.DataFrame(errors)
        except:
            pass

        return pd.DataFrame()

    def _render_announcement_form(self):
        """Render announcement form."""
        with st.form("announcement_form"):
            st.subheader("📧 Send Announcement")
            subject = st.text_input("Subject")
            message = st.text_area("Message", height=100)
            target = st.selectbox("Target", ["All Users", "Active Users", "Partners"])

            if st.form_submit_button("Send Announcement"):
                # Placeholder for email sending logic
                st.success(f"Announcement sent to {target}")

    def _render_bulk_actions(self):
        """Render bulk actions interface."""
        st.subheader("🔧 Bulk Actions")

        action = st.selectbox("Action", [
            "Activate Users", 
            "Deactivate Users", 
            "Reset Passwords",
            "Update Roles"
        ])

        if st.button("Execute Bulk Action"):
            st.warning("⚠️ Bulk action would be executed here")

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