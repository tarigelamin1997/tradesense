
#!/usr/bin/env python3
"""
TradeSense Startup Module
Handles application initialization and main entry point
"""

import streamlit as st
import sys
import os
import logging
from typing import Optional

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "current_page": "login",
        "startup_complete": False,
        "data_uploaded": False,
        "data_analyzed": False,
        "trade_data": None,
        "analytics_result": None,
        "analysis_complete": False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def check_system_dependencies():
    """Check if critical system dependencies are available."""
    missing_deps = []
    
    try:
        import pandas as pd
    except ImportError:
        missing_deps.append("pandas")
    
    try:
        import numpy as np
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import plotly.graph_objects as go
    except ImportError:
        missing_deps.append("plotly")
    
    if missing_deps:
        st.error(f"Missing critical dependencies: {', '.join(missing_deps)}")
        st.info("🔄 Installing dependencies... Please wait and refresh the page.")
        return False
    
    return True


def main():
    """Main application entry point."""
    try:
        initialize_session_state()
        
        # Check system dependencies first
        if not check_system_dependencies():
            st.stop()
        
        # Import auth module with fallback
        try:
            from auth import render_auth_interface
        except ImportError as e:
            logger.error(f"Auth module import error: {str(e)}")
            st.error("🔧 System is initializing. Please refresh the page.")
            st.stop()

        if not st.session_state.authenticated:
            current_user = render_auth_interface()
            if current_user:
                st.session_state.authenticated = True
                st.session_state.user_id = current_user.get("id") or current_user.get("user_id")
                st.session_state.startup_complete = True
                logger.info(f"User authenticated: {st.session_state.user_id}")
                st.rerun()
        else:
            try:
                from core.app_factory import AppFactory
                app_factory = AppFactory()
                app_factory.create_app()
            except ImportError as core_err:
                logger.error(f"Core import error: {core_err}")
                st.error("⚠️ Application core is loading. Please refresh the page.")
                show_debug_tools()

            if not st.session_state.get('startup_complete', False):
                st.session_state.startup_complete = True

    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        logger.error(f"Unexpected error in main(): {str(e)}")
        show_debug_tools()


def show_debug_tools():
    """UI for developer tools like log download or session reset."""
    st.divider()
    st.subheader("🛠 Developer Tools")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reload App"):
            st.rerun()

    with col2:
        if st.button("🧹 Reset Session"):
            st.session_state.clear()
            st.rerun()
    
    with col3:
        if st.button("📋 System Info"):
            st.text(f"Python: {sys.version}")
            st.text(f"Platform: {sys.platform}")

    if os.path.exists("logs/application.log"):
        with open("logs/application.log", "r") as f:
            st.download_button(
                label="📥 Download Log File",
                data=f.read(),
                file_name="application.log",
                mime="text/plain"
            )


if __name__ == "__main__":
    main()
