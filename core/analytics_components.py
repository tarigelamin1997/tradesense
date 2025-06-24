import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import logging

try:
    from toast_system import success_toast, error_toast, info_toast
except ImportError:
    def success_toast(message, duration=3000):
        import streamlit as st
        st.success(message)

    def error_toast(message, duration=5000):
        import streamlit as st
        st.error(message)

    def info_toast(message, duration=3000):
        import streamlit as st
        st.info(message)

logger = logging.getLogger(__name__)

# Beautiful Tableau-Inspired Styling
TABLEAU_CSS = """
<style>
/* Import beautiful fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global styling */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Beautiful gradient backgrounds */
.main-dashboard {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    padding: 2.5rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.2);
}

.dashboard-header {
    text-align: center;
    color: white;
    margin-bottom: 2rem;
}

.dashboard-title {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 0 4px 20px rgba(0,0,0,0.2);
    background: linear-gradient(45deg, #fff, #f0f8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.dashboard-subtitle {
    font-size: 1.3rem;
    opacity: 0.95;
    font-weight: 400;
    letter-spacing: 0.5px;
}

/* Beautiful metric cards */
.metric-card {
    background: rgba(255,255,255,0.98);
    padding: 2rem 1.5rem;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.3);
    margin-bottom: 1.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.metric-card:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #4facfe, #00f2fe);
}

.metric-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.12);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    line-height: 1.2;
}

.metric-label {
    font-size: 0.9rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin-bottom: 0.5rem;
}

.metric-change {
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 0.5rem;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    display: inline-block;
}

.positive { 
    color: #059669; 
    background: rgba(5, 150, 105, 0.1);
}
.negative { 
    color: #dc2626; 
    background: rgba(220, 38, 38, 0.1);
}
.neutral { 
    color: #6b7280; 
    background: rgba(107, 114, 128, 0.1);
}

/* Chart containers */
.chart-container {
    background: rgba(255,255,255,0.98);
    padding: 2rem;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    margin-bottom: 2rem;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.3);
}

.chart-title {
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    color: #1f2937;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    margin: 3rem 0 2rem 0;
    padding: 1.5rem;
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.2);
}

.section-icon {
    font-size: 2rem;
    margin-right: 1rem;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.section-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: white;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Performance indicators */
.performance-indicator {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 1rem;
    border-radius: 25px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-left: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.indicator-excellent { 
    background: linear-gradient(135deg, #10b981, #059669); 
    color: white; 
}
.indicator-good { 
    background: linear-gradient(135deg, #3b82f6, #1d4ed8); 
    color: white; 
}
.indicator-warning { 
    background: linear-gradient(135deg, #f59e0b, #d97706); 
    color: white; 
}
.indicator-poor { 
    background: linear-gradient(135deg, #ef4444, #dc2626); 
    color: white; 
}

/* Loading states */
.loading-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 4rem;
    background: rgba(255,255,255,0.1);
    border-radius: 16px;
    backdrop-filter: blur(20px);
}

.loading-spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(255,255,255,0.3);
    border-top: 4px solid #4facfe;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.1);
    padding: 0.5rem;
    border-radius: 12px;
    backdrop-filter: blur(20px);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    padding: 0.75rem 1.5rem;
    transition: all 0.3s ease;
}

.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    color: white;
    margin: 2rem 0;
}

.empty-state-icon {
    font-size: 5rem;
    margin-bottom: 2rem;
    filter: drop-shadow(0 4px 20px rgba(0,0,0,0.2));
}

.empty-state-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.empty-state-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 2rem;
    font-weight: 400;
}

.empty-state-features {
    background: rgba(255,255,255,0.15);
    padding: 1.5rem;
    border-radius: 12px;
    backdrop-filter: blur(10px);
    margin-top: 2rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .dashboard-title { font-size: 2.5rem; }
    .metric-card { padding: 1.5rem 1rem; }
    .metric-value { font-size: 2rem; }
    .chart-container { padding: 1.5rem; }
    .section-header { padding: 1rem; }
    .section-title { font-size: 1.5rem; }
}
</style>
"""

def render_analytics():
    """Render beautiful Tableau-inspired analytics dashboard."""
    # Inject beautiful CSS
    st.markdown(TABLEAU_CSS, unsafe_allow_html=True)

    # Check for data
    if 'trade_data' not in st.session_state or st.session_state.trade_data is None:
        render_beautiful_empty_state()
        return None

    data = st.session_state.trade_data

    try:
        # Calculate comprehensive analytics
        stats = calculate_comprehensive_analytics(data)

        if not stats:
            st.error("❌ Unable to calculate analytics from the provided data")
            return None

        # Render beautiful dashboard
        render_beautiful_dashboard_header()
        render_executive_metrics(stats)
        render_performance_charts(data, stats)
        render_detailed_insights(data, stats)
        render_export_section(data, stats)

        return stats

    except Exception as e:
        logger.error(f"Analytics calculation error: {e}")
        st.error(f"❌ Error calculating analytics: {e}")
        return None

def render_beautiful_empty_state():
    """Render beautiful empty state inspired by Tableau."""
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <h1 class="empty-state-title">Welcome to TradeSense Analytics</h1>
        <p class="empty-state-subtitle">Transform your trading data into actionable insights with our professional-grade analytics platform</p>
        <div class="empty-state-features">
            <p style="margin: 0; font-size: 1rem; font-weight: 500;">
                📈 Advanced Performance Analysis • 🎯 Risk Assessment • 📊 Interactive Visualizations • 💡 AI-Powered Insights
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_beautiful_dashboard_header():
    """Render beautiful dashboard header."""
    st.markdown("""
    <div class="main-dashboard">
        <div class="dashboard-header">
            <div class="dashboard-title">Trading Performance Analytics</div>
            <div class="dashboard-subtitle">Professional insights for data-driven trading decisions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_executive_metrics(stats):
    """Render executive-level metrics with beautiful cards."""
    st.markdown('<div class="section-header"><span class="section-icon">🎯</span><span class="section-title">Executive Dashboard</span></div>', unsafe_allow_html=True)

    # First row - Core Performance
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_pnl = stats.get('total_pnl', 0)
        pnl_class = "positive" if total_pnl > 0 else "negative" if total_pnl < 0 else "neutral"
        pnl_indicator = get_performance_indicator(total_pnl, 'pnl')

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net P&L</div>
            <div class="metric-value {pnl_class}">${total_pnl:,.2f}</div>
            <div class="metric-change {pnl_class}">
                {'📈' if total_pnl > 0 else '📉' if total_pnl < 0 else '➡️'} 
                {pnl_indicator}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        win_rate = stats.get('win_rate', 0)
        wr_class = "positive" if win_rate > 60 else "neutral" if win_rate > 40 else "negative"
        wr_indicator = get_performance_indicator(win_rate, 'win_rate')

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Win Rate</div>
            <div class="metric-value {wr_class}">{win_rate:.1f}%</div>
            <div class="metric-change {wr_class}">
                🎯 {wr_indicator}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        profit_factor = stats.get('profit_factor', 0)
        pf_display = "∞" if profit_factor == float('inf') else f"{profit_factor:.2f}"
        pf_class = "positive" if profit_factor > 1.5 else "neutral" if profit_factor > 1.0 else "negative"
        pf_indicator = get_performance_indicator(profit_factor, 'profit_factor')

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Profit Factor</div>
            <div class="metric-value {pf_class}">{pf_display}</div>
            <div class="metric-change {pf_class}">
                ⚡ {pf_indicator}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        total_trades = stats.get('total_trades', 0)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Trades</div>
            <div class="metric-value neutral">{total_trades:,}</div>
            <div class="metric-change neutral">
                📊 {get_volume_indicator(total_trades)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Second row - Advanced Metrics
    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        expectancy = stats.get('expectancy', 0)
        exp_class = "positive" if expectancy > 0 else "negative"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Expectancy</div>
            <div class="metric-value {exp_class}">${expectancy:.2f}</div>
            <div class="metric-change {exp_class}">
                💡 Per Trade Expected
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        best_trade = stats.get('best_trade', 0)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Best Trade</div>
            <div class="metric-value positive">${best_trade:,.2f}</div>
            <div class="metric-change positive">
                🏆 Peak Performance
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col7:
        avg_duration = stats.get('avg_trade_duration', 0)

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Avg Duration</div>
            <div class="metric-value neutral">{avg_duration:.1f}h</div>
            <div class="metric-change neutral">
                ⏱️ Holding Time
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col8:
        consistency = stats.get('consistency_score', 0)
        cons_class = "positive" if consistency > 70 else "neutral" if consistency > 50 else "negative"
        cons_indicator = get_performance_indicator(consistency, 'consistency')

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Consistency</div>
            <div class="metric-value {cons_class}">{consistency:.0f}/100</div>
            <div class="metric-change {cons_class}">
                🎯 {cons_indicator}
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_performance_charts(data, stats):
    """Render beautiful performance charts that actually work."""
    st.markdown('<div class="section-header"><span class="section-icon">📈</span><span class="section-title">Performance Overview</span></div>', unsafe_allow_html=True)

    # Chart tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Equity Curve", "🎯 Distribution", "📈 Performance", "🔄 Breakdown"])

    with tab1:
        render_beautiful_equity_curve(data, stats)

    with tab2:
        render_beautiful_distribution_chart(data)

    with tab3:
        render_beautiful_performance_metrics(data, stats)

    with tab4:
        render_beautiful_breakdown_analysis(data)

def render_beautiful_equity_curve(data, stats):
    """Render beautiful equity curve with guaranteed data."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">💰 Cumulative Performance Journey</div>', unsafe_allow_html=True)

    try:
        if 'pnl' in data.columns:
            # Ensure we have numeric data
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').fillna(0)

            if len(pnl_data) == 0:
                st.warning("⚠️ No valid P&L data found for equity curve")
                return

            # Calculate cumulative P&L
            cumulative_pnl = pnl_data.cumsum()
            trade_numbers = list(range(1, len(cumulative_pnl) + 1))

            # Create beautiful equity curve
            fig = go.Figure()

            # Main equity line with gradient fill
            fig.add_trace(go.Scatter(
                x=trade_numbers,
                y=cumulative_pnl,
                mode='lines',
                name='Equity Curve',
                line=dict(
                    color='#4facfe',
                    width=3,
                    shape='spline'
                ),
                fill='tonexty',
                fillcolor='rgba(79, 172, 254, 0.1)',
                hovertemplate='<b>Trade #%{x}</b><br>Cumulative P&L: $%{y:,.2f}<extra></extra>'
            ))

            # Add peak markers
            running_max = cumulative_pnl.expanding().max()
            peak_indices = []
            peak_values = []

            for i, (curr_val, max_val) in enumerate(zip(cumulative_pnl, running_max)):
                if curr_val == max_val and (i == 0 or curr_val > running_max.iloc[i-1]):
                    peak_indices.append(i + 1)
                    peak_values.append(curr_val)

            if peak_indices:
                fig.add_trace(go.Scatter(
                    x=peak_indices,
                    y=peak_values,
                    mode='markers',
                    name='New Peaks',
                    marker=dict(
                        color='#10b981',
                        size=10,
                        symbol='star',
                        line=dict(width=2, color='white')
                    ),
                    hovertemplate='<b>🏆 New Peak!</b><br>Trade #%{x}<br>P&L: $%{y:,.2f}<extra></extra>'
                ))

            # Beautiful layout
            fig.update_layout(
                title=None,
                xaxis=dict(
                    title='Trade Number',
                    gridcolor='rgba(0,0,0,0.1)',
                    showgrid=True,
                    title_font=dict(size=14, color='#374151')
                ),
                yaxis=dict(
                    title='Cumulative P&L ($)',
                    gridcolor='rgba(0,0,0,0.1)',
                    showgrid=True,
                    title_font=dict(size=14, color='#374151')
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=450,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor='rgba(255,255,255,0.8)',
                    bordercolor='rgba(0,0,0,0.1)',
                    borderwidth=1
                ),
                font=dict(family='Inter, sans-serif', size=12, color='#374151')
            )

            st.plotly_chart(fig, use_container_width=True, key="equity_curve_analytics_dashboard")

            # Add insights below the chart
            final_pnl = cumulative_pnl.iloc[-1]
            max_pnl = cumulative_pnl.max()
            min_pnl = cumulative_pnl.min()
            drawdown = max_pnl - final_pnl

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final P&L", f"${final_pnl:,.2f}")
            with col2:
                st.metric("Peak P&L", f"${max_pnl:,.2f}")
            with col3:
                st.metric("Current Drawdown", f"${drawdown:,.2f}")

        else:
            st.error("❌ P&L column not found in data")

    except Exception as e:
        logger.error(f"Error rendering equity curve: {e}")
        st.error(f"❌ Error rendering equity curve: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def render_beautiful_distribution_chart(data):
    """Render beautiful P&L distribution."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📊 Trade P&L Distribution</div>', unsafe_allow_html=True)

    try:
        if 'pnl' in data.columns:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').dropna()

            if len(pnl_data) == 0:
                st.warning("⚠️ No valid P&L data for distribution")
                return

            # Create beautiful distribution
            fig = go.Figure()

            # Histogram with beautiful colors
            fig.add_trace(go.Histogram(
                x=pnl_data,
                nbinsx=min(30, len(pnl_data)//2),
                name='Trade Distribution',
                marker=dict(
                    color='rgba(79, 172, 254, 0.7)',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='P&L Range: %{x}<br>Frequency: %{y}<extra></extra>'
            ))

            # Add statistical lines
            mean_pnl = pnl_data.mean()
            median_pnl = pnl_data.median()

            fig.add_vline(
                x=mean_pnl,
                line_dash="dash",
                line_color="#10b981",
                line_width=3,
                annotation_text=f"Mean: ${mean_pnl:.2f}",
                annotation_position="top"
            )

            fig.add_vline(
                x=median_pnl,
                line_dash="dot",
                line_color="#f59e0b",
                line_width=3,
                annotation_text=f"Median: ${median_pnl:.2f}",
                annotation_position="bottom"
            )

            fig.update_layout(
                title=None,
                xaxis_title='P&L ($)',
                yaxis_title='Frequency',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400,
                showlegend=False,
                font=dict(family='Inter, sans-serif', size=12, color='#374151')
            )

            st.plotly_chart(fig, use_container_width=True, key="pnl_distribution_analytics")

        else:
            st.error("❌ P&L column not found")

    except Exception as e:
        logger.error(f"Error rendering distribution: {e}")
        st.error(f"❌ Error rendering distribution: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def render_beautiful_performance_metrics(data, stats):
    """Render beautiful performance metrics."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">⚡ Performance Gauges</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Beautiful Win Rate Gauge
        win_rate = stats.get('win_rate', 0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=win_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Win Rate (%)"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#4facfe"},
                'steps': [
                    {'range': [0, 40], 'color': "rgba(239, 68, 68, 0.2)"},
                    {'range': [40, 60], 'color': "rgba(245, 158, 11, 0.2)"},
                    {'range': [60, 100], 'color': "rgba(16, 185, 129, 0.2)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig_gauge.update_layout(
            height=300,
            font={'color': "#374151", 'family': "Inter, sans-serif"},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_gauge, use_container_width=True, key="win_rate_gauge_main_dashboard")

    with col2:
        # Beautiful Profit Factor Gauge
        profit_factor = min(stats.get('profit_factor', 0), 5)  # Cap at 5 for display
        fig_pf = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=profit_factor,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Profit Factor"},
            delta={'reference': 1.5},
            gauge={
                'axis': {'range': [None, 5]},
                'bar': {'color': "#10b981"},
                'steps': [
                    {'range': [0, 1], 'color': "rgba(239, 68, 68, 0.2)"},
                    {'range': [1, 1.5], 'color': "rgba(245, 158, 11, 0.2)"},
                    {'range': [1.5, 5], 'color': "rgba(16, 185, 129, 0.2)"}
                ],
                'threshold': {
                    'line': {'color': "green", 'width': 4},
                    'thickness': 0.75,
                    'value': 2
                }
            }
        ))

        fig_pf.update_layout(
            height=300,
            font={'color': "#374151", 'family': "Inter, sans-serif"},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pf, use_container_width=True, key="profit_factor_gauge_main_dashboard")

    st.markdown('</div>', unsafe_allow_html=True)

def render_beautiful_breakdown_analysis(data):
    """Render beautiful breakdown analysis."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">🔍 Performance by Symbol</div>', unsafe_allow_html=True)

    try:
        if 'symbol' in data.columns and 'pnl' in data.columns:
            # Symbol performance breakdown
            symbol_performance = data.groupby('symbol').agg({
                'pnl': ['sum', 'count', 'mean']
            }).round(2)

            symbol_performance.columns = ['Total P&L', 'Trade Count', 'Avg P&L']
            symbol_performance = symbol_performance.reset_index()
            symbol_performance = symbol_performance.sort_values('Total P&L', ascending=True)

            if len(symbol_performance) == 0:
                st.warning("⚠️ No symbol data available")
                return

            # Create beautiful horizontal bar chart
            fig = go.Figure()

            colors = ['#ef4444' if x < 0 else '#10b981' for x in symbol_performance['Total P&L']]

            fig.add_trace(go.Bar(
                y=symbol_performance['symbol'],
                x=symbol_performance['Total P&L'],
                orientation='h',
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>%{y}</b><br>' +
                              'Total P&L: $%{x:,.2f}<br>' +
                              'Trade Count: %{customdata[0]}<br>' +
                              'Avg P&L: $%{customdata[1]:,.2f}<br>' +
                              '<extra></extra>',
                customdata=symbol_performance[['Trade Count', 'Avg P&L']].values
            ))

            fig.update_layout(
                title=None,
                xaxis_title='Total P&L ($)',
                yaxis_title='Symbol',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=max(400, len(symbol_performance) * 40),
                showlegend=False,
                font=dict(family='Inter, sans-serif', size=12, color='#374151')
            )

            st.plotly_chart(fig, use_container_width=True, key="symbol_performance_breakdown_chart")

        else:
            st.warning("⚠️ Symbol or P&L data not available")

    except Exception as e:
        logger.error(f"Error rendering breakdown: {e}")
        st.error(f"❌ Error rendering breakdown: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

def render_detailed_insights(data, stats):
    """Render detailed insights section."""
    st.markdown('<div class="section-header"><span class="section-icon">💡</span><span class="section-title">Trading Insights</span></div>', unsafe_allow_html=True)

    # Generate insights
    insights = generate_trading_insights(stats)

    if insights:
        for insight in insights:
            icon = insight['icon']
            title = insight['title']
            message = insight['message']
            level = insight['level']

            if level == 'success':
                st.success(f"{icon} **{title}**: {message}")
            elif level == 'warning':
                st.warning(f"{icon} **{title}**: {message}")
            elif level == 'error':
                st.error(f"{icon} **{title}**: {message}")
            else:
                st.info(f"{icon} **{title}**: {message}")
    else:
        st.info("💡 No specific insights available. Keep trading to generate more data!")

def render_export_section(data, stats):
    """Render export section."""
    st.markdown('<div class="section-header"><span class="section-icon">📤</span><span class="section-title">Export & Share</span></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export Report", type="primary", use_container_width=True):
            st.info("📊 Report export functionality coming soon!")

    with col2:
        if st.button("📊 Download Data", type="secondary", use_container_width=True):
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"tradesense_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col3:
        if st.button("📋 Copy Summary", type="secondary", use_container_width=True):
            summary = generate_summary_text(stats)
            st.code(summary, language="text")
            st.success("✅ Summary ready to copy!")

# Helper Functions
def get_performance_indicator(value, metric_type):
    """Get performance indicator based on value and type."""
    if metric_type == 'pnl':
        if value > 1000: return '<span class="performance-indicator indicator-excellent">Excellent</span>'
        elif value > 0: return '<span class="performance-indicator indicator-good">Profitable</span>'
        elif value > -500: return '<span class="performance-indicator indicator-warning">Needs Work</span>'
        else: return '<span class="performance-indicator indicator-poor">Critical</span>'

    elif metric_type == 'win_rate':
        if value > 60: return '<span class="performance-indicator indicator-excellent">Excellent</span>'
        elif value > 50: return '<span class="performance-indicator indicator-good">Good</span>'
        elif value > 40: return '<span class="performance-indicator indicator-warning">Fair</span>'
        else: return '<span class="performance-indicator indicator-poor">Poor</span>'

    elif metric_type == 'profit_factor':
        if value > 2: return '<span class="performance-indicator indicator-excellent">Excellent</span>'
        elif value > 1.5: return '<span class="performance-indicator indicator-good">Good</span>'
        elif value > 1: return '<span class="performance-indicator indicator-warning">Fair</span>'
        else: return '<span class="performance-indicator indicator-poor">Poor</span>'

    elif metric_type == 'consistency':
        if value > 80: return '<span class="performance-indicator indicator-excellent">Very Consistent</span>'
        elif value > 60: return '<span class="performance-indicator indicator-good">Consistent</span>'
        elif value > 40: return '<span class="performance-indicator indicator-warning">Inconsistent</span>'
        else: return '<span class="performance-indicator indicator-poor">Very Inconsistent</span>'

    return '<span class="performance-indicator indicator-good">Good</span>'

def get_volume_indicator(trades):
    """Get volume indicator for trade count."""
    if trades > 100: return "High Volume"
    elif trades > 50: return "Medium Volume"
    elif trades > 20: return "Low Volume"
    else: return "Very Low Volume"

def generate_trading_insights(stats):
    """Generate trading insights based on statistics."""
    insights = []

    win_rate = stats.get('win_rate', 0)
    profit_factor = stats.get('profit_factor', 0)
    total_pnl = stats.get('total_pnl', 0)

    # Win rate insights
    if win_rate > 70:
        insights.append({
            'icon': '🎯',
            'title': 'Excellent Trade Selection',
            'message': f'Your {win_rate:.1f}% win rate indicates strong market analysis skills.',
            'level': 'success'
        })
    elif win_rate < 40:
        insights.append({
            'icon': '⚠️',
            'title': 'Review Entry Strategy',
            'message': f'Win rate of {win_rate:.1f}% suggests need for better entry criteria.',
            'level': 'warning'
        })

    # Profit factor insights
    if profit_factor > 2:
        insights.append({
            'icon': '⚡',
            'title': 'Strong Risk Management',
            'message': f'Profit factor of {profit_factor:.2f} shows excellent risk control.',
            'level': 'success'
        })
    elif profit_factor < 1:
        insights.append({
            'icon': '🚨',
            'title': 'Risk Management Critical',
            'message': f'Profit factor of {profit_factor:.2f} indicates losses exceed profits.',
            'level': 'error'
        })

    # Overall performance
    if total_pnl > 0:
        insights.append({
            'icon': '📈',
            'title': 'Profitable Trading',
            'message': f'Total profit of ${total_pnl:,.2f} demonstrates positive edge.',
            'level': 'success'
        })

    return insights

def generate_summary_text(stats):
    """Generate summary text for copying."""
    return f"""
Trading Performance Summary
==========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Key Metrics:
• Total P&L: ${stats.get('total_pnl', 0):,.2f}
• Win Rate: {stats.get('win_rate', 0):.1f}%
• Profit Factor: {stats.get('profit_factor', 0):.2f}
• Total Trades: {stats.get('total_trades', 0):,}
• Expectancy: ${stats.get('expectancy', 0):.2f}
• Best Trade: ${stats.get('best_trade', 0):,.2f}
• Consistency Score: {stats.get('consistency_score', 0):.0f}/100

Powered by TradeSense Analytics
    """

def calculate_comprehensive_analytics(data):
    """Calculate comprehensive analytics with all metrics."""
    try:
        stats = {}

        # Basic metrics
        stats['total_trades'] = len(data)

        if 'pnl' in data.columns:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').fillna(0)

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
                    stats['avg_trade_duration'] = durations.mean()
            except:
                stats['avg_trade_duration'] = 0

        # Consistency score calculation
        if 'pnl' in data.columns:
            pnl_data = pd.to_numeric(data['pnl'], errors='coerce').fillna(0)
            if not pnl_data.empty and len(pnl_data) > 1:
                # Calculate consistency based on standard deviation relative to mean
                mean_pnl = pnl_data.mean()
                std_pnl = pnl_data.std()

                if abs(mean_pnl) > 0:
                    consistency_score = max(0, min(100, (1 - (std_pnl / abs(mean_pnl))) * 100))
                else:
                    consistency_score = 0

                stats['consistency_score'] = consistency_score
            else:
                stats['consistency_score'] = 0

        return stats

    except Exception as e:
        logger.error(f"Error calculating comprehensive analytics: {e}")
        return {
            'total_trades': 0,
            'total_pnl': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'expectancy': 0,
            'best_trade': 0,
            'avg_trade_duration': 0,
            'consistency_score': 0
        }

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

            st.plotly_chart(fig, use_container_width=True, key="modern_equity_curve_detailed")
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

        st.plotly_chart(fig, use_container_width=True, key="correlation_matrix_heatmap")

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
                    st.plotly_chart(fig, use_container_width=True, key="duration_histogram_unique")

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

    # PDF Export button
    try:
        from pdf_export import render_pdf_export_button
        render_pdf_export_button(df, stats)
    except ImportError:
        if st.button("📄 Export Professional Report", type="primary"):
            st.info("PDF export functionality is being set up")

    # Charts Export
    if st.button("📈 Export Charts", type="secondary"):
        st.info("Chart export functionality would be implemented here")

    # Summary Export
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
                st.plotly_chart(fig, use_container_width=True, key="duration_histogram_unique")

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
            st.plotly_chart(fig, use_container_width=True, key="pnl_histogram_distribution")

            # Equity Curve
            cumulative_pnl = trade_data['pnl'].cumsum()
            fig = px.line(x=trade_data.index, y=cumulative_pnl, title='Equity Curve')
            st.plotly_chart(fig, use_container_width=True, key="equity_line_chart_main")
from interactive_table import render_interactive_table
from notification_system import create_system_alert, NotificationType, NotificationPriority