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
                try:
                    self._render_dashboard()
                except Exception as e:
                    st.error(f"Dashboard error: {str(e)}")
                    logger.error(f"Dashboard rendering error: {str(e)}")
            
            with tab2:
                try:
                    self._render_analytics()
                except Exception as e:
                    st.error(f"Analytics error: {str(e)}")
                    logger.error(f"Analytics rendering error: {str(e)}")
            
            with tab3:
                try:
                    self._render_trade_data()
                except Exception as e:
                    st.error(f"Trade Data error: {str(e)}")
                    logger.error(f"Trade data rendering error: {str(e)}")
            
            with tab4:
                try:
                    self._render_settings()
                except Exception as e:
                    st.error(f"Settings error: {str(e)}")
                    logger.error(f"Settings rendering error: {str(e)}")

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
        trade_data = st.session_state.get('trade_data')
        if trade_data is not None and not trade_data.empty:
            st.write("Dashboard content would go here")

            # Show basic stats if available
            analytics_result = st.session_state.get('analytics_result')
            if analytics_result is not None:
                analytics = analytics_result
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
        analytics_result = st.session_state.get('analytics_result')
        if analytics_result is not None:
            analytics = analytics_result
            
            st.subheader("📊 Trading Performance Analytics")
            
            # Key Performance Indicators
            st.subheader("🎯 Key Performance Indicators")
            kpis = analytics.get('kpis', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", kpis.get('total_trades', 0))
            with col2:
                st.metric("Gross P&L", f"${kpis.get('gross_pnl', 0):,.2f}")
            with col3:
                st.metric("Net P&L", f"${kpis.get('net_pnl_after_commission', 0):,.2f}")
            with col4:
                st.metric("Win Rate", f"{kpis.get('win_rate_percent', 0):.1f}%")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Max Win", f"${kpis.get('max_single_trade_win', 0):,.2f}")
            with col2:
                st.metric("Max Loss", f"${kpis.get('max_single_trade_loss', 0):,.2f}")
            with col3:
                st.metric("Total Commission", f"${kpis.get('total_commission', 0):,.2f}")
            with col4:
                st.metric("Avg R:R Ratio", f"{kpis.get('average_rr', 0):.2f}")
            
            # Basic Statistics
            st.subheader("📈 Trading Statistics")
            basic_stats = analytics.get('basic_stats', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Win", f"${basic_stats.get('average_win', 0):,.2f}")
                st.metric("Profit Factor", f"{basic_stats.get('profit_factor', 0):.2f}")
            with col2:
                st.metric("Average Loss", f"${basic_stats.get('average_loss', 0):,.2f}")
                st.metric("Expectancy", f"${basic_stats.get('expectancy', 0):,.2f}")
            with col3:
                st.metric("Max Drawdown", f"${basic_stats.get('max_drawdown', 0):,.2f}")
                st.metric("Sharpe Ratio", f"{basic_stats.get('sharpe_ratio', 0):.2f}")
            
            # Performance Analysis
            st.subheader("⏱️ Trade Duration Analysis")
            duration_stats = analytics.get('duration_stats', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Duration", f"{duration_stats.get('average_minutes', 0):.1f} min")
            with col2:
                st.metric("Min Duration", f"{duration_stats.get('min_minutes', 0):.1f} min")
            with col3:
                st.metric("Max Duration", f"{duration_stats.get('max_minutes', 0):.1f} min")
            with col4:
                st.metric("Median Duration", f"{duration_stats.get('median_minutes', 0):.1f} min")
            
            # Streak Analysis
            st.subheader("🔥 Streak Analysis")
            streaks = analytics.get('streaks', {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Max Win Streak", streaks.get('max_win_streak', 0))
            with col2:
                st.metric("Max Loss Streak", streaks.get('max_loss_streak', 0))
            
            # Median Results
            st.subheader("📊 Median Results")
            median_results = analytics.get('median_results', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Median P&L", f"${median_results.get('median_pnl', 0):,.2f}")
            with col2:
                st.metric("Median Win", f"${median_results.get('median_win', 0):,.2f}")
            with col3:
                st.metric("Median Loss", f"${median_results.get('median_loss', 0):,.2f}")
            
            # Symbol Performance
            st.subheader("🎯 Performance by Symbol")
            symbol_performance = analytics.get('symbol_performance', [])
            
            if symbol_performance is not None and len(symbol_performance) > 0:
                import pandas as pd
                df_symbols = pd.DataFrame(symbol_performance)
                if not df_symbols.empty:
                    st.dataframe(df_symbols, use_container_width=True)
                else:
                    st.info("No symbol performance data available")
            else:
                st.info("No symbol performance data available")
            
            # Monthly Performance
            st.subheader("📅 Monthly Performance")
            monthly_performance = analytics.get('monthly_performance', [])
            
            if monthly_performance is not None and len(monthly_performance) > 0:
                import pandas as pd
                df_monthly = pd.DataFrame(monthly_performance)
                if not df_monthly.empty:
                    st.dataframe(df_monthly, use_container_width=True)
                    
                    # Simple chart if data is available
                    if 'pnl' in df_monthly.columns:
                        st.line_chart(df_monthly.set_index('period')['pnl'])
                else:
                    st.info("No monthly performance data available")
            else:
                st.info("No monthly performance data available")
            
            # Rolling Metrics
            st.subheader("📊 Rolling Performance (10-trade windows)")
            rolling_metrics = analytics.get('rolling_metrics', [])
            
            if rolling_metrics is not None and len(rolling_metrics) > 0:
                import pandas as pd
                try:
                    df_rolling = pd.DataFrame(rolling_metrics)
                    if not df_rolling.empty and len(df_rolling) > 0:
                        st.write(f"Showing rolling metrics for {len(df_rolling)} periods")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if 'win_rate' in df_rolling.columns:
                                st.line_chart(df_rolling['win_rate'], height=300)
                                st.caption("Rolling Win Rate (%)")
                        with col2:
                            if 'profit_factor' in df_rolling.columns:
                                st.line_chart(df_rolling['profit_factor'], height=300)
                                st.caption("Rolling Profit Factor")
                                
                        # Add cumulative P&L chart if basic_stats has equity_curve
                        if 'basic_stats' in analytics and 'equity_curve' in analytics['basic_stats']:
                            equity_curve = analytics['basic_stats']['equity_curve']
                            if equity_curve is not None and len(equity_curve) > 0:
                                st.subheader("💰 Equity Curve")
                                st.line_chart(equity_curve, height=400)
                                st.caption("Cumulative P&L over time")
                    else:
                        st.info("No rolling metrics data available")
                except Exception as e:
                    st.error(f"Error displaying rolling metrics: {str(e)}")
                    st.info("Rolling metrics data is available but cannot be displayed")
            else:
                st.info("No rolling metrics data available")
                
        else:
            st.info("Upload trade data and run analysis to view detailed analytics")

    def _render_trade_data(self):
        """Render trade data page."""
        trade_data = st.session_state.get('trade_data')
        if trade_data is not None and not trade_data.empty:
            st.write(f"Showing {len(trade_data)} trades")
            st.dataframe(trade_data, use_container_width=True)
        else:
            st.info("No trade data available")

    def _render_settings(self):
        """Render settings page."""
        st.write("Settings page - configuration options would go here")