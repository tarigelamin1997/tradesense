
#!/usr/bin/env python3
"""
TradeSense - Advanced Trading Analytics Platform
Main Streamlit application entry point
"""

import streamlit as st
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
    from core.dashboard_manager import DashboardManager
    from auth import AuthManager
    from analytics import TradingAnalytics
    from data_validation import DataValidator
    from error_handler import ErrorHandler
    from health_monitoring import HealthMonitor
    from notification_system import NotificationSystem
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Critical import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="TradeSense - Trading Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2d5aa0;
        margin: 0.5rem 0;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online { background-color: #28a745; }
    .status-warning { background-color: #ffc107; }
    .status-offline { background-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

class TradeSenseApp:
    """Main TradeSense application class."""
    
    def __init__(self):
        """Initialize the TradeSense application."""
        self.auth_manager = AuthManager()
        self.dashboard_manager = DashboardManager()
        self.health_monitor = HealthMonitor()
        self.notification_system = NotificationSystem()
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
            health_status = self.health_monitor.get_system_status()
            status_class = "status-online" if health_status['status'] == 'healthy' else "status-warning"
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <span class="status-indicator {status_class}"></span>
                System Status: {health_status['status'].title()}
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
    
    def run(self):
        """Run the main application."""
        try:
            # Render header
            self.render_header()
            
            # Authentication check
            if not st.session_state.authenticated:
                if self.auth_manager.render_login():
                    st.rerun()
                return
            
            # Render sidebar
            self.render_sidebar()
            
            # Render main content based on selected page
            if st.session_state.current_page == "Dashboard":
                self.dashboard_manager.render_dashboard()
            elif st.session_state.current_page == "Analytics":
                self.dashboard_manager.render_analytics()
            elif st.session_state.current_page == "Trade Data":
                self.dashboard_manager.render_trade_data()
            elif st.session_state.current_page == "Integrations":
                self.dashboard_manager.render_integrations()
            elif st.session_state.current_page == "Settings":
                self.dashboard_manager.render_settings()
            elif st.session_state.current_page == "Admin Panel" and st.session_state.user_role == 'admin':
                self.dashboard_manager.render_admin_panel()
            elif st.session_state.current_page == "System Monitor" and st.session_state.user_role == 'admin':
                self.dashboard_manager.render_system_monitor()
            
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
