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

        # Symbol analysis for optimization
        if 'symbol' in df.columns and 'pnl' in df.columns:
            symbol_performance = df.groupby('symbol')['pnl'].agg(['sum', 'count']).reset_index()
            symbol_performance['avg_pnl'] = symbol_performance['sum'] / symbol_performance['count']

            # Find best and worst performing symbols
            best_symbols = symbol_performance.nlargest(3, 'avg_pnl')['symbol'].tolist()
            worst_symbols = symbol_performance.nsmallest(3, 'avg_pnl')['symbol'].tolist()

            if len(best_symbols) > 0:
                suggestions.append({
                    "category": "Symbol Selection",
                    "priority": "Medium",
                    "suggestion": f"Best performing symbols: {', '.join(best_symbols)}",
                    "action": "Consider increasing allocation to these symbols"
                })

            if len(worst_symbols) > 0:
                suggestions.append({
                    "category": "Symbol Selection",
                    "priority": "Medium",
                    "suggestion": f"Worst performing symbols: {', '.join(worst_symbols)}",
                    "action": "Review strategy for these symbols or consider avoiding them"
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

        # General recommendations
        st.subheader("General Recommendations")

        st.write("""
        **Continuous Improvement Tips:**
        • Maintain a trading journal to track decision-making process
        • Regularly review and update your trading plan
        • Consider backtesting new strategies before implementation
        • Monitor market conditions and adapt accordingly
        • Keep learning through education and market analysis
        """)

    except Exception as e:
        logger.error(f"Error in optimization suggestions: {e}")
        st.error("Unable to generate optimization suggestions")

def render_export_options(df, stats):
    """Render data export and sharing options."""
    st.subheader("📤 Export & Share")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Export Analytics Report", type="primary"):
            # Generate analytics report
            report_data = {
                "generated_at": datetime.now().isoformat(),
                "summary_stats": stats,
                "trade_count": len(df),
                "data_columns": df.columns.tolist()
            }

            st.download_button(
                label="💾 Download Analytics JSON",
                data=pd.Series(report_data).to_json(),
                file_name=f"trading_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

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

#!/usr/bin/env python3
"""
Analytics Components
Core analytics rendering and calculation functions
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def render_analytics():
    """Main analytics rendering function."""
    st.header("📈 Trading Analytics")

    # Check if trade data is available
    if 'trade_data' not in st.session_state or st.session_state.trade_data is None:
        st.info("📊 No trade data available. Please upload your trade data first.")
        return None

    data = st.session_state.trade_data

    # Basic analytics calculations
    try:
        total_trades = len(data)

        # Calculate P&L if available
        if 'pnl' in data.columns:
            total_pnl = data['pnl'].sum()
            winning_trades = len(data[data['pnl'] > 0])
            losing_trades = len(data[data['pnl'] < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # Calculate profit factor
            gross_profit = data[data['pnl'] > 0]['pnl'].sum() if winning_trades > 0 else 0
            gross_loss = abs(data[data['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        else:
            total_pnl = 0
            win_rate = 0
            profit_factor = 0

        # Create basic P&L chart
        charts = []
        if 'pnl' in data.columns and 'date' in data.columns:
            # Sort by date and calculate cumulative P&L
            data_sorted = data.sort_values('date')
            data_sorted['cumulative_pnl'] = data_sorted['pnl'].cumsum()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data_sorted['date'],
                y=data_sorted['cumulative_pnl'],
                mode='lines',
                name='Cumulative P&L',
                line=dict(color='#00d4ff', width=2)
            ))
            fig.update_layout(
                title='Cumulative P&L Over Time',
                xaxis_title='Date',
                yaxis_title='Cumulative P&L ($)',
                template='plotly_dark'
            )
            charts.append(fig)

        # Return analytics result
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'charts': charts
        }

    except Exception as e:
        logger.error(f"Analytics calculation error: {e}")
        st.error(f"Error calculating analytics: {e}")
        return None