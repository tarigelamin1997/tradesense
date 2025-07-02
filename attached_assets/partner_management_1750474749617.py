
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from auth import AuthManager, require_auth, check_partner_access
from credential_manager import render_credential_management_ui

class PartnerManager:
    """Manages partner integrations and user access."""
    
    def __init__(self):
        self.auth_manager = AuthManager()
    
    def render_partner_dashboard(self, current_user: Dict):
        """Render partner-specific dashboard."""
        partner_id = current_user.get('partner_id')
        
        if not partner_id:
            self.render_individual_dashboard(current_user)
        else:
            partner = self.auth_manager.db.get_partner(partner_id)
            if partner:
                self.render_partner_specific_dashboard(current_user, partner)
            else:
                st.error("Partner not found")
    
    def render_individual_dashboard(self, current_user: Dict):
        """Render dashboard for individual users."""
        st.subheader(f"Welcome, {current_user['first_name']}!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Account Type", "Individual")
        with col2:
            st.metric("Subscription", current_user['subscription_tier'].title())
        with col3:
            if current_user['subscription_tier'] == 'free':
                if st.button("🚀 Upgrade to Pro", type="primary"):
                    self.show_upgrade_modal()
    
    def render_partner_specific_dashboard(self, current_user: Dict, partner: Dict):
        """Render dashboard for partner users."""
        st.subheader(f"Welcome to {partner['name']}")
        st.caption(f"Partner: {partner['type'].title()} • Role: {current_user['partner_role'].title()}")
        
        # Partner-specific branding
        partner_settings = partner.get('settings', {})
        
        if partner_settings.get('custom_logo'):
            st.image(partner_settings['custom_logo'], width=200)
        
        # Partner-specific features
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Partner", partner['name'])
        with col2:
            st.metric("Account Type", partner['type'].title())
        with col3:
            st.metric("Your Role", current_user['partner_role'].title())
        
        # Partner-specific analytics and features
        if partner['type'] == 'broker':
            self.render_broker_features(current_user, partner)
        elif partner['type'] == 'prop_firm':
            self.render_prop_firm_features(current_user, partner)
        elif partner['type'] == 'trading_group':
            self.render_trading_group_features(current_user, partner)
    
    def render_broker_features(self, current_user: Dict, partner: Dict):
        """Render broker-specific features."""
        st.subheader("🏦 Broker Dashboard")
        
        # Broker-specific metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Commission Rate", f"{partner['settings'].get('commission_rate', 3.5)}")
        with col2:
            st.metric("Platform", partner['settings'].get('platform', 'Custom'))
        with col3:
            st.metric("Account Status", "Active")
        
        # Broker-specific trade tagging
        if st.checkbox("Enable Broker Trade Tagging"):
            st.info("All trades will be automatically tagged with broker information")
    
    def render_prop_firm_features(self, current_user: Dict, partner: Dict):
        """Render prop firm-specific features."""
        st.subheader("🏢 Prop Firm Dashboard")
        
        settings = partner.get('settings', {})
        
        # Prop firm rules and limits
        col1, col2, col3 = st.columns(3)
        with col1:
            daily_limit = settings.get('daily_loss_limit', 1000)
            st.metric("Daily Loss Limit", f"${daily_limit:,.2f}")
        with col2:
            max_drawdown = settings.get('max_drawdown', 5000)
            st.metric("Max Drawdown", f"${max_drawdown:,.2f}")
        with col3:
            profit_target = settings.get('profit_target', 10000)
            st.metric("Profit Target", f"${profit_target:,.2f}")
        
        # Risk monitoring
        st.subheader("📊 Risk Monitoring")
        if st.button("📈 View Risk Dashboard"):
            self.show_risk_dashboard(current_user, partner)
    
    def render_trading_group_features(self, current_user: Dict, partner: Dict):
        """Render trading group-specific features."""
        st.subheader("👥 Trading Group Dashboard")
        
        # Group-specific features
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Group Members", partner['settings'].get('member_count', 1))
        with col2:
            st.metric("Group Performance", "+12.5%")
        
        # Collaboration features
        if st.checkbox("Share Analytics with Group"):
            st.info("Your performance metrics will be shared with group administrators")
    
    def show_upgrade_modal(self):
        """Show subscription upgrade modal."""
        with st.modal("🚀 Upgrade to TradeSense Pro"):
            st.write("**Unlock Premium Features:**")
            st.write("• Unlimited trade imports")
            st.write("• Advanced analytics")
            st.write("• Partner integrations")
            st.write("• Priority support")
            st.write("• Custom reports")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💳 Monthly - $29/mo", type="primary"):
                    st.success("Redirecting to payment...")
            with col2:
                if st.button("💎 Annual - $290/yr", type="secondary"):
                    st.success("Redirecting to payment...")
    
    def show_risk_dashboard(self, current_user: Dict, partner: Dict):
        """Show partner-specific risk dashboard."""
        with st.modal("📊 Risk Dashboard"):
            st.write(f"**Risk Monitoring for {partner['name']}**")
            
            # Sample risk metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Drawdown", "$450", "-2.3%")
            with col2:
                st.metric("Daily P&L", "+$125", "+0.8%")
            with col3:
                st.metric("Risk Score", "3/10", "Low")
            
            # Risk alerts
            st.subheader("🚨 Risk Alerts")
            st.success("✅ All limits within acceptable range")
            st.info("ℹ️ Consider taking profits at +$500 today")
    
    @require_auth
    @check_partner_access('admin')
    def render_partner_admin_panel(self, current_user: Dict):
        """Render partner admin panel."""
        st.subheader("🛠️ Partner Administration")
        
        tabs = st.tabs(["Users", "Settings", "Analytics", "API", "Credentials"])
        
        with tabs[0]:
            self.render_user_management(current_user)
        
        with tabs[1]:
            self.render_partner_settings(current_user)
        
        with tabs[2]:
            self.render_partner_analytics(current_user)
        
        with tabs[3]:
            self.render_api_management(current_user)
        
        with tabs[4]:
            render_credential_management_ui(current_user)
    
    def render_user_management(self, current_user: Dict):
        """Render user management for partner admins."""
        st.subheader("👥 User Management")
        
        # Add new user
        with st.expander("➕ Add New User"):
            with st.form("add_user_form"):
                email = st.text_input("Email")
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                role = st.selectbox("Role", ["user", "admin"])
                
                if st.form_submit_button("Add User"):
                    result = self.auth_manager.db.create_user(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        partner_id=current_user['partner_id']
                    )
                    
                    if result['success']:
                        st.success(f"User {email} added successfully!")
                    else:
                        st.error(f"Error: {result['error']}")
        
        # User list
        st.subheader("Current Users")
        # This would show a list of users from the database
        st.info("User management interface would display partner users here")
    
    def render_partner_settings(self, current_user: Dict):
        """Render partner settings."""
        st.subheader("⚙️ Partner Settings")
        
        partner = self.auth_manager.db.get_partner(current_user['partner_id'])
        if partner:
            settings = partner.get('settings', {})
            
            # Settings form
            with st.form("partner_settings"):
                custom_logo = st.text_input("Custom Logo URL", 
                                          value=settings.get('custom_logo', ''))
                
                if partner['type'] == 'broker':
                    commission_rate = st.number_input("Commission Rate", 
                                                    value=settings.get('commission_rate', 3.5))
                    platform = st.text_input("Trading Platform", 
                                            value=settings.get('platform', ''))
                
                elif partner['type'] == 'prop_firm':
                    daily_loss_limit = st.number_input("Daily Loss Limit", 
                                                     value=settings.get('daily_loss_limit', 1000))
                    max_drawdown = st.number_input("Max Drawdown", 
                                                 value=settings.get('max_drawdown', 5000))
                    profit_target = st.number_input("Profit Target", 
                                                  value=settings.get('profit_target', 10000))
                
                if st.form_submit_button("Save Settings"):
                    st.success("Settings saved successfully!")
    
    def render_partner_analytics(self, current_user: Dict):
        """Render partner-level analytics."""
        st.subheader("📈 Partner Analytics")
        
        # Sample analytics data
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", "127", "+12")
        with col2:
            st.metric("Active Traders", "89", "+5")
        with col3:
            st.metric("Total Volume", "$2.4M", "+18%")
        
        # Analytics charts would go here
        st.info("Partner-level analytics dashboard would be displayed here")
    
    def render_api_management(self, current_user: Dict):
        """Render API management for partners."""
        st.subheader("🔑 API Management")
        
        partner = self.auth_manager.db.get_partner(current_user['partner_id'])
        if partner:
            # Show API key (masked)
            api_key = "ts_" + "*" * 20 + "abcd1234"
            st.text_input("API Key", value=api_key, disabled=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Regenerate API Key"):
                    st.warning("This will invalidate the current API key!")
            
            with col2:
                if st.button("📋 Copy API Key"):
                    st.success("API key copied to clipboard!")
            
            # API documentation
            st.subheader("📚 API Documentation")
            st.code("""
# TradeSense Partner API Example
import requests

headers = {
    'Authorization': 'Bearer your_api_key_here',
    'Content-Type': 'application/json'
}

# Get user trades
response = requests.get(
    'https://api.tradesense.com/v1/trades',
    headers=headers
)
            """, language="python")


def render_auth_interface():
    """Render the main authentication interface."""
    auth_manager = AuthManager()
    
    # Check if user is already authenticated
    current_user = auth_manager.get_current_user()
    
    if current_user:
        # User is authenticated, show main app
        partner_manager = PartnerManager()
        partner_manager.render_partner_dashboard(current_user)
        
        # Logout button in sidebar
        with st.sidebar:
            st.write(f"Logged in as: {current_user['email']}")
            if st.button("🚪 Logout"):
                auth_manager.logout_user()
                st.rerun()
        
        return current_user
    
    else:
        # User not authenticated, show login/register
        st.title("🔐 TradeSense Authentication")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            render_login_form(auth_manager)
        
        with tab2:
            render_register_form(auth_manager)
        
        # OAuth login
        if auth_manager.oauth_flow:
            st.divider()
            st.subheader("🔗 Quick Login")
            
            if st.button("Sign in with Google", type="secondary"):
                redirect_uri = "https://your-app.replit.dev/oauth2callback"
                oauth_url = auth_manager.oauth_login_url(redirect_uri)
                if oauth_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={oauth_url}">', 
                              unsafe_allow_html=True)
        
        st.stop()


def render_login_form(auth_manager: AuthManager):
    """Render login form."""
    with st.form("login_form"):
        st.subheader("Login to Your Account")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("🔓 Login", type="primary"):
            if email and password:
                result = auth_manager.login_user(email, password)
                
                if result['success']:
                    st.session_state.session_id = result['session_id']
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result['error'])
            else:
                st.error("Please enter both email and password")


def render_register_form(auth_manager: AuthManager):
    """Render registration form."""
    with st.form("register_form"):
        st.subheader("Create New Account")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
        with col2:
            last_name = st.text_input("Last Name")
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        # Partner invitation code
        partner_code = st.text_input("Partner Code (Optional)", 
                                   help="Enter if you have a partner invitation code")
        
        if st.form_submit_button("🚀 Create Account", type="primary"):
            if not all([first_name, last_name, email, password, confirm_password]):
                st.error("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                result = auth_manager.register_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    partner_id=partner_code if partner_code else None
                )
                
                if result['success']:
                    st.success("Account created successfully! Please login.")
                    st.balloons()
                else:
                    st.error(result['error'])
