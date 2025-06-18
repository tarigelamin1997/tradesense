
#!/usr/bin/env python3
"""
TradeSense App Factory
Handles main application initialization and routing
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

class AppFactory:
    """Factory class for creating and initializing the main TradeSense application."""
    
    def __init__(self):
        """Initialize the app factory."""
        self.app_initialized = False
    
    def create_app(self):
        """Create and initialize the main application."""
        try:
            if not self.app_initialized:
                self._initialize_app()
                self.app_initialized = True
        except Exception as e:
            st.error(f"Failed to create application: {str(e)}")
            logger.error(f"App creation error: {str(e)}")
    
    def _initialize_app(self):
        """Initialize the main application."""
        try:
            # Page config is now handled in app.py to avoid duplicate calls
            
            # Import main modules (with error handling for missing modules)
            try:
                from analytics import TradingAnalytics
            except ImportError:
                st.warning("Analytics module not fully available - some features may be limited")
                TradingAnalytics = None
            
            try:
                from interactive_table import render_interactive_table
            except ImportError:
                st.warning("Interactive table module not available - using basic displays")
                render_interactive_table = None
            
            # Create main application interface
            st.title("📈 TradeSense - Trading Analytics Platform")
            
            # Data upload section
            self._render_data_upload_section()
            
            # Show analysis if data is available
            if st.session_state.get('analysis_complete', False):
                st.info("✅ Analysis completed! Results are displayed above.")
            elif st.session_state.get('trade_data') is not None:
                if st.button("🔄 Run Comprehensive Analysis", type="primary"):
                    st.session_state.data_uploaded = True
                    st.rerun()
            
            # Sidebar navigation
            with st.sidebar:
                st.header("Navigation")
                page = st.selectbox(
                    "Select Page",
                    ["Dashboard", "Analytics", "Trade Data", "Settings"],
                    key="main_nav"
                )
            
            # Main content area
            if page == "Dashboard":
                self._render_dashboard()
            elif page == "Analytics":
                self._render_analytics()
            elif page == "Trade Data":
                self._render_trade_data()
            elif page == "Settings":
                self._render_settings()
                
        except Exception as e:
            st.error(f"Failed to initialize application: {str(e)}")
            logger.error(f"App initialization error: {str(e)}")
    
    def _render_data_upload_section(self):
        """Render data upload interface."""
        st.subheader("📁 Upload Trade Data")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=['csv', 'xlsx', 'xls'],
            help="Upload your trade history file for analysis"
        )
        
        if uploaded_file is not None:
            try:
                # Import data processing modules
                from data_import.utils import load_trade_data
                from data_validation import DataValidator
                
                # Load and validate data
                with st.spinner("Loading and validating data..."):
                    df = load_trade_data(uploaded_file)
                    
                    if df.empty:
                        st.error("The uploaded file is empty or could not be read.")
                        return
                    
                    # Validate data
                    validator = DataValidator()
                    cleaned_df, report = validator.validate_and_clean(df)
                    
                    if cleaned_df.empty:
                        st.error("No valid data found after cleaning. Please check your file format.")
                        st.write("Validation Report:", report)
                        return
                    
                    # Store data in session state
                    st.session_state.trade_data = cleaned_df
                    st.session_state.data_uploaded = True
                    
                    st.success(f"✅ Successfully loaded {len(cleaned_df)} trades!")
                    
                    # Show data preview
                    with st.expander("📊 Data Preview", expanded=True):
                        st.dataframe(cleaned_df.head(10), use_container_width=True)
                    
                    # Trigger immediate analysis
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.info("Please ensure your file has the required columns: symbol, entry_time, exit_time, entry_price, exit_price, pnl, direction")
    
    def _render_dashboard(self):
        """Render the main dashboard."""
        st.header("📊 Dashboard")
        st.info("Welcome to TradeSense! Use the sidebar to navigate.")
        
        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", "0")
        with col2:
            st.metric("Win Rate", "0%")
        with col3:
            st.metric("Total P&L", "$0.00")
    
    def _render_analytics(self):
        """Render analytics page."""
        st.header("📈 Analytics")
        st.info("Analytics features will be available once trade data is imported.")
    
    def _render_trade_data(self):
        """Render trade data page."""
        st.header("📋 Trade Data")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload trade data",
            type=['csv', 'xlsx'],
            help="Upload your trading data in CSV or Excel format"
        )
        
        if uploaded_file:
            st.success("File uploaded successfully!")
            st.info("Trade data processing will be implemented here.")
    
    def _render_settings(self):
        """Render settings page."""
        st.header("⚙️ Settings")
        
        st.subheader("Account Settings")
        st.text_input("Display Name", value="User")
        st.text_input("Email", value="user@example.com")
        
        st.subheader("Preferences")
        st.selectbox("Theme", ["Light", "Dark"])
        st.selectbox("Currency", ["USD", "EUR", "GBP"])
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")
