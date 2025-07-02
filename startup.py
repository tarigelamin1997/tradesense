#!/usr/bin/env python3
"""
TradeSense Application Startup Module
Handles initialization, error recovery, and application launch
"""

import streamlit as st
import logging
import sys
import os
from pathlib import Path

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

def show_debug_info():
    """Show debug information in case of startup issues."""
    with st.expander("🔍 Debug Information"):
        st.write("**Python Version:**", sys.version)
        st.write("**Python Path:**", sys.path)
        st.write("**Working Directory:**", os.getcwd())
        st.write("**Session State Keys:**", list(st.session_state.keys()))

        # Check for core modules
        try:
            import pandas
            st.write("✅ Pandas:", pandas.__version__)
        except ImportError:
            st.write("❌ Pandas: Not available")

        try:
            import numpy
            st.write("✅ Numpy:", numpy.__version__)
        except ImportError:
            st.write("❌ Numpy: Not available")

        try:
            import plotly
            st.write("✅ Plotly:", plotly.__version__)
        except ImportError:
            st.write("❌ Plotly: Not available")

def main():
    """Main application entry point."""
    try:
        # Initialize session state
        initialize_session_state()

        # Import and create the app factory
        from core.app_factory import AppFactory

        # Create and run the application
        app = AppFactory()
        app.create_app()

        logger.info("✅ TradeSense application started successfully")

    except ImportError as e:
        st.error(f"❌ Import Error: {str(e)}")
        logger.error(f"Import error in main(): {str(e)}")

        st.write("🔧 **Application Recovery Mode**")
        st.write("Some components couldn't be loaded. Please check the debug information below.")
        show_debug_info()

        if st.button("🔄 Retry Loading"):
            st.rerun()
            
    except ValueError as e:
        if "truth value of a DataFrame is ambiguous" in str(e):
            st.error("❌ DataFrame Comparison Error: Please refresh the page")
            logger.error(f"DataFrame ambiguity error: {str(e)}")
            if st.button("🔄 Refresh Page"):
                st.rerun()
        else:
            st.error(f"❌ Value Error: {str(e)}")
            show_debug_info()
            
    except Exception as e:
        # Catch any DataFrame comparison errors specifically
        if "truth value of a DataFrame is ambiguous" in str(e):
            st.error("❌ DataFrame Error: The application encountered a data comparison issue")
            logger.error(f"DataFrame error in startup: {str(e)}")
            st.info("Try refreshing the page or clearing your data")
            if st.button("🔄 Clear Session and Restart"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            st.error(f"❌ Application Error: {str(e)}")
            logger.error(f"Unexpected error in main(): {str(e)}")
            show_debug_info()

        if st.button("🔄 Restart Application"):
            st.rerun()

    

if __name__ == "__main__":
    main()