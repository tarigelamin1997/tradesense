
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import sqlite3
import hashlib
import secrets
from auth import AuthManager, require_auth, check_partner_access
from credential_manager import CredentialManager
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class PartnerPortalManager:
    """Manages the partner portal for B2B integration."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.auth_manager = AuthManager()
        self.init_partner_portal_tables()
    
    def init_partner_portal_tables(self):
        """Initialize partner portal specific tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced partners table with branding
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_branding (
                partner_id TEXT PRIMARY KEY,
                logo_url TEXT,
                primary_color TEXT DEFAULT '#1f77b4',
                secondary_color TEXT DEFAULT '#ff7f0e',
                background_color TEXT DEFAULT '#ffffff',
                text_color TEXT DEFAULT '#333333',
                custom_css TEXT,
                company_description TEXT,
                website_url TEXT,
                support_email TEXT,
                terms_url TEXT,
                privacy_url TEXT,
                custom_domain TEXT,
                favicon_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Partner analytics tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_type TEXT NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Partner user activity
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Partner subscriptions and billing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id TEXT NOT NULL,
                plan_type TEXT NOT NULL DEFAULT 'starter',
                monthly_fee REAL DEFAULT 0.0,
                revenue_share REAL DEFAULT 0.0,
                user_limit INTEGER DEFAULT 10,
                features JSON,
                status TEXT DEFAULT 'active',
                billing_contact TEXT,
                next_billing_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        # Partner white-label configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_whitelabel (
                partner_id TEXT PRIMARY KEY,
                app_name TEXT,
                app_tagline TEXT,
                hide_tradesense_branding BOOLEAN DEFAULT FALSE,
                custom_footer TEXT,
                analytics_disclaimer TEXT,
                risk_disclaimer TEXT,
                custom_menu_items JSON,
                enable_custom_reports BOOLEAN DEFAULT FALSE,
                custom_report_templates JSON,
                FOREIGN KEY (partner_id) REFERENCES partners (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_partner_registration(self, registration_data: Dict) -> Dict:
        """Handle partner registration process."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Create main partner record
            partner_id = f"partner_{secrets.token_urlsafe(8)}"
            api_key = f"ts_partner_{secrets.token_urlsafe(32)}"
            
            cursor.execute('''
                INSERT INTO partners (id, name, type, contact_email, api_key, settings)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                partner_id,
                registration_data['company_name'],
                registration_data['partner_type'],
                registration_data['contact_email'],
                api_key,
                json.dumps(registration_data.get('settings', {}))
            ))
            
            # Create default branding
            cursor.execute('''
                INSERT INTO partner_branding (partner_id, company_description, website_url, support_email)
                VALUES (?, ?, ?, ?)
            ''', (
                partner_id,
                registration_data.get('description', ''),
                registration_data.get('website', ''),
                registration_data['contact_email']
            ))
            
            # Create default subscription
            cursor.execute('''
                INSERT INTO partner_subscriptions (partner_id, plan_type, billing_contact)
                VALUES (?, ?, ?)
            ''', (
                partner_id,
                registration_data.get('plan_type', 'starter'),
                registration_data['contact_email']
            ))
            
            # Create white-label configuration
            cursor.execute('''
                INSERT INTO partner_whitelabel (partner_id, app_name, app_tagline)
                VALUES (?, ?, ?)
            ''', (
                partner_id,
                registration_data.get('app_name', registration_data['company_name']),
                registration_data.get('tagline', 'Professional Trading Analytics')
            ))
            
            conn.commit()
            return {
                'success': True,
                'partner_id': partner_id,
                'api_key': api_key
            }
            
        except Exception as e:
            conn.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_partner_branding(self, partner_id: str) -> Dict:
        """Get partner branding configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM partner_branding WHERE partner_id = ?
        ''', (partner_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return {}
    
    def update_partner_branding(self, partner_id: str, branding_data: Dict) -> bool:
        """Update partner branding configuration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE partner_branding 
                SET logo_url = ?, primary_color = ?, secondary_color = ?,
                    background_color = ?, text_color = ?, custom_css = ?,
                    company_description = ?, website_url = ?, support_email = ?,
                    terms_url = ?, privacy_url = ?, custom_domain = ?,
                    favicon_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE partner_id = ?
            ''', (
                branding_data.get('logo_url'),
                branding_data.get('primary_color', '#1f77b4'),
                branding_data.get('secondary_color', '#ff7f0e'),
                branding_data.get('background_color', '#ffffff'),
                branding_data.get('text_color', '#333333'),
                branding_data.get('custom_css'),
                branding_data.get('company_description'),
                branding_data.get('website_url'),
                branding_data.get('support_email'),
                branding_data.get('terms_url'),
                branding_data.get('privacy_url'),
                branding_data.get('custom_domain'),
                branding_data.get('favicon_url'),
                partner_id
            ))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_partner_analytics(self, partner_id: str, days: int = 30) -> Dict:
        """Get partner analytics data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user count and activity
        cursor.execute('''
            SELECT COUNT(*) as total_users,
                   COUNT(CASE WHEN last_login > datetime('now', '-7 days') THEN 1 END) as active_users,
                   COUNT(CASE WHEN created_at > datetime('now', '-30 days') THEN 1 END) as new_users
            FROM users WHERE partner_id = ?
        ''', (partner_id,))
        
        user_stats = cursor.fetchone()
        
        # Get trade volume and activity
        cursor.execute('''
            SELECT COUNT(*) as total_trades,
                   COUNT(CASE WHEN created_at > datetime('now', '-7 days') THEN 1 END) as recent_trades
            FROM user_trades WHERE partner_id = ?
        ''', (partner_id,))
        
        trade_stats = cursor.fetchone()
        
        # Get revenue metrics (simulated)
        cursor.execute('''
            SELECT monthly_fee, revenue_share, user_limit
            FROM partner_subscriptions 
            WHERE partner_id = ? AND status = 'active'
        ''', (partner_id,))
        
        subscription = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_users': user_stats[0] if user_stats else 0,
            'active_users': user_stats[1] if user_stats else 0,
            'new_users': user_stats[2] if user_stats else 0,
            'total_trades': trade_stats[0] if trade_stats else 0,
            'recent_trades': trade_stats[1] if trade_stats else 0,
            'monthly_fee': subscription[0] if subscription else 0,
            'revenue_share': subscription[1] if subscription else 0,
            'user_limit': subscription[2] if subscription else 10
        }


def render_partner_portal():
    """Main partner portal interface."""
    st.set_page_config(
        page_title="TradeSense Partner Portal",
        page_icon="🤝",
        layout="wide"
    )
    
    # Check if accessing through partner subdomain or specific URL
    partner_id = st.experimental_get_query_params().get('partner_id', [None])[0]
    
    portal_manager = PartnerPortalManager()
    
    # Header
    st.title("🤝 TradeSense Partner Portal")
    st.caption("B2B Integration & White-Label Solutions")
    
    # Authentication check
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        render_partner_auth()
        return
    
    # Main portal navigation
    if current_user.get('partner_id'):
        render_partner_dashboard(portal_manager, current_user)
    else:
        render_partner_registration(portal_manager)


def render_partner_auth():
    """Partner-specific authentication interface."""
    st.subheader("🔐 Partner Access")
    
    tab1, tab2 = st.tabs(["Partner Login", "New Partner Registration"])
    
    with tab1:
        render_partner_login()
    
    with tab2:
        render_partner_registration_form()


def render_partner_login():
    """Partner login form."""
    with st.form("partner_login"):
        st.subheader("Partner Login")
        
        partner_email = st.text_input("Partner Email")
        partner_key = st.text_input("Partner Key", type="password")
        
        if st.form_submit_button("🔓 Login to Partner Portal", type="primary"):
            auth_manager = AuthManager()
            result = auth_manager.login_user(partner_email, partner_key)
            
            if result['success']:
                st.session_state.session_id = result['session_id']
                st.success("Partner login successful!")
                st.rerun()
            else:
                st.error("Invalid partner credentials")


def render_partner_registration_form():
    """New partner registration form."""
    st.subheader("🚀 Become a TradeSense Partner")
    st.write("Join our partner program and offer white-labeled trading analytics to your clients.")
    
    with st.form("partner_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Company Information")
            company_name = st.text_input("Company Name *")
            contact_email = st.text_input("Contact Email *")
            website = st.text_input("Website URL")
            phone = st.text_input("Phone Number")
            
        with col2:
            st.subheader("Partnership Details")
            partner_type = st.selectbox(
                "Partner Type *",
                options=['broker', 'prop_firm', 'trading_group', 'educator', 'technology_provider'],
                format_func=lambda x: {
                    'broker': '🏦 Brokerage',
                    'prop_firm': '🏢 Prop Trading Firm',
                    'trading_group': '👥 Trading Community',
                    'educator': '📚 Trading Education',
                    'technology_provider': '⚙️ Technology Provider'
                }[x]
            )
            
            expected_users = st.selectbox(
                "Expected User Count",
                options=['1-10', '11-50', '51-200', '201-1000', '1000+']
            )
            
            plan_type = st.selectbox(
                "Partnership Plan",
                options=['starter', 'professional', 'enterprise'],
                format_func=lambda x: {
                    'starter': 'Starter - $99/month (up to 50 users)',
                    'professional': 'Professional - $299/month (up to 200 users)',
                    'enterprise': 'Enterprise - Custom pricing'
                }[x]
            )
        
        st.subheader("Branding Preferences")
        col3, col4 = st.columns(2)
        
        with col3:
            app_name = st.text_input("Custom App Name", placeholder=f"{company_name} Analytics")
            tagline = st.text_input("App Tagline", placeholder="Professional Trading Analytics")
            
        with col4:
            primary_color = st.color_picker("Primary Brand Color", "#1f77b4")
            hide_branding = st.checkbox("Hide TradeSense Branding (Enterprise only)")
        
        description = st.text_area("Company Description")
        
        # Terms and agreement
        st.subheader("Agreement")
        agree_terms = st.checkbox("I agree to the TradeSense Partner Terms of Service")
        agree_privacy = st.checkbox("I agree to the Privacy Policy")
        marketing_consent = st.checkbox("I consent to receive partner program updates")
        
        if st.form_submit_button("🎯 Submit Partner Application", type="primary"):
            if not all([company_name, contact_email, partner_type, agree_terms, agree_privacy]):
                st.error("Please fill in all required fields and agree to terms")
            else:
                portal_manager = PartnerPortalManager()
                
                registration_data = {
                    'company_name': company_name,
                    'contact_email': contact_email,
                    'partner_type': partner_type,
                    'website': website,
                    'description': description,
                    'plan_type': plan_type,
                    'app_name': app_name or f"{company_name} Analytics",
                    'tagline': tagline,
                    'settings': {
                        'expected_users': expected_users,
                        'phone': phone,
                        'primary_color': primary_color,
                        'hide_branding': hide_branding,
                        'marketing_consent': marketing_consent
                    }
                }
                
                result = portal_manager.create_partner_registration(registration_data)
                
                if result['success']:
                    st.success("🎉 Partner application submitted successfully!")
                    st.balloons()
                    
                    # Show next steps
                    st.subheader("🚀 Next Steps")
                    st.info(f"""
                    **Partner ID:** `{result['partner_id']}`
                    **API Key:** `{result['api_key'][:20]}...`
                    
                    1. Our team will review your application within 2 business days
                    2. You'll receive setup instructions via email
                    3. Schedule a demo call to configure your white-label solution
                    """)
                    
                    st.write("**Contact our partner team:** partners@tradesense.com")
                else:
                    st.error(f"Registration failed: {result['error']}")


def render_partner_dashboard(portal_manager: PartnerPortalManager, current_user: Dict):
    """Main partner dashboard."""
    partner_id = current_user['partner_id']
    partner = portal_manager.auth_manager.db.get_partner(partner_id)
    
    if not partner:
        st.error("Partner not found")
        return
    
    # Apply partner branding
    branding = portal_manager.get_partner_branding(partner_id)
    apply_partner_branding(branding)
    
    # Header with partner branding
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if branding.get('logo_url'):
            st.image(branding['logo_url'], width=200)
        
        st.title(f"Welcome to {partner['name']}")
        st.caption(f"Partner Portal • {partner['type'].title()}")
    
    with col2:
        st.metric("Partner Status", "✅ Active")
    
    with col3:
        if st.button("🚪 Logout"):
            portal_manager.auth_manager.logout_user()
            st.rerun()
    
    # Main navigation tabs
    tabs = st.tabs([
        "📊 Dashboard", 
        "🎨 Branding", 
        "👥 Users", 
        "📈 Analytics", 
        "⚙️ Settings",
        "🔑 API",
        "💳 Billing"
    ])
    
    with tabs[0]:
        render_partner_overview(portal_manager, partner_id)
    
    with tabs[1]:
        render_branding_management(portal_manager, partner_id)
    
    with tabs[2]:
        render_user_management(portal_manager, partner_id)
    
    with tabs[3]:
        render_partner_analytics_dashboard(portal_manager, partner_id)
    
    with tabs[4]:
        render_partner_settings(portal_manager, partner_id)
    
    with tabs[5]:
        render_api_management(portal_manager, partner_id)
    
    with tabs[6]:
        render_billing_management(portal_manager, partner_id)


def render_partner_overview(portal_manager: PartnerPortalManager, partner_id: str):
    """Partner overview dashboard."""
    st.subheader("📊 Partner Overview")
    
    # Get analytics data
    analytics = portal_manager.get_partner_analytics(partner_id)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Users", 
            analytics['total_users'],
            delta=f"{analytics['new_users']} new this month"
        )
    
    with col2:
        st.metric(
            "Active Users", 
            analytics['active_users'],
            delta=f"{analytics['active_users']}/{analytics['total_users']} ({analytics['active_users']/max(analytics['total_users'], 1)*100:.1f}%)"
        )
    
    with col3:
        st.metric(
            "Trade Volume", 
            f"{analytics['total_trades']:,}",
            delta=f"{analytics['recent_trades']} this week"
        )
    
    with col4:
        monthly_revenue = analytics['monthly_fee'] + (analytics['total_trades'] * analytics['revenue_share'])
        st.metric(
            "Monthly Revenue", 
            f"${monthly_revenue:,.2f}",
            delta="+12.5%"
        )
    
    st.divider()
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Invite Users", type="primary"):
            st.session_state.show_invite_modal = True
    
    with col2:
        if st.button("📊 Generate Report"):
            st.success("Monthly partner report generated!")
    
    with col3:
        if st.button("🎨 Customize Branding"):
            st.session_state.active_tab = 1  # Switch to branding tab
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    
    # Sample recent activity data
    activity_data = [
        {'Time': '2 hours ago', 'Activity': 'New user registration', 'User': 'john.doe@email.com'},
        {'Time': '5 hours ago', 'Activity': 'Trade data sync', 'Details': '127 trades imported'},
        {'Time': '1 day ago', 'Activity': 'API key generated', 'Details': 'New integration setup'},
        {'Time': '2 days ago', 'Activity': 'Branding updated', 'Details': 'Logo and colors modified'},
    ]
    
    for activity in activity_data:
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                st.caption(activity['Time'])
            with col2:
                st.write(f"**{activity['Activity']}**")
                if 'User' in activity:
                    st.caption(f"User: {activity['User']}")
                elif 'Details' in activity:
                    st.caption(activity['Details'])
        st.divider()


def render_branding_management(portal_manager: PartnerPortalManager, partner_id: str):
    """Branding and white-label management."""
    st.subheader("🎨 Branding & White-Label Configuration")
    
    branding = portal_manager.get_partner_branding(partner_id)
    
    with st.form("branding_form"):
        st.subheader("Visual Branding")
        
        col1, col2 = st.columns(2)
        
        with col1:
            logo_url = st.text_input("Logo URL", value=branding.get('logo_url', ''))
            favicon_url = st.text_input("Favicon URL", value=branding.get('favicon_url', ''))
            
            # Color scheme
            st.write("**Color Scheme**")
            primary_color = st.color_picker("Primary Color", value=branding.get('primary_color', '#1f77b4'))
            secondary_color = st.color_picker("Secondary Color", value=branding.get('secondary_color', '#ff7f0e'))
            
        with col2:
            background_color = st.color_picker("Background Color", value=branding.get('background_color', '#ffffff'))
            text_color = st.color_picker("Text Color", value=branding.get('text_color', '#333333'))
            
            # Preview
            st.write("**Color Preview**")
            st.markdown(f"""
            <div style="
                background-color: {background_color}; 
                color: {text_color}; 
                padding: 20px; 
                border-radius: 8px;
                border: 2px solid {primary_color};
            ">
                <h3 style="color: {primary_color}; margin: 0;">Sample Header</h3>
                <p style="margin: 10px 0;">This is how your branded interface will look.</p>
                <button style="
                    background-color: {primary_color}; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 4px;
                ">Primary Button</button>
                <button style="
                    background-color: {secondary_color}; 
                    color: white; 
                    border: none; 
                    padding: 8px 16px; 
                    border-radius: 4px;
                    margin-left: 10px;
                ">Secondary Button</button>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("Company Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            company_description = st.text_area(
                "Company Description", 
                value=branding.get('company_description', ''),
                height=100
            )
            website_url = st.text_input("Website URL", value=branding.get('website_url', ''))
            
        with col4:
            support_email = st.text_input("Support Email", value=branding.get('support_email', ''))
            terms_url = st.text_input("Terms of Service URL", value=branding.get('terms_url', ''))
            privacy_url = st.text_input("Privacy Policy URL", value=branding.get('privacy_url', ''))
        
        st.subheader("Advanced Customization")
        
        custom_css = st.text_area(
            "Custom CSS", 
            value=branding.get('custom_css', ''),
            height=150,
            help="Add custom CSS to further customize the appearance"
        )
        
        custom_domain = st.text_input(
            "Custom Domain", 
            value=branding.get('custom_domain', ''),
            help="e.g., analytics.yourcompany.com"
        )
        
        if st.form_submit_button("💾 Save Branding", type="primary"):
            branding_data = {
                'logo_url': logo_url,
                'favicon_url': favicon_url,
                'primary_color': primary_color,
                'secondary_color': secondary_color,
                'background_color': background_color,
                'text_color': text_color,
                'company_description': company_description,
                'website_url': website_url,
                'support_email': support_email,
                'terms_url': terms_url,
                'privacy_url': privacy_url,
                'custom_css': custom_css,
                'custom_domain': custom_domain
            }
            
            if portal_manager.update_partner_branding(partner_id, branding_data):
                st.success("✅ Branding updated successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to update branding")


def render_user_management(portal_manager: PartnerPortalManager, partner_id: str):
    """Partner user management interface."""
    st.subheader("👥 User Management")
    
    # User invitation
    with st.expander("➕ Invite New Users"):
        with st.form("invite_users"):
            st.write("**Invite Users to Your Platform**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                invite_method = st.radio(
                    "Invitation Method",
                    options=['email', 'bulk_upload', 'signup_link']
                )
            
            with col2:
                user_role = st.selectbox("Default Role", options=['user', 'admin'])
            
            if invite_method == 'email':
                emails = st.text_area("Email Addresses (one per line)")
                personal_message = st.text_area("Personal Message (Optional)")
                
            elif invite_method == 'bulk_upload':
                uploaded_file = st.file_uploader("Upload CSV with user data", type=['csv'])
                st.caption("CSV should contain: email, first_name, last_name, role")
                
            else:  # signup_link
                st.info("Generate a signup link that automatically associates users with your organization")
                signup_code = f"{partner_id[:8]}-{secrets.token_urlsafe(4)}"
                st.code(f"https://tradesense.com/signup?partner={signup_code}")
            
            if st.form_submit_button("📧 Send Invitations", type="primary"):
                if invite_method == 'email' and emails:
                    email_list = [email.strip() for email in emails.split('\n') if email.strip()]
                    st.success(f"✅ Invitations sent to {len(email_list)} users!")
                elif invite_method == 'bulk_upload' and uploaded_file:
                    st.success("✅ Bulk invitations processed!")
                else:
                    st.success("✅ Signup link generated!")
    
    # Current users
    st.subheader("Current Users")
    
    # Sample user data
    users_data = [
        {'Name': 'John Smith', 'Email': 'john@company.com', 'Role': 'Admin', 'Status': 'Active', 'Last Login': '2 hours ago', 'Trades': 245},
        {'Name': 'Sarah Johnson', 'Email': 'sarah@company.com', 'Role': 'User', 'Status': 'Active', 'Last Login': '1 day ago', 'Trades': 156},
        {'Name': 'Mike Chen', 'Email': 'mike@company.com', 'Role': 'User', 'Status': 'Inactive', 'Last Login': '2 weeks ago', 'Trades': 89},
        {'Name': 'Emily Brown', 'Email': 'emily@company.com', 'Role': 'User', 'Status': 'Active', 'Last Login': '3 hours ago', 'Trades': 312},
    ]
    
    # User filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", options=['All', 'Active', 'Inactive'])
    
    with col2:
        role_filter = st.selectbox("Filter by Role", options=['All', 'Admin', 'User'])
    
    with col3:
        search_term = st.text_input("Search users", placeholder="Name or email...")
    
    # Users table
    df = pd.DataFrame(users_data)
    
    for i, user in enumerate(users_data):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{user['Name']}**")
                st.caption(user['Email'])
            
            with col2:
                st.write(f"Role: {user['Role']}")
                st.caption(f"Last login: {user['Last Login']}")
            
            with col3:
                if user['Status'] == 'Active':
                    st.success(user['Status'])
                else:
                    st.warning(user['Status'])
            
            with col4:
                st.metric("Trades", user['Trades'])
            
            with col5:
                if st.button("⚙️", key=f"user_manage_{i}", help="Manage user"):
                    st.session_state[f"manage_user_{i}"] = True
            
            # User management options
            if st.session_state.get(f"manage_user_{i}", False):
                with st.container():
                    ucol1, ucol2, ucol3 = st.columns(3)
                    
                    with ucol1:
                        if st.button("📧 Send Message", key=f"message_{i}"):
                            st.info("Message sent to user")
                    
                    with ucol2:
                        if user['Status'] == 'Active':
                            if st.button("⏸️ Suspend", key=f"suspend_{i}"):
                                st.warning("User suspended")
                        else:
                            if st.button("▶️ Activate", key=f"activate_{i}"):
                                st.success("User activated")
                    
                    with ucol3:
                        if st.button("🗑️ Remove", key=f"remove_{i}", type="secondary"):
                            st.error("User removed from organization")
                    
                    st.session_state[f"manage_user_{i}"] = False
        
        st.divider()


def render_partner_analytics_dashboard(portal_manager: PartnerPortalManager, partner_id: str):
    """Partner-specific analytics dashboard."""
    st.subheader("📈 Partner Analytics Dashboard")
    
    # Time range selector
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.selectbox("Time Period", options=['7 days', '30 days', '90 days', '1 year'])
    
    with col2:
        metric_type = st.selectbox("Primary Metric", options=['Users', 'Trades', 'Revenue', 'Engagement'])
    
    # Analytics data (simulated)
    analytics_data = portal_manager.get_partner_analytics(partner_id)
    
    # Revenue analytics
    st.subheader("💰 Revenue Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        monthly_revenue = analytics_data['monthly_fee']
        st.metric("Monthly Fee", f"${monthly_revenue:,.2f}")
    
    with col2:
        trade_revenue = analytics_data['total_trades'] * analytics_data['revenue_share']
        st.metric("Trade Revenue", f"${trade_revenue:,.2f}", delta="+15.2%")
    
    with col3:
        total_revenue = monthly_revenue + trade_revenue
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col4:
        projected_annual = total_revenue * 12
        st.metric("Projected Annual", f"${projected_annual:,.2f}")
    
    # User growth chart
    st.subheader("👥 User Growth")
    
    # Generate sample data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    user_growth = pd.DataFrame({
        'Date': dates,
        'Total Users': range(10, 10 + len(dates)),
        'Active Users': [max(1, x + np.random.randint(-5, 10)) for x in range(5, 5 + len(dates))],
        'New Signups': [max(0, np.random.randint(0, 5)) for _ in range(len(dates))]
    })
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('User Growth Over Time', 'Trade Volume', 'Revenue Trend', 'Engagement Metrics'),
        specs=[[{"secondary_y": True}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # User growth
    fig.add_trace(
        go.Scatter(x=user_growth['Date'][-30:], y=user_growth['Total Users'][-30:], 
                  name='Total Users', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Trade volume
    fig.add_trace(
        go.Bar(x=user_growth['Date'][-30:], y=user_growth['New Signups'][-30:], 
               name='Daily Trades', marker_color='green'),
        row=1, col=2
    )
    
    # Revenue trend
    revenue_data = [total_revenue + np.random.uniform(-500, 500) for _ in range(30)]
    fig.add_trace(
        go.Scatter(x=user_growth['Date'][-30:], y=revenue_data, 
                  name='Revenue', line=dict(color='orange')),
        row=2, col=1
    )
    
    # Engagement metrics
    engagement_data = [np.random.uniform(60, 95) for _ in range(30)]
    fig.add_trace(
        go.Scatter(x=user_growth['Date'][-30:], y=engagement_data, 
                  name='Engagement %', line=dict(color='purple')),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("📊 Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**User Engagement**")
        engagement_metrics = {
            'Daily Active Users': '74%',
            'Weekly Retention': '68%',
            'Monthly Retention': '45%',
            'Avg Session Duration': '24 min',
            'Feature Adoption': '82%'
        }
        
        for metric, value in engagement_metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.write("**Platform Performance**")
        performance_metrics = {
            'Uptime': '99.9%',
            'Avg Load Time': '1.2s',
            'Error Rate': '0.1%',
            'API Response Time': '245ms',
            'Data Sync Success': '98.5%'
        }
        
        for metric, value in performance_metrics.items():
            st.metric(metric, value)


def render_partner_settings(portal_manager: PartnerPortalManager, partner_id: str):
    """Partner settings management."""
    st.subheader("⚙️ Partner Settings")
    
    tabs = st.tabs(["General", "White-Label", "Notifications", "Integrations"])
    
    with tabs[0]:
        render_general_settings(portal_manager, partner_id)
    
    with tabs[1]:
        render_whitelabel_settings(portal_manager, partner_id)
    
    with tabs[2]:
        render_notification_settings(portal_manager, partner_id)
    
    with tabs[3]:
        render_integration_settings(portal_manager, partner_id)


def render_general_settings(portal_manager: PartnerPortalManager, partner_id: str):
    """General partner settings."""
    st.subheader("🏢 General Settings")
    
    partner = portal_manager.auth_manager.db.get_partner(partner_id)
    
    with st.form("general_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input("Company Name", value=partner['name'])
            contact_email = st.text_input("Contact Email", value=partner['contact_email'])
            timezone = st.selectbox("Timezone", options=['UTC', 'US/Eastern', 'US/Pacific', 'Europe/London'])
            
        with col2:
            industry = st.selectbox("Industry", options=['Financial Services', 'Trading Education', 'Technology', 'Other'])
            company_size = st.selectbox("Company Size", options=['1-10', '11-50', '51-200', '200+'])
            phone = st.text_input("Phone Number")
        
        # Data retention settings
        st.subheader("Data Management")
        
        col3, col4 = st.columns(2)
        
        with col3:
            data_retention = st.selectbox("Data Retention Period", options=['30 days', '90 days', '1 year', '2 years', 'Indefinite'])
            auto_cleanup = st.checkbox("Auto-cleanup inactive users")
            
        with col4:
            export_format = st.selectbox("Default Export Format", options=['CSV', 'Excel', 'JSON', 'PDF'])
            backup_frequency = st.selectbox("Backup Frequency", options=['Daily', 'Weekly', 'Monthly'])
        
        if st.form_submit_button("💾 Save General Settings", type="primary"):
            st.success("✅ General settings updated successfully!")


def render_whitelabel_settings(portal_manager: PartnerPortalManager, partner_id: str):
    """White-label configuration settings."""
    st.subheader("🏷️ White-Label Settings")
    
    with st.form("whitelabel_settings"):
        # App branding
        st.write("**Application Branding**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            app_name = st.text_input("Application Name", value="Analytics Pro")
            app_tagline = st.text_input("Tagline", value="Professional Trading Analytics")
            hide_tradesense = st.checkbox("Hide TradeSense Branding")
            
        with col2:
            custom_footer = st.text_area("Custom Footer Text")
            analytics_disclaimer = st.text_area("Analytics Disclaimer")
            risk_disclaimer = st.text_area("Risk Disclaimer")
        
        # Feature customization
        st.write("**Feature Customization**")
        
        col3, col4 = st.columns(2)
        
        with col3:
            enable_reports = st.checkbox("Enable Custom Reports", value=True)
            enable_alerts = st.checkbox("Enable Custom Alerts", value=True)
            enable_sharing = st.checkbox("Enable Social Sharing")
            
        with col4:
            enable_export = st.checkbox("Enable Data Export", value=True)
            enable_api = st.checkbox("Enable API Access", value=True)
            enable_webhooks = st.checkbox("Enable Webhooks")
        
        # Menu customization
        st.write("**Navigation Menu**")
        
        menu_items = st.text_area(
            "Custom Menu Items (JSON)",
            value='{"Trading Tools": "/tools", "Education": "/learn", "Support": "/help"}',
            help="Add custom navigation items"
        )
        
        if st.form_submit_button("💾 Save White-Label Settings", type="primary"):
            st.success("✅ White-label settings updated successfully!")


def render_notification_settings(portal_manager: PartnerPortalManager, partner_id: str):
    """Notification preferences."""
    st.subheader("🔔 Notification Settings")
    
    with st.form("notification_settings"):
        # Email notifications
        st.write("**Email Notifications**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_user_notify = st.checkbox("New user registrations", value=True)
            error_notify = st.checkbox("System errors", value=True)
            revenue_notify = st.checkbox("Revenue milestones", value=True)
            
        with col2:
            weekly_report = st.checkbox("Weekly reports", value=True)
            monthly_report = st.checkbox("Monthly reports", value=True)
            security_alerts = st.checkbox("Security alerts", value=True)
        
        # Webhook notifications
        st.write("**Webhook Notifications**")
        
        webhook_url = st.text_input("Webhook URL")
        webhook_events = st.multiselect(
            "Events to notify",
            options=['user.created', 'user.deleted', 'trade.imported', 'error.occurred', 'subscription.changed']
        )
        
        # Notification frequency
        st.write("**Frequency Settings**")
        
        col3, col4 = st.columns(2)
        
        with col3:
            digest_frequency = st.selectbox("Digest Frequency", options=['Daily', 'Weekly', 'Monthly'])
            
        with col4:
            quiet_hours = st.checkbox("Enable quiet hours (10 PM - 8 AM)")
        
        if st.form_submit_button("💾 Save Notification Settings", type="primary"):
            st.success("✅ Notification settings updated successfully!")


def render_integration_settings(portal_manager: PartnerPortalManager, partner_id: str):
    """Integration and API settings."""
    st.subheader("🔗 Integration Settings")
    
    # SSO Configuration
    st.write("**Single Sign-On (SSO)**")
    
    with st.expander("Configure SSO"):
        sso_provider = st.selectbox("SSO Provider", options=['None', 'SAML', 'OAuth2', 'Active Directory'])
        
        if sso_provider != 'None':
            sso_endpoint = st.text_input("SSO Endpoint URL")
            sso_certificate = st.text_area("Certificate/Key")
            auto_provision = st.checkbox("Auto-provision new users")
    
    # Webhook configuration
    st.write("**Webhook Configuration**")
    
    with st.form("webhook_config"):
        webhook_url = st.text_input("Webhook URL")
        webhook_secret = st.text_input("Webhook Secret", type="password")
        
        webhook_events = st.multiselect(
            "Events",
            options=[
                'user.created', 'user.updated', 'user.deleted',
                'trade.imported', 'trade.updated', 'trade.deleted',
                'report.generated', 'alert.triggered'
            ]
        )
        
        if st.form_submit_button("💾 Save Webhook Config"):
            st.success("✅ Webhook configuration saved!")
    
    # API rate limits
    st.write("**API Configuration**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Rate Limit", "1000 req/hour")
        st.metric("Monthly Quota", "50,000 requests")
        
    with col2:
        st.metric("API Calls Used", "12,847")
        st.metric("Quota Remaining", "37,153")


def render_api_management(portal_manager: PartnerPortalManager, partner_id: str):
    """API management interface."""
    st.subheader("🔑 API Management")
    
    partner = portal_manager.auth_manager.db.get_partner(partner_id)
    
    # API Key management
    st.write("**API Key**")
    
    api_key_display = f"ts_partner_{partner_id[:8]}{'*' * 20}"
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.code(api_key_display)
    
    with col2:
        if st.button("🔄 Regenerate"):
            st.warning("This will invalidate all existing integrations!")
    
    with col3:
        if st.button("📋 Copy"):
            st.success("API key copied!")
    
    # API documentation
    st.subheader("📚 API Documentation")
    
    tab1, tab2, tab3 = st.tabs(["Authentication", "Users API", "Trades API"])
    
    with tab1:
        st.write("**Authentication**")
        st.code("""
# Include your API key in the Authorization header
headers = {
    'Authorization': f'Bearer {your_api_key}',
    'Content-Type': 'application/json'
}
        """, language="python")
    
    with tab2:
        st.write("**Users API**")
        st.code("""
# Get all users for your organization
GET /api/v1/partner/users

# Create new user
POST /api/v1/partner/users
{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
}

# Update user
PUT /api/v1/partner/users/{user_id}
{
    "role": "admin"
}
        """, language="http")
    
    with tab3:
        st.write("**Trades API**")
        st.code("""
# Get trades for all users
GET /api/v1/partner/trades

# Get trades for specific user
GET /api/v1/partner/users/{user_id}/trades

# Import trades for user
POST /api/v1/partner/users/{user_id}/trades
{
    "trades": [
        {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 150.00,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    ]
}
        """, language="http")
    
    # API usage statistics
    st.subheader("📊 API Usage")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", "45,672")
    
    with col2:
        st.metric("This Month", "12,847")
    
    with col3:
        st.metric("Success Rate", "99.2%")
    
    with col4:
        st.metric("Avg Response", "245ms")


def render_billing_management(portal_manager: PartnerPortalManager, partner_id: str):
    """Billing and subscription management."""
    st.subheader("💳 Billing & Subscription")
    
    # Current plan
    st.write("**Current Plan**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Plan", "Professional")
        st.metric("Monthly Fee", "$299.00")
        
    with col2:
        st.metric("User Limit", "200")
        st.metric("API Calls", "50,000/month")
        
    with col3:
        st.metric("Next Billing", "Feb 15, 2024")
        st.metric("Status", "✅ Active")
    
    # Usage this month
    st.write("**Usage This Month**")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("Active Users", "127/200", delta="12 new")
    
    with col5:
        st.metric("API Calls", "12,847/50,000", delta="+2,341")
    
    with col6:
        revenue_share = 127 * 0.50  # $0.50 per user
        st.metric("Revenue Share", f"${revenue_share:.2f}", delta="+$6.00")
    
    # Billing history
    st.write("**Billing History**")
    
    billing_history = [
        {'Date': '2024-01-15', 'Description': 'Monthly Subscription', 'Amount': '$299.00', 'Status': 'Paid'},
        {'Date': '2024-01-15', 'Description': 'Revenue Share (127 users)', 'Amount': '$63.50', 'Status': 'Paid'},
        {'Date': '2023-12-15', 'Description': 'Monthly Subscription', 'Amount': '$299.00', 'Status': 'Paid'},
        {'Date': '2023-12-15', 'Description': 'Revenue Share (115 users)', 'Amount': '$57.50', 'Status': 'Paid'},
    ]
    
    df_billing = pd.DataFrame(billing_history)
    st.dataframe(df_billing, use_container_width=True)
    
    # Plan management
    st.write("**Plan Management**")
    
    col7, col8 = st.columns(2)
    
    with col7:
        if st.button("📈 Upgrade Plan"):
            st.info("Contact sales for Enterprise plan options")
    
    with col8:
        if st.button("📥 Download Invoice"):
            st.success("Invoice downloaded!")
    
    # Payment method
    st.write("**Payment Method**")
    
    col9, col10 = st.columns(2)
    
    with col9:
        st.write("💳 **** **** **** 1234")
        st.caption("Expires 12/25")
    
    with col10:
        if st.button("🔄 Update Payment Method"):
            st.info("Redirecting to payment portal...")


def apply_partner_branding(branding: Dict):
    """Apply partner branding to the interface."""
    if not branding:
        return
    
    # Custom CSS for partner branding
    custom_css = f"""
    <style>
    .stApp {{
        background-color: {branding.get('background_color', '#ffffff')};
        color: {branding.get('text_color', '#333333')};
    }}
    
    .stButton > button {{
        background-color: {branding.get('primary_color', '#1f77b4')};
        color: white;
        border: none;
    }}
    
    .stSelectbox > div > div {{
        background-color: {branding.get('background_color', '#ffffff')};
    }}
    
    .stMetric {{
        background-color: {branding.get('primary_color', '#1f77b4')}20;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid {branding.get('primary_color', '#1f77b4')};
    }}
    
    h1, h2, h3 {{
        color: {branding.get('primary_color', '#1f77b4')};
    }}
    
    {branding.get('custom_css', '')}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)


if __name__ == "__main__":
    render_partner_portal()
