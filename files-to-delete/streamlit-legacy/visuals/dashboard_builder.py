
"""
Comprehensive trading analytics dashboard for Streamlit.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from metrics import PerformanceSummary, EquityCurveEngine, calculate_batch_trade_metrics, analyze_trade_tags


class TradingDashboard:
    """Complete trading analytics dashboard with multiple views."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize dashboard with trade data.
        
        Args:
            df: DataFrame containing trade data
        """
        self.df = df.copy()
        self.performance_summary = None
        self.equity_engine = None
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for dashboard display."""
        if len(self.df) == 0:
            return
        
        # Calculate trade metrics
        self.df = calculate_batch_trade_metrics(self.df)
        
        # Initialize analysis engines
        self.performance_summary = PerformanceSummary(self.df)
        self.equity_engine = EquityCurveEngine(self.df)
    
    def render_complete_dashboard(self):
        """Render the complete trading dashboard."""
        if len(self.df) == 0:
            st.warning("📊 No trade data available for analysis")
            return
        
        # Header
        st.title("🎯 Trading Performance Analytics")
        st.markdown("---")
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Equity & Returns",
            "🎯 Win/Loss Analysis", 
            "🔁 Streak & Consistency",
            "⏱ Time Analysis",
            "📊 Frequency & Session",
            "⚠️ Behavioral Insights"
        ])
        
        with tab1:
            self._render_equity_returns_tab()
        
        with tab2:
            self._render_win_loss_tab()
        
        with tab3:
            self._render_streak_consistency_tab()
        
        with tab4:
            self._render_time_analysis_tab()
        
        with tab5:
            self._render_frequency_session_tab()
        
        with tab6:
            self._render_behavioral_insights_tab()
    
    def _render_equity_returns_tab(self):
        """Render equity curve and returns analysis."""
        st.subheader("📈 Equity Curve & Returns Dashboard")
        
        # Key metrics at top
        metrics = self.performance_summary.calculate_all_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total P&L", f"${metrics.total_pnl:,.2f}")
        with col2:
            st.metric("Total Return", f"{metrics.total_return_percent:.2f}%")
        with col3:
            st.metric("Max Drawdown", f"${metrics.max_drawdown:,.2f}")
        with col4:
            st.metric("Recovery Factor", f"{metrics.recovery_factor:.2f}")
        
        # Equity curve chart
        st.subheader("Cumulative P&L & Drawdown")
        equity_chart = self.equity_engine.generate_equity_curve_chart(
            show_streaks=True, 
            show_drawdown=True
        )
        st.plotly_chart(equity_chart, use_container_width=True, key="equity_curve_main")
        
        # Drawdown analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📉 Drawdown Analysis")
            drawdown_analysis = self.equity_engine.get_drawdown_analysis()
            
            if drawdown_analysis:
                st.metric("Max Drawdown ($)", f"${drawdown_analysis['max_drawdown_dollar']:,.2f}")
                st.metric("Max Drawdown (%)", f"{drawdown_analysis['max_drawdown_percent']:.2f}%")
                st.metric("Current Drawdown", f"${drawdown_analysis['current_drawdown']:,.2f}")
                st.metric("Drawdown Periods", drawdown_analysis['drawdown_periods'])
        
        with col2:
            st.subheader("🔄 Recovery Analysis")
            recovery_analysis = self.equity_engine.get_recovery_analysis()
            
            if recovery_analysis:
                st.metric("Avg Recovery Time", f"{recovery_analysis['avg_recovery_time']:.1f} trades")
                st.metric("Longest Recovery", f"{recovery_analysis['longest_recovery']} trades")
                st.metric("Recovery Periods", recovery_analysis['recovery_periods'])
    
    def _render_win_loss_tab(self):
        """Render win/loss analysis."""
        st.subheader("🎯 Win/Loss Performance Analysis")
        
        metrics = self.performance_summary.calculate_all_metrics()
        
        # Key ratios
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Win Rate", f"{metrics.win_rate:.1f}%")
        with col2:
            st.metric("Profit Factor", f"{metrics.profit_factor:.2f}")
        with col3:
            st.metric("Expectancy", f"${metrics.expectancy:.2f}")
        with col4:
            st.metric("Avg Win/Loss", f"{metrics.avg_win_loss_ratio:.2f}")
        
        # Win/Loss distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("P&L Distribution")
            pnl_data = pd.to_numeric(self.df['pnl'], errors='coerce').dropna()
            
            fig = px.histogram(
                x=pnl_data,
                nbins=30,
                title="Trade P&L Distribution",
                labels={'x': 'P&L ($)', 'y': 'Frequency'}
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Breakeven")
            st.plotly_chart(fig, use_container_width=True, key="pnl_distribution")
        
        with col2:
            st.subheader("Win/Loss Summary")
            
            summary_data = {
                'Metric': ['Winning Trades', 'Losing Trades', 'Breakeven Trades'],
                'Count': [
                    metrics.winning_trades,
                    metrics.losing_trades,
                    metrics.total_trades - metrics.winning_trades - metrics.losing_trades
                ],
                'Percentage': [
                    metrics.win_rate,
                    (metrics.losing_trades / metrics.total_trades) * 100 if metrics.total_trades > 0 else 0,
                    ((metrics.total_trades - metrics.winning_trades - metrics.losing_trades) / metrics.total_trades) * 100 if metrics.total_trades > 0 else 0
                ]
            }
            
            fig = px.pie(
                values=summary_data['Count'],
                names=summary_data['Metric'],
                title="Trade Outcome Distribution"
            )
            st.plotly_chart(fig, use_container_width=True, key="outcome_pie")
        
        # Detailed metrics table
        st.subheader("📊 Detailed Performance Metrics")
        summary_dict = self.performance_summary.get_summary_dict()
        
        for category, metrics_dict in summary_dict.items():
            with st.expander(f"📈 {category}"):
                metrics_df = pd.DataFrame([
                    {"Metric": k, "Value": v} for k, v in metrics_dict.items()
                ])
                st.dataframe(metrics_df, use_container_width=True)
    
    def _render_streak_consistency_tab(self):
        """Render streak and consistency analysis."""
        st.subheader("🔁 Streak & Consistency Analysis")
        
        metrics = self.performance_summary.calculate_all_metrics()
        
        # Streak metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Max Win Streak", metrics.max_win_streak)
        with col2:
            st.metric("Max Loss Streak", metrics.max_loss_streak)
        with col3:
            st.metric("Current Streak", f"{metrics.current_streak} ({metrics.current_streak_type})")
        with col4:
            # Calculate consistency score
            pnl_data = pd.to_numeric(self.df['pnl'], errors='coerce').dropna()
            consistency_score = (1 - (pnl_data.std() / abs(pnl_data.mean()))) * 100 if abs(pnl_data.mean()) > 0 else 0
            st.metric("Consistency Score", f"{max(0, consistency_score):.1f}%")
        
        # Streak visualization
        st.subheader("📈 Streak Pattern Analysis")
        
        # Create streak chart
        if 'cumulative_pnl' in self.df.columns:
            fig = go.Figure()
            
            # Color trades by win/loss
            colors = ['green' if pnl > 0 else 'red' for pnl in self.df['pnl']]
            
            fig.add_trace(go.Scatter(
                x=list(range(len(self.df))),
                y=self.df['cumulative_pnl'],
                mode='lines+markers',
                marker=dict(color=colors, size=6),
                line=dict(color='blue', width=1),
                name='Cumulative P&L',
                hovertemplate='<b>Trade #%{x}</b><br>' +
                             'Cumulative P&L: $%{y:,.2f}<br>' +
                             'Trade P&L: $%{customdata:,.2f}<br>' +
                             '<extra></extra>',
                customdata=self.df['pnl']
            ))
            
            fig.update_layout(
                title="Trade Sequence with Win/Loss Indicators",
                xaxis_title="Trade Number",
                yaxis_title="Cumulative P&L ($)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True, key="streak_sequence")
        
        # Rolling statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Rolling Win Rate (20 trades)")
            if len(self.df) >= 20:
                rolling_wins = self.df['is_winner'].rolling(window=20).mean() * 100
                
                fig = px.line(
                    x=list(range(len(rolling_wins))),
                    y=rolling_wins,
                    title="Rolling Win Rate (20-trade window)",
                    labels={'x': 'Trade Number', 'y': 'Win Rate (%)'}
                )
                fig.add_hline(y=50, line_dash="dash", annotation_text="50% Win Rate")
                st.plotly_chart(fig, use_container_width=True, key="rolling_winrate")
            else:
                st.info("Need at least 20 trades for rolling statistics")
        
        with col2:
            st.subheader("📈 Rolling Average P&L")
            if len(self.df) >= 10:
                rolling_pnl = pd.to_numeric(self.df['pnl'], errors='coerce').rolling(window=10).mean()
                
                fig = px.line(
                    x=list(range(len(rolling_pnl))),
                    y=rolling_pnl,
                    title="Rolling Average P&L (10-trade window)",
                    labels={'x': 'Trade Number', 'y': 'Average P&L ($)'}
                )
                fig.add_hline(y=0, line_dash="dash", annotation_text="Breakeven")
                st.plotly_chart(fig, use_container_width=True, key="rolling_pnl")
            else:
                st.info("Need at least 10 trades for rolling statistics")
    
    def _render_time_analysis_tab(self):
        """Render time-based analysis."""
        st.subheader("⏱ Holding Time & Duration Analysis")
        
        # Duration metrics
        if 'duration_hours' in self.df.columns:
            duration_data = pd.to_numeric(self.df['duration_hours'], errors='coerce').dropna()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg Duration", f"{duration_data.mean():.2f} hrs")
            with col2:
                st.metric("Median Duration", f"{duration_data.median():.2f} hrs")
            with col3:
                st.metric("Min Duration", f"{duration_data.min():.2f} hrs")
            with col4:
                st.metric("Max Duration", f"{duration_data.max():.2f} hrs")
            
            # Duration distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Duration Distribution")
                fig = px.histogram(
                    x=duration_data,
                    nbins=20,
                    title="Trade Duration Distribution",
                    labels={'x': 'Duration (hours)', 'y': 'Frequency'}
                )
                st.plotly_chart(fig, use_container_width=True, key="duration_dist")
            
            with col2:
                st.subheader("💰 Profit by Duration")
                # Create duration bins for analysis
                duration_bins = pd.cut(duration_data, bins=5, labels=['Very Short', 'Short', 'Medium', 'Long', 'Very Long'])
                
                duration_profit = self.df.groupby(duration_bins)['pnl'].agg(['mean', 'count']).round(2)
                duration_profit.columns = ['Avg P&L', 'Trade Count']
                
                fig = px.bar(
                    x=duration_profit.index,
                    y=duration_profit['Avg P&L'],
                    title="Average P&L by Duration Category",
                    labels={'x': 'Duration Category', 'y': 'Average P&L ($)'}
                )
                st.plotly_chart(fig, use_container_width=True, key="duration_profit")
        
        # Time of day analysis
        if 'entry_time' in self.df.columns:
            st.subheader("🕐 Trading Time Analysis")
            
            try:
                entry_times = pd.to_datetime(self.df['entry_time'])
                self.df['entry_hour'] = entry_times.dt.hour
                self.df['entry_day'] = entry_times.dt.day_name()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Hour of day performance
                    hourly_stats = self.df.groupby('entry_hour').agg({
                        'pnl': ['count', 'mean', 'sum']
                    }).round(2)
                    
                    hourly_stats.columns = ['Trade Count', 'Avg P&L', 'Total P&L']
                    
                    fig = px.bar(
                        x=hourly_stats.index,
                        y=hourly_stats['Total P&L'],
                        title="Total P&L by Hour of Day",
                        labels={'x': 'Hour of Day', 'y': 'Total P&L ($)'}
                    )
                    st.plotly_chart(fig, use_container_width=True, key="hourly_pnl")
                
                with col2:
                    # Day of week performance
                    daily_stats = self.df.groupby('entry_day').agg({
                        'pnl': ['count', 'mean', 'sum']
                    }).round(2)
                    
                    daily_stats.columns = ['Trade Count', 'Avg P&L', 'Total P&L']
                    
                    fig = px.bar(
                        x=daily_stats.index,
                        y=daily_stats['Total P&L'],
                        title="Total P&L by Day of Week",
                        labels={'x': 'Day of Week', 'y': 'Total P&L ($)'}
                    )
                    st.plotly_chart(fig, use_container_width=True, key="daily_pnl")
            
            except Exception as e:
                st.error(f"Error analyzing time data: {str(e)}")
    
    def _render_frequency_session_tab(self):
        """Render trading frequency and session analysis."""
        st.subheader("📊 Trading Frequency & Session Performance")
        
        if 'entry_time' in self.df.columns:
            try:
                entry_times = pd.to_datetime(self.df['entry_time'])
                self.df['entry_date'] = entry_times.dt.date
                
                # Daily trading frequency
                daily_trades = self.df.groupby('entry_date').agg({
                    'pnl': ['count', 'sum', 'mean']
                }).round(2)
                
                daily_trades.columns = ['Trade Count', 'Total P&L', 'Avg P&L']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📅 Daily Trade Count")
                    fig = px.bar(
                        x=daily_trades.index,
                        y=daily_trades['Trade Count'],
                        title="Number of Trades per Day"
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True, key="daily_count")
                
                with col2:
                    st.subheader("💰 Daily P&L")
                    fig = px.bar(
                        x=daily_trades.index,
                        y=daily_trades['Total P&L'],
                        title="Daily P&L Performance",
                        color=daily_trades['Total P&L'],
                        color_continuous_scale=['red', 'yellow', 'green']
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True, key="daily_pnl_freq")
                
                # Trading frequency heatmap
                st.subheader("🔥 Trading Activity Heatmap")
                
                # Create hour and day columns
                self.df['hour'] = pd.to_datetime(self.df['entry_time']).dt.hour
                self.df['day'] = pd.to_datetime(self.df['entry_time']).dt.day_name()
                
                # Create heatmap data
                heatmap_data = self.df.groupby(['day', 'hour']).size().reset_index(name='trade_count')
                
                if not heatmap_data.empty:
                    heatmap_pivot = heatmap_data.pivot(index='day', columns='hour', values='trade_count').fillna(0)
                    
                    fig = px.imshow(
                        heatmap_pivot,
                        title="Trading Activity Heatmap (Trades per Hour/Day)",
                        labels=dict(x="Hour of Day", y="Day of Week", color="Trade Count"),
                        aspect="auto"
                    )
                    st.plotly_chart(fig, use_container_width=True, key="activity_heatmap")
            
            except Exception as e:
                st.error(f"Error analyzing frequency data: {str(e)}")
        else:
            st.info("Entry time data not available for frequency analysis")
    
    def _render_behavioral_insights_tab(self):
        """Render behavioral analysis and insights."""
        st.subheader("⚠️ Behavioral Insights & Trading Psychology")
        
        # Execution type analysis
        tag_analysis = analyze_trade_tags(self.df)
        
        if 'execution_type' in tag_analysis:
            st.subheader("🤖 Manual vs Auto Execution")
            
            exec_data = tag_analysis['execution_type']
            exec_summary = []
            
            for exec_type in exec_data.index:
                row_data = exec_data.loc[exec_type]
                exec_summary.append({
                    'Execution Type': exec_type.title(),
                    'Total Trades': int(row_data[('is_winner', 'count')]),
                    'Winning Trades': int(row_data[('is_winner', 'sum')]),
                    'Win Rate (%)': round(row_data[('is_winner', 'mean')] * 100, 2),
                    'Avg Return (%)': round(row_data[('return_percentage', 'mean')], 2),
                    'Total P&L ($)': round(row_data[('pnl', 'sum')], 2)
                })
            
            exec_df = pd.DataFrame(exec_summary)
            st.dataframe(exec_df, use_container_width=True)
            
            # Visualization
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    exec_df, 
                    x='Execution Type', 
                    y='Win Rate (%)',
                    title="Win Rate by Execution Type"
                )
                st.plotly_chart(fig, use_container_width=True, key="exec_winrate")
            
            with col2:
                fig = px.bar(
                    exec_df, 
                    x='Execution Type', 
                    y='Total P&L ($)',
                    title="Total P&L by Execution Type",
                    color='Total P&L ($)',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                st.plotly_chart(fig, use_container_width=True, key="exec_pnl")
        
        # Confidence score analysis
        if 'confidence_score' in tag_analysis:
            st.subheader("🎯 Confidence vs Performance")
            
            conf_data = tag_analysis['confidence_score']
            conf_summary = []
            
            for score in conf_data.index:
                if pd.notna(score):
                    row_data = conf_data.loc[score]
                    conf_summary.append({
                        'Confidence Score': int(score),
                        'Total Trades': int(row_data[('is_winner', 'count')]),
                        'Win Rate (%)': round(row_data[('is_winner', 'mean')] * 100, 2),
                        'Avg Return (%)': round(row_data[('return_percentage', 'mean')], 2),
                        'Total P&L ($)': round(row_data[('pnl', 'sum')], 2)
                    })
            
            if conf_summary:
                conf_df = pd.DataFrame(conf_summary)
                st.dataframe(conf_df, use_container_width=True)
                
                # Scatter plot: Confidence vs Performance
                fig = px.scatter(
                    conf_df,
                    x='Confidence Score',
                    y='Win Rate (%)',
                    size='Total Trades',
                    color='Avg Return (%)',
                    title="Confidence Score vs Win Rate",
                    hover_data=['Total P&L ($)']
                )
                st.plotly_chart(fig, use_container_width=True, key="confidence_scatter")
        
        # Strategy analysis
        if 'strategy_tag' in tag_analysis:
            st.subheader("📈 Strategy Performance Analysis")
            
            strategy_data = tag_analysis['strategy_tag']
            strategy_summary = []
            
            for strategy in strategy_data.index:
                if pd.notna(strategy):
                    row_data = strategy_data.loc[strategy]
                    strategy_summary.append({
                        'Strategy': strategy,
                        'Total Trades': int(row_data[('is_winner', 'count')]),
                        'Win Rate (%)': round(row_data[('is_winner', 'mean')] * 100, 2),
                        'Avg Return (%)': round(row_data[('return_percentage', 'mean')], 2),
                        'Total P&L ($)': round(row_data[('pnl', 'sum')], 2)
                    })
            
            if strategy_summary:
                strategy_df = pd.DataFrame(strategy_summary)
                st.dataframe(strategy_df, use_container_width=True)
        
        # Behavioral insights and recommendations
        st.subheader("🧠 Behavioral Insights & Recommendations")
        
        insights = []
        
        # Analyze impulse trading patterns
        if 'execution_type' in self.df.columns:
            manual_trades = self.df[self.df['execution_type'] == 'manual']
            auto_trades = self.df[self.df['execution_type'] == 'auto']
            
            if len(manual_trades) > 0 and len(auto_trades) > 0:
                manual_winrate = (manual_trades['pnl'] > 0).mean() * 100
                auto_winrate = (auto_trades['pnl'] > 0).mean() * 100
                
                if manual_winrate < auto_winrate - 5:
                    insights.append("⚠️ **Manual trades underperforming**: Consider sticking to automated rules")
                elif manual_winrate > auto_winrate + 5:
                    insights.append("✅ **Manual discretion adding value**: Your intuition is helping performance")
        
        # Analyze overconfidence
        if 'confidence_score' in self.df.columns and self.df['confidence_score'].notna().any():
            high_conf_trades = self.df[self.df['confidence_score'] >= 8]
            low_conf_trades = self.df[self.df['confidence_score'] <= 5]
            
            if len(high_conf_trades) > 0 and len(low_conf_trades) > 0:
                high_conf_winrate = (high_conf_trades['pnl'] > 0).mean() * 100
                low_conf_winrate = (low_conf_trades['pnl'] > 0).mean() * 100
                
                if high_conf_winrate < low_conf_winrate:
                    insights.append("🚨 **Overconfidence bias detected**: High confidence trades performing worse")
        
        # Display insights
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.info("No specific behavioral patterns detected. Keep monitoring your trading psychology!")
