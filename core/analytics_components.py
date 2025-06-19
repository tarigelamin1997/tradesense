#!/usr/bin/env python3
"""
Analytics Components
Renders detailed analytics content
"""

import streamlit as st
import pandas as pd

def render_analytics():
    """Render analytics page."""
    analytics_result = st.session_state.get('analytics_result')
    if analytics_result is not None:
        _render_comprehensive_analytics(analytics_result)
    else:
        st.info("Upload trade data and run analysis to view detailed analytics")

def _render_comprehensive_analytics(analytics_result):
    """Render comprehensive analytics."""
    st.markdown("# 📊 Trading Performance Analytics")

    # Basic metrics
    _render_hero_metrics(analytics_result)

    # Detailed sections
    _render_streak_analysis(analytics_result)
    _render_distribution_analysis(analytics_result)
    _render_symbol_performance(analytics_result)

def _render_hero_metrics(analytics_result):
    """Render hero metrics section."""
    st.markdown("## 🎯 Performance Overview")

    kpis = analytics_result.get('kpis', {})
    basic_stats = analytics_result.get('basic_stats', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        net_pnl = kpis.get('net_pnl_after_commission', 0)
        st.metric("💰 Net P&L", f"${net_pnl:,.2f}")

    with col2:
        win_rate = kpis.get('win_rate_percent', 0)
        st.metric("🎯 Win Rate", f"{win_rate:.1f}%")

    with col3:
        profit_factor = basic_stats.get('profit_factor', 0)
        st.metric("📈 Profit Factor", f"{profit_factor:.2f}")

def _render_streak_analysis(analytics_result):
    """Render streak analysis."""
    st.markdown("## 🔥 Streak Analysis")

    streaks = analytics_result.get('streaks', {})

    col1, col2 = st.columns(2)
    with col1:
        max_win_streak = streaks.get('max_win_streak', 0)
        st.metric("🔥 Max Win Streak", f"{max_win_streak} trades")

    with col2:
        max_loss_streak = streaks.get('max_loss_streak', 0)
        st.metric("❄️ Max Loss Streak", f"{max_loss_streak} trades")

def _render_distribution_analysis(analytics_result):
    """Render distribution analysis."""
    st.markdown("## 📊 Trade Distribution")

    median_results = analytics_result.get('median_results', {})

    col1, col2, col3 = st.columns(3)
    with col1:
        median_pnl = median_results.get('median_pnl', 0)
        st.metric("📈 Median P&L", f"${median_pnl:.2f}")

    with col2:
        median_win = median_results.get('median_win', 0)
        st.metric("✅ Median Win", f"${median_win:.2f}")

    with col3:
        median_loss = median_results.get('median_loss', 0)
        st.metric("📉 Median Loss", f"${median_loss:.2f}")

def _render_symbol_performance(analytics_result):
    """Render symbol performance."""
    st.markdown("## 🎯 Performance by Symbol")

    symbol_performance = analytics_result.get('symbol_performance', [])

    if symbol_performance and len(symbol_performance) > 0:
        df_symbols = pd.DataFrame(symbol_performance)
        st.dataframe(df_symbols, use_container_width=True)
    else:
        # Fallback to manual calculation
        trade_data = st.session_state.get('trade_data')
        if trade_data is not None and 'symbol' in trade_data.columns and 'pnl' in trade_data.columns:
            symbol_stats = _calculate_symbol_performance(trade_data)
            if symbol_stats:
                df_symbols = pd.DataFrame(symbol_stats)
                st.dataframe(df_symbols, use_container_width=True)
            else:
                st.info("No symbol data available")
        else:
            st.info("Symbol performance data not available")

def _calculate_symbol_performance(trade_data):
    """Calculate symbol performance manually."""
    try:
        symbol_stats = []
        for symbol in trade_data['symbol'].unique():
            symbol_trades = trade_data[trade_data['symbol'] == symbol]
            total_trades = len(symbol_trades)
            total_pnl = symbol_trades['pnl'].sum()
            wins = len(symbol_trades[symbol_trades['pnl'] > 0])
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

            symbol_stats.append({
                'Symbol': symbol,
                'Trades': total_trades,
                'Total P&L': f"${total_pnl:,.2f}",
                'Win Rate': f"{win_rate:.1f}%"
            })

        return symbol_stats
    except Exception:
        return []
```

Adding the provided changes.