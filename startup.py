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
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s',
                    handlers=[
                        logging.FileHandler('logs/application.log'),
                        logging.StreamHandler()
                    ])

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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Main application entry point."""
    try:
        initialize_session_state()
        from auth import render_auth_interface

        if not st.session_state.authenticated:
            current_user = render_auth_interface()
            if current_user:
                st.session_state.authenticated = True
                st.session_state.user_id = current_user.get(
                    "id") or current_user.get("user_id")
                st.session_state.startup_complete = True
                logger.info(f"User authenticated: {st.session_state.user_id}")
                st.rerun()
        else:
            try:
                from core.app_factory import AppFactory
                app_factory = AppFactory()
                app_factory.create_app()
            except ImportError as core_err:
                st.error("⚠️ Could not load core application module.")
                logger.error(f"Import error: {core_err}")
                show_debug_tools()

            if not st.session_state.get('startup_complete', False):
                st.session_state.startup_complete = True

    except ImportError as e:
        st.error(f"❌ Import Error: {str(e)}")
        logger.error(f"Import error in main(): {str(e)}")
        show_debug_tools()

    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        logger.error(f"Unexpected error in main(): {str(e)}")
        show_debug_tools()


def trigger_comprehensive_analysis():
    """Placeholder function to trigger the comprehensive analysis."""
    logger.info("Comprehensive data analysis triggered.")
    st.session_state['data_analyzed'] = True
    st.success("✅ Data analyzed successfully (placeholder logic).")


def show_debug_tools():
    """UI for developer tools like log download or session reset."""
    st.divider()
    st.subheader("🛠 Developer Tools")

    if st.button("🔁 Reload App"):
        st.rerun()

    if st.button("🧹 Reset Session State"):
        st.session_state.clear()
        st.rerun()

    if os.path.exists("logs/application.log"):
        with open("logs/application.log", "r") as f:
            st.download_button(label="📥 Download Log File",
                               data=f.read(),
                               file_name="application.log",
                               mime="text/plain")


if __name__ == "__main__":
    main()
