#!/usr/bin/env python3
"""
TradeSense App Factory
Lightweight coordinator for the modular TradeSense application
"""

import streamlit as st
import logging
from module_checker import module_checker

logger = logging.getLogger(__name__)

class AppFactory:
    """Lightweight factory class for creating and managing the TradeSense application."""

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

            # Import and render components
            from core.data_upload_handler import render_data_upload_section
            from core.analysis_engine import render_analysis_controls
            from core.dashboard_manager import render_dashboard_tabs

            # Data upload section
            render_data_upload_section()

            # Analysis controls
            render_analysis_controls()

            # Main dashboard tabs
            render_dashboard_tabs()

        except Exception as e:
            st.error(f"Failed to initialize application: {str(e)}")
            logger.error(f"App initialization error: {str(e)}")

            # Show fallback interface
            self._render_fallback_interface()

    def _render_fallback_interface(self):
        """Render a basic interface when main app fails to load."""
        st.warning("🔧 Application is in recovery mode")

        # Basic file upload
        uploaded_file = st.file_uploader("Upload CSV trade data", type=['csv'])
        if uploaded_file is not None:
            try:
                import pandas as pd
                df = pd.read_csv(uploaded_file)
                st.success(f"✅ Loaded {len(df)} rows")
                st.dataframe(df.head())
                st.session_state.trade_data = df
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")

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
                # Process the uploaded file with enhanced error handling
                from trade_entry_manager import trade_manager
                import pandas as pd
                import io

                # Read the file with better error handling
                try:
                    if uploaded_file.name.endswith('.csv'):
                        # Try different encodings to handle various CSV formats
                        try:
                            df = pd.read_csv(uploaded_file, encoding='utf-8')
                        except UnicodeDecodeError:
                            uploaded_file.seek(0)  # Reset file pointer
                            df = pd.read_csv(uploaded_file, encoding='latin-1')
                    else:
                        df = pd.read_excel(uploaded_file)
                        
                    # Display file info first
                    st.write(f"**File:** {uploaded_file.name}")
                    st.write(f"**Size:** {uploaded_file.size / 1024:.1f}KB")
                    st.write(f"**Rows:** {len(df)}")
                    st.write(f"**Columns:** {list(df.columns)}")
                    
                    # Show a preview of the data
                    with st.expander("📄 Data Preview", expanded=False):
                        st.dataframe(df.head(), use_container_width=True)
                    
                except Exception as read_error:
                    st.error(f"Error reading file: {str(read_error)}")
                    st.info("The file might be corrupted or in an unsupported format. Please try a different file.")
                    return

                # Add trades to manager with enhanced error handling
                try:
                    result = trade_manager.add_file_trades(df, f"file_{uploaded_file.name}")

                    if result['status'] == 'success':
                        st.success(f"✅ Successfully processed {result['trades_added']} trades")
                        st.session_state.trade_data = trade_manager.get_all_trades_dataframe()
                        
                        # Auto-run analysis after successful upload
                        st.session_state.auto_run_analysis = True
                        
                    else:
                        st.error(f"Error processing file: {result['message']}")
                        
                        # Show detailed column information to help user
                        st.info("**Required columns:** symbol, entry_time, exit_time, entry_price, exit_price, pnl, direction")
                        st.info(f"**Your file has:** {', '.join(df.columns)}")
                        
                        # Suggest column mapping if similar columns exist
                        required_cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction']
                        suggestions = []
                        for req_col in required_cols:
                            for file_col in df.columns:
                                if req_col.lower() in file_col.lower() or file_col.lower() in req_col.lower():
                                    suggestions.append(f"'{file_col}' might map to '{req_col}'")
                        
                        if suggestions:
                            st.info("**Possible column mappings:**")
                            for suggestion in suggestions:
                                st.info(f"• {suggestion}")
                                
                except Exception as processing_error:
                    st.error(f"Error during trade processing: {str(processing_error)}")
                    
                    # If it's a library error, try a simpler processing approach
                    if "libstdc++" in str(processing_error) or "shared object" in str(processing_error):
                        st.warning("🔧 System library issue detected. Trying alternative processing method...")
                        
                        try:
                            # Simple validation without heavy analytics
                            required_columns = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction']
                            missing_cols = [col for col in required_columns if col not in df.columns]
                            
                            if missing_cols:
                                st.error(f"Missing required columns: {', '.join(missing_cols)}")
                            else:
                                # Store raw data temporarily
                                st.session_state.trade_data = df
                                st.success("✅ File uploaded successfully! Some advanced analytics may be limited due to system constraints.")
                                st.info("📊 Basic analytics are available in the Analytics tab.")
                                
                        except Exception as fallback_error:
                            st.error(f"Fallback processing also failed: {str(fallback_error)}")
                            st.info("Please try uploading a smaller file or contact support.")

            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
                st.info("Please ensure your file has the required columns: symbol, entry_time, exit_time, entry_price, exit_price, pnl, direction")
                
                # System diagnostics
                st.expander("🔧 System Diagnostics", expanded=False)
                with st.expander("🔧 System Diagnostics"):
                    st.code(f"Error type: {type(e).__name__}")
                    st.code(f"Error message: {str(e)}")
                    
                    # Check if it's a system library issue
                    if "libstdc++" in str(e) or "shared object" in str(e):
                        st.warning("This appears to be a system library issue. The Replit environment may need additional dependencies.")
                        st.info("Try refreshing the page or restarting the Repl if the issue persists.")

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
            
            # Create a prominent container for streak analysis with enhanced styling
            with st.container():
                # Add custom CSS for better visual appeal
                st.markdown("""
                <style>
                .streak-container {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 15px;
                    margin: 1rem 0;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }
                .streak-title {
                    color: white;
                    font-size: 1.5rem;
                    font-weight: bold;
                    text-align: center;
                    margin-bottom: 1.5rem;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .metric-container {
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 10px;
                    padding: 1rem;
                    margin: 0.5rem 0;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .insight-box {
                    background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin: 1rem 0;
                    color: white;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }
                .psychology-box {
                    background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin: 1rem 0;
                    color: white;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="streak-container">', unsafe_allow_html=True)
                st.markdown('<div class="streak-title">⚡ Consecutive Trade Performance Analysis ⚡</div>', unsafe_allow_html=True)
                
                # Get streak values with fallback calculation
                max_win_streak = streaks.get('max_win_streak', 0)
                max_loss_streak = streaks.get('max_loss_streak', 0)
                
                # If streaks are 0, try to calculate them directly from trade data
                if max_win_streak == 0 and max_loss_streak == 0:
                    # Import pandas for streak calculations
                    import pandas as pd
                    
                    trade_data = st.session_state.get('trade_data')
                    if trade_data is not None and not trade_data.empty and 'pnl' in trade_data.columns:
                        # Calculate streaks manually as fallback
                        pnl_data = pd.to_numeric(trade_data['pnl'], errors='coerce').dropna()
                        if not pnl_data.empty:
                            # Sort by exit_time if available
                            if 'exit_time' in trade_data.columns:
                                sorted_data = trade_data.sort_values('exit_time')['pnl']
                            else:
                                sorted_data = pnl_data
                            
                            # Calculate streaks manually
                            current_win_streak = 0
                            current_loss_streak = 0
                            max_win_streak = 0
                            max_loss_streak = 0
                            
                            for pnl in sorted_data:
                                if pd.notna(pnl):
                                    if pnl > 0:  # Win
                                        current_win_streak += 1
                                        current_loss_streak = 0
                                        max_win_streak = max(max_win_streak, current_win_streak)
                                    elif pnl < 0:  # Loss
                                        current_loss_streak += 1
                                        current_win_streak = 0
                                        max_loss_streak = max(max_loss_streak, current_loss_streak)
                
                # Ensure we have valid values
                max_win_streak = max(0, int(max_win_streak)) if pd.notna(max_win_streak) else 0
                max_loss_streak = max(0, int(max_loss_streak)) if pd.notna(max_loss_streak) else 0
                
                # Main streak display with enhanced visuals
                streak_col1, streak_col2, streak_col3, streak_col4 = st.columns([1, 1, 1, 1])
                
                with streak_col1:
                    # Enhanced win streak display
                    if max_win_streak >= 15:
                        win_streak_emoji = "🔥🔥🔥"
                        win_streak_color = "🟢"
                        win_streak_desc = "EXCEPTIONAL"
                        win_streak_bg = "#00C851"
                    elif max_win_streak >= 10:
                        win_streak_emoji = "🔥🔥"
                        win_streak_color = "🟢"
                        win_streak_desc = "EXCELLENT"
                        win_streak_bg = "#4CAF50"
                    elif max_win_streak >= 5:
                        win_streak_emoji = "🔥"
                        win_streak_color = "🟡"
                        win_streak_desc = "GOOD"
                        win_streak_bg = "#FFC107"
                    elif max_win_streak >= 3:
                        win_streak_emoji = "✨"
                        win_streak_color = "🟡"
                        win_streak_desc = "MODERATE"
                        win_streak_bg = "#FF9800"
                    else:
                        win_streak_emoji = "📈"
                        win_streak_color = "🔴"
                        win_streak_desc = "LOW"
                        win_streak_bg = "#F44336"
                    
                    # Custom styled metric box
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {win_streak_bg} 0%, {win_streak_bg}80 100%); 
                                padding: 1.5rem; border-radius: 15px; text-align: center; 
                                box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{win_streak_emoji}</div>
                        <div style="color: white; font-weight: bold; font-size: 1.1rem;">Longest Win Streak</div>
                        <div style="color: white; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">{max_win_streak}</div>
                        <div style="color: white; opacity: 0.9;">consecutive wins</div>
                        <div style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; 
                                    margin-top: 0.5rem; display: inline-block;">
                            <span style="color: white; font-weight: bold;">{win_streak_desc}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with streak_col2:
                    # Enhanced loss streak display
                    if max_loss_streak >= 15:
                        loss_streak_emoji = "❄️❄️❄️"
                        loss_streak_color = "🔴"
                        loss_streak_desc = "CONCERNING"
                        loss_streak_bg = "#D32F2F"
                    elif max_loss_streak >= 10:
                        loss_streak_emoji = "❄️❄️"
                        loss_streak_color = "🔴"
                        loss_streak_desc = "HIGH"
                        loss_streak_bg = "#F44336"
                    elif max_loss_streak >= 5:
                        loss_streak_emoji = "❄️"
                        loss_streak_color = "🟡"
                        loss_streak_desc = "MODERATE"
                        loss_streak_bg = "#FF9800"
                    elif max_loss_streak >= 3:
                        loss_streak_emoji = "📉"
                        loss_streak_color = "🟡"
                        loss_streak_desc = "NORMAL"
                        loss_streak_bg = "#FFC107"
                    else:
                        loss_streak_emoji = "🔻"
                        loss_streak_color = "🟢"
                        loss_streak_desc = "EXCELLENT"
                        loss_streak_bg = "#4CAF50"
                    
                    # Custom styled metric box for loss streak
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {loss_streak_bg} 0%, {loss_streak_bg}80 100%); 
                                padding: 1.5rem; border-radius: 15px; text-align: center; 
                                box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{loss_streak_emoji}</div>
                        <div style="color: white; font-weight: bold; font-size: 1.1rem;">Longest Loss Streak</div>
                        <div style="color: white; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">{max_loss_streak}</div>
                        <div style="color: white; opacity: 0.9;">consecutive losses</div>
                        <div style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; 
                                    margin-top: 0.5rem; display: inline-block;">
                            <span style="color: white; font-weight: bold;">{loss_streak_desc}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with streak_col3:
                    # Streak Recovery Ratio
                    if max_loss_streak > 0 and max_win_streak > 0:
                        recovery_ratio = max_win_streak / max_loss_streak
                        if recovery_ratio >= 2.0:
                            recovery_emoji = "🚀"
                            recovery_desc = "STRONG RECOVERY"
                            recovery_bg = "#00C851"
                        elif recovery_ratio >= 1.5:
                            recovery_emoji = "⚡"
                            recovery_desc = "GOOD RECOVERY"
                            recovery_bg = "#4CAF50"
                        elif recovery_ratio >= 1.0:
                            recovery_emoji = "🎯"
                            recovery_desc = "BALANCED"
                            recovery_bg = "#FFC107"
                        else:
                            recovery_emoji = "⚠️"
                            recovery_desc = "NEEDS WORK"
                            recovery_bg = "#F44336"
                        
                        recovery_value = f"{recovery_ratio:.1f}x"
                    else:
                        recovery_emoji = "🎯"
                        recovery_desc = "BALANCED"
                        recovery_bg = "#4CAF50"
                        recovery_value = "∞"
                    
                    # Custom styled metric box for recovery power
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {recovery_bg} 0%, {recovery_bg}80 100%); 
                                padding: 1.5rem; border-radius: 15px; text-align: center; 
                                box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{recovery_emoji}</div>
                        <div style="color: white; font-weight: bold; font-size: 1.1rem;">Recovery Power</div>
                        <div style="color: white; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">{recovery_value}</div>
                        <div style="color: white; opacity: 0.9;">win/loss ratio</div>
                        <div style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; 
                                    margin-top: 0.5rem; display: inline-block;">
                            <span style="color: white; font-weight: bold;">{recovery_desc}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
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
                        psych_bg = "#00C851"
                    elif psychology_score >= 60:
                        psych_emoji = "🧠"
                        psych_desc = "SOLID PSYCHOLOGY"
                        psych_bg = "#4CAF50"
                    elif psychology_score >= 40:
                        psych_emoji = "🤔"
                        psych_desc = "ROOM FOR GROWTH"
                        psych_bg = "#FFC107"
                    else:
                        psych_emoji = "😤"
                        psych_desc = "FOCUS ON DISCIPLINE"
                        psych_bg = "#F44336"
                    
                    # Custom styled metric box for psychology score
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {psych_bg} 0%, {psych_bg}80 100%); 
                                padding: 1.5rem; border-radius: 15px; text-align: center; 
                                box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 1rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{psych_emoji}</div>
                        <div style="color: white; font-weight: bold; font-size: 1.1rem;">Psychology Score</div>
                        <div style="color: white; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">{psychology_score}</div>
                        <div style="color: white; opacity: 0.9;">out of 100</div>
                        <div style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.8rem; border-radius: 20px; 
                                    margin-top: 0.5rem; display: inline-block;">
                            <span style="color: white; font-weight: bold;">{psych_desc}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)  # Close streak-container
                
                # Enhanced streak insights with beautiful styling
                st.markdown("---")
                
                # Key Observations Section
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown("### 💡 **Key Observations & Insights**")
                
                insight_col1, insight_col2 = st.columns(2)
                
                with insight_col1:
                    st.markdown("#### 🎯 **Win Streak Analysis**")
                    if max_win_streak >= 10:
                        st.markdown(f"🔥 **Hot Hand Effect**: Your **{max_win_streak}-trade** win streak shows excellent momentum trading!")
                    elif max_win_streak >= 5:
                        st.markdown(f"✨ **Solid Execution**: **{max_win_streak}** consecutive wins demonstrates good strategy consistency.")
                    else:
                        st.markdown(f"📈 **Build Momentum**: Work on extending win streaks beyond **{max_win_streak}** trades.")
                    
                    # Win streak quality assessment
                    if max_win_streak >= 15:
                        st.markdown("🌟 **Elite Performance**: You're in the top 5% of traders with this streak!")
                    elif max_win_streak >= 10:
                        st.markdown("🏆 **Professional Level**: This streak indicates strong psychological control.")
                
                with insight_col2:
                    st.markdown("#### 🛡️ **Risk Control Analysis**")
                    if max_loss_streak <= 3:
                        st.markdown(f"🛡️ **Excellent Risk Control**: Max **{max_loss_streak}** losses shows great discipline!")
                    elif max_loss_streak <= 5:
                        st.markdown(f"⚖️ **Good Discipline**: **{max_loss_streak}** max losses is within acceptable range.")
                    else:
                        st.markdown(f"⚠️ **Risk Alert**: **{max_loss_streak}** consecutive losses - review risk management!")
                    
                    # Loss streak impact assessment
                    if max_loss_streak <= 5:
                        st.markdown("💎 **Diamond Hands**: You cut losses quickly and maintain discipline.")
                    elif max_loss_streak <= 8:
                        st.markdown("⚡ **Room for Improvement**: Consider tighter stop-loss protocols.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Performance Psychology Section
                st.markdown('<div class="psychology-box">', unsafe_allow_html=True)
                st.markdown("### 🧠 **Performance Psychology Analysis**")
                
                psych_col1, psych_col2 = st.columns(2)
                
                with psych_col1:
                    st.markdown("#### 📈 **Momentum Metrics**")
                    # Calculate streak efficiency
                    total_possible_streaks = max_win_streak + max_loss_streak
                    if total_possible_streaks > 0:
                        win_streak_pct = (max_win_streak / total_possible_streaks) * 100
                        st.markdown(f"**Positive Momentum**: **{win_streak_pct:.1f}%** of your extreme streaks were winning streaks")
                    
                    # Streak momentum indicator
                    momentum_score = (max_win_streak / (max_loss_streak + 1)) * 10
                    if momentum_score >= 20:
                        st.markdown("🚀 **Momentum Master**: You build and maintain winning streaks effectively!")
                    elif momentum_score >= 15:
                        st.markdown("⚡ **Strong Momentum**: You capitalize well on winning opportunities.")
                    else:
                        st.markdown("🎯 **Build Momentum**: Focus on extending profitable runs.")
                
                with psych_col2:
                    st.markdown("#### 🎭 **Trading Psychology**")
                    # Streak balance analysis
                    if max_win_streak > max_loss_streak * 1.5:
                        st.markdown("🎯 **Momentum Trader**: You excel at riding winning streaks!")
                    elif max_loss_streak > max_win_streak * 1.5:
                        st.markdown("🛑 **Risk Review**: Loss streaks exceed win streaks - check your strategy!")
                    else:
                        st.markdown("⚖️ **Balanced Approach**: Your streaks show measured risk-taking.")
                    
                    # Provide actionable advice
                    if max_loss_streak >= 7:
                        st.markdown("💡 **Pro Tip**: Consider implementing a 'circuit breaker' after 3-5 consecutive losses.")
                    elif max_win_streak >= 10:
                        st.markdown("💡 **Pro Tip**: Document what you did during your win streak to replicate success!")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Enhanced Distribution Analysis with Beautiful Visuals
            st.markdown("## 📊 Trade Distribution & Risk Analytics")
            median_results = analytics.get('median_results', {})
            basic_stats = analytics.get('basic_stats', {})
            
            # Import pandas for distribution analysis
            import pandas as pd
            import numpy as np
            
            # Add enhanced CSS for distribution analysis
            st.markdown("""
            <style>
            .distribution-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 20px;
                margin: 1.5rem 0;
                box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                backdrop-filter: blur(10px);
            }
            .distribution-title {
                color: white;
                font-size: 1.8rem;
                font-weight: bold;
                text-align: center;
                margin-bottom: 2rem;
                text-shadow: 2px 2px 6px rgba(0,0,0,0.3);
            }
            .metric-card {
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(15px);
                border-radius: 15px;
                padding: 1.5rem;
                margin: 0.5rem;
                border: 2px solid rgba(255,255,255,0.2);
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            }
            .metric-value {
                font-size: 2.2rem;
                font-weight: bold;
                color: white;
                margin: 0.5rem 0;
                text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
            }
            .metric-label {
                color: rgba(255,255,255,0.9);
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 0.5rem;
            }
            .metric-subtitle {
                color: rgba(255,255,255,0.7);
                font-size: 0.9rem;
                margin-top: 0.5rem;
            }
            .insight-card {
                background: linear-gradient(45deg, #ff6b6b 0%, #feca57 100%);
                padding: 1.5rem;
                border-radius: 15px;
                margin: 1rem 0;
                color: white;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            .distribution-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }
            .percentile-box {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 1.2rem;
                border-radius: 12px;
                text-align: center;
                color: white;
                box-shadow: 0 6px 20px rgba(0,0,0,0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Main Distribution Container
            st.markdown('<div class="distribution-container">', unsafe_allow_html=True)
            st.markdown('<div class="distribution-title">📈 Trade Distribution Analysis 📊</div>', unsafe_allow_html=True)
            
            # Enhanced Median Metrics with Beautiful Cards
            dist_col1, dist_col2, dist_col3 = st.columns(3)
            
            with dist_col1:
                median_pnl = median_results.get('median_pnl', 0)
                pnl_trend = "📈" if median_pnl > 0 else "📉" if median_pnl < 0 else "➡️"
                pnl_color = "#00C851" if median_pnl > 0 else "#FF3547" if median_pnl < 0 else "#FFC107"
                
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid {pnl_color};">
                    <div class="metric-label">{pnl_trend} Median P&L</div>
                    <div class="metric-value">${median_pnl:,.2f}</div>
                    <div class="metric-subtitle">Middle trade value</div>
                </div>
                """, unsafe_allow_html=True)
            
            with dist_col2:
                median_win = median_results.get('median_win', 0)
                win_trend = "🚀" if median_win > 100 else "✅" if median_win > 50 else "📈"
                
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #00C851;">
                    <div class="metric-label">{win_trend} Typical Win</div>
                    <div class="metric-value">${median_win:,.2f}</div>
                    <div class="metric-subtitle">50% of wins exceed this</div>
                </div>
                """, unsafe_allow_html=True)
            
            with dist_col3:
                median_loss = median_results.get('median_loss', 0)
                loss_trend = "🛡️" if median_loss > -100 else "⚠️" if median_loss > -200 else "🚨"
                
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #FF3547;">
                    <div class="metric-label">{loss_trend} Typical Loss</div>
                    <div class="metric-value">${median_loss:,.2f}</div>
                    <div class="metric-subtitle">50% of losses exceed this</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close main container
            
            # Enhanced Distribution Insights
            st.markdown("### 🎯 Distribution Intelligence")
            
            # Get actual trade data for enhanced analysis
            trade_data = st.session_state.get('trade_data')
            if trade_data is not None and not trade_data.empty and 'pnl' in trade_data.columns:
                # Calculate additional distribution metrics
                pnl_data = pd.to_numeric(trade_data['pnl'], errors='coerce').dropna()
                
                if not pnl_data.empty:
                    # Calculate percentiles
                    p25 = pnl_data.quantile(0.25)
                    p75 = pnl_data.quantile(0.75)
                    p10 = pnl_data.quantile(0.10)
                    p90 = pnl_data.quantile(0.90)
                    
                    # Risk-Reward Distribution Analysis
                    insight_col1, insight_col2 = st.columns(2)
                    
                    with insight_col1:
                        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                        st.markdown("#### 📊 **Percentile Breakdown**")
                        
                        # Risk distribution analysis
                        risk_ratio = abs(median_win / median_loss) if median_loss != 0 else 0
                        if risk_ratio >= 1.5:
                            risk_assessment = "🎯 **Favorable Distribution** - Your typical wins significantly outweigh typical losses!"
                        elif risk_ratio >= 1.0:
                            risk_assessment = "⚖️ **Balanced Distribution** - Your wins and losses are reasonably balanced."
                        else:
                            risk_assessment = "⚠️ **Risk Alert** - Your typical losses exceed typical wins. Review position sizing!"
                        
                        st.markdown(risk_assessment)
                        
                        # Distribution consistency
                        iqr = p75 - p25
                        if iqr < 100:
                            consistency = "🎯 **Highly Consistent** - Your trade outcomes are very predictable!"
                        elif iqr < 200:
                            consistency = "✅ **Good Consistency** - Your trade results show moderate variation."
                        else:
                            consistency = "🎲 **High Variation** - Your trade outcomes vary significantly."
                        
                        st.markdown(consistency)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with insight_col2:
                        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
                        st.markdown("#### 🎯 **Distribution Quality Score**")
                        
                        # Calculate distribution score
                        score = 0
                        if median_pnl > 0: score += 25
                        if risk_ratio >= 1.0: score += 25
                        if iqr < 150: score += 25  # Consistency bonus
                        if p10 > -200: score += 25  # Tail risk bonus
                        
                        if score >= 75:
                            score_emoji = "🌟"
                            score_desc = "EXCELLENT DISTRIBUTION"
                            score_color = "#00C851"
                        elif score >= 50:
                            score_emoji = "⭐"
                            score_desc = "GOOD DISTRIBUTION"
                            score_color = "#4CAF50"
                        elif score >= 25:
                            score_emoji = "⚡"
                            score_desc = "NEEDS IMPROVEMENT"
                            score_color = "#FFC107"
                        else:
                            score_emoji = "⚠️"
                            score_desc = "REQUIRES ATTENTION"
                            score_color = "#FF3547"
                        
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem;">
                            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{score_emoji}</div>
                            <div style="font-size: 2rem; font-weight: bold; color: white; margin-bottom: 0.5rem;">{score}/100</div>
                            <div style="background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 20px; display: inline-block;">
                                <span style="color: white; font-weight: bold;">{score_desc}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Percentile Grid Display
                    st.markdown("### 📈 **Trade Outcome Percentiles**")
                    
                    percentile_col1, percentile_col2, percentile_col3, percentile_col4 = st.columns(4)
                    
                    with percentile_col1:
                        st.markdown(f"""
                        <div class="percentile-box">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔸</div>
                            <div style="font-weight: bold; font-size: 1.1rem;">25th Percentile</div>
                            <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">${p25:.2f}</div>
                            <div style="opacity: 0.8; font-size: 0.9rem;">Bottom quartile</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with percentile_col2:
                        st.markdown(f"""
                        <div class="percentile-box">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔹</div>
                            <div style="font-weight: bold; font-size: 1.1rem;">75th Percentile</div>
                            <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">${p75:.2f}</div>
                            <div style="opacity: 0.8; font-size: 0.9rem;">Top quartile</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with percentile_col3:
                        st.markdown(f"""
                        <div class="percentile-box">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔻</div>
                            <div style="font-weight: bold; font-size: 1.1rem;">10th Percentile</div>
                            <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">${p10:.2f}</div>
                            <div style="opacity: 0.8; font-size: 0.9rem;">Worst 10%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with percentile_col4:
                        st.markdown(f"""
                        <div class="percentile-box">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔺</div>
                            <div style="font-weight: bold; font-size: 1.1rem;">90th Percentile</div>
                            <div style="font-size: 1.8rem; font-weight: bold; margin: 0.5rem 0;">${p90:.2f}</div>
                            <div style="opacity: 0.8; font-size: 0.9rem;">Best 10%</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Distribution Visualization
                    st.markdown("### 📊 **P&L Distribution Visualization**")
                    
                    try:
                        import plotly.graph_objects as go
                        import plotly.express as px
                        
                        # Create histogram of P&L distribution
                        fig = go.Figure()
                        
                        # Add histogram
                        fig.add_trace(go.Histogram(
                            x=pnl_data,
                            nbinsx=30,
                            marker_color='rgba(55, 128, 191, 0.7)',
                            marker_line_color='rgba(55, 128, 191, 1.0)',
                            marker_line_width=1,
                            name='Trade Distribution'
                        ))
                        
                        # Add median line
                        fig.add_vline(
                            x=median_pnl, 
                            line_dash="dash", 
                            line_color="red",
                            annotation_text=f"Median: ${median_pnl:.2f}"
                        )
                        
                        # Add mean line
                        mean_pnl = pnl_data.mean()
                        fig.add_vline(
                            x=mean_pnl, 
                            line_dash="dot", 
                            line_color="green",
                            annotation_text=f"Mean: ${mean_pnl:.2f}"
                        )
                        
                        fig.update_layout(
                            title='📊 P&L Distribution Analysis',
                            xaxis_title='P&L ($)',
                            yaxis_title='Number of Trades',
                            showlegend=False,
                            height=400,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except ImportError:
                        # Fallback to simple histogram using streamlit
                        st.bar_chart(pnl_data.value_counts().sort_index())
                        st.caption("P&L Distribution (Simple View)")
                
                else:
                    st.info("📊 No valid P&L data available for distribution analysis")
            else:
                st.info("📊 Upload trade data to view detailed distribution analysis")
            
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
``````python