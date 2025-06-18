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
            
            # Hero Section with Overall Performance
            st.markdown("# 📊 Trading Performance Analytics")
            st.markdown("---")
            
            # Overall Performance Overview
            kpis = analytics.get('kpis', {})
            basic_stats = analytics.get('basic_stats', {})
            
            # Hero metrics with color coding
            hero_col1, hero_col2, hero_col3 = st.columns(3)
            
            with hero_col1:
                net_pnl = kpis.get('net_pnl_after_commission', 0)
                pnl_color = "normal" if net_pnl >= 0 else "inverse"
                st.metric(
                    label="💰 **Net P&L**", 
                    value=f"${net_pnl:,.2f}",
                    delta=f"After ${kpis.get('total_commission', 0):,.2f} commission"
                )
            
            with hero_col2:
                win_rate = kpis.get('win_rate_percent', 0)
                win_rate_delta = "Strong" if win_rate >= 60 else "Moderate" if win_rate >= 50 else "Needs Improvement"
                st.metric(
                    label="🎯 **Win Rate**",
                    value=f"{win_rate:.1f}%",
                    delta=win_rate_delta
                )
            
            with hero_col3:
                profit_factor = basic_stats.get('profit_factor', 0)
                pf_delta = "Excellent" if profit_factor >= 2.0 else "Good" if profit_factor >= 1.5 else "Fair" if profit_factor >= 1.0 else "Poor"
                st.metric(
                    label="📈 **Profit Factor**",
                    value=f"{profit_factor:.2f}",
                    delta=pf_delta
                )
            
            st.markdown("---")
            
            # Key Performance Indicators Section
            st.markdown("## 🎯 Key Performance Indicators")
            
            # Create tabs for different metric categories
            kpi_tab1, kpi_tab2, kpi_tab3 = st.tabs(["💵 Financial Metrics", "📊 Performance Ratios", "🎲 Risk Metrics"])
            
            with kpi_tab1:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_trades = kpis.get('total_trades', 0)
                    st.metric(
                        label="**Total Trades**", 
                        value=f"{total_trades:,}",
                        help="Total number of completed trades"
                    )
                with col2:
                    gross_pnl = kpis.get('gross_pnl', 0)
                    st.metric(
                        label="**Gross P&L**", 
                        value=f"${gross_pnl:,.2f}",
                        help="Profit/Loss before commissions"
                    )
                with col3:
                    max_win = kpis.get('max_single_trade_win', 0)
                    st.metric(
                        label="**Best Trade**", 
                        value=f"${max_win:,.2f}",
                        help="Largest single trade profit"
                    )
                with col4:
                    max_loss = kpis.get('max_single_trade_loss', 0)
                    st.metric(
                        label="**Worst Trade**", 
                        value=f"${max_loss:,.2f}",
                        help="Largest single trade loss"
                    )
            
            with kpi_tab2:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_win = basic_stats.get('average_win', 0)
                    st.metric(
                        label="**Average Win**", 
                        value=f"${avg_win:,.2f}",
                        help="Average profit per winning trade"
                    )
                with col2:
                    avg_loss = basic_stats.get('average_loss', 0)
                    st.metric(
                        label="**Average Loss**", 
                        value=f"${avg_loss:,.2f}",
                        help="Average loss per losing trade"
                    )
                with col3:
                    rr_ratio = kpis.get('average_rr', 0)
                    st.metric(
                        label="**Risk:Reward**", 
                        value=f"1:{rr_ratio:.2f}",
                        help="Average risk to reward ratio"
                    )
                with col4:
                    expectancy = basic_stats.get('expectancy', 0)
                    st.metric(
                        label="**Expectancy**", 
                        value=f"${expectancy:,.2f}",
                        help="Expected value per trade"
                    )
            
            with kpi_tab3:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    max_dd = basic_stats.get('max_drawdown', 0)
                    st.metric(
                        label="**Max Drawdown**", 
                        value=f"${max_dd:,.2f}",
                        help="Largest peak-to-trough decline"
                    )
                with col2:
                    sharpe = basic_stats.get('sharpe_ratio', 0)
                    sharpe_rating = "Excellent" if sharpe >= 2.0 else "Good" if sharpe >= 1.0 else "Fair" if sharpe >= 0.5 else "Poor"
                    st.metric(
                        label="**Sharpe Ratio**", 
                        value=f"{sharpe:.2f}",
                        delta=sharpe_rating,
                        help="Risk-adjusted return measure"
                    )
                with col3:
                    commission = kpis.get('total_commission', 0)
                    comm_pct = (commission / gross_pnl * 100) if gross_pnl != 0 else 0
                    st.metric(
                        label="**Total Commission**", 
                        value=f"${commission:,.2f}",
                        delta=f"{comm_pct:.1f}% of gross P&L",
                        help="Total trading commissions paid"
                    )
                with col4:
                    # Performance score calculation
                    score = 0
                    if win_rate >= 50: score += 25
                    if profit_factor >= 1.0: score += 25
                    if sharpe >= 0.5: score += 25
                    if expectancy > 0: score += 25
                    
                    score_color = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
                    st.metric(
                        label="**Performance Score**", 
                        value=f"{score_color} {score}/100",
                        help="Overall performance rating"
                    )
            
            st.markdown("---")
            
            # Enhanced Performance Analysis Section
            st.markdown("## ⏱️ Trade Duration & Timing Analysis")
            # Get duration stats from the correct key
            duration_stats = analytics.get('trade_duration_stats', {})
            
            # Create an attractive container for duration stats
            with st.container():
                duration_col1, duration_col2, duration_col3, duration_col4 = st.columns(4)
                
                with duration_col1:
                    avg_duration = duration_stats.get('average_minutes', 0)
                    st.metric(
                        label="**⏱️ Avg Duration**", 
                        value=f"{avg_duration:.1f} min",
                        help="Average time spent in trades"
                    )
                
                with duration_col2:
                    min_duration = duration_stats.get('min_minutes', 0)
                    st.metric(
                        label="**⚡ Fastest Trade**", 
                        value=f"{min_duration:.1f} min",
                        help="Shortest trade duration"
                    )
                
                with duration_col3:
                    max_duration = duration_stats.get('max_minutes', 0)
                    st.metric(
                        label="**🕐 Longest Trade**", 
                        value=f"{max_duration:.1f} min",
                        help="Longest trade duration"
                    )
                
                with duration_col4:
                    median_duration = duration_stats.get('median_minutes', 0)
                    st.metric(
                        label="**📊 Median Duration**", 
                        value=f"{median_duration:.1f} min",
                        help="Middle value of all trade durations"
                    )
            
            st.markdown("---")
            
            # Enhanced Streak Analysis
            st.markdown("## 🔥 Streak Analysis & Trading Psychology")
            streaks = analytics.get('streaks', {})
            
            # Create a prominent container for streak analysis
            with st.container():
                st.markdown("### Consecutive Trade Performance")
                
                # Get streak values
                max_win_streak = streaks.get('max_win_streak', 0)
                max_loss_streak = streaks.get('max_loss_streak', 0)
                
                # Main streak display
                streak_col1, streak_col2, streak_col3, streak_col4 = st.columns([1, 1, 1, 1])
                
                with streak_col1:
                    # Enhanced win streak display
                    if max_win_streak >= 15:
                        win_streak_emoji = "🔥🔥🔥"
                        win_streak_color = "🟢"
                        win_streak_desc = "EXCEPTIONAL"
                    elif max_win_streak >= 10:
                        win_streak_emoji = "🔥🔥"
                        win_streak_color = "🟢"
                        win_streak_desc = "EXCELLENT"
                    elif max_win_streak >= 5:
                        win_streak_emoji = "🔥"
                        win_streak_color = "🟡"
                        win_streak_desc = "GOOD"
                    elif max_win_streak >= 3:
                        win_streak_emoji = "✨"
                        win_streak_color = "🟡"
                        win_streak_desc = "MODERATE"
                    else:
                        win_streak_emoji = "📈"
                        win_streak_color = "🔴"
                        win_streak_desc = "LOW"
                    
                    st.metric(
                        label=f"**{win_streak_emoji} Longest Win Streak**", 
                        value=f"{max_win_streak} consecutive wins",
                        delta=f"{win_streak_color} {win_streak_desc}",
                        help=f"Your best winning streak shows discipline and strategy execution. {max_win_streak} wins in a row!"
                    )
                
                with streak_col2:
                    # Enhanced loss streak display
                    if max_loss_streak >= 15:
                        loss_streak_emoji = "❄️❄️❄️"
                        loss_streak_color = "🔴"
                        loss_streak_desc = "CONCERNING"
                    elif max_loss_streak >= 10:
                        loss_streak_emoji = "❄️❄️"
                        loss_streak_color = "🔴"
                        loss_streak_desc = "HIGH"
                    elif max_loss_streak >= 5:
                        loss_streak_emoji = "❄️"
                        loss_streak_color = "🟡"
                        loss_streak_desc = "MODERATE"
                    elif max_loss_streak >= 3:
                        loss_streak_emoji = "📉"
                        loss_streak_color = "🟡"
                        loss_streak_desc = "NORMAL"
                    else:
                        loss_streak_emoji = "🔻"
                        loss_streak_color = "🟢"
                        loss_streak_desc = "EXCELLENT"
                    
                    st.metric(
                        label=f"**{loss_streak_emoji} Longest Loss Streak**", 
                        value=f"{max_loss_streak} consecutive losses",
                        delta=f"{loss_streak_color} {loss_streak_desc}",
                        help=f"Risk management is key. Your worst streak was {max_loss_streak} losses in a row."
                    )
                
                with streak_col3:
                    # Streak Recovery Ratio
                    if max_loss_streak > 0 and max_win_streak > 0:
                        recovery_ratio = max_win_streak / max_loss_streak
                        if recovery_ratio >= 2.0:
                            recovery_emoji = "🚀"
                            recovery_desc = "STRONG RECOVERY"
                            recovery_color = "🟢"
                        elif recovery_ratio >= 1.5:
                            recovery_emoji = "⚡"
                            recovery_desc = "GOOD RECOVERY"
                            recovery_color = "🟡"
                        elif recovery_ratio >= 1.0:
                            recovery_emoji = "🎯"
                            recovery_desc = "BALANCED"
                            recovery_color = "🟡"
                        else:
                            recovery_emoji = "⚠️"
                            recovery_desc = "NEEDS WORK"
                            recovery_color = "🔴"
                        
                        st.metric(
                            label=f"**{recovery_emoji} Recovery Power**", 
                            value=f"{recovery_ratio:.1f}x ratio",
                            delta=f"{recovery_color} {recovery_desc}",
                            help=f"Win streak vs loss streak ratio. Higher is better for psychological resilience."
                        )
                    else:
                        st.metric(
                            label="**🎯 Recovery Power**", 
                            value="Perfect!",
                            delta="🟢 No significant streaks",
                            help="Balanced trading without extreme streaks"
                        )
                
                with streak_col4:
                    # Psychological Impact Score
                    psychology_score = 0
                    if max_win_streak >= 5:
                        psychology_score += 30
                    if max_loss_streak <= 5:
                        psychology_score += 30
                    if max_win_streak > max_loss_streak:
                        psychology_score += 25
                    if max_loss_streak <= 3:
                        psychology_score += 15
                    
                    if psychology_score >= 80:
                        psych_emoji = "🧠✨"
                        psych_desc = "EXCELLENT MINDSET"
                        psych_color = "🟢"
                    elif psychology_score >= 60:
                        psych_emoji = "🧠"
                        psych_desc = "SOLID PSYCHOLOGY"
                        psych_color = "🟡"
                    elif psychology_score >= 40:
                        psych_emoji = "🤔"
                        psych_desc = "ROOM FOR GROWTH"
                        psych_color = "🟡"
                    else:
                        psych_emoji = "😤"
                        psych_desc = "FOCUS ON DISCIPLINE"
                        psych_color = "🔴"
                    
                    st.metric(
                        label=f"**{psych_emoji} Psychology Score**", 
                        value=f"{psychology_score}/100",
                        delta=f"{psych_color} {psych_desc}",
                        help="Based on streak patterns. Good traders minimize loss streaks and build win streaks."
                    )
                
                # Add streak insights
                st.markdown("---")
                st.markdown("### 🧠 **Streak Insights & Psychology**")
                
                insight_col1, insight_col2 = st.columns(2)
                
                with insight_col1:
                    st.markdown("#### 💡 **Key Observations**")
                    if max_win_streak >= 10:
                        st.success(f"🔥 **Hot Hand Effect**: Your {max_win_streak}-trade win streak shows excellent momentum trading!")
                    elif max_win_streak >= 5:
                        st.info(f"✨ **Solid Execution**: {max_win_streak} consecutive wins demonstrates good strategy consistency.")
                    else:
                        st.warning(f"📈 **Build Momentum**: Work on extending win streaks beyond {max_win_streak} trades.")
                    
                    if max_loss_streak <= 3:
                        st.success(f"🛡️ **Excellent Risk Control**: Max {max_loss_streak} losses shows great discipline!")
                    elif max_loss_streak <= 5:
                        st.info(f"⚖️ **Good Discipline**: {max_loss_streak} max losses is within acceptable range.")
                    else:
                        st.error(f"⚠️ **Risk Alert**: {max_loss_streak} consecutive losses - review risk management!")
                
                with insight_col2:
                    st.markdown("#### 📊 **Performance Psychology**")
                    
                    # Calculate streak efficiency
                    total_possible_streaks = max_win_streak + max_loss_streak
                    if total_possible_streaks > 0:
                        win_streak_pct = (max_win_streak / total_possible_streaks) * 100
                        st.write(f"**Positive Momentum**: {win_streak_pct:.1f}% of your extreme streaks were winning streaks")
                    
                    # Streak balance analysis
                    if max_win_streak > max_loss_streak * 1.5:
                        st.success("🎯 **Momentum Trader**: You excel at riding winning streaks!")
                    elif max_loss_streak > max_win_streak * 1.5:
                        st.warning("🛑 **Risk Review**: Loss streaks exceed win streaks - check your strategy!")
                    else:
                        st.info("⚖️ **Balanced Approach**: Your streaks show measured risk-taking.")
                    
                    # Provide actionable advice
                    if max_loss_streak >= 7:
                        st.error("💡 **Tip**: Consider implementing a 'circuit breaker' after 3-5 consecutive losses.")
                    elif max_win_streak >= 10:
                        st.success("💡 **Tip**: Document what you did during your win streak to replicate success!")
            
            st.markdown("---")
            
            # Enhanced Median Results
            st.markdown("## 📊 Distribution Analysis")
            median_results = analytics.get('median_results', {})
            
            median_col1, median_col2, median_col3 = st.columns(3)
            with median_col1:
                median_pnl = median_results.get('median_pnl', 0)
                pnl_trend = "📈" if median_pnl > 0 else "📉" if median_pnl < 0 else "➡️"
                st.metric(
                    label=f"**{pnl_trend} Median P&L**", 
                    value=f"${median_pnl:,.2f}",
                    help="Middle value of all trade P&L"
                )
            with median_col2:
                median_win = median_results.get('median_win', 0)
                st.metric(
                    label="**🟢 Median Win**", 
                    value=f"${median_win:,.2f}",
                    help="Typical winning trade size"
                )
            with median_col3:
                median_loss = median_results.get('median_loss', 0)
                st.metric(
                    label="**🔴 Median Loss**", 
                    value=f"${median_loss:,.2f}",
                    help="Typical losing trade size"
                )
            
            st.markdown("---")
            
            # Enhanced Symbol Performance Section
            st.markdown("## 🎯 Performance by Symbol")
            symbol_performance = analytics.get('symbol_performance', [])
            
            # Import pandas at the start to avoid scope issues
            import pandas as pd
            
            if symbol_performance is not None and len(symbol_performance) > 0:
                df_symbols = pd.DataFrame(symbol_performance)
                if not df_symbols.empty:
                    # Create attractive columns for symbol metrics
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("### 📊 Symbol Breakdown")
                        st.dataframe(df_symbols, use_container_width=True)
                    
                    with col2:
                        st.markdown("### 🏆 Top Performers")
                        if 'profit_factor' in df_symbols.columns:
                            top_symbols = df_symbols.nlargest(3, 'profit_factor')
                            for idx, row in top_symbols.iterrows():
                                st.metric(
                                    label=f"**{row['symbol']}**",
                                    value=f"{row['profit_factor']:.2f}",
                                    help="Profit Factor"
                                )
                else:
                    st.info("📊 Symbol performance data is being processed...")
            else:
                # Get the actual trade data to show symbol performance manually
                trade_data = st.session_state.get('trade_data')
                if trade_data is not None and not trade_data.empty:
                    # Calculate symbol performance manually
                    if 'symbol' in trade_data.columns and 'pnl' in trade_data.columns:
                        symbol_stats = []
                        for symbol in trade_data['symbol'].unique():
                            symbol_trades = trade_data[trade_data['symbol'] == symbol]
                            total_trades = len(symbol_trades)
                            total_pnl = symbol_trades['pnl'].sum()
                            wins = len(symbol_trades[symbol_trades['pnl'] > 0])
                            losses = len(symbol_trades[symbol_trades['pnl'] < 0])
                            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                            
                            # Calculate profit factor
                            gross_profit = symbol_trades[symbol_trades['pnl'] > 0]['pnl'].sum()
                            gross_loss = abs(symbol_trades[symbol_trades['pnl'] < 0]['pnl'].sum())
                            profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit if gross_profit > 0 else 0
                            
                            symbol_stats.append({
                                'Symbol': symbol,
                                'Trades': total_trades,
                                'Total P&L': f"${total_pnl:,.2f}",
                                'Win Rate': f"{win_rate:.1f}%",
                                'Profit Factor': f"{profit_factor:.2f}"
                            })
                        
                        if symbol_stats:
                            st.markdown("### 📊 Performance by Symbol")
                            df_symbols = pd.DataFrame(symbol_stats)
                            st.dataframe(df_symbols, use_container_width=True)
                        else:
                            st.info("📊 No symbol data available")
                    else:
                        st.info("📊 Symbol or P&L data not found in trade data")
                else:
                    st.info("📊 No trade data available for symbol analysis")
            
            st.markdown("---")
            
            # Enhanced Monthly Performance Section
            st.markdown("## 📅 Monthly Performance Trends")
            monthly_performance = analytics.get('monthly_performance', [])
            
            if monthly_performance is not None and len(monthly_performance) > 0:
                df_monthly = pd.DataFrame(monthly_performance)
                if not df_monthly.empty:
                    # Create tabs for different views
                    month_tab1, month_tab2 = st.tabs(["📊 Data Table", "📈 Visual Trends"])
                    
                    with month_tab1:
                        st.markdown("### Monthly Performance Summary")
                        st.dataframe(df_monthly, use_container_width=True)
                        
                        # Quick monthly stats
                        if 'pnl' in df_monthly.columns:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                best_month = df_monthly.loc[df_monthly['pnl'].idxmax()]
                                st.metric(
                                    "🏆 Best Month", 
                                    f"${best_month['pnl']:,.2f}",
                                    delta=f"{best_month['period']}"
                                )
                            with col2:
                                avg_monthly = df_monthly['pnl'].mean()
                                st.metric(
                                    "📊 Avg Monthly", 
                                    f"${avg_monthly:,.2f}",
                                    help="Average monthly P&L"
                                )
                            with col3:
                                total_months = len(df_monthly)
                                profitable_months = len(df_monthly[df_monthly['pnl'] > 0])
                                st.metric(
                                    "✅ Success Rate", 
                                    f"{profitable_months}/{total_months}",
                                    delta=f"{profitable_months/total_months*100:.1f}%"
                                )
                    
                    with month_tab2:
                        st.markdown("### Performance Visualization")
                        if 'pnl' in df_monthly.columns:
                            try:
                                import plotly.graph_objects as go
                                
                                fig = go.Figure()
                                
                                # Add bar chart for monthly P&L
                                colors = ['green' if x > 0 else 'red' for x in df_monthly['pnl']]
                                fig.add_trace(go.Bar(
                                    x=df_monthly['period'].astype(str),
                                    y=df_monthly['pnl'],
                                    marker_color=colors,
                                    name='Monthly P&L',
                                    text=[f'${x:,.0f}' for x in df_monthly['pnl']],
                                    textposition='outside'
                                ))
                                
                                fig.update_layout(
                                    title='📈 Monthly Performance Breakdown',
                                    xaxis_title='Month',
                                    yaxis_title='P&L ($)',
                                    showlegend=False,
                                    height=400
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            except ImportError:
                                st.line_chart(df_monthly.set_index('period')['pnl'], height=400)
                        else:
                            st.line_chart(df_monthly.set_index('period').select_dtypes(include=[np.number]))
                else:
                    st.info("📅 Monthly performance data is being processed...")
            else:
                # Get the actual trade data to show monthly performance manually
                trade_data = st.session_state.get('trade_data')
                if trade_data is not None and not trade_data.empty:
                    # Calculate monthly performance manually
                    if 'exit_time' in trade_data.columns and 'pnl' in trade_data.columns:
                        try:
                            trade_data_copy = trade_data.copy()
                            trade_data_copy['exit_time'] = pd.to_datetime(trade_data_copy['exit_time'], errors='coerce')
                            trade_data_copy = trade_data_copy.dropna(subset=['exit_time'])
                            
                            if not trade_data_copy.empty:
                                # Group by month-year
                                trade_data_copy['month_year'] = trade_data_copy['exit_time'].dt.to_period('M')
                                monthly_stats = trade_data_copy.groupby('month_year').agg({
                                    'pnl': ['sum', 'count', lambda x: (x > 0).sum()]
                                }).round(2)
                                
                                monthly_stats.columns = ['Total P&L', 'Total Trades', 'Winning Trades']
                                monthly_stats['Win Rate'] = (monthly_stats['Winning Trades'] / monthly_stats['Total Trades'] * 100).round(1)
                                monthly_stats.index = monthly_stats.index.astype(str)
                                
                                st.markdown("### 📅 Monthly Performance")
                                
                                # Display metrics
                                if len(monthly_stats) > 0:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        best_month_idx = monthly_stats['Total P&L'].idxmax()
                                        best_pnl = monthly_stats.loc[best_month_idx, 'Total P&L']
                                        st.metric("🏆 Best Month", f"${best_pnl:,.2f}", delta=f"{best_month_idx}")
                                    with col2:
                                        avg_monthly = monthly_stats['Total P&L'].mean()
                                        st.metric("📊 Avg Monthly", f"${avg_monthly:,.2f}")
                                    with col3:
                                        profitable_months = len(monthly_stats[monthly_stats['Total P&L'] > 0])
                                        total_months = len(monthly_stats)
                                        st.metric("✅ Success Rate", f"{profitable_months}/{total_months}", 
                                                delta=f"{profitable_months/total_months*100:.1f}%")
                                
                                # Display table
                                st.dataframe(monthly_stats, use_container_width=True)
                                
                                # Simple chart
                                st.bar_chart(monthly_stats['Total P&L'])
                            else:
                                st.info("📅 No valid date data for monthly analysis")
                        except Exception as e:
                            st.error(f"📅 Error calculating monthly performance: {str(e)}")
                    else:
                        st.info("📅 Exit time or P&L data not found in trade data")
                else:
                    st.info("📅 No trade data available for monthly analysis")
            
            # Rolling Metrics
            st.subheader("📊 Rolling Performance (10-trade windows)")
            rolling_metrics = analytics.get('rolling_metrics', [])
            
            if rolling_metrics is not None and len(rolling_metrics) > 0:
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