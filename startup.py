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

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'

def main():
    """Main application entry point."""
    try:
        logger.info("Starting TradeSense application...")

        # Initialize session state
        initialize_session_state()

        # Import authentication after session state is initialized
        from auth import render_auth_interface

        # Check if user is authenticated
        if not st.session_state.authenticated:
            # Show authentication interface
            current_user = render_auth_interface()

            if current_user:
                st.session_state.authenticated = True
                st.session_state.user_id = current_user.get('id') or current_user.get('user_id')
                st.rerun()
        else:
            # User is authenticated, show main application
            from core.app_factory import AppFactory

            app_factory = AppFactory()
            app_factory.create_app()

            # Check if data was just uploaded and trigger analysis
            if st.session_state.get('data_uploaded', False):
                # Trigger comprehensive analysis
                # Assuming trigger_comprehensive_analysis is defined elsewhere
                # For demonstration purposes, let's just print a message
                st.info("Triggering comprehensive data analysis...")
                logger.info("Triggering comprehensive data analysis...")

    except ImportError as e:
        st.error(f"Import Error: {str(e)}")
        logger.error(f"Import error in main(): {str(e)}")
        st.info("Please check that all required modules are available.")

    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        logger.error(f"Error in main(): {str(e)}")
        st.info("Please check the logs for more details.")

# Placeholder for the trigger_comprehensive_analysis function.
# You will need to implement the actual data analysis pipeline here.
def trigger_comprehensive_analysis():
    """Placeholder function to trigger the comprehensive analysis."""
    # Add your data analysis pipeline logic here.
    # This is just a placeholder.
    logger.info("Comprehensive data analysis triggered.")
    st.session_state['data_analyzed'] = True  # Example: set a session state variable

if __name__ == "__main__":
    main()