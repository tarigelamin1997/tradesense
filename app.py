#!/usr/bin/env python3
"""
TradeSense - Advanced Trading Analytics Platform
Main Application Entry Point
"""

import streamlit as st
import sys
import os

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

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main function from startup module
from startup import main

# Run the application
if __name__ == "__main__":
    main()