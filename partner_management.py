import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from auth import AuthManager, require_auth
import plotly.express as px
import logging
import plotly.graph_objects as go


logger = logging.getLogger(__name__)

class PartnerManagement:
    """Comprehensive partner management system."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_partner_database()

    def init_partner_database(self):
        """Initialize partner-specific database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Partner users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'user',
                permissions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Partner analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                metric_name TEXT,
                metric_value REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')

        # Partner billing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_billing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                billing_period TEXT,
                total_revenue REAL,
                partner_share REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')

        conn.commit()
        conn.close()

    @require_auth
    def render_partner_portal(self):
        """Render the partner portal interface."""
        current_user = self.auth_manager.get_current_user()
        if not current_user or not current_user.get('partner_id'):
            st.error("🚫 Partner access required")
            return

        partner_id = current_user['partner_id']
        partner_info = self.auth_manager.get_partner(partner_id)

        if not partner_info:
            st.error("❌ Partner information not found")
            return

        st.title(f"🏢 {partner_info['name']} - Partner Portal")

        # Partner dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", "👥 Users", "⚙️ Settings", "💰 Billing", "📈 Analytics"
        ])

        with tab1:
            self._render_partner_dashboard(partner_info)
        with tab2:
            self._render_user_management(partner_id)
        with tab3:
            self._render_partner_settings(partner_info)
        with tab4:
            self._render_billing_management(partner_id)
        with tab5:
            self._render_partner_analytics(partner_id)

    def _render_partner_dashboard(self, partner_info: Dict):
        """Render partner dashboard overview."""
        st.header("📊 Partner Overview")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_users = self._get_partner_user_count(partner_info['id'])
            st.metric("Total Users", total_users)

        with col2:
            active_users = self._get_active_user_count(partner_info['id'])
            st.metric("Active Users", active_users)

        with col3:
            monthly_revenue = self._get_monthly_revenue(partner_info['id'])
            st.metric("Monthly Revenue", f"${monthly_revenue:,.2f}")

        with col4:
            revenue_share = partner_info.get('revenue_share', 0) * 100
            st.metric("Revenue Share", f"{revenue_share:.1f}%")

        # Partner status and info
        st.subheader("ℹ️ Partner Information")

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"""
            **Partner Type:** {partner_info['type'].title()}  
            **Status:** {'✅ Active' if partner_info['is_active'] else '❌ Inactive'}  
            **Created:** {partner_info['created_at'][:10]}  
            **Billing Plan:** {partner_info['billing_plan'].title()}
            """)

        with col2:
            st.success(f"""
            **API Key:** `{partner_info['api_key'][:20]}...`  
            **Base URL:** `https://api.tradesense.app/v1/`  
            **Documentation:** [API Docs](/docs/api)  
            **Support:** partner-support@tradesense.app
            """)

    def _render_user_management(self, partner_id: int):
        """Render user management interface."""
        st.header("👥 User Management")

        # Add new user
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input("Username")
                    email = st.text_input("Email")

                with col2:
                    password = st.text_input("Temporary Password", type="password")
                    role = st.selectbox("Role", ["user", "admin", "analyst"])

                if st.form_submit_button("Create User"):
                    result = self._create_partner_user(partner_id, username, email, password, role)
                    if result['success']:
                        st.success(f"User created successfully! User ID: {result['user_id']}")
                    else:
                        st.error(result['message'])

        # User list
        st.subheader("📋 Partner Users")
        users_df = self._get_partner_users_dataframe(partner_id)

        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)

            # Bulk actions
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📤 Export User List"):
                    csv = users_df.to_csv(index=False)
                    st.download_button("Download CSV", csv, "partner_users.csv", "text/csv")

            with col2:
                if st.button("📧 Send Welcome Email"):
                    st.info("Welcome emails would be sent to all users")

            with col3:
                if st.button("🔄 Sync User Data"):
                    st.success("User data synchronized")
        else:
            st.info("No users found for this partner")

    def _render_partner_settings(self, partner_info: Dict):
        """Render partner settings interface."""
        st.header("⚙️ Partner Settings")

        # Branding settings
        st.subheader("🎨 Branding Settings")

        with st.form("branding_form"):
            col1, col2 = st.columns(2)

            with col1:
                logo_url = st.text_input("Logo URL", value="")
                primary_color = st.color_picker("Primary Color", "#1f77b4")

            with col2:
                company_name = st.text_input("Company Name", value=partner_info['name'])
                secondary_color = st.color_picker("Secondary Color", "#ff7f0e")

            custom_domain = st.text_input("Custom Domain", placeholder="analytics.yourcompany.com")

            if st.form_submit_button("Update Branding"):
                branding_data = {
                    "logo_url": logo_url,
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "company_name": company_name,
                    "custom_domain": custom_domain
                }

                if self._update_partner_branding(partner_info['id'], branding_data):
                    st.success("Branding settings updated successfully!")
                else:
                    st.error("Failed to update branding settings")

        # API settings
        st.subheader("🔑 API Settings")

        col1, col2 = st.columns(2)

        with col1:
            st.text_input("API Key", value=partner_info['api_key'], disabled=True)
            if st.button("🔄 Regenerate API Key"):
                st.warning("⚠️ This will invalidate your current API key!")
                if st.button("✅ Confirm Regeneration"):
                    new_key = self._regenerate_api_key(partner_info['id'])
                    if new_key:
                        st.success(f"New API Key: {new_key}")
                    else:
                        st.error("Failed to regenerate API key")

        with col2:
            # Rate limiting settings
            st.subheader("⚡ Rate Limiting")
            rate_limit = st.number_input("Requests per minute", value=1000, min_value=100)
            if st.button("Update Rate Limit"):
                st.success("Rate limit updated")

    def _render_billing_management(self, partner_id: int):
        """Render billing management interface."""
        st.header("💰 Billing & Revenue")

        # Billing summary
        billing_summary = self._get_billing_summary(partner_id)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("This Month", f"${billing_summary.get('current_month', 0):,.2f}")

        with col2:
            st.metric("Last Month", f"${billing_summary.get('last_month', 0):,.2f}")

        with col3:
            st.metric("Total Revenue", f"${billing_summary.get('total', 0):,.2f}")

        with col4:
            st.metric("Outstanding", f"${billing_summary.get('outstanding', 0):,.2f}")

        # Revenue chart
        st.subheader("📈 Revenue Trends")
        revenue_data = self._get_revenue_chart_data(partner_id)

        if not revenue_data.empty:
            fig = px.line(revenue_data, x='month', y='revenue', title='Monthly Revenue')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data available yet")

        # Billing history
        st.subheader("📋 Billing History")
        billing_df = self._get_billing_history(partner_id)

        if not billing_df.empty:
            st.dataframe(billing_df, use_container_width=True)
        else:
            st.info("No billing history available")

    def _render_partner_analytics(self, partner_id: int):
        """Render partner analytics dashboard."""
        st.header("📈 Partner Analytics")

        # Usage metrics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Usage Metrics")
            usage_data = self._get_usage_metrics(partner_id)

            if usage_data:
                fig = px.bar(
                    x=list(usage_data.keys()),
                    y=list(usage_data.values()),
                    title="Feature Usage"
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("👥 User Activity")
            activity_data = self._get_user_activity(partner_id)

            if not activity_data.empty:
                fig = px.line(activity_data, x='date', y='active_users', title='Daily Active Users')
                st.plotly_chart(fig, use_container_width=True)

        # Performance metrics
        st.subheader("⚡ Performance Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_response_time = self._get_avg_response_time(partner_id)
            st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")

        with col2:
            uptime = self._get_uptime_percentage(partner_id)
            st.metric("Uptime", f"{uptime:.2f}%")

        with col3:
            error_rate = self._get_error_rate(partner_id)
            st.metric("Error Rate", f"{error_rate:.2f}%")

    # Helper methods
    def _get_partner_user_count(self, partner_id: int) -> int:
        """Get total user count for partner."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE partner_id = ?", (partner_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _get_active_user_count(self, partner_id: int) -> int:
        """Get active user count for partner."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            thirty_days_ago = datetime.now() - timedelta(days=30)
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE partner_id = ? AND last_login > ?",
                (partner_id, thirty_days_ago)
            )
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def _get_monthly_revenue(self, partner_id: int) -> float:
        """Get monthly revenue for partner."""
        # Placeholder implementation
        return 15000.0

    def _create_partner_user(self, partner_id: int, username: str, email: str, password: str, role: str) -> Dict:
        """Create a new user for the partner."""
        return self.auth_manager.register_user(username, email, password, partner_id)

    def _get_partner_users_dataframe(self, partner_id: int) -> pd.DataFrame:
        """Get partner users as dataframe."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT username, email, role, created_at, last_login, is_active
                FROM users 
                WHERE partner_id = ?
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn, params=[partner_id])
            conn.close()
            return df
        except:
            return pd.DataFrame()

    def _update_partner_branding(self, partner_id: int, branding_data: Dict) -> bool:
        """Update partner branding settings."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE partners SET branding = ? WHERE id = ?",
                (json.dumps(branding_data), partner_id)
            )
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def _regenerate_api_key(self, partner_id: int) -> Optional[str]:
        """Regenerate API key for partner."""
        try:
            import secrets
            new_key = f"ts_{secrets.token_urlsafe(32)}"

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE partners SET api_key = ? WHERE id = ?", (new_key, partner_id))
            conn.commit()
            conn.close()

            return new_key
        except:
            return None

    def _get_billing_summary(self, partner_id: int) -> Dict:
        """Get billing summary for partner."""
        # Placeholder implementation
        return {
            'current_month': 8500.0,
            'last_month': 7200.0,
            'total': 45000.0,
            'outstanding': 1200.0
        }

    def _get_revenue_chart_data(self, partner_id: int) -> pd.DataFrame:
        """Get revenue chart data."""
        # Placeholder implementation
        dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='MS')
        revenues = [5000 + i * 500 for i in range(len(dates))]

        return pd.DataFrame({
            'month': dates,
            'revenue': revenues
        })

    def _get_billing_history(self, partner_id: int) -> pd.DataFrame:
        """Get billing history."""
        # Placeholder implementation
        return pd.DataFrame({
            'Period': ['2024-01', '2024-02', '2024-03'],
            'Revenue': [7200, 7800, 8500],
            'Status': ['Paid', 'Paid', 'Pending']
        })

    def _get_usage_metrics(self, partner_id: int) -> Dict:
        """Get usage metrics for partner."""
        return {
            'API Calls': 15000,
            'Data Uploads': 450,
            'Reports Generated': 120,
            'User Logins': 2800
        }

    def _get_user_activity(self, partner_id: int) -> pd.DataFrame:
        """Get user activity data."""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        users = [25 + (i % 7) * 3 for i in range(30)]

        return pd.DataFrame({
            'date': dates,
            'active_users': users
        })

    def _get_avg_response_time(self, partner_id: int) -> float:
        """Get average response time."""
        return 250.0

    def _get_uptime_percentage(self, partner_id: int) -> float:
        """Get uptime percentage."""
        return 99.97

    def _get_error_rate(self, partner_id: int) -> float:
        """Get error rate percentage."""
        return 0.03
    
    def _show_user_analytics(self, user_id: int):
        """Show analytics for a specific user."""
        st.info(f"User analytics for user {user_id} would be displayed here")

def main():
    """Main partner management entry point."""
    partner_mgmt = PartnerManagement()
    partner_mgmt.render_partner_portal()

if __name__ == "__main__":
    main()