#!/usr/bin/env python3
"""
TradeSense App Factory
Handles main application initialization and routing
"""

import streamlit as st
import logging
from module_checker import module_checker

logger = logging.getLogger(__name__)

class AppFactory:
    """Factory class for creating and managing the TradeSense application."""

    def __init__(self):
        self.initialized = False

    def create_app(self):
        """Create and initialize the main TradeSense application."""
        try:
            # Main application header
            st.title("📈 TradeSense - Trading Analytics Platform")

            # Only show module warnings after user has uploaded data
            if st.session_state.get('trade_data') is not None:
                module_checker.display_warnings_if_needed()

            # Data upload section
            self._render_data_upload_section()

            # Show analysis if data is available
            if st.session_state.get('analysis_complete', False):
                st.info("✅ Analysis completed! Results are displayed above.")
            elif st.session_state.get('trade_data') is not None:
                if st.button("🔄 Run Comprehensive Analysis", type="primary"):
                    self._run_analysis()

            # Navigation tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Analytics", "📋 Trade Data", "⚙️ Settings"])
            
            with tab1:
                self._render_dashboard()
            
            with tab2:
                self._render_analytics()
            
            with tab3:
                self._render_trade_data()
            
            with tab4:
                self._render_settings()

        except Exception as e:
            st.error(f"Failed to initialize application: {str(e)}")
            logger.error(f"App initialization error: {str(e)}")

    def _render_data_upload_section(self):
        """Render data upload interface."""
        st.subheader("📁 Upload Trade Data")
        st.write("Choose a CSV or Excel file")

        # File uploader
        uploaded_file = st.file_uploader(
            "Drag and drop file here",
            type=['csv', 'xlsx', 'xls'],
            help="Limit 200MB per file • CSV, XLSX, XLS"
        )

        if uploaded_file is not None:
            try:
                # Process the uploaded file
                from trade_entry_manager import trade_manager
                import pandas as pd

                # Read the file
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                # Add trades to manager
                result = trade_manager.add_file_trades(df, f"file_{uploaded_file.name}")

                if result['status'] == 'success':
                    st.success(f"✅ Successfully processed {result['trades_added']} trades")
                    st.session_state.trade_data = trade_manager.get_all_trades_dataframe()

                    # Display basic info about uploaded data
                    st.write(f"**File:** {uploaded_file.name}")
                    st.write(f"**Size:** {uploaded_file.size / 1024:.1f}KB")
                else:
                    st.error(f"Error processing file: {result['message']}")
                    st.info("Please ensure your file has the required columns: symbol, entry_time, exit_time, entry_price, exit_price, pnl, direction")

            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.info("Please ensure your file has the required columns: symbol, entry_time, exit_time, entry_price, exit_price, pnl, direction")

    def _run_analysis(self):
        """Run comprehensive analysis without causing infinite loops."""
        try:
            from trade_entry_manager import trade_manager

            # Get analytics
            analytics_result = trade_manager.get_unified_analytics()

            # Store results in session state
            st.session_state.analytics_result = analytics_result
            st.session_state.analysis_complete = True

            st.success("✅ Analysis completed successfully!")

        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            logger.error(f"Analysis error: {str(e)}")

    def _render_dashboard(self):
        """Render main dashboard."""
        if st.session_state.get('trade_data') is not None:
            st.write("Dashboard content would go here")

            # Show basic stats if available
            if st.session_state.get('analytics_result'):
                analytics = st.session_state.analytics_result
                basic_stats = analytics.get('basic_stats', {})

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Trades", basic_stats.get('total_trades', 0))
                with col2:
                    st.metric("Win Rate", f"{basic_stats.get('win_rate', 0):.1f}%")
                with col3:
                    st.metric("Profit Factor", f"{basic_stats.get('profit_factor', 0):.2f}")
                with col4:
                    st.metric("Expectancy", f"${basic_stats.get('expectancy', 0):.2f}")
        else:
            st.info("Upload trade data to view dashboard")

    def _render_analytics(self):
        """Render analytics page."""
        if st.session_state.get('analytics_result'):
            st.write("Detailed analytics would be displayed here")
        else:
            st.info("Upload trade data and run analysis to view detailed analytics")

    def _render_trade_data(self):
        """Render trade data page."""
        if st.session_state.get('trade_data') is not None:
            df = st.session_state.trade_data
            st.write(f"Showing {len(df)} trades")
            st.dataframe(df)
        else:
            st.info("No trade data available")

    def _render_settings(self):
        """Render settings page."""
        st.write("Settings page - configuration options would go here")