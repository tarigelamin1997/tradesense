#!/usr/bin/env python3
"""
TradeSense - Advanced Trading Analytics Platform
Main Streamlit application entry point
"""

import streamlit as st

# Page configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="TradeSense - Trading Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os
import logging
import traceback

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import core components with error handling
try:
    from auth import AuthManager
    from data_validation import DataValidator
    from error_handler import ErrorHandler
    from notification_system import notification_manager

    # Import dashboard manager functions directly
    from core.dashboard_manager import render_dashboard_tabs

    # Import health monitoring with fallback
    try:
        from health_monitoring import SystemHealthMonitor
        HEALTH_MONITORING_AVAILABLE = True
    except ImportError:
        HEALTH_MONITORING_AVAILABLE = False
        logger.warning("Health monitoring not available")

except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Critical import error: {e}")
    st.stop()

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Modern Design System */
    .stApp {
        background: var(--background-color, #f8fafc);
    }

    /* Remove default sidebar */
    .css-1d391kg {
        display: none;
    }

    /* Modern header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }

    /* Enhanced metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(45deg, #667eea, #764ba2);
    }

    /* Modern buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 0.75rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Enhanced file uploader */
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 1rem;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        transition: all 0.3s ease;
    }

    .stFileUploader > div:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    }

    /* Modern table styling */
    .stDataFrame {
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: #f1f5f9;
        border-radius: 0.75rem;
        padding: 0.75rem 1.5rem;
        border: none;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    /* Toast notifications */
    .toast-container {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 9999;
        pointer-events: none;
    }

    .toast {
        background: white;
        border-radius: 0.75rem;
        padding: 1rem 1.5rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border-left: 4px solid #10b981;
        animation: slideIn 0.3s ease;
        pointer-events: auto;
    }

    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    /* Light/Dark theme support */
    [data-theme="light"] {
        --background-color: #ffffff;
        --text-color: #1f2937;
        --card-background: #ffffff;
    }

    [data-theme="dark"] {
        --background-color: #1f2937;
        --text-color: #f9fafb;
        --card-background: #374151;
    }

    /* Modern info banner */
    .info-banner {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        font-weight: 500;
        box-shadow: 0 4px 14px 0 rgba(251, 191, 36, 0.3);
    }

    /* Loading animations */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

class TradeSenseApp:
    """Main TradeSense application class."""

    def __init__(self):
        """Initialize the TradeSense application."""
        self.auth_manager = AuthManager()

        # Initialize health monitor with fallback
        if HEALTH_MONITORING_AVAILABLE:
            self.health_monitor = SystemHealthMonitor()
        else:
            self.health_monitor = None

        self.notification_manager = notification_manager
        self.error_handler = ErrorHandler()

        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_role' not in st.session_state:
            st.session_state.user_role = 'user'
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'Dashboard'
        if 'trade_data' not in st.session_state:
            st.session_state.trade_data = None
        if 'analytics_result' not in st.session_state:
            st.session_state.analytics_result = None

    def render_header(self):
        """Render the main application header."""
        st.markdown("""
        <div class="main-header">
            <h1>📊 TradeSense</h1>
            <p>Advanced Trading Analytics Platform</p>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render the application sidebar navigation."""
        with st.sidebar:
            st.markdown("### Navigation")

            # Health status indicator
            if self.health_monitor:
                try:
                    health_status = self.health_monitor.get_overall_health_status()
                    status_class = "status-online" if str(health_status) == 'HealthStatus.HEALTHY' else "status-warning"
                    status_text = str(health_status).split('.')[-1].title()
                except:
                    status_class = "status-online"
                    status_text = "Online"
            else:
                status_class = "status-online"
                status_text = "Online"

            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <span class="status-indicator {status_class}"></span>
                System Status: {status_text}
            </div>
            """, unsafe_allow_html=True)

            # Navigation menu
            pages = [
                "Dashboard",
                "Analytics",
                "Trade Data",
                "Integrations",
                "Settings"
            ]

            if st.session_state.user_role == 'admin':
                pages.extend(["Admin Panel", "System Monitor"])

            st.session_state.current_page = st.selectbox(
                "Select Page",
                pages,
                index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0
            )

            # Quick actions
            st.markdown("### Quick Actions")
            if st.button("🔄 Refresh Data"):
                st.rerun()

            if st.button("📥 Sample Data"):
                self._load_sample_data()

    def _load_sample_data(self):
        """Load sample trading data for demonstration."""
        try:
            sample_data_path = "sample_data/futures_sample.csv"
            if os.path.exists(sample_data_path):
                st.session_state.trade_data = pd.read_csv(sample_data_path)
                st.success("Sample data loaded successfully!")
            else:
                # Generate synthetic sample data
                dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
                sample_data = pd.DataFrame({
                    'date': np.random.choice(dates, 100),
                    'symbol': np.random.choice(['ES', 'NQ', 'YM', 'RTY'], 100),
                    'direction': np.random.choice(['Long', 'Short'], 100),
                    'entry_price': np.random.uniform(4000, 5000, 100),
                    'exit_price': np.random.uniform(4000, 5000, 100),
                    'quantity': np.random.randint(1, 10, 100)
                })
                sample_data['pnl'] = (sample_data['exit_price'] - sample_data['entry_price']) * sample_data['quantity']
                st.session_state.trade_data = sample_data
                st.success("Synthetic sample data generated!")
        except Exception as e:
            self.error_handler.handle_error(e, "Failed to load sample data")

    def _render_login_page(self):
        """Render the login page."""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### 🔐 Login to TradeSense")

            with st.form("login_form"):
                username = st.text_input("Username/Email")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login", type="primary")

                if login_btn and username and password:
                    result = self.auth_manager.login_user(username, password)
                    if result["success"]:
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result["message"])

            st.markdown("---")

            with st.expander("Create New Account"):
                with st.form("register_form"):
                    new_username = st.text_input("Username", key="reg_username")
                    new_email = st.text_input("Email", key="reg_email")
                    new_password = st.text_input("Password", type="password", key="reg_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                    register_btn = st.form_submit_button("Register")

                    if register_btn and new_username and new_email and new_password:
                        if new_password != confirm_password:
                            st.error("Passwords don't match")
                        else:
                            result = self.auth_manager.register_user(new_username, new_email, new_password)
                            if result["success"]:
                                st.success("Registration successful! You can now login.")
                            else:
                                st.error(result["message"])

    def run(self):
        """Run the main application."""
        try:
            # Render header
            self.render_header()

            # Authentication check
            if not st.session_state.authenticated:
                self._render_login_page()
                return

            # Render sidebar
            self.render_sidebar()

            # Render main content based on selected page
            if st.session_state.current_page == "Dashboard":
                render_dashboard_tabs()
            elif st.session_state.current_page == "Analytics":
                render_dashboard_tabs()
            elif st.session_state.current_page == "Trade Data":
                render_dashboard_tabs()
            elif st.session_state.current_page == "Integrations":
                render_dashboard_tabs()
            elif st.session_state.current_page == "Settings":
                render_dashboard_tabs()
            elif st.session_state.current_page == "Admin Panel" and st.session_state.user_role == 'admin':
                st.info("Admin panel functionality coming soon")
            elif st.session_state.current_page == "System Monitor" and st.session_state.user_role == 'admin':
                if self.health_monitor:
                    try:
                        health_checks = self.health_monitor.run_health_checks()
                        st.json({k: {
                            'status': str(v.status),
                            'message': v.message,
                            'value': v.value
                        } for k, v in health_checks.items()})
                    except Exception as e:
                        st.error(f"Health monitoring error: {e}")
                else:
                    st.info("Health monitoring not available")

        except Exception as e:
            self.error_handler.handle_error(e, f"Error in page: {st.session_state.current_page}")
            st.error("An error occurred. Please check the error logs or contact support.")

def main():
    """Main application entry point."""
    try:
        app = TradeSenseApp()
        app.run()
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        logger.error(traceback.format_exc())
        st.error("Critical application error. Please restart the application.")

if __name__ == "__main__":
    main()