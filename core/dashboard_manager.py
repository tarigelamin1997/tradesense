
#!/usr/bin/env python3
"""
Dashboard Manager
Handles the main dashboard tabs and routing
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_dashboard_tabs():
    """Render main dashboard tabs."""
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Analytics", "📋 Trade Data", "⚙️ Settings"])
    
    with tab1:
        try:
            from core.dashboard_components import render_dashboard
            render_dashboard()
        except Exception as e:
            st.error(f"Dashboard error: {str(e)}")
            _render_basic_dashboard()
    
    with tab2:
        try:
            from core.analytics_components import render_analytics
            render_analytics()
        except Exception as e:
            st.error(f"Analytics error: {str(e)}")
            _render_basic_analytics()
    
    with tab3:
        try:
            from core.trade_data_components import render_trade_data
            render_trade_data()
        except Exception as e:
            st.error(f"Trade Data error: {str(e)}")
            _render_basic_trade_data()
    
    with tab4:
        try:
            from core.settings_components import render_settings
            render_settings()
        except Exception as e:
            st.error(f"Settings error: {str(e)}")
            _render_basic_settings()

def _render_basic_dashboard():
    """Render basic dashboard when main fails."""
    analytics_result = st.session_state.get('analytics_result')
    if analytics_result is not None:
        basic_stats = analytics_result.get('basic_stats', {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", basic_stats.get('total_trades', 0))
        with col2:
            st.metric("Win Rate", f"{basic_stats.get('win_rate', 0):.1f}%")
        with col3:
            st.metric("Total P&L", f"${basic_stats.get('total_pnl', 0):,.2f}")
        with col4:
            st.metric("Wins", basic_stats.get('wins', 0))
    else:
        st.info("Upload trade data and run analysis to view dashboard")

def _render_basic_analytics():
    """Render basic analytics when main fails."""
    analytics_result = st.session_state.get('analytics_result')
    if analytics_result is not None:
        st.markdown("## 📊 Basic Analytics")
        basic_stats = analytics_result.get('basic_stats', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Trades", basic_stats.get('total_trades', 0))
            st.metric("Wins", basic_stats.get('wins', 0))
        with col2:
            st.metric("Win Rate", f"{basic_stats.get('win_rate', 0):.1f}%")
            st.metric("Total P&L", f"${basic_stats.get('total_pnl', 0):,.2f}")
    else:
        st.info("Upload trade data and run analysis to view analytics")

def _render_basic_trade_data():
    """Render basic trade data when main fails."""
    trade_data = st.session_state.get('trade_data')
    if trade_data is not None and not trade_data.empty:
        st.write(f"Showing {len(trade_data)} trades")
        st.dataframe(trade_data, use_container_width=True)
    else:
        st.info("No trade data available")

def _render_basic_settings():
    """Render basic settings when main fails."""
    st.write("Settings page - configuration options would go here")
    
    if st.button("🧹 Clear Session Data"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Session data cleared!")
        st.rerun()
