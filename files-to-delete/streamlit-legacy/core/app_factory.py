#!/usr/bin/env python3
"""
TradeSense App Factory
Main application coordinator and interface renderer
"""

import streamlit as st
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)

class AppFactory:
    """Main application factory for TradeSense."""

    def __init__(self):
        """Initialize the app factory."""
        self.components_loaded = False
        self._load_components()

    def _load_components(self):
        """Load all necessary components with error handling."""
        try:
            # Import all core components
            from .data_upload_handler import render_data_upload_section
            from .analysis_engine import render_analysis_controls, run_analysis
            from .dashboard_manager import render_dashboard_tabs
            from .dashboard_components import render_dashboard
            from .analytics_components import render_analytics
            from .trade_data_components import render_trade_data
            from .settings_components import render_settings

            # Store components as instance attributes
            self.render_data_upload = render_data_upload_section
            self.render_analysis_controls = render_analysis_controls
            self.run_analysis = run_analysis
            self.render_dashboard_tabs = render_dashboard_tabs
            self.render_dashboard = render_dashboard
            self.render_analytics = render_analytics
            self.render_trade_data = render_trade_data
            self.render_settings = render_settings

            self.components_loaded = True
            logger.info("✅ All core components loaded successfully")

        except ImportError as e:
            logger.error(f"❌ Failed to load core components: {e}")
            self.components_loaded = False

    def create_app(self):
        """Create and render the main application interface."""
        if not self.components_loaded:
            st.error("🔧 Application components are loading... Please refresh.")
            st.stop()

        try:
            # Main app header
            st.title("📈 TradeSense - Trading Analytics")

            # Sidebar for navigation
            with st.sidebar:
                st.header("🎯 Navigation")

                # Check if user has uploaded data
                if not st.session_state.get('data_uploaded', False):
                    st.info("👆 Upload trade data to begin analysis")

                # Analysis controls
                if st.session_state.get('data_uploaded', False):
                    self.render_analysis_controls()

            # Main content area
            if not st.session_state.get('data_uploaded', False):
                # Data upload section
                st.header("📊 Upload Trade Data")
                self.render_data_upload()

            else:
                # Main dashboard tabs
                self.render_dashboard_tabs()

        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"❌ Application Error: {str(e)}")

            # Debug information
            with st.expander("🔍 Debug Information"):
                st.code(f"Error: {str(e)}")
                st.code(f"Session State Keys: {list(st.session_state.keys())}")

                # Add traceback for debugging
                import traceback
                st.code(f"Traceback:\n{traceback.format_exc()}")
        # Check if data exists and is valid
        if st.session_state.get('trade_data') is not None and len(st.session_state.trade_data) > 0:
            # Data validation passed - dashboard can render properly
            pass