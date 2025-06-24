#!/usr/bin/env python3
"""
TradeSense - Advanced Trading Analytics Platform
Main Streamlit application entry point
"""

import streamlit as st

# Set up the page configuration FIRST - before any other Streamlit commands
st.set_page_config(
    page_title="TradeSense - Trading Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
import os
import logging
from datetime import datetime

# Defer heavy imports until needed
def get_pandas():
    import pandas as pd
    return pd

def get_plotly():
    import plotly.graph_objects as go
    import plotly.express as px
    return go, px

def get_numpy():
    import numpy as np
    return np

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

    # Import dashboard manager functions directly
    from core.dashboard_manager import render_dashboard_tabs

    # Import optional components with fallbacks
    try:
        from data_validation import DataValidator
    except ImportError:
        logger.warning("Data validation not available")
        DataValidator = None

    try:
        from error_handler import ErrorHandler
    except ImportError:
        logger.warning("Error handler not available")
        ErrorHandler = None

    try:
        from notification_system import notification_manager
    except ImportError:
        logger.warning("Notification system not available")
        notification_manager = None

    try:
        from health_monitoring import SystemHealthMonitor
        HEALTH_MONITORING_AVAILABLE = True
    except ImportError:
        HEALTH_MONITORING_AVAILABLE = False
        logger.warning("Health monitoring not available")

except ImportError as e:
    logger.error(f"Critical import error: {e}")
    st.error(f"Critical import error: {e}")
    st.info("Please check that all required dependencies are installed.")
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
        # Lazy initialization for faster startup
        self.auth_manager = None
        self.health_monitor = None
        self.notification_manager = None
        self.error_handler = None
        
        # Initialize session state immediately
        self._initialize_session_state()
        
        # Initialize components only when needed
        self._init_auth_manager()

    def _init_auth_manager(self):
        """Initialize auth manager lazily."""
        if self.auth_manager is None:
            try:
                self.auth_manager = AuthManager()
                # Skip database repair during startup for speed
                current_user = self.auth_manager.get_current_user()
                if current_user and not st.session_state.authenticated:
                    st.session_state.authenticated = True
                    st.session_state.user_role = current_user.get('role', 'user')
            except Exception as e:
                logger.warning(f"Auth initialization failed: {e}")
                self.auth_manager = None

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

        # Check if user is already authenticated from auth manager
        if self.auth_manager:
            try:
                current_user = self.auth_manager.get_current_user()
                if current_user and not st.session_state.authenticated:
                    st.session_state.authenticated = True
                    st.session_state.user_role = current_user.get('role', 'user')
            except Exception as e:
                logger.warning(f"Auth check failed: {e}")
                pass

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
            # App branding
            st.markdown('<div class="sidebar-logo">📊 TradeSense</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-tagline">Professional Trading Analytics</div>', unsafe_allow_html=True)
            st.markdown("---")

            # Enhanced Theme toggle with System theme as default
            st.subheader("🎨 Appearance")
            if 'theme_mode' not in st.session_state:
                st.session_state.theme_mode = 'system'  # Default to system theme

            theme_mode = st.radio(
                "Theme",
                options=['system', 'dark', 'light'],
                index=['system', 'dark', 'light'].index(st.session_state.theme_mode),
                format_func=lambda x: {'system': '🖥️ System', 'dark': '🌙 Dark', 'light': '☀️ Light'}[x],
                horizontal=True
            )

            if theme_mode != st.session_state.theme_mode:
                st.session_state.theme_mode = theme_mode
                st.rerun()

            st.markdown("---")

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

            # Quick actions
            st.markdown("### Quick Actions")
            if st.button("🔄 Refresh Data"):
                st.rerun()

            if st.button("📥 Sample Data"):
                self._load_sample_data()

    def _load_sample_data(self):
        """Load sample trading data for demonstration."""
        try:
            # Import pandas and numpy here to avoid import issues
            pd = get_pandas()
            np = get_numpy()
            
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
            logger.error(f"Failed to load sample data: {e}")
            st.error(f"Failed to load sample data: {e}")

    def _render_login_page(self):
        """Render the login page."""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### 🔐 Login to TradeSense")

            with st.form("login_form"):
                username = st.text_input("Username/Email")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login", type="primary")

                if login_btn:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("Logging in..."):
                            result = self.auth_manager.login_user(username, password)
                            if result["success"]:
                                st.success("Login successful!")
                                # Force a rerun to refresh the app state
                                st.session_state.just_logged_in = True
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

                    if register_btn:
                        if not all([new_username, new_email, new_password, confirm_password]):
                            st.error("All fields are required")
                        elif new_password != confirm_password:
                            st.error("Passwords don't match")
                        else:
                            with st.spinner("Creating account..."):
                                result = self.auth_manager.register_user(new_username, new_email, new_password)
                                if result["success"]:
                                    st.success("Registration successful! You can now login.")
                                else:
                                    st.error(result["message"])

    def run(self):
        """Run the main application."""
        try:
            # Apply theme
            apply_modern_theme()

            # Render header
            self.render_header()

            # Authentication check
            if not st.session_state.authenticated:
                self._render_login_page()
                return

            # Create main layout with sidebar and content
            col_sidebar, col_main = st.columns([1, 4])

            with col_sidebar:
                self.render_sidebar()

            with col_main:
                # Modern status card
                if 'trade_data' not in st.session_state or st.session_state.trade_data is None:
                    st.markdown("""
                    <div class="info-banner">
                        <h3 style="margin: 0 0 0.5rem 0;">📊 Welcome to TradeSense</h3>
                        <p style="margin: 0;">Upload your trade data to unlock powerful analytics and insights</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    total_trades = len(st.session_state.trade_data) if st.session_state.trade_data is not None else 0
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #10b981 0%, #059669 100%); color: white; padding: 1rem; border-radius: 8px; text-align: center; margin: 1rem 0; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                        <h3 style="margin: 0 0 0.5rem 0;">✅ Analytics Active</h3>
                        <p style="margin: 0;">Analyzing {total_trades:,} trades • Professional Mode Enabled</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Render main content using tab navigation
                render_dashboard_tabs()

        except Exception as e:
            logger.error(f"Application error: {e}")
            if self.error_handler:
                try:
                    self.error_handler.handle_error(e, "Application runtime error")
                except:
                    # Fallback error handling
                    st.error("An error occurred. Please refresh the page.")
            else:
                st.error("An error occurred. Please refresh the page.")

def apply_modern_theme():
    """Apply modern theme and styling with system/light/dark mode support."""
    theme_mode = st.session_state.get('theme_mode', 'system')

    # Enhanced theme detection and application
    if theme_mode == 'system':
        # Default to dark theme for system (can be enhanced with JS detection)
        actual_theme = 'dark'
    else:
        actual_theme = theme_mode

    if actual_theme == 'light':
        theme_css = """
        <style>
        /* Enhanced Light Theme - Improved Readability */
        .stApp {
            background: #ffffff;
            color: #1f2937;
        }

        .main-header {
            background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.1);
        }

        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
            border: 1px solid #e1e5e9;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(180deg, #6366f1 0%, #8b5cf6 100%);
        }

        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.12);
            border-color: #c7d2fe;
        }

        .metric-value {
            font-size: 2.25rem;
            font-weight: 800;
            margin-top: 0.75rem;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .info-banner {
            background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            margin: 2rem 0;
            text-align: center;
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.3);
        }

        .sidebar-logo {
            font-size: 28px;
            font-weight: bold;
            color: #3b82f6;
            text-align: center;
            margin-bottom: 0.5rem;
        }

        .sidebar-tagline {
            font-size: 13px;
            color: #64748b;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        /* Enhanced Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 16px;
            padding: 1rem 2rem;
            font-weight: 700;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: 0 16px 48px rgba(99, 102, 241, 0.5);
            background: linear-gradient(135deg, #5855eb 0%, #7c3aed 100%);
        }

        /* Enhanced File uploader */
        .stFileUploader > div {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 3px dashed #c7d2fe;
            border-radius: 24px;
            padding: 4rem 2rem;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
        }

        .stFileUploader > div:hover {
            border-color: #6366f1;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
        }

        /* Enhanced Tables */
        .stDataFrame {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }

        /* Enhanced Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            margin-bottom: 2rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px;
            background: white;
            border-radius: 12px;
            padding: 0 32px;
            border: 1px solid #e2e8f0;
            color: #64748b;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            color: white;
            border: none;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        }
        </style>
        """
    else:
        theme_css = """
        <style>
        /* Enhanced Dark Theme */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
        }

        .main-header {
            background: linear-gradient(90deg, #06b6d4 0%, #8b5cf6 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(6, 182, 212, 0.4);
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.08);
            padding: 1.5rem;
            border-radius: 16px;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            background: rgba(255, 255, 255, 0.12);
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            margin-top: 0.5rem;
        }

        .info-banner {
            background: linear-gradient(90deg, #06b6d4 0%, #0891b2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            text-align: center;
            box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4);
        }

        .sidebar-logo {
            font-size: 28px;
            font-weight: bold;
            color: #06b6d4;
            text-align: center;
            margin-bottom: 0.5rem;
        }

        .sidebar-tagline {
            font-size: 13px;
            color: #94a3b8;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        /* Enhanced Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(6, 182, 212, 0.6);
        }

        /* Enhanced File uploader */
        .stFileUploader > div {
            background: rgba(255, 255, 255, 0.05);
            border: 2px dashed rgba(6, 182, 212, 0.5);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
        }

        .stFileUploader > div:hover {
            border-color: #06b6d4;
            background: rgba(6, 182, 212, 0.1);
            transform: scale(1.02);
        }

        /* Enhanced Tables */
        .stDataFrame {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            overflow: hidden;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        }

        /* Enhanced Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            margin-bottom: 2rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: 60px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 0 32px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #94a3b8;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
            color: white;
            border: none;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(6, 182, 212, 0.4);
        }
        </style>
        """

    # Animated loading spinner and responsive design (common to both themes)
    common_css = """
    <style>
    /* Animated loading spinner */
    .loading-spinner {
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top: 3px solid#00d4ff;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* Counter animations */
    @keyframes countUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .metric-card {
        animation: countUp 0.6s ease-out;
    }

    /* Hover effects for tables */
    .dataframe tbody tr:hover {
        background-color: rgba(0, 212, 255, 0.1);
        transition: background-color 0.2s ease;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h2 {
            font-size: 1.5rem;
        }

        .metric-card {
            padding: 1rem;
        }

        .sidebar-logo {
            font-size: 20px;
        }
    }
    </style>
    """

    st.markdown(theme_css + common_css, unsafe_allow_html=True)

def main():
    """Main application entry point."""
    try:
        app = TradeSenseApp()
        app.run()
    except Exception as e:
        logger.error(f"Critical application error: {e}")
        st.error("Critical application error. Please refresh the page.")

if __name__ == "__main__":
    main()