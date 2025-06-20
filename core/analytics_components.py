#!/usr/bin/env python3
"""
Analytics Components
Renders detailed analytics content
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging
import io
from datetime import datetime

logger = logging.getLogger(__name__)

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
    
    render_export_section()

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
        st.metric("📈 Profit Factor", f"${profit_factor:.2f}")

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

def render_export_section():
    """Render data export options."""
    st.subheader("📤 Export Data")

    # Get trade data from session state
    trade_data = st.session_state.get('trade_data')
    analysis_results = st.session_state.get('analytics_result')

    if trade_data is None:
        st.warning("No trade data available for export")
        return

    # Export options in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        # Export raw trade data
        if st.button("📋 Export Trade Data (CSV)", key="export_trades"):
            csv_data = export_to_csv(trade_data, "trade_data")
            if csv_data:
                st.download_button(
                    label="⬇️ Download Trade Data CSV",
                    data=csv_data,
                    file_name=f"tradesense_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_trades"
                )

    with col2:
        # Export analysis results
        if analysis_results and st.button("📈 Export Analytics (CSV)", key="export_analytics"):
            analytics_csv = export_analytics_to_csv(analysis_results)
            if analytics_csv:
                st.download_button(
                    label="⬇️ Download Analytics CSV",
                    data=analytics_csv,
                    file_name=f"tradesense_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_analytics"
                )

    with col3:
        # Export Excel format
        if st.button("📊 Export Complete Report (Excel)", key="export_excel"):
            excel_data = export_to_excel(trade_data, analysis_results)
            if excel_data:
                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=excel_data,
                    file_name=f"tradesense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )

def export_to_csv(data, data_type="trade_data"):
    """Export data to CSV format."""
    try:
        if isinstance(data, pd.DataFrame):
            # Create CSV buffer
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue()
        else:
            st.error("Data format not supported for CSV export")
            return None
    except Exception as e:
        st.error(f"Export failed: {str(e)}")
        logger.error(f"CSV export error: {e}")
        return None

def export_analytics_to_csv(analysis_results):
    """Export analysis results to CSV format."""
    try:
        if not analysis_results:
            st.warning("No analysis results to export")
            return None

        # Create a DataFrame from analysis results
        analytics_data = []

        # Basic metrics
        if 'kpis' in analysis_results:
            kpis = analysis_results['kpis']
            for key, value in kpis.items():
                analytics_data.append({
                    'Metric': key.replace('_', ' ').title(),
                    'Value': value,
                    'Type': 'Performance Metric'
                })

        # Risk metrics - not implemented, keep for future use
        #if 'risk_metrics' in analysis_results:
        #    risk_metrics = analysis_results['risk_metrics']
        #    for key, value in risk_metrics.items():
        #        analytics_data.append({
        #            'Metric': key.replace('_', ' ').title(),
        #            'Value': value,
        #            'Type': 'Risk Metric'
        #        })
        if 'basic_stats' in analysis_results:
            basic_stats = analysis_results['basic_stats']
            for key, value in basic_stats.items():
                analytics_data.append({
                   'Metric': key.replace('_', ' ').title(),
                   'Value': value,
                   'Type': 'Basic Stats'
                })

        if analytics_data:
            df = pd.DataFrame(analytics_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue()
        else:
            st.warning("No analytics data found to export")
            return None

    except Exception as e:
        st.error(f"Analytics export failed: {str(e)}")
        logger.error(f"Analytics CSV export error: {e}")
        return None

def export_to_excel(trade_data, analysis_results=None):
    """Export data to Excel format with multiple sheets."""
    try:
        # Create Excel buffer
        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Sheet 1: Raw trade data
            if isinstance(trade_data, pd.DataFrame):
                trade_data.to_excel(writer, sheet_name='Trade Data', index=False)

            # Sheet 2: Analytics summary
            if analysis_results:
                analytics_data = []

                # Combine all metrics
                if 'kpis' in analysis_results:
                    for key, value in analysis_results['kpis'].items():
                        analytics_data.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value,
                            'Category': 'Performance'
                        })
                if 'basic_stats' in analysis_results:
                    for key, value in analysis_results['basic_stats'].items():
                        analytics_data.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value,
                            'Category': 'Basic Stats'
                        })

                # Enhanced risk metrics
                if 'risk_metrics' in analysis_results:
                    for key, value in analysis_results['risk_metrics'].items():
                        analytics_data.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value,
                            'Category': 'Risk'
                        })

                # Streak analysis
                if 'streaks' in analysis_results:
                    for key, value in analysis_results['streaks'].items():
                        analytics_data.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value,
                            'Category': 'Streaks'
                        })

                # Time-based analysis
                if 'time_analysis' in analysis_results:
                    for key, value in analysis_results['time_analysis'].items():
                        analytics_data.append({
                            'Metric': key.replace('_', ' ').title(),
                            'Value': value,
                            'Category': 'Time Analysis'
                        })

                if analytics_data:
                    analytics_df = pd.DataFrame(analytics_data)
                    analytics_df.to_excel(writer, sheet_name='Analytics Summary', index=False)

                    # Add symbol performance if available
                    if 'symbol_performance' in analysis_results and analysis_results['symbol_performance']:
                        symbol_df = pd.DataFrame(analysis_results['symbol_performance'])
                        symbol_df.to_excel(writer, sheet_name='Symbol Performance', index=False)

            # Sheet 3: Enhanced export metadata
            from auth import AuthManager
            auth_manager = AuthManager()
            current_user = auth_manager.get_current_user()

            metadata = pd.DataFrame([
                {'Field': 'Export Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                {'Field': 'Application', 'Value': 'TradeSense Professional'},
                {'Field': 'Version', 'Value': '2.0.0'},
                {'Field': 'Total Trades', 'Value': len(trade_data) if isinstance(trade_data, pd.DataFrame) else 'N/A'},
                {'Field': 'Export Type', 'Value': 'Complete Report'},
                {'Field': 'User', 'Value': current_user['username'] if current_user else 'Anonymous'},
                {'Field': 'Partner', 'Value': current_user.get('partner_id', 'None') if current_user else 'None'}
            ])
            metadata.to_excel(writer, sheet_name='Export Info', index=False)

            # Sheet 4: Risk summary (if available)
            if analysis_results and any(key in analysis_results for key in ['risk_metrics', 'drawdown_analysis']):
                risk_data = []

                if 'risk_metrics' in analysis_results:
                    risk_data.extend([
                        {'Risk Metric': k.replace('_', ' ').title(), 'Value': v}
                        for k, v in analysis_results['risk_metrics'].items()
                    ])

                if risk_data:
                    risk_df = pd.DataFrame(risk_data)
                    risk_df.to_excel(writer, sheet_name='Risk Analysis', index=False)

        excel_buffer.seek(0)
        return excel_buffer.read()

    except Exception as e:
        st.error(f"Excel export failed: {str(e)}")
        logger.error(f"Excel export error: {e}")
        return None