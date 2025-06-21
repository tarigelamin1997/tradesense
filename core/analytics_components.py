import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import logging
from toast_system import success_toast, info_toast, error_toast
from pdf_export import render_pdf_export_button
from email_scheduler import render_email_scheduling_ui

logger = logging.getLogger(__name__)

def render_analytics():
    """Render the main analytics page with comprehensive dashboard."""
    st.header("📊 Professional Trading Analytics")

    if 'trade_data' not in st.session_state or st.session_state.trade_data is None:
        st.info("📥 Upload trade data to view comprehensive analytics")
        return

    data = st.session_state.trade_data

    try:
        # Import the new dashboard system
        from visuals.dashboard_builder import TradingDashboard

        # Create and render comprehensive dashboard
        dashboard = TradingDashboard(data)
        dashboard.render_complete_dashboard()

    except ImportError:
        # Fallback to basic analytics if new system not available
        _render_basic_analytics(data)
    except Exception as e:
        st.error(f"Error rendering comprehensive analytics: {str(e)}")
        _render_basic_analytics(data)


def _render_basic_analytics(data):
    """Fallback basic analytics rendering."""
    st.warning("Using basic analytics mode")

    # Basic metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_trades = len(data)
        st.metric("Total Trades", total_trades)

    with col2:
        if 'pnl' in data.columns:
            total_pnl = data['pnl'].sum()
            st.metric("Total P&L", f"${total_pnl:,.2f}")

    with col3:
        if 'pnl' in data.columns:
            avg_pnl = data['pnl'].mean()
            st.metric("Avg P&L per Trade", f"${avg_pnl:,.2f}")

    with col4:
        if 'pnl' in data.columns:
            win_rate = (data['pnl'] > 0).mean() * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")

    # Charts
    if 'pnl' in data.columns:
        st.subheader("📈 Performance Over Time")

        # Cumulative P&L chart
        if 'date' in data.columns:
            data_sorted = data.sort_values('date')
            data_sorted['cumulative_pnl'] = data_sorted['pnl'].cumsum()

            fig = px.line(data_sorted, x='date', y='cumulative_pnl', 
                         title='Cumulative P&L Over Time')
            st.plotly_chart(fig, use_container_width=True)

        # P&L distribution
        st.subheader("📊 P&L Distribution")
        fig = px.histogram(data, x='pnl', title='P&L Distribution', nbins=30)
        st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from analytics import compute_basic_stats, performance_over_time
from datetime import datetime, timedelta
import numpy as np
import logging
from interactive_table import render_interactive_table
from notification_system import create_system_alert, NotificationType, NotificationPriority
from toast_system import success_toast, info_toast, error_toast
from pdf_export import render_pdf_export_button
from email_scheduler import render_email_scheduling_ui

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_analytics_dashboard(df):
    """Render comprehensive analytics dashboard with enhanced features."""
    if df is None or df.empty:
        st.warning("No data available for analytics")
        return

    try:
        # Header with system health indicator
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title("📊 Trading Analytics Dashboard")

        with col2:
            # Health indicator
            try:
                from health_monitoring import system_monitor
                system_monitor.render_status_widget()
            except:
                pass  # Health monitoring not available

        st.markdown("---")

        # Compute analytics
        stats = compute_basic_stats(df)

        if not stats:
            st.error("Unable to compute analytics from the provided data")
            return

        # Key Metrics Row
        render_key_metrics(stats)

        # Enhanced Interactive Data Table
        st.markdown("---")
        render_enhanced_data_table(df)

        # Charts Section
        st.markdown("---")
        render_performance_charts(df, stats)

        # Advanced Analysis
        st.markdown("---")
        render_advanced_analysis(df)

        # Export and Sharing Options
        st.markdown("---")
        render_export_options(df, stats)

    except Exception as e:
        logger.error(f"Error in render_analytics_dashboard: {e}")
        st.error(f"Analytics error: {str(e)}")

        # Create error notification
        create_system_alert(
            title="Analytics Error",
            message=f"Failed to render analytics dashboard: {str(e)}",
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH
        )

def render_enhanced_data_table(df):
    """Render enhanced interactive data table."""
    st.subheader("🗃️ Trade Data Explorer")

    # Data filtering options
    with st.expander("🔍 Filter Options", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            if 'symbol' in df.columns:
                symbols = st.multiselect(
                    "Filter by Symbol",
                    options=df['symbol'].unique(),
                    default=df['symbol'].unique()[:5] if len(df['symbol'].unique()) > 5 else df['symbol'].unique()
                )
            else:
                symbols = None

        with col2:
            if 'direction' in df.columns:
                directions = st.multiselect(
                    "Filter by Direction",
                    options=df['direction'].unique(),
                    default=df['direction'].unique()
                )
            else:
                directions = None

        with col3:
            if 'pnl' in df.columns:
                pnl_filter = st.selectbox(
                    "P&L Filter",
                    options=['All', 'Winners Only', 'Losers Only', 'Breakeven']
                )
            else:
                pnl_filter = 'All'

    # Apply filters
    filtered_df = df.copy()

    if symbols and 'symbol' in df.columns:
        filtered_df = filtered_df[filtered_df['symbol'].isin(symbols)]

    if directions and 'direction' in df.columns:
        filtered_df = filtered_df[filtered_df['direction'].isin(directions)]

    if pnl_filter != 'All' and 'pnl' in df.columns:
        pnl_numeric = pd.to_numeric(filtered_df['pnl'], errors='coerce')
        if pnl_filter == 'Winners Only':
            filtered_df = filtered_df[pnl_numeric > 0]
        elif pnl_filter == 'Losers Only':
            filtered_df = filtered_df[pnl_numeric < 0]
        elif pnl_filter == 'Breakeven':
            filtered_df = filtered_df[pnl_numeric == 0]

    # Render interactive table
    table_result = render_interactive_table(filtered_df, height=500)

    # Show selected trade details
    if table_result.get('selected_rows'):
        st.subheader("🔍 Selected Trade Details")
        selected_trade = table_result['selected_rows'][0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Symbol:** {selected_trade.get('symbol', 'N/A')}")
            st.write(f"**Direction:** {selected_trade.get('direction', 'N/A')}")
            st.write(f"**Quantity:** {selected_trade.get('qty', 'N/A')}")

        with col2:
            st.write(f"**Entry Price:** ${selected_trade.get('entry_price', 0):.2f}")
            st.write(f"**Exit Price:** ${selected_trade.get('exit_price', 0):.2f}")
            st.write(f"**Entry Time:** {selected_trade.get('entry_time', 'N/A')}")

        with col3:
            pnl = selected_trade.get('pnl', 0)
            if pnl > 0:
                st.success(f"**P&L:** +${pnl:.2f}")
            else:
                st.error(f"**P&L:** ${pnl:.2f}")
            st.write(f"**Exit Time:** {selected_trade.get('exit_time', 'N/A')}")

def render_key_metrics(stats):
    """Render enhanced key performance metrics."""
    st.subheader("🎯 Key Performance Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        win_rate = stats.get('win_rate', 0)
        delta_color = "normal" if win_rate > 50 else "inverse"
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta="Good" if win_rate > 50 else "Needs Improvement",
            delta_color=delta_color
        )

    with col2:
        total_trades = stats.get('total_trades', 0)
        st.metric("Total Trades", f"{total_trades:,}")

    with col3:
        profit_factor = stats.get('profit_factor', 0)
        delta_color = "normal" if profit_factor > 1.2 else "inverse"
        st.metric(
            "Profit Factor",
            f"{profit_factor:.2f}",
            delta="Good" if profit_factor > 1.2 else "Poor",
            delta_color=delta_color
        )

    with col4:
        expectancy = stats.get('expectancy', 0)
        delta_color = "normal" if expectancy > 0 else "inverse"
        st.metric(
            "Expectancy",
            f"${expectancy:.2f}",
            delta_color=delta_color
        )

    with col5:
        sharpe_ratio = stats.get('sharpe_ratio', 0)
        delta_color = "normal" if sharpe_ratio > 1.0 else "inverse"
        st.metric(
            "Sharpe Ratio",
            f"{sharpe_ratio:.2f}",
            delta="Good" if sharpe_ratio > 1.0 else "Poor",
            delta_color=delta_color
        )

def render_performance_charts(df, stats):
    """Render enhanced performance visualization charts."""
    st.subheader("📈 Performance Analysis")

    # Create tabs for different chart types
    chart_tabs = st.tabs([
        "Equity Curve", 
        "Monthly Performance", 
        "Drawdown Analysis",
        "Trade Distribution",
        "Correlation Analysis"
    ])

    with chart_tabs[0]:
        render_equity_curve(df, stats)

    with chart_tabs[1]:
        render_monthly_performance(df)

    with chart_tabs[2]:
        render_drawdown_analysis(df, stats)

    with chart_tabs[3]:
        render_trade_distribution(df)

    with chart_tabs[4]:
        render_correlation_analysis(df)

def render_equity_curve(df, stats):
    """Render enhanced equity curve chart."""
    try:
        if 'equity_curve' in stats and len(stats['equity_curve']) > 0:
            equity_data = stats['equity_curve']
            cumulative_pnl = equity_data.cumsum()

            # Calculate running maximum for drawdown visualization
            running_max = cumulative_pnl.expanding().max()

            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Cumulative P&L', 'Drawdown'),
                vertical_spacing=0.1,
                row_heights=[0.7, 0.3]
            )

            # Equity curve
            fig.add_trace(go.Scatter(
                y=cumulative_pnl,
                mode='lines',
                name='Equity Curve',
                line=dict(color='#1f77b4', width=2)
            ), row=1, col=1)

            # Running maximum
            fig.add_trace(go.Scatter(
                y=running_max,
                mode='lines',
                name='Peak Equity',
                line=dict(color='#ff7f0e', width=1, dash='dash'),
                opacity=0.7
            ), row=1, col=1)

            # Drawdown
            drawdown = running_max - cumulative_pnl
            fig.add_trace(go.Scatter(
                y=-drawdown,
                mode='lines',
                name='Drawdown',
                line=dict(color='#d62728', width=1),
                fill='tonexty'
            ), row=2, col=1)

            fig.update_layout(
                title="Equity Curve and Drawdown Analysis",
                xaxis_title="Trade Number",
                yaxis_title="Cumulative P&L ($)",
                hovermode='x unified',
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Equity curve data not available")
    except Exception as e:
        logger.error(f"Error rendering equity curve: {e}")
        st.error("Unable to render equity curve")

def render_correlation_analysis(df):
    """Render correlation analysis between different metrics."""
    try:
        if df.empty:
            st.info("No data available for correlation analysis")
            return

        # Select numeric columns for correlation
        numeric_cols = []
        for col in ['pnl', 'qty', 'entry_price', 'exit_price']:
            if col in df.columns:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                if not numeric_data.isna().all():
                    numeric_cols.append(col)

        if len(numeric_cols) < 2:
            st.info("Insufficient numeric data for correlation analysis")
            return

        # Calculate correlation matrix
        correlation_data = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        correlation_matrix = correlation_data.corr()

        # Create heatmap
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="Correlation Matrix of Trading Metrics",
            color_continuous_scale='RdBu_r'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        st.subheader("Correlation Insights")

        high_correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:
                    col1, col2 = correlation_matrix.columns[i], correlation_matrix.columns[j]
                    high_correlations.append((col1, col2, corr_value))

        if high_correlations:
            st.write("**Significant Correlations (|r| > 0.5):**")
            for col1, col2, corr in high_correlations:
                direction = "positive" if corr > 0 else "negative"
                st.write(f"• {col1} and {col2}: {direction} correlation (r={corr:.3f})")
        else:
            st.write("No strong correlations found between trading metrics.")

    except Exception as e:
        logger.error(f"Error in correlation analysis: {e}")
        st.error("Unable to perform correlation analysis")

def render_advanced_analysis(df):
    """Render advanced trading analysis with machine learning insights."""
    st.subheader("🧠 Advanced Analysis")

    analysis_tabs = st.tabs([
        "Performance Patterns",
        "Risk Analysis", 
        "Behavioral Insights",
        "Optimization Suggestions"
    ])

    with analysis_tabs[0]:
        render_performance_patterns(df)

    with analysis_tabs[1]:
        render_advanced_risk_analysis(df)

    with analysis_tabs[2]:
        render_behavioral_insights(df)

    with analysis_tabs[3]:
        render_optimization_suggestions(df)

def render_performance_patterns(df):
    """Analyze and visualize performance patterns."""
    try:
        if 'pnl' not in df.columns:
            st.info("P&L data required for pattern analysis")
            return

        pnl_data = pd.to_numeric(df['pnl'], errors='coerce').dropna()

        if len(pnl_data) < 10:
            st.info("Insufficient data for pattern analysis")
            return

        # Streak analysis
        is_winner = pnl_data > 0
        streaks = []
        current_streak = 1
        current_type = is_winner.iloc[0]

        for i in range(1, len(is_winner)):
            if is_winner.iloc[i] == current_type:
                current_streak += 1
            else:
                streaks.append((current_type, current_streak))
                current_streak = 1
                current_type = is_winner.iloc[i]

        streaks.append((current_type, current_streak))

        # Analyze streaks
        win_streaks = [length for is_win, length in streaks if is_win]
        loss_streaks = [length for is_win, length in streaks if not is_win]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Streak Analysis")
            if win_streaks:
                st.metric("Max Win Streak", max(win_streaks))
                st.metric("Avg Win Streak", f"{np.mean(win_streaks):.1f}")
            else:
                st.metric("Max Win Streak", 0)
                st.metric("Avg Win Streak", 0)

        with col2:
            if loss_streaks:
                st.metric("Max Loss Streak", max(loss_streaks))
                st.metric("Avg Loss Streak", f"{np.mean(loss_streaks):.1f}")
            else:
                st.metric("Max Loss Streak", 0)
                st.metric("Avg Loss Streak", 0)

        # Pattern insights
        st.subheader("Pattern Insights")

        if max(win_streaks) if win_streaks else 0 > 5:
            st.success("✅ Good winning momentum - you maintain winning streaks well")

        if max(loss_streaks) if loss_streaks else 0 > 5:
            st.warning("⚠️ Long losing streaks detected - consider position sizing adjustments")

    except Exception as e:
        logger.error(f"Error in performance patterns: {e}")
        st.error("Unable to analyze performance patterns")

def render_advanced_risk_analysis(df):
    """Render advanced risk analysis with multiple risk metrics."""
    try:
        if 'pnl' not in df.columns:
            st.info("P&L data required for risk analysis")
            return

        pnl_data = pd.to_numeric(df['pnl'], errors='coerce').dropna()

        if pnl_data.empty:
            st.info("No valid P&L data for risk analysis")
            return

        # Advanced risk metrics
        returns_std = pnl_data.std()
        var_95 = pnl_data.quantile(0.05)  # Value at Risk (95%)
        var_99 = pnl_data.quantile(0.01)  # Value at Risk (99%)

        # Conditional Value at Risk (Expected Shortfall)
        cvar_95 = pnl_data[pnl_data <= var_95].mean() if len(pnl_data[pnl_data <= var_95]) > 0 else 0

        # Maximum consecutive loss
        consecutive_losses = []
        current_loss = 0
        for pnl in pnl_data:
            if pnl < 0:
                current_loss += pnl
            else:
                if current_loss < 0:
                    consecutive_losses.append(current_loss)
                current_loss = 0

        if current_loss < 0:
            consecutive_losses.append(current_loss)

        max_consecutive_loss = min(consecutive_losses) if consecutive_losses else 0

        # Display risk metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("VaR (95%)", f"${var_95:.2f}")

        with col2:
            st.metric("VaR (99%)", f"${var_99:.2f}")

        with col3:
            st.metric("CVaR (95%)", f"${cvar_95:.2f}")

        with col4:
            st.metric("Max Consecutive Loss", f"${max_consecutive_loss:.2f}")

        # Risk assessment with recommendations
        st.subheader("Risk Assessment & Recommendations")

        if abs(var_99) > 2000:
            st.error("🚨 Very High Risk Profile")
            st.write("**Recommendations:**")
            st.write("• Reduce position sizes significantly")
            st.write("• Implement stricter stop losses")
            st.write("• Consider risk management training")
        elif abs(var_99) > 1000:
            st.warning("⚠️ High Risk Profile")
            st.write("**Recommendations:**")
            st.write("• Review and tighten risk management rules")
            st.write("• Consider reducing position sizes")
        elif abs(var_99) > 500:
            st.info("ℹ️ Moderate Risk Profile")
            st.write("**Recommendations:**")
            st.write("• Current risk levels appear manageable")
            st.write("• Monitor for any increase in volatility")
        else:
            st.success("✅ Conservative Risk Profile")
            st.write("Low risk detected - good risk management practices")

    except Exception as e:
        logger.error(f"Error in advanced risk analysis: {e}")
        st.error("Unable to perform advanced risk analysis")

def render_behavioral_insights(df):
    """Analyze trading behavior patterns."""
    try:
        st.subheader("Trading Behavior Analysis")

        if 'entry_time' in df.columns and 'exit_time' in df.columns:
            # Trade timing analysis
            df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
            df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')

            valid_times = df.dropna(subset=['entry_time', 'exit_time'])

            if not valid_times.empty:
                # Trade duration
                valid_times['duration_minutes'] = (
                    valid_times['exit_time'] - valid_times['entry_time']
                ).dt.total_seconds() / 60

                avg_duration = valid_times['duration_minutes'].mean()

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Average Trade Duration", f"{avg_duration:.0f} minutes")

                    # Duration distribution
                    fig = px.histogram(
                        valid_times,
                        x='duration_minutes',
                        title='Trade Duration Distribution',
                        labels={'duration_minutes': 'Duration (minutes)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Hour of day analysis
                    valid_times['entry_hour'] = valid_times['entry_time'].dt.hour
                    hourly_stats = valid_times.groupby('entry_hour').agg({
                        'pnl': ['count', 'mean']
                    }).round(2)

                    hourly_stats.columns = ['Trade Count', 'Avg P&L']

                    st.write("**Trading Activity by Hour**")
                    st.dataframe(hourly_stats)

        # Position sizing behavior
        if 'qty' in df.columns and 'pnl' in df.columns:
            qty_data = pd.to_numeric(df['qty'], errors='coerce').dropna()
            pnl_data = pd.to_numeric(df['pnl'], errors='coerce').dropna()

            if not qty_data.empty:
                st.subheader("Position Sizing Behavior")

                # Analyze if position size affects performance
                df_clean = df.copy()
                df_clean['qty'] = pd.to_numeric(df_clean['qty'], errors='coerce')
                df_clean['pnl'] = pd.to_numeric(df_clean['pnl'], errors='coerce')
                df_clean = df_clean.dropna(subset=['qty', 'pnl'])

                if len(df_clean) > 10:
                    # Correlation between position size and P&L
                    correlation = df_clean['qty'].corr(df_clean['pnl'])

                    st.metric("Position Size vs P&L Correlation", f"{correlation:.3f}")

                    if abs(correlation) > 0.3:
                        if correlation > 0:
                            st.info("ℹ️ Larger positions tend to be more profitable")
                        else:
                            st.warning("⚠️ Larger positions tend to be less profitable")
                    else:
                        st.success("✅ Position size appears independent of P&L")

    except Exception as e:
        logger.error(f"Error in behavioral insights: {e}")
        st.error("Unable to analyze trading behavior")

def render_optimization_suggestions(df):
    """Provide data-driven optimization suggestions."""
    try:
        st.subheader("Optimization Suggestions")

        suggestions = []

        if 'pnl' in df.columns:
            pnl_data = pd.to_numeric(df['pnl'], errors='coerce').dropna()

            if not pnl_data.empty:
                win_rate = (pnl_data > 0).mean() * 100
                avg_win = pnl_data[pnl_data > 0].mean() if len(pnl_data[pnl_data > 0]) > 0 else 0
                avg_loss = pnl_data[pnl_data < 0].mean() if len(pnl_data[pnl_data < 0]) > 0 else 0

                # Win rate optimization
                if win_rate < 40:
                    suggestions.append({
                        "category": "Trade Selection",
                        "priority": "High",
                        "suggestion": "Focus on improving trade selection criteria - win rate below 40%",
                        "action": "Review entry signals and market conditions for winning vs losing trades"
                    })

                # Risk-reward optimization
                if avg_loss != 0:
                    rr_ratio = abs(avg_win / avg_loss)
                    if rr_ratio < 1.2:
                        suggestions.append({
                            "category": "Risk Management",
                            "priority": "High",
                            "suggestion": f"Improve risk-reward ratio (current: {rr_ratio:.2f})",
                            "action": "Consider tighter stop losses or wider profit targets"
                        })

                # Consistency optimization
                volatility = pnl_data.std()
                if volatility > abs(pnl_data.mean()) * 5:
                    suggestions.append({
                        "category": "Consistency",
                        "priority": "Medium",
                        "suggestion": "High volatility in returns detected",
                        "action": "Consider more consistent position sizing and risk management"
                    })

        # Display suggestions
        if suggestions:
            for i, suggestion in enumerate(suggestions):
                priority_color = {
                    "High": "🔴",
                    "Medium": "🟡", 
                    "Low": "🟢"
                }.get(suggestion["priority"], "⚪")

                with st.expander(f"{priority_color} {suggestion['category']}: {suggestion['suggestion']}"):
                    st.write(f"**Priority:** {suggestion['priority']}")
                    st.write(f"**Suggested Action:** {suggestion['action']}")
        else:
            st.success("✅ No major optimization opportunities identified. Your trading appears well-optimized!")

    except Exception as e:
        logger.error(f"Error in optimization suggestions: {e}")
        st.error("Unable to generate optimization suggestions")

def render_export_options(df, stats):
    """Render data export and sharing options."""
    st.subheader("📤 Export & Share")

    col1, col2, col3 = st.columns(3)

    with col1:
        # PDF Export button
        from pdf_export import render_pdf_export_button
        render_pdf_export_button(df, stats)

    with col2:
        if st.button("📈 Export Charts", type="secondary"):
            st.info("Chart export functionality would be implemented here")

    with col3:
        if st.button("📋 Copy Summary", type="secondary"):
            summary_text = f"""
Trading Analytics Summary:
Total Trades: {stats.get('total_trades', 0)}
Win Rate: {stats.get('win_rate', 0):.1f}%
Profit Factor: {stats.get('profit_factor', 0):.2f}
Expectancy: ${stats.get('expectancy', 0):.2f}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            st.code(summary_text)
            st.success("Summary ready to copy!")

def render_analytics():
    """Main analytics rendering function with comprehensive dashboard."""
    st.header("📈 Trading Analytics")

    # Check if trade data is available
    if 'trade_data' not in st.session_state or st.session_state.trade_data is None:
        st.info("📊 No analytics available. Please upload your trades to generate insights.")
        return None

    data = st.session_state.trade_data

    try:
        # Comprehensive analytics calculations
        total_trades = len(data)

        if total_trades == 0:
            st.warning("No trade data found. Please upload valid trade data.")
            return None

        # Enhanced analytics with all requested metrics
        stats = calculate_comprehensive_analytics(data)

        if not stats:
            st.error("Unable to calculate analytics from the provided data")
            return None

        # Render enhanced dashboard
        render_comprehensive_dashboard(data, stats)

        return stats

    except Exception as e:
        logger.error(f"Analytics calculation error: {e}")
        st.error(f"Error calculating analytics: {e}")
        return None

def calculate_comprehensive_analytics(data):
    """Calculate comprehensive trading analytics."""
    try:
        stats = {}

        # Basic metrics
        stats['total_trades'] = len(data)

        if 'pnl' in data.columns:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').dropna()

            if not pnl_data.empty:
                stats['total_pnl'] = pnl_data.sum()
                stats['avg_pnl'] = pnl_data.mean()

                winning_trades = pnl_data[pnl_data > 0]
                losing_trades = pnl_data[pnl_data < 0]

                stats['win_rate'] = (len(winning_trades) / len(pnl_data) * 100) if len(pnl_data) > 0 else 0
                stats['winning_trades'] = len(winning_trades)
                stats['losing_trades'] = len(losing_trades)

                # Profit factor
                gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
                gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
                stats['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')

                # Best/Worst trades
                stats['best_trade'] = pnl_data.max()
                stats['worst_trade'] = pnl_data.min()

                # Expectancy
                stats['expectancy'] = pnl_data.mean()

        # Duration analysis
        if 'entry_time' in data.columns and 'exit_time' in data.columns:
            try:
                data['entry_time'] = pd.to_datetime(data['entry_time'], errors='coerce')
                data['exit_time'] = pd.to_datetime(data['exit_time'], errors='coerce')

                valid_duration = data.dropna(subset=['entry_time', 'exit_time'])
                if not valid_duration.empty:
                    durations = (valid_duration['exit_time'] - valid_duration['entry_time']).dt.total_seconds() / 3600
                    stats['avg_holding_time'] = durations.mean()
                    stats['avg_trade_duration'] = durations.mean()
            except:
                stats['avg_holding_time'] = 0
                stats['avg_trade_duration'] = 0

        # Direction analysis
        if 'direction' in data.columns:
            direction_counts = data['direction'].value_counts()
            total = direction_counts.sum()
            ```python
            if total > 0:
                stats['long_percentage'] = (direction_counts.get('Long', 0) / total * 100)
                stats['short_percentage'] = (direction_counts.get('Short', 0) / total * 100)

        # Consistency score (streak analysis)
        if 'pnl' in data.columns:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').dropna()
            if not pnl_data.empty:
                # Calculate win/loss streaks
                wins = (pnl_data > 0).astype(int)
                streaks = []
                current_streak = 1

                for i in range(1, len(wins)):
                    if wins.iloc[i] == wins.iloc[i-1]:
                        current_streak += 1
                    else:
                        streaks.append(current_streak)
                        current_streak = 1
                streaks.append(current_streak)

                # Consistency score based on average streak length vs volatility
                avg_streak = np.mean(streaks) if streaks else 0
                volatility = pnl_data.std()
                consistency_score = min(100, max(0, (avg_streak * 20) - (volatility / 100)))
                stats['consistency_score'] = consistency_score

        return stats

    except Exception as e:
        logger.error(f"Error calculating comprehensive analytics: {e}")
        return {}

def render_comprehensive_dashboard(data, stats):
    """Render the comprehensive analytics dashboard."""

    # Key Metrics Cards with animations
    st.subheader("🎯 Key Performance Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Total Trades</h3>
            <div class="metric-value">{:,}</div>
        </div>
        """.format(stats.get('total_trades', 0)), unsafe_allow_html=True)

    with col2:
        win_rate = stats.get('win_rate', 0)
        color = "#10b981" if win_rate > 50 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 Win Rate</h3>
            <div class="metric-value" style="color: {color}">{win_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        total_pnl = stats.get('total_pnl', 0)
        color = "#10b981" if total_pnl > 0 else "#ef4444"
        sign = "+" if total_pnl > 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Net P&L</h3>
            <div class="metric-value" style="color: {color}">{sign}${total_pnl:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        profit_factor = stats.get('profit_factor', 0)
        if profit_factor == float('inf'):
            pf_display = "∞"
            color = "#10b981"
        else:
            pf_display = f"{profit_factor:.2f}"
            color = "#10b981" if profit_factor > 1.5 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Profit Factor</h3>
            <div class="metric-value" style="color: {color}">{pf_display}</div>
        </div>
        """, unsafe_allow_html=True)

    # Second row of metrics
    st.markdown("---")
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        avg_duration = stats.get('avg_trade_duration', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏱️ Avg Duration</h3>
            <div class="metric-value">{avg_duration:.1f}h</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        long_pct = stats.get('long_percentage', 50)
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Long vs Short</h3>
            <div class="metric-value">{long_pct:.0f}% / {100-long_pct:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col7:
        best_trade = stats.get('best_trade', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏆 Best Trade</h3>
            <div class="metric-value" style="color: #10b981">${best_trade:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col8:
        consistency = stats.get('consistency_score', 0)
        color = "#10b981" if consistency > 70 else "#f59e0b" if consistency > 40 else "#ef4444"
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 Consistency</h3>
            <div class="metric-value" style="color: {color}">{consistency:.0f}/100</div>
        </div>
        """, unsafe_allow_html=True)

    # Charts section
    st.markdown("---")
    st.subheader("📈 Performance Charts")

    chart_tabs = st.tabs(["Equity Curve", "P&L Distribution", "Performance by Symbol"])

    with chart_tabs[0]:
        render_equity_curve_chart(data, stats)

    with chart_tabs[1]:
        render_pnl_distribution_chart(data)

    with chart_tabs[2]:
        render_symbol_performance_chart(data)

    # Export options
    st.markdown("---")
    render_export_options(data, stats)

def render_equity_curve_chart(data, stats):
    """Render equity curve chart."""
    if 'pnl' in data.columns:
        try:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').dropna()
            cumulative_pnl = pnl_data.cumsum()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=cumulative_pnl,
                mode='lines',
                name='Cumulative P&L',
                line=dict(color='#00d4ff', width=3)
            ))

            fig.update_layout(
                title='Equity Curve',
                xaxis_title='Trade Number',
                yaxis_title='Cumulative P&L ($)',
                template='plotly_dark',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering equity curve: {e}")
    else:
        st.info("P&L data required for equity curve")

def render_pnl_distribution_chart(data):
    """Render P&L distribution histogram."""
    if 'pnl' in data.columns:
        try:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').dropna()

            fig = px.histogram(
                x=pnl_data,
                nbins=30,
                title='P&L Distribution',
                color_discrete_sequence=['#00d4ff']
            )

            fig.update_layout(
                xaxis_title='P&L ($)',
                yaxis_title='Frequency',
                template='plotly_dark',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering P&L distribution: {e}")
    else:
        st.info("P&L data required for distribution chart")

def render_symbol_performance_chart(data):
    """Render performance by symbol chart."""
    if 'symbol' in data.columns and 'pnl' in data.columns:
        try:
            symbol_performance = data.groupby('symbol')['pnl'].sum().reset_index()
            symbol_performance = symbol_performance.sort_values('pnl', ascending=True)

            fig = px.bar(
                symbol_performance,
                x='pnl',
                y='symbol',
                orientation='h',
                title='P&L by Symbol',
                color='pnl',
                color_continuous_scale='RdYlGn'
            )

            fig.update_layout(
                xaxis_title='Total P&L ($)',
                yaxis_title='Symbol',
                template='plotly_dark',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error rendering symbol performance: {e}")
    else:
        st.info("Symbol and P&L data required for this chart")

    

class TradingDashboard:
    """
    Trading Dashboard class for rendering comprehensive analytics.
    """
    def __init__(self, trade_data: pd.DataFrame):
        """Initialise with trade data."""
        self.trade_data = trade_data
        self.logger = logging.getLogger(__name__)

    def render_complete_dashboard(self):
        """Render complete trading analytics dashboard."""
        st.header("📊 Trading Analytics Dashboard")

        # Check if trade data is available
        if self.trade_data is None or self.trade_data.empty:
            st.info("📈 No trade data available. Please upload your trades to generate insights.")
            return

        try:
            # Enhanced analytics rendering
            self.render_enhanced_analytics(self.trade_data)

            # Charts and Visualizations
            st.subheader("📈 Charts and Visualizations")
            self._render_charts(self.trade_data)

        except Exception as e:
            self.logger.error(f"Dashboard rendering error: {e}")
            st.error(f"Error rendering dashboard: {e}")

    def render_enhanced_analytics(self, trade_data: pd.DataFrame):
        """Render enhanced analytics dashboard."""
        if trade_data is None or trade_data.empty:
            st.warning("📊 No trade data available for analytics")
            return

        # Enhanced Analytics Overview
        st.markdown("### 🎯 Enhanced Performance Analytics")

        # Create columns for comprehensive metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_trades = len(trade_data)
            st.metric("Total Trades", f"{total_trades:,}")

        with col2:
            if 'pnl' in trade_data.columns:
                total_pnl = trade_data['pnl'].sum()
                st.metric("Total P&L", f"${total_pnl:,.2f}")

        with col3:
            if 'pnl' in trade_data.columns:
                winning_trades = len(trade_data[trade_data['pnl'] > 0])
                win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")

        with col4:
            if 'pnl' in trade_data.columns:
                avg_trade = trade_data['pnl'].mean()
                st.metric("Avg Trade", f"${avg_trade:,.2f}")

        # Additional enhanced metrics
        st.markdown("---")
        self._render_advanced_metrics(trade_data)

        # Trade Duration Analysis
        st.markdown("---")
        self._render_duration_analysis(trade_data)

        # Long vs Short Analysis
        st.markdown("---")
        self._render_long_short_analysis(trade_data)

        # Best/Worst Trade Analysis
        st.markdown("---")
        self._render_best_worst_analysis(trade_data)

        # Consistency Scoring
        st.markdown("---")
        self._render_consistency_scoring(trade_data)

    def _render_advanced_metrics(self, trade_data: pd.DataFrame):
        """Render advanced trading metrics."""
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📈 Profit Factor")
            if 'pnl' in trade_data.columns:
                gross_profit = trade_data[trade_data['pnl'] > 0]['pnl'].sum()
                gross_loss = abs(trade_data[trade_data['pnl'] < 0]['pnl'].sum())
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                st.metric("Profit Factor", f"{profit_factor:.2f}")

        with col2:
            st.subheader("📊 Sharpe Ratio")
            if 'pnl' in trade_data.columns:
                returns = trade_data['pnl']
                sharpe = returns.mean() / returns.std() if returns.std() > 0 else 0
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")

        with col3:
            st.subheader("📉 Max Drawdown")
            if 'pnl' in trade_data.columns:
                cumulative_pnl = trade_data['pnl'].cumsum()
                running_max = cumulative_pnl.expanding().max()
                drawdown = (cumulative_pnl - running_max)
                max_drawdown = drawdown.min()
                st.metric("Max Drawdown", f"${max_drawdown:,.2f}")

    def _render_duration_analysis(self, trade_data: pd.DataFrame):
        """Render trade duration analysis."""
        st.subheader("⏱️ Trade Duration Analysis")

        # Calculate holding times if date columns exist
        if 'entry_time' in trade_data.columns and 'exit_time' in trade_data.columns:
            try:
                trade_data['entry_time'] = pd.to_datetime(trade_data['entry_time'])
                trade_data['exit_time'] = pd.to_datetime(trade_data['exit_time'])
                trade_data['holding_time'] = (trade_data['exit_time'] - trade_data['entry_time']).dt.total_seconds() / 3600  # hours

                col1, col2, col3 = st.columns(3)

                with col1:
                    avg_holding = trade_data['holding_time'].mean()
                    st.metric("Avg Holding Time", f"{avg_holding:.1f} hours")

                with col2:
                    median_holding = trade_data['holding_time'].median()
                    st.metric("Median Holding Time", f"{median_holding:.1f} hours")

                with col3:
                    max_holding = trade_data['holding_time'].max()
                    st.metric("Max Holding Time", f"{max_holding:.1f} hours")

                # Holding time distribution chart
                fig = px.histogram(trade_data, x='holding_time', bins=20, 
                                 title="Trade Duration Distribution")
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.info("💡 Trade duration analysis requires entry_time and exit_time columns")
        else:
            st.info("💡 Upload data with entry_time and exit_time columns for duration analysis")

    def _render_long_short_analysis(self, trade_data: pd.DataFrame):
        """Render long vs short position analysis."""
        st.subheader("📊 Long vs Short Analysis")

        if 'direction' in trade_data.columns:
            direction_stats = trade_data.groupby('direction').agg({
                'pnl': ['count', 'sum', 'mean']
            }).round(2)

            col1, col2 = st.columns(2)

            with col1:
                long_trades = len(trade_data[trade_data['direction'].str.lower() == 'long'])
                short_trades = len(trade_data[trade_data['direction'].str.lower() == 'short'])
                total = long_trades + short_trades

                long_pct = (long_trades / total * 100) if total > 0 else 0
                short_pct = (short_trades / total * 100) if total > 0 else 0

                st.metric("Long Trades", f"{long_trades} ({long_pct:.1f}%)")
                st.metric("Short Trades", f"{short_trades} ({short_pct:.1f}%)")

            with col2:
                if 'pnl' in trade_data.columns:
                    long_pnl = trade_data[trade_data['direction'].str.lower() == 'long']['pnl'].sum()
                    short_pnl = trade_data[trade_data['direction'].str.lower() == 'short']['pnl'].sum()

                    st.metric("Long P&L", f"${long_pnl:,.2f}")
                    st.metric("Short P&L", f"${short_pnl:,.2f}")
        else:
            st.info("💡 Upload data with 'direction' column for long/short analysis")

    def _render_best_worst_analysis(self, trade_data: pd.DataFrame):
        """Render best and worst trade analysis."""
        st.subheader("🏆 Best & Worst Trades")

        if 'pnl' in trade_data.columns:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🥇 Best Trades")
                best_trades = trade_data.nlargest(5, 'pnl')[['symbol', 'pnl', 'date'] if 'symbol' in trade_data.columns and 'date' in trade_data.columns else ['pnl']]
                st.dataframe(best_trades, hide_index=True)

            with col2:
                st.markdown("#### 🔴 Worst Trades")
                worst_trades = trade_data.nsmallest(5, 'pnl')[['symbol', 'pnl', 'date'] if 'symbol' in trade_data.columns and 'date' in trade_data.columns else ['pnl']]
                st.dataframe(worst_trades, hide_index=True)

    def _render_consistency_scoring(self, trade_data: pd.DataFrame):
        """Render consistency scoring analysis."""
        st.subheader("🎯 Consistency Scoring")

        if 'pnl' in trade_data.columns and len(trade_data) > 0:
            # Calculate consistency metrics
            returns = trade_data['pnl']
            winning_trades = len(returns[returns > 0])
            total_trades = len(returns)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            # Calculate rolling performance (if enough data)
            if len(trade_data) >= 10:
                rolling_returns = returns.rolling(window=10).sum()
                positive_periods = len(rolling_returns[rolling_returns > 0])
                total_periods = len(rolling_returns.dropna())
                consistency_score = (positive_periods / total_periods * 100) if total_periods > 0 else 0
            else:
                consistency_score = win_rate * 100

            # Return consistency
            return_std = returns.std()
            return_mean = returns.mean()
            coefficient_of_variation = abs(return_std / return_mean) if return_mean != 0 else float('inf')

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Consistency Score", f"{consistency_score:.1f}%")
                if consistency_score >= 70:
                    st.success("🟢 Highly Consistent")
                elif consistency_score >= 50:
                    st.warning("🟡 Moderately Consistent")
                else:
                    st.error("🔴 Needs Improvement")

            with col2:
                st.metric("Return Volatility", f"{return_std:.2f}")
                if coefficient_of_variation < 1:
                    st.success("🟢 Low Volatility")
                elif coefficient_of_variation < 2:
                    st.warning("🟡 Medium Volatility")
                else:
                    st.error("🔴 High Volatility")

            with col3:
                monthly_consistency = self._calculate_monthly_consistency(trade_data)
                st.metric("Monthly Win Rate", f"{monthly_consistency:.1f}%")

    def _calculate_monthly_consistency(self, trade_data: pd.DataFrame):
        """Calculate monthly consistency rate."""
        try:
            if 'date' in trade_data.columns and 'pnl' in trade_data.columns:
                trade_data['date'] = pd.to_datetime(trade_data['date'])
                monthly_pnl = trade_data.groupby(trade_data['date'].dt.to_period('M'))['pnl'].sum()
                winning_months = len(monthly_pnl[monthly_pnl > 0])
                total_months = len(monthly_pnl)
                return (winning_months / total_months * 100) if total_months > 0 else 0
            else:
                return 0
        except:
            return 0

    def _render_charts(self, trade_data: pd.DataFrame):
        """Render charts and visualizations for trading data."""
        # Example charts (you can expand this section)
        if 'pnl' in trade_data.columns:
            st.subheader("P&L Distribution")
            fig = px.histogram(trade_data, x='pnl', title='P&L Distribution')
            st.plotly_chart(fig, use_container_width=True)

            # Equity Curve
            cumulative_pnl = trade_data['pnl'].cumsum()
            fig = px.line(x=trade_data.index, y=cumulative_pnl, title='Equity Curve')
            st.plotly_chart(fig, use_container_width=True)