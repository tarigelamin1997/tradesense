import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

class RealTimeRiskDashboard:
    """Real-time risk monitoring and alerting dashboard."""

    def __init__(self):
        self.risk_limits = {
            'max_portfolio_risk': 0.05,  # 5% max portfolio risk
            'max_correlation_exposure': 0.3,  # 30% max to correlated positions
            'max_daily_loss': 0.02,  # 2% max daily loss
            'max_position_size': 0.1,  # 10% max single position
        }

    def render_risk_dashboard(self, df: pd.DataFrame, portfolio_value: float = 100000):
        """Render comprehensive risk dashboard."""

        st.subheader("🛡️ Real-Time Risk Monitor")

        if df.empty:
            st.warning("No trade data available for risk analysis")
            return

        # Calculate current risk metrics
        risk_metrics = self._calculate_risk_metrics(df, portfolio_value)

        # Risk alerts at the top
        self._render_risk_alerts(risk_metrics)

        # Risk metrics overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            self._render_risk_gauge("Portfolio Risk", 
                                  risk_metrics['portfolio_risk'], 
                                  self.risk_limits['max_portfolio_risk'])

        with col2:
            self._render_risk_gauge("Daily P&L", 
                                  risk_metrics['daily_pnl_pct'], 
                                  self.risk_limits['max_daily_loss'],
                                  is_loss_metric=True)

        with col3:
            self._render_risk_gauge("Position Concentration", 
                                  risk_metrics['max_position_pct'], 
                                  self.risk_limits['max_position_size'])

        with col4:
            drawdown_pct = abs(risk_metrics['current_drawdown']) / portfolio_value * 100
            self._render_risk_gauge("Current Drawdown", 
                                  drawdown_pct, 
                                  5.0,  # 5% max drawdown threshold
                                  is_loss_metric=True)

        # Detailed risk analysis tabs
        risk_tabs = st.tabs(["📊 Exposure Analysis", "⚡ Volatility Risk", "🔗 Correlation Risk", "📈 VaR Analysis"])

        with risk_tabs[0]:
            self._render_exposure_analysis(df, risk_metrics)

        with risk_tabs[1]:
            self._render_volatility_analysis(df, risk_metrics)

        with risk_tabs[2]:
            self._render_correlation_analysis(df, risk_metrics)

        with risk_tabs[3]:
            self._render_var_analysis(df, risk_metrics, portfolio_value)

    def _calculate_risk_metrics(self, df: pd.DataFrame, portfolio_value: float) -> dict:
        """Calculate comprehensive risk metrics."""

        # Ensure numeric PnL
        df['pnl_numeric'] = pd.to_numeric(df['pnl'], errors='coerce')
        df = df.dropna(subset=['pnl_numeric'])

        if df.empty:
            return self._empty_risk_metrics()

        # Position sizing metrics
        if 'qty' in df.columns and 'entry_price' in df.columns:
            df['position_value'] = pd.to_numeric(df['qty'], errors='coerce') * pd.to_numeric(df['entry_price'], errors='coerce')
            df['position_pct'] = df['position_value'] / portfolio_value
        else:
            df['position_pct'] = 0.01  # Default 1%

        # Current portfolio risk
        current_positions = df[df['exit_time'].isna()] if 'exit_time' in df.columns else df.tail(10)
        portfolio_risk = current_positions['position_pct'].sum() if not current_positions.empty else 0

        # Daily P&L
        today = datetime.now().date()
        if 'exit_time' in df.columns:
            df['exit_date'] = pd.to_datetime(df['exit_time']).dt.date
            today_trades = df[df['exit_date'] == today]
        else:
            today_trades = df.tail(10)  # Approximate

        daily_pnl = today_trades['pnl_numeric'].sum() if not today_trades.empty else 0
        daily_pnl_pct = abs(daily_pnl) / portfolio_value * 100

        # Drawdown calculation
        cumulative_pnl = df['pnl_numeric'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        current_drawdown = (running_max.iloc[-1] - cumulative_pnl.iloc[-1]) if len(cumulative_pnl) > 0 else 0

        # Volatility metrics
        returns = df['pnl_numeric'] / portfolio_value
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0

        return {
            'portfolio_risk': portfolio_risk,
            'daily_pnl': daily_pnl,
            'daily_pnl_pct': daily_pnl_pct,
            'max_position_pct': df['position_pct'].max() if 'position_pct' in df.columns else 0,
            'current_drawdown': current_drawdown,
            'volatility': volatility,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'var_95': np.percentile(returns, 5) * portfolio_value if len(returns) > 0 else 0,
            'var_99': np.percentile(returns, 1) * portfolio_value if len(returns) > 0 else 0,
            'total_trades': len(df),
            'win_rate': (df['pnl_numeric'] > 0).mean() * 100 if len(df) > 0 else 0
        }

    def _render_risk_alerts(self, risk_metrics: dict):
        """Render risk alerts based on thresholds."""
        alerts = []

        # Check each risk limit
        if risk_metrics['portfolio_risk'] > self.risk_limits['max_portfolio_risk']:
            alerts.append(f"🚨 Portfolio risk ({risk_metrics['portfolio_risk']:.1%}) exceeds limit ({self.risk_limits['max_portfolio_risk']:.1%})")

        if risk_metrics['daily_pnl_pct'] > self.risk_limits['max_daily_loss']:
            alerts.append(f"🚨 Daily loss ({risk_metrics['daily_pnl_pct']:.1f}%) exceeds limit ({self.risk_limits['max_daily_loss']:.1%})")

        if risk_metrics['max_position_pct'] > self.risk_limits['max_position_size']:
            alerts.append(f"⚠️ Position size ({risk_metrics['max_position_pct']:.1%}) exceeds limit ({self.risk_limits['max_position_size']:.1%})")

        # Display alerts
        if alerts:
            for alert in alerts:
                st.error(alert)
        else:
            st.success("✅ All risk metrics within acceptable limits")

    def _render_risk_gauge(self, title: str, value: float, threshold: float, is_loss_metric: bool = False):
        """Render risk gauge with color coding."""

        # Determine color based on risk level
        if is_loss_metric:
            if value <= threshold * 0.5:
                color = "green"
            elif value <= threshold:
                color = "orange"
            else:
                color = "red"
        else:
            if value <= threshold * 0.7:
                color = "green"
            elif value <= threshold:
                color = "orange"
            else:
                color = "red"

        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = value,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title, 'font': {'size': 14}},
            delta = {'reference': threshold, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [None, max(threshold * 2, value * 1.2)]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, threshold * 0.7], 'color': "lightgray"},
                    {'range': [threshold * 0.7, threshold], 'color': "yellow"},
                    {'range': [threshold, threshold * 2], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': threshold
                }
            }
        ))

        fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    def _render_var_analysis(self, df: pd.DataFrame, risk_metrics: dict, portfolio_value: float):
        """Render Value at Risk analysis."""
        st.subheader("📈 Value at Risk (VaR) Analysis")

        if len(df) < 10:
            st.warning("Insufficient data for VaR analysis (need at least 10 trades)")
            return

        # Calculate returns
        returns = pd.to_numeric(df['pnl'], errors='coerce') / portfolio_value
        returns = returns.dropna()

        # VaR calculations
        var_95 = np.percentile(returns, 5) * portfolio_value
        var_99 = np.percentile(returns, 1) * portfolio_value
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * portfolio_value

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("VaR (95%)", f"${var_95:,.2f}", help="Maximum expected loss over 1 day with 95% confidence")

        with col2:
            st.metric("VaR (99%)", f"${var_99:,.2f}", help="Maximum expected loss over 1 day with 99% confidence")

        with col3:
            st.metric("CVaR (95%)", f"${cvar_95:,.2f}", help="Expected loss if VaR threshold is exceeded")

        # Returns distribution chart
        fig = px.histogram(x=returns * portfolio_value, nbins=20, 
                          title="P&L Distribution with VaR Thresholds")

        # Add VaR lines
        fig.add_vline(x=var_95, line_dash="dash", line_color="orange", 
                     annotation_text="VaR 95%")
        fig.add_vline(x=var_99, line_dash="dash", line_color="red", 
                     annotation_text="VaR 99%")

        fig.update_layout(xaxis_title="Daily P&L ($)", yaxis_title="Frequency")
        st.plotly_chart(fig, use_container_width=True)

    def _empty_risk_metrics(self):
        """Return empty risk metrics when no data available."""
        return {
            'portfolio_risk': 0,
            'daily_pnl': 0,
            'daily_pnl_pct': 0,
            'max_position_pct': 0,
            'current_drawdown': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'var_95': 0,
            'var_99': 0,
            'total_trades': 0,
            'win_rate': 0
        }
class RiskDashboard:
    """Advanced risk management dashboard with hedge fund level analytics."""

    def __init__(self):
        self.risk_metrics = {}
        self.alert_thresholds = {
            'max_drawdown': 0.15,  # 15%
            'var_95': 0.05,        # 5% VaR
            'sharpe_ratio': 1.0,   # Minimum Sharpe
            'win_rate': 0.45       # Minimum win rate
        }

    def render_risk_analysis(self, trades_df):
        """Render hedge fund level risk analysis."""
        if trades_df.empty:
            st.warning("No trade data available for risk analysis.")
            return

        st.markdown("### 🎯 **Advanced Risk Intelligence**")

        # Risk overview cards
        self._render_risk_overview_cards(trades_df)

        # Core risk metrics
        self._render_core_risk_metrics(trades_df)

        # Advanced risk charts
        self._render_advanced_risk_charts(trades_df)

        # Risk alerts and recommendations
        self._render_risk_alerts(trades_df)

        # Portfolio stress testing
        self._render_stress_testing(trades_df)

    def _render_risk_overview_cards(self, trades_df):
        """Render executive risk overview cards."""
        col1, col2, col3, col4 = st.columns(4)

        # Calculate key metrics
        returns = trades_df['pnl']
        max_dd = self._calculate_max_drawdown(returns)
        var_95 = self._calculate_var(returns, 0.95)
        sharpe = self._calculate_sharpe_ratio(returns)
        win_rate = (returns > 0).mean()

        with col1:
            dd_color = "#ff4444" if max_dd > self.alert_thresholds['max_drawdown'] else "#00ff88"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {dd_color} 0%, {dd_color}80 100%); 
                        padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                <h3 style="margin: 0;">{max_dd:.1%}</h3>
                <p style="margin: 0;">Max Drawdown</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            var_color = "#ff4444" if var_95 > self.alert_thresholds['var_95'] else "#00ff88"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {var_color} 0%, {var_color}80 100%); 
                        padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                <h3 style="margin: 0;">{var_95:.1%}</h3>
                <p style="margin: 0;">VaR (95%)</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            sharpe_color = "#ff4444" if sharpe < self.alert_thresholds['sharpe_ratio'] else "#00ff88"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {sharpe_color} 0%, {sharpe_color}80 100%); 
                        padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                <h3 style="margin: 0;">{sharpe:.2f}</h3>
                <p style="margin: 0;">Sharpe Ratio</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            wr_color = "#ff4444" if win_rate < self.alert_thresholds['win_rate'] else "#00ff88"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {wr_color} 0%, {wr_color}80 100%); 
                        padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                <h3 style="margin: 0;">{win_rate:.1%}</h3>
                <p style="margin: 0;">Win Rate</p>
            </div>
            """, unsafe_allow_html=True)

    def _calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown."""
        cumulative = (1 + returns / abs(returns.sum()) if returns.sum() != 0 else returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min())

    def _calculate_var(self, returns, confidence):
        """Calculate Value at Risk."""
        return abs(returns.quantile(1 - confidence))

    def _calculate_sharpe_ratio(self, returns):
        """Calculate Sharpe ratio."""
        if returns.std() == 0:
            return 0
        return returns.mean() / returns.std() * np.sqrt(252)  # Annualized

    def _render_core_risk_metrics(self, trades_df):
        """Render detailed risk metrics table."""
        st.markdown("### 📊 **Risk Metrics Analysis**")

        returns = trades_df['pnl']

        metrics = {
            'Total P&L': f"${returns.sum():.2f}",
            'Average Return': f"${returns.mean():.2f}",
            'Volatility': f"${returns.std():.2f}",
            'Skewness': f"{returns.skew():.3f}",
            'Kurtosis': f"{returns.kurtosis():.3f}",
            'Best Trade': f"${returns.max():.2f}",
            'Worst Trade': f"${returns.min():.2f}",
            'Profit Factor': f"{abs(returns[returns > 0].sum() / returns[returns < 0].sum()):.2f}" if returns[returns < 0].sum() != 0 else "∞",
            'Calmar Ratio': f"{returns.mean() / self._calculate_max_drawdown(returns):.2f}" if self._calculate_max_drawdown(returns) != 0 else "∞",
            'Sortino Ratio': f"{returns.mean() / returns[returns < 0].std():.2f}" if returns[returns < 0].std() != 0 else "∞"
        }

        # Create metrics table with styling
        metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])

        st.dataframe(
            metrics_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Metric": st.column_config.TextColumn("Risk Metric"),
                "Value": st.column_config.TextColumn("Value")
            }
        )

    def _render_advanced_risk_charts(self, trades_df):
        """Render advanced risk visualization charts."""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 **Drawdown Analysis**")
            returns = trades_df['pnl']
            cumulative = (1 + returns / abs(returns.sum()) if returns.sum() != 0 else returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max

            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=list(range(len(drawdown))),
                y=drawdown,
                fill='tozeroy',
                name='Drawdown',
                line=dict(color='red', width=2)
            ))
            fig_dd.update_layout(
                title="Portfolio Drawdown Over Time",
                xaxis_title="Trade Number",
                yaxis_title="Drawdown (%)",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig_dd, use_container_width=True)

        with col2:
            st.markdown("### 📊 **Return Distribution**")
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=trades_df['pnl'],
                nbinsx=30,
                name='Returns',
                marker_color='rgba(0, 255, 136, 0.7)'
            ))
            fig_hist.update_layout(
                title="Return Distribution Analysis",
                xaxis_title="P&L ($)",
                yaxis_title="Frequency",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    def _render_risk_alerts(self, trades_df):
        """Generate and display risk alerts."""
        st.markdown("### 🚨 **Risk Alerts & Recommendations**")

        returns = trades_df['pnl']
        alerts = []

        # Check thresholds
        max_dd = self._calculate_max_drawdown(returns)
        if max_dd > self.alert_thresholds['max_drawdown']:
            alerts.append(f"⚠️ **High Drawdown Risk**: Current max drawdown ({max_dd:.1%}) exceeds threshold ({self.alert_thresholds['max_drawdown']:.1%})")

        var_95 = self._calculate_var(returns, 0.95)
        if var_95 > self.alert_thresholds['var_95']:
            alerts.append(f"⚠️ **VaR Risk**: 95% VaR ({var_95:.1%}) indicates high tail risk")

        win_rate = (returns > 0).mean()
        if win_rate < self.alert_thresholds['win_rate']:
            alerts.append(f"⚠️ **Low Win Rate**: Current win rate ({win_rate:.1%}) below recommended threshold")

        if alerts:
            for alert in alerts:
                st.warning(alert)
        else:
            st.success("✅ **All Risk Metrics Within Acceptable Ranges**")

        # Recommendations
        st.markdown("### 💡 **Risk Management Recommendations**")

        recommendations = []

        if max_dd > 0.10:
            recommendations.append("Consider reducing position sizes to limit drawdown")

        if returns.std() > returns.mean() * 2:
            recommendations.append("High volatility detected - consider implementing stop losses")

        if (returns < 0).sum() > len(returns) * 0.6:
            recommendations.append("Review trading strategy - high loss frequency detected")

        if not recommendations:
            recommendations.append("Risk profile appears healthy - continue current approach")

        for rec in recommendations:
            st.info(f"💡 {rec}")

    def _render_stress_testing(self, trades_df):
        """Render portfolio stress testing scenarios."""
        st.markdown("### 🧪 **Stress Testing Scenarios**")

        returns = trades_df['pnl']

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Market Shock Scenarios**")

            # Simulate different market conditions
            base_return = returns.mean()
            scenarios = {
                'Normal Market': base_return,
                'Bear Market (-30%)': base_return * 0.7,
                'Market Crash (-50%)': base_return * 0.5,
                'Volatility Spike': base_return * 0.8
            }

            scenario_df = pd.DataFrame(list(scenarios.items()), columns=['Scenario', 'Expected Return'])
            scenario_df['Expected Return'] = scenario_df['Expected Return'].apply(lambda x: f"${x:.2f}")

            st.dataframe(scenario_df, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("**Risk Scenario Analysis**")

            # Portfolio composition analysis
            if 'symbol' in trades_df.columns:
                symbol_exposure = trades_df.groupby('symbol')['pnl'].sum().abs()
                total_exposure = symbol_exposure.sum()
                concentration_risk = (symbol_exposure / total_exposure).max() if total_exposure > 0 else 0

                st.metric("Max Symbol Concentration", f"{concentration_risk:.1%}")

                if concentration_risk > 0.3:
                    st.warning("⚠️ High concentration risk detected")
                else:
                    st.success("✅ Diversification appears adequate")