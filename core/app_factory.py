def _initialize_app(self):
        """Initialize the main application."""
        try:
            # Page config is now handled in app.py to avoid duplicate calls
            
            # Import main modules
            from analytics import TradingAnalytics
            from interactive_table import render_interactive_table
            
            # Create main application interface
            st.title("📈 TradeSense - Trading Analytics Platform")
            
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
            import logging
            logging.error(f"App initialization error: {str(e)}")
    
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