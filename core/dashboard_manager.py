#!/usr/bin/env python3
"""
Dashboard Manager
Manages the main dashboard interface and tab navigation
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_dashboard_tabs():
    """Render the main dashboard with tab navigation."""
    try:
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", 
            "📈 Analytics", 
            "📁 Trade Data", 
            "🔗 Integrations", 
            "⚙️ Settings"
        ])

        with tab1:
            try:
                render_dashboard_overview()
            except Exception as e:
                logger.error(f"Dashboard overview error: {e}")
                st.error("Dashboard section unavailable. Please try refreshing.")

        with tab2:
            try:
                render_analytics_tab()
            except Exception as e:
                logger.error(f"Analytics tab error: {e}")
                st.error("Analytics section unavailable. Please try refreshing.")

        with tab3:
            try:
                render_trade_data_tab()
            except Exception as e:
                logger.error(f"Trade data tab error: {e}")
                st.error("Trade data section unavailable. Please try refreshing.")

        with tab4:
            try:
                render_integrations_tab()
            except Exception as e:
                logger.error(f"Integrations tab error: {e}")
                st.error("Integrations section unavailable. Please try refreshing.")

        with tab5:
            try:
                render_settings_tab()
            except Exception as e:
                logger.error(f"Settings tab error: {e}")
                st.error("Settings section unavailable. Please try refreshing.")

    except Exception as e:
        logger.error(f"Critical error rendering dashboard tabs: {e}")
        st.error("⚠️ Dashboard temporarily unavailable")
        st.info("🔄 Try refreshing the page or contact support if the issue persists")

def render_dashboard_overview():
    """Render the main dashboard overview."""
    st.header("📊 TradeSense Dashboard")

    if 'trade_data' not in st.session_state or st.session_state.trade_data is None:
        st.info("📥 Upload your trade data to get started with analytics")

        # Add quick upload section right on the dashboard
        st.markdown("### Quick Upload")
        try:
            from core.data_upload_handler import render_data_upload_section
            render_data_upload_section(unique_key="dashboard_upload")
        except ImportError:
            try:
                from core.simple_upload import simple_file_upload
                simple_file_upload(unique_key="dashboard_simple_upload")
            except ImportError:
                st.error("Upload functionality not available")

        st.markdown("### Quick Start Guide")
        st.markdown("1. Upload your CSV or Excel file above")
        st.markdown("2. View your analytics in the **Analytics** tab")
        st.markdown("3. Explore detailed data in the **Trade Data** tab")
    else:
        # Show dashboard metrics if data is available
        try:
            from core.analytics_components import render_analytics
            render_analytics()
        except ImportError:
            st.warning("Analytics components not available")

def render_analytics_tab():
    """Render the analytics tab."""
    try:
        from core.analytics_components import render_analytics
        render_analytics()
    except ImportError as e:
        logger.error(f"Analytics import error: {e}")
        st.error("Analytics functionality not available")

def render_trade_data_tab():
    """Render the trade data management tab."""
    st.header("📁 Trade Data Management")

    # Add file upload section
    try:
        from core.data_upload_handler import render_data_upload_section
        render_data_upload_section(unique_key="trade_data_upload")
    except ImportError:
        try:
            from core.simple_upload import simple_file_upload
            simple_file_upload(unique_key="trade_data_simple_upload")
        except ImportError:
            st.error("Upload functionality not available")

    # Show current data if available
    if 'trade_data' in st.session_state and st.session_state.trade_data is not None:
        st.markdown("---")
        st.subheader("📊 Current Data Overview")

        data = st.session_state.trade_data
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Rows", len(data))
        with col2:
            st.metric("Columns", len(data.columns))
        with col3:
            if 'pnl' in data.columns:
                total_pnl = data['pnl'].sum()
                st.metric("Total P&L", f"${total_pnl:,.2f}")

        # Data preview
        with st.expander("📋 Data Preview", expanded=False):
            st.dataframe(data.head(10), use_container_width=True)

def render_integrations_tab():
    """Render the integrations tab."""
    st.header("🔗 Broker Integrations")
    st.info("Broker integration functionality coming soon")

    # Placeholder for future integrations
    st.markdown("### Supported Brokers (Coming Soon)")
    brokers = ["Interactive Brokers", "TD Ameritrade", "E*TRADE", "Charles Schwab", "Apex Trader"]

    for broker in brokers:
        with st.expander(f"{broker} Integration"):
            st.write(f"Connect your {broker} account to automatically import trades")
            st.button(f"Connect {broker}", disabled=True)

def render_settings_tab():
    """Render the settings tab."""
    st.header("⚙️ Settings")

    # User preferences
    st.subheader("User Preferences")

    # Theme selection
    theme = st.selectbox("Theme", ["Light", "Dark"], index=0)

    # Currency preferences
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD"], index=0)

    # Time zone
    timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"], index=0)

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")

    # Data management
    st.markdown("---")
    st.subheader("Data Management")

    if st.button("Clear All Data", type="secondary"):
        if 'trade_data' in st.session_state:
            del st.session_state.trade_data
        st.success("All data cleared!")
        st.rerun()

    # Export options
    if 'trade_data' in st.session_state and st.session_state.trade_data is not None:
        st.markdown("---")
        st.subheader("Export Data")

        if st.button("Export as CSV"):
            csv = st.session_state.trade_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="tradesense_data.csv",
                mime="text/csv"
            )