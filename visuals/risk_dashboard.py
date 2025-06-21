
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
