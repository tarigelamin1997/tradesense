
#!/usr/bin/env python3
"""
Dashboard Components
Renders the main dashboard content
"""

import streamlit as st

def render_dashboard():
    """Render main dashboard."""
    trade_data = st.session_state.get('trade_data')
    if trade_data is not None and not trade_data.empty:
        analytics_result = st.session_state.get('analytics_result')
        if analytics_result is not None:
            _render_kpi_metrics(analytics_result)
            _render_performance_charts(analytics_result)
        else:
            st.info("Run analysis to view detailed dashboard")
    else:
        st.info("Upload trade data to view dashboard")

def _render_kpi_metrics(analytics_result):
    """Render KPI metrics."""
    st.markdown("## 📊 Key Performance Indicators")
    
    basic_stats = analytics_result.get('basic_stats', {})
    kpis = analytics_result.get('kpis', {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", basic_stats.get('total_trades', 0))
    with col2:
        st.metric("Win Rate", f"{basic_stats.get('win_rate', 0):.1f}%")
    with col3:
        st.metric("Profit Factor", f"{basic_stats.get('profit_factor', 0):.2f}")
    with col4:
        st.metric("Net P&L", f"${kpis.get('net_pnl_after_commission', 0):,.2f}")

def _render_performance_charts(analytics_result):
    """Render performance charts."""
    st.markdown("## 📈 Performance Overview")
    
    # Try to render equity curve
    try:
        equity_curve = analytics_result.get('basic_stats', {}).get('equity_curve')
        if equity_curve and len(equity_curve) > 0:
            st.line_chart(equity_curve, height=300)
            st.caption("Cumulative P&L")
        else:
            st.info("Equity curve data not available")
    except Exception:
        st.info("Performance charts unavailable")
