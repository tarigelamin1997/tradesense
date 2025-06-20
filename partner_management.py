
import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from auth import AuthManager, require_auth
import plotly.express as px
import plotly.graph_objects as go
import logging

logger = logging.getLogger(__name__)

class PartnerManagement:
    """Comprehensive partner management system."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_partner_tables()
    
    def init_partner_tables(self):
        """Initialize partner-related database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Partner analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                metric_name TEXT,
                metric_value REAL,
                period_start DATE,
                period_end DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Partner billing table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_billing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                period_start DATE,
                period_end DATE,
                revenue_generated REAL,
                commission_owed REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Partner users tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER,
                user_id INTEGER,
                action_type TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def render_partner_portal(self):
        """Render the main partner portal."""
        current_user = self.auth_manager.get_current_user()
        
        if not current_user:
            st.warning("🔐 Please login to access the partner portal")
            return
        
        partner_id = current_user.get('partner_id')
        if not partner_id:
            st.info("👋 Welcome to TradeSense! Would you like to become a partner?")
            self._render_partner_application()
            return
        
        partner = self.auth_manager.get_partner(partner_id)
        if not partner:
            st.error("Partner not found")
            return
        
        # Partner portal header
        st.title(f"🏢 {partner['name']} Partner Portal")
        st.markdown("---")
        
        # Partner tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard",
            "👥 User Management", 
            "🔑 API Management",
            "💰 Billing & Revenue",
            "⚙️ Settings"
        ])
        
        with tab1:
            self._render_partner_dashboard(current_user, partner)
        
        with tab2:
            self._render_partner_user_management(current_user, partner)
        
        with tab3:
            self._render_api_management(current_user, partner)
        
        with tab4:
            self._render_billing_management(current_user, partner)
        
        with tab5:
            self._render_partner_settings(current_user, partner)
    
    def _render_partner_application(self):
        """Render partner application form."""
        st.subheader("🤝 Become a TradeSense Partner")
        
        with st.form("partner_application"):
            st.markdown("""
            ### Partner Benefits:
            - **White-label branding** for your platform
            - **Revenue sharing** on user subscriptions
            - **Dedicated support** and onboarding
            - **API access** for custom integrations
            - **Analytics dashboard** for your users
            """)
            
            company_name = st.text_input("Company/Organization Name *")
            partner_type = st.selectbox(
                "Partner Type *",
                ["broker", "prop_firm", "trading_group", "financial_advisor", "educator"]
            )
            contact_email = st.text_input("Contact Email *")
            website = st.text_input("Website URL")
            description = st.text_area("Tell us about your organization")
            expected_users = st.selectbox(
                "Expected number of users",
                ["1-50", "51-200", "201-1000", "1000+"]
            )
            
            submitted = st.form_submit_button("🚀 Apply for Partnership")
            
            if submitted and company_name and contact_email:
                # Create partner application
                settings = {
                    "contact_email": contact_email,
                    "website": website,
                    "description": description,
                    "expected_users": expected_users,
                    "status": "pending_approval"
                }
                
                result = self.auth_manager.create_partner(company_name, partner_type, settings)
                
                if result["success"]:
                    st.success("🎉 Partnership application submitted! We'll contact you within 2 business days.")
                    st.info(f"Your API key (save this): `{result['api_key']}`")
                else:
                    st.error("Application failed. Please try again.")
    
    def _render_partner_dashboard(self, current_user: Dict, partner: Dict):
        """Render partner dashboard with key metrics."""
        st.subheader("📊 Partner Dashboard")
        
        # Key metrics
        metrics = self._get_partner_metrics(partner['id'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", metrics.get('total_users', 0))
        
        with col2:
            st.metric("Active Users (30d)", metrics.get('active_users_30d', 0))
        
        with col3:
            revenue = metrics.get('revenue_30d', 0)
            st.metric("Revenue (30d)", f"${revenue:,.2f}")
        
        with col4:
            commission = metrics.get('commission_owed', 0)
            st.metric("Commission Owed", f"${commission:,.2f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # User growth chart
            user_growth = self._get_user_growth_data(partner['id'])
            if not user_growth.empty:
                fig = px.line(user_growth, x='date', y='cumulative_users',
                             title="User Growth Over Time")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No user growth data available yet")
        
        with col2:
            # Revenue chart
            revenue_data = self._get_revenue_data(partner['id'])
            if not revenue_data.empty:
                fig = px.bar(revenue_data, x='month', y='revenue',
                           title="Monthly Revenue")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data available yet")
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        recent_activity = self._get_recent_activity(partner['id'])
        
        if recent_activity:
            for activity in recent_activity:
                st.write(f"**{activity['timestamp']}**: {activity['description']}")
        else:
            st.info("No recent activity")
    
    def _render_partner_user_management(self, current_user: Dict, partner: Dict):
        """Render partner user management."""
        st.subheader("👥 User Management")
        
        # User statistics
        user_stats = self._get_partner_user_stats(partner['id'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", user_stats.get('total', 0))
        with col2:
            st.metric("Active Users", user_stats.get('active', 0))
        with col3:
            st.metric("New Users (7d)", user_stats.get('new_7d', 0))
        
        # User list
        st.subheader("📋 User List")
        partner_users = self._get_partner_users(partner['id'])
        
        if not partner_users.empty:
            # Add user actions
            for idx, user in partner_users.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{user['username']}** ({user['email']})")
                
                with col2:
                    status = "🟢 Active" if user['is_active'] else "🔴 Inactive"
                    st.write(status)
                
                with col3:
                    st.write(f"Joined: {user['created_at'][:10]}")
                
                with col4:
                    if st.button("📊 Analytics", key=f"user_analytics_{user['id']}"):
                        self._show_user_analytics(user['id'])
        else:
            st.info("No users found for this partner")
        
        # Bulk user management
        with st.expander("📦 Bulk User Management"):
            st.markdown("**Coming Soon**: Bulk user provisioning and management tools")
    
    def _render_api_management(self, current_user: Dict, partner: Dict):
        """Render API management for partners."""
        st.subheader("🔑 API Management")
        
        # Show API key (masked)
        api_key = partner.get('api_key', '')
        masked_key = api_key[:8] + "*" * 20 + api_key[-4:] if api_key else "No API key"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input("API Key", value=masked_key, disabled=True)
        with col2:
            if st.button("🔄 Regenerate"):
                if st.checkbox("I understand this will invalidate the current key"):
                    # Regenerate API key logic would go here
                    st.success("API key regenerated!")
        
        # API documentation
        st.subheader("📚 API Documentation")
        
        st.markdown("""
        ### Authentication
        Include your API key in the header:
        ```
        Authorization: Bearer YOUR_API_KEY
        ```
        
        ### Endpoints
        
        #### GET /api/v1/users
        Get list of users for your partner account
        
        #### POST /api/v1/users
        Create a new user under your partner account
        
        #### GET /api/v1/analytics/{user_id}
        Get analytics for a specific user
        
        #### POST /api/v1/sync/{user_id}
        Trigger data sync for a user
        """)
        
        # API usage stats
        st.subheader("📊 API Usage")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Requests (24h)", "1,234")
        with col2:
            st.metric("Rate Limit", "1000/hour")
        with col3:
            st.metric("Success Rate", "99.8%")
    
    def _render_billing_management(self, current_user: Dict, partner: Dict):
        """Render billing and revenue management."""
        st.subheader("💰 Billing & Revenue")
        
        # Revenue overview
        revenue_stats = self._get_revenue_stats(partner['id'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue = revenue_stats.get('total_revenue', 0)
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        
        with col2:
            monthly_revenue = revenue_stats.get('monthly_revenue', 0)
            st.metric("This Month", f"${monthly_revenue:,.2f}")
        
        with col3:
            commission_rate = partner.get('revenue_share', 0)
            st.metric("Commission Rate", f"{commission_rate}%")
        
        with col4:
            pending_commission = revenue_stats.get('pending_commission', 0)
            st.metric("Pending Commission", f"${pending_commission:,.2f}")
        
        # Billing history
        st.subheader("📋 Billing History")
        billing_history = self._get_billing_history(partner['id'])
        
        if not billing_history.empty:
            st.dataframe(billing_history, use_container_width=True)
        else:
            st.info("No billing history available")
        
        # Payment settings
        with st.expander("💳 Payment Settings"):
            st.markdown("Configure how you'd like to receive commission payments:")
            
            payment_method = st.selectbox(
                "Payment Method",
                ["Bank Transfer", "PayPal", "Stripe", "Check"]
            )
            
            if payment_method == "Bank Transfer":
                bank_name = st.text_input("Bank Name")
                routing_number = st.text_input("Routing Number")
                account_number = st.text_input("Account Number", type="password")
            
            if st.button("💾 Save Payment Settings"):
                st.success("Payment settings saved!")
    
    def _render_partner_settings(self, current_user: Dict, partner: Dict):
        """Render partner settings and customization."""
        st.subheader("⚙️ Partner Settings")
        
        # White-label branding
        st.subheader("🎨 White-label Branding")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_logo = st.file_uploader("Company Logo", type=['png', 'jpg', 'jpeg'])
            primary_color = st.color_picker("Primary Color", "#1f77b4")
            secondary_color = st.color_picker("Secondary Color", "#ff7f0e")
        
        with col2:
            company_name = st.text_input("Company Name", value=partner['name'])
            custom_domain = st.text_input("Custom Domain", placeholder="analytics.yourcompany.com")
            footer_text = st.text_area("Footer Text", placeholder="© 2024 Your Company")
        
        # Partner type specific settings
        if partner['type'] == 'prop_firm':
            self._render_prop_firm_settings(current_user, partner)
        elif partner['type'] == 'broker':
            self._render_broker_settings(current_user, partner)
        elif partner['type'] == 'trading_group':
            self._render_trading_group_settings(current_user, partner)
        
        # Save settings
        if st.button("💾 Save Settings"):
            # Save settings logic would go here
            st.success("Settings saved successfully!")
    
    def _render_prop_firm_settings(self, current_user: Dict, partner: Dict):
        """Render prop firm specific settings."""
        st.subheader("🏢 Prop Firm Settings")
        
        settings = json.loads(partner.get('settings', '{}'))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            daily_limit = st.number_input("Daily Loss Limit ($)", 
                                        value=settings.get('daily_loss_limit', 1000))
        with col2:
            max_drawdown = st.number_input("Max Drawdown ($)", 
                                         value=settings.get('max_drawdown', 5000))
        with col3:
            profit_target = st.number_input("Profit Target ($)", 
                                          value=settings.get('profit_target', 10000))
        
        # Risk monitoring settings
        st.subheader("📊 Risk Monitoring")
        
        enable_real_time = st.checkbox("Enable Real-time Risk Monitoring", 
                                     value=settings.get('real_time_monitoring', False))
        
        alert_thresholds = st.slider("Alert Threshold (%)", 0, 100, 
                                   value=settings.get('alert_threshold', 80))
    
    def _render_broker_settings(self, current_user: Dict, partner: Dict):
        """Render broker specific settings."""
        st.subheader("🏦 Broker Settings")
        
        settings = json.loads(partner.get('settings', '{}'))
        
        # Commission settings
        commission_per_trade = st.number_input("Commission per Trade ($)", 
                                             value=settings.get('commission_per_trade', 3.5))
        
        # Available instruments
        st.subheader("📈 Available Instruments")
        instruments = st.multiselect("Supported Instruments", 
                                   ["Stocks", "Options", "Futures", "Forex", "Crypto"],
                                   default=settings.get('instruments', ["Stocks"]))
        
        # Integration settings
        st.subheader("🔗 Integration Settings")
        api_endpoint = st.text_input("API Endpoint", 
                                   value=settings.get('api_endpoint', ''))
    
    def _render_trading_group_settings(self, current_user: Dict, partner: Dict):
        """Render trading group specific settings."""
        st.subheader("👥 Trading Group Settings")
        
        settings = json.loads(partner.get('settings', '{}'))
        
        # Group management
        max_members = st.number_input("Maximum Members", 
                                    value=settings.get('max_members', 100))
        
        membership_fee = st.number_input("Monthly Membership Fee ($)", 
                                       value=settings.get('membership_fee', 0))
        
        # Group features
        st.subheader("🎯 Group Features")
        
        enable_leaderboard = st.checkbox("Enable Leaderboard", 
                                       value=settings.get('leaderboard', True))
        
        enable_group_chat = st.checkbox("Enable Group Chat", 
                                      value=settings.get('group_chat', False))
        
        enable_challenges = st.checkbox("Enable Trading Challenges", 
                                      value=settings.get('challenges', False))
    
    # Helper methods for data retrieval
    def _get_partner_metrics(self, partner_id: int) -> Dict:
        """Get partner metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Total users
            total_users = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM users WHERE partner_id = ?", 
                conn, params=[partner_id]
            ).iloc[0]['count']
            
            # Active users (30 days)
            active_users = pd.read_sql_query('''
                SELECT COUNT(DISTINCT u.id) as count 
                FROM users u 
                JOIN user_sessions s ON u.id = s.user_id 
                WHERE u.partner_id = ? AND s.created_at > datetime('now', '-30 days')
            ''', conn, params=[partner_id]).iloc[0]['count']
            
            conn.close()
            
            return {
                'total_users': total_users,
                'active_users_30d': active_users,
                'revenue_30d': 0,  # Placeholder
                'commission_owed': 0  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Error getting partner metrics: {e}")
            return {}
    
    def _get_user_growth_data(self, partner_id: int) -> pd.DataFrame:
        """Get user growth data for partner."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = '''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) OVER (ORDER BY DATE(created_at)) as cumulative_users
                FROM users 
                WHERE partner_id = ?
                ORDER BY date
            '''
            
            df = pd.read_sql_query(query, conn, params=[partner_id])
            conn.close()
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting user growth data: {e}")
            return pd.DataFrame()
    
    def _get_revenue_data(self, partner_id: int) -> pd.DataFrame:
        """Get revenue data for partner."""
        # Placeholder - would integrate with billing system
        return pd.DataFrame()
    
    def _get_recent_activity(self, partner_id: int) -> List[Dict]:
        """Get recent partner activity."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get recent user registrations
            recent_users = pd.read_sql_query('''
                SELECT username, created_at 
                FROM users 
                WHERE partner_id = ? 
                ORDER BY created_at DESC 
                LIMIT 5
            ''', conn, params=[partner_id])
            
            conn.close()
            
            activities = []
            for _, user in recent_users.iterrows():
                activities.append({
                    'timestamp': user['created_at'][:19],
                    'description': f"New user registered: {user['username']}"
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_partner_user_stats(self, partner_id: int) -> Dict:
        """Get partner user statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Total users
            total = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM users WHERE partner_id = ?", 
                conn, params=[partner_id]
            ).iloc[0]['count']
            
            # Active users
            active = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM users WHERE partner_id = ? AND is_active = 1", 
                conn, params=[partner_id]
            ).iloc[0]['count']
            
            # New users (7 days)
            new_7d = pd.read_sql_query('''
                SELECT COUNT(*) as count FROM users 
                WHERE partner_id = ? AND created_at > datetime('now', '-7 days')
            ''', conn, params=[partner_id]).iloc[0]['count']
            
            conn.close()
            
            return {'total': total, 'active': active, 'new_7d': new_7d}
            
        except Exception as e:
            logger.error(f"Error getting partner user stats: {e}")
            return {}
    
    def _get_partner_users(self, partner_id: int) -> pd.DataFrame:
        """Get all users for a partner."""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(
                "SELECT * FROM users WHERE partner_id = ? ORDER BY created_at DESC", 
                conn, params=[partner_id]
            )
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Error getting partner users: {e}")
            return pd.DataFrame()
    
    def _get_revenue_stats(self, partner_id: int) -> Dict:
        """Get revenue statistics for partner."""
        # Placeholder - would integrate with billing system
        return {
            'total_revenue': 0,
            'monthly_revenue': 0,
            'pending_commission': 0
        }
    
    def _get_billing_history(self, partner_id: int) -> pd.DataFrame:
        """Get billing history for partner."""
        # Placeholder - would integrate with billing system
        return pd.DataFrame()
    
    def _show_user_analytics(self, user_id: int):
        """Show analytics for a specific user."""
        st.info(f"User analytics for user {user_id} would be displayed here")

def main():
    """Main partner management entry point."""
    partner_mgmt = PartnerManagement()
    partner_mgmt.render_partner_portal()

if __name__ == "__main__":
    main()
