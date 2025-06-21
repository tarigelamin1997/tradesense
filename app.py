#!/usr/bin/env python3
"""
TradeSense - Advanced Trading Analytics Platform
Main Application Entry Point
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Check for required modules before importing Streamlit
missing_modules = []
required_modules = ['streamlit', 'pandas', 'numpy', 'plotly']

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print(f"❌ Missing required modules: {', '.join(missing_modules)}")
    print("Please install dependencies with:")
    print("python3 -m pip install --user streamlit pandas numpy plotly")
    sys.exit(1)

# Now safely import Streamlit
import streamlit as st
import os
import sys

# Fix Python path for Replit .pythonlibs
pythonlibs_path = "/home/runner/workspace/.pythonlibs/lib/python3.12/site-packages"
if pythonlibs_path not in sys.path:
    sys.path.insert(0, pythonlibs_path)
import logging

# Configure Streamlit page FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="TradeSense - Trading Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://tradesense.app/help',
        'Report a bug': 'https://tradesense.app/support',
        'About': """
        # TradeSense Trading Analytics

        Advanced trading performance analytics platform.

        **Version:** 2.0.0
        **Contact:** support@tradesense.app
        """
    }
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables."""
    if 'data_uploaded' not in st.session_state:
        st.session_state.data_uploaded = False
    if 'trade_data' not in st.session_state:
        st.session_state.trade_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None

def main():
    """Main application function."""
    try:
        # Initialize session state
        initialize_session_state()

        # Initialize and test authentication system
        from auth import AuthManager, render_auth_sidebar
        
        # Test authentication system
        try:
            auth_manager = AuthManager()
            db_test = auth_manager.test_database_connection()
            if not db_test["success"]:
                st.error(f"🔧 Authentication system issue: {db_test['message']}")
                st.info("🔄 Attempting to fix...")
                auth_manager.init_database()
                st.success("✅ Authentication system initialized")
        except Exception as e:
            st.error(f"❌ Authentication system failed to initialize: {e}")
            st.stop()
        
        # Render authentication sidebar
        render_auth_sidebar()

        # Try to import the main app factory
        try:
            from core.app_factory import create_app
            create_app()
        except ImportError as e:
            logger.warning(f"Could not import app_factory: {e}")
            # Fallback to enhanced app structure with authentication
            
            from auth import AuthManager
            auth_manager = AuthManager()
            current_user = auth_manager.get_current_user()
            
            # Enterprise Features Navigation
            st.sidebar.markdown("---")
            st.sidebar.subheader("🏢 Enterprise Features")
            
            # Check for admin access
            if current_user and current_user.get('role') == 'admin':
                if st.sidebar.button("🛠️ Admin Dashboard", use_container_width=True):
                    from admin_dashboard import AdminDashboard
                    admin_dash = AdminDashboard()
                    admin_dash.render_dashboard()
                    return
            
            # Check for partner access
            if current_user and current_user.get('partner_id'):
                if st.sidebar.button("🏢 Partner Portal", use_container_width=True):
                    from partner_management import PartnerManagement
                    partner_mgmt = PartnerManagement()
                    partner_mgmt.render_partner_portal()
                    return
            
            # Affiliate program (available to all users)
            if st.sidebar.button("💰 Affiliate Program", use_container_width=True):
                from affiliate_system import AffiliateTrackingSystem
                affiliate_system = AffiliateTrackingSystem()
                affiliate_system.render_affiliate_dashboard()
                return
            
            # Support center
            if st.sidebar.button("🆘 Support Center", use_container_width=True):
                from error_notification_ui import render_error_notification_interface
                render_error_notification_interface()
                return
            
            # Main application
            st.title("🏆 TradeSense - Trading Analytics")
            
            if current_user:
                st.success(f"Welcome back, {current_user['username']}! 👋")
                
                # Enhanced feature showcase for authenticated users
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 📊 Analytics")
                    st.write("• Advanced performance metrics")
                    st.write("• Risk analysis & recommendations")
                    st.write("• Interactive charts & reports")
                
                with col2:
                    st.markdown("### 🔗 Integrations")
                    st.write("• Multiple broker connections")
                    st.write("• Automated data sync")
                    st.write("• Real-time updates")
                
                with col3:
                    st.markdown("### 🏢 Enterprise")
                    st.write("• Partner management")
                    st.write("• White-label solutions")
                    st.write("• API access")
            
            else:
                st.info("Welcome to TradeSense! Please login to access the full platform.")
                
                # Feature showcase for non-authenticated users
                st.markdown("### 🚀 Platform Features")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    #### 📊 Trading Analytics
                    - **Performance Metrics**: Win rate, profit factor, Sharpe ratio
                    - **Risk Analysis**: Drawdown, position sizing, risk metrics
                    - **Interactive Charts**: Equity curves, performance over time
                    - **Export Reports**: PDF and Excel report generation
                    """)
                
                with col2:
                    st.markdown("""
                    #### 🔗 Broker Integrations
                    - **Interactive Brokers**: Real-time data sync
                    - **TD Ameritrade**: Automated trade import
                    - **Prop Firms**: Apex, TopStep, and more
                    - **CSV Import**: Universal trade data support
                    """)
                
                st.markdown("### 🏢 Enterprise Solutions")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                    #### 🤝 Partner Program
                    - White-label branding
                    - Revenue sharing
                    - Dedicated support
                    - Custom integrations
                    """)
                
                with col2:
                    st.markdown("""
                    #### 💰 Affiliate Program
                    - Up to 40% commission
                    - Tiered rewards
                    - Marketing materials
                    - Real-time tracking
                    """)
                
                with col3:
                    st.markdown("""
                    #### 🛠️ Admin Tools
                    - User management
                    - System monitoring
                    - Analytics dashboard
                    - Health monitoring
                    """)

            # Basic file uploader as fallback
            uploaded_file = st.file_uploader(
                "Upload your trading data",
                type=['csv', 'xlsx', 'xls'],
                help="Upload your trade history file to get started with analytics"
            )

            if uploaded_file:
                st.success("File uploaded successfully!")
                st.info("Analytics engine is initializing...")
            else:
                if current_user:
                    st.markdown("""
                    ### Getting Started
                    1. Upload your trading data using the file uploader above
                    2. Review and map your data columns
                    3. Analyze your trading performance with interactive charts
                    4. Get risk management recommendations
                    """)

    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"Application Error: {str(e)}")
        st.info("Please check the logs for more details or contact support.")

# Run the application
if __name__ == "__main__":
    main()