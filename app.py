import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Dict
from st_aggrid import AgGrid, GridUpdateMode
from interactive_table import (
    compute_trade_result,
    get_grid_options,
    trade_detail,
)
from fpdf import FPDF

from data_import.futures_importer import FuturesImporter
from data_import.base_importer import REQUIRED_COLUMNS
from data_import.utils import load_trade_data
from analytics import (
    compute_basic_stats,
    performance_over_time,
    median_results,
    profit_factor_by_symbol,
    trade_duration_stats,
    max_streaks,
    rolling_metrics,
    calculate_kpis,
)
from risk_tool import assess_risk
from payment import PaymentGateway


def log_feedback(page: str, feedback: str) -> None:
    """Log user feedback to feedback.csv with timestamp and page info."""
    import os

    feedback_entry = {
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'page': page,
        'feedback': feedback.strip(),
        'session_id': st.session_state.get('session_id', 'unknown')
    }

    feedback_file = 'feedback.csv'

    try:
        # Check if file exists
        file_exists = os.path.exists(feedback_file)

        if not file_exists:
            # Create new file with headers
            feedback_df = pd.DataFrame([feedback_entry])
            feedback_df.to_csv(feedback_file, index=False)
        else:
            # Append to existing file
            feedback_df = pd.DataFrame([feedback_entry])
            feedback_df.to_csv(feedback_file, mode='a', header=False, index=False)

        return True
    except Exception as e:
        st.error(f"Failed to log feedback: {str(e)}")
        return False


def generate_pdf(stats: Dict[str, float], risk: Dict[str, float]) -> bytes:
    """Create a simple PDF report with core stats."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "TradeSense Analytics Report", ln=1)
    for k, v in stats.items():
        if k == "equity_curve":
            continue
        pdf.cell(0, 10, f"{k}: {v}", ln=1)
    for k, v in risk.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=1)
    return pdf.output(dest="S").encode("latin1")


def safe_format_number(number, format_type="number", precision=2):
    """Safely format a number for PDF reports, handling non-numeric values."""
    try:
        if format_type == "currency":
            return f"${number:,.{precision}f}"
        else:
            return f"{number:,.{precision}f}"
    except (ValueError, TypeError):
        return "N/A"


def generate_comprehensive_pdf(filtered_df: pd.DataFrame, kpis: dict, stats: dict) -> bytes:
    """Generate a comprehensive PDF report with filtered trades, KPIs, and analytics."""
    import io
    import base64
    from datetime import datetime

    pdf = FPDF()
    pdf.add_page()

    # Title and Header
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 15, "TradeSense - Comprehensive Trading Report", ln=1, align='C')

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='C')
    pdf.cell(0, 8, f"Filtered Dataset: {len(filtered_df)} trades", ln=1, align='C')
    pdf.ln(5)

    # Executive Summary Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Executive Summary", ln=1)
    pdf.set_font("Arial", "", 10)

    # Summary metrics in a clean format
    summary_data = [
        ("Total Trades", f"{kpis['total_trades']:,}"),
        ("Net P&L (After Commission)", safe_format_number(kpis['net_pnl_after_commission'], "currency", 2)),
        ("Win Rate", f"{kpis['win_rate_percent']:.1f}%"),
        ("Average R:R Ratio", f"{kpis['average_rr']:.2f}" if kpis['average_rr'] != np.inf else "∞"),
        ("Best Single Trade", safe_format_number(kpis['max_single_trade_win'], "currency", 2)),
        ("Worst Single Trade", safe_format_number(kpis['max_single_trade_loss'], "currency", 2)),
        ("Total Commission Paid", safe_format_number(kpis['total_commission'], "currency", 2))
    ]

    for label, value in summary_data:
        pdf.cell(95, 6, f"{label}:", border=0)
        pdf.cell(95, 6, value, border=0, ln=1)

    pdf.ln(5)

    # Detailed Performance Metrics
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Detailed Performance Metrics", ln=1)
    pdf.set_font("Arial", "", 10)

    performance_data = [
        ("Profit Factor", f"{stats['profit_factor']:.2f}"),
        ("Expectancy", safe_format_number(stats['expectancy'], "currency", 2)),
        ("Max Drawdown", safe_format_number(stats['max_drawdown'], "currency", 2)),
        ("Sharpe Ratio", f"{stats['sharpe_ratio']:.2f}"),
        ("Average Win", safe_format_number(stats['average_win'], "currency", 2)),
        ("Average Loss", safe_format_number(stats['average_loss'], "currency", 2)),
        ("Reward:Risk Ratio", f"{stats['reward_risk']:.2f}")
    ]

    for label, value in performance_data:
        pdf.cell(95, 6, f"{label}:", border=0)
        pdf.cell(95, 6, value, border=0, ln=1)

    pdf.ln(10)

    # Symbol Breakdown
    if not filtered_df.empty:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Performance by Symbol", ln=1)
        pdf.set_font("Arial", "", 9)

        # Group by symbol
        symbol_stats = filtered_df.groupby('symbol').agg({
            'pnl': ['count', 'sum', 'mean'],
            'direction': lambda x: (filtered_df.loc[x.index, 'pnl'] > 0).mean() * 100
        }).round(2)

        symbol_stats.columns = ['Trades', 'Total_PnL', 'Avg_PnL', 'Win_Rate']
        symbol_stats = symbol_stats.reset_index()

        # Table headers
        pdf.cell(30, 8, "Symbol", border=1, align='C')
        pdf.cell(25, 8, "Trades", border=1, align='C')
        pdf.cell(35, 8, "Total P&L", border=1, align='C')
        pdf.cell(35, 8, "Avg P&L", border=1, align='C')
        pdf.cell(30, 8, "Win Rate %", border=1, align='C', ln=1)

        # Table data
        for _, row in symbol_stats.head(10).iterrows():  # Limit to top 10 symbols
            pdf.cell(30, 6, str(row['symbol']), border=1, align='C')
            pdf.cell(25, 6, str(int(row['Trades'])), border=1, align='C')
            pdf.cell(35, 6, safe_format_number(row['Total_PnL'], "currency", 2), border=1, align='C')
            pdf.cell(35, 6, safe_format_number(row['Avg_PnL'], "currency", 2), border=1, align='C')
            pdf.cell(30, 6, f"{row['Win_Rate']:.1f}%", border=1, align='C', ln=1)

    pdf.ln(10)

    # Recent Trade Performance
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Recent Trade History (Last 10 Trades)", ln=1)
    pdf.set_font("Arial", "", 8)

    if not filtered_df.empty:
        # Prepare display columns
        recent_trades = filtered_df.tail(10).copy()
        recent_trades['pnl_formatted'] = recent_trades['pnl'].apply(lambda x: safe_format_number(x, "currency"))
        recent_trades['date_formatted'] = pd.to_datetime(recent_trades['exit_time']).dt.strftime('%Y-%m-%d')

        # Table headers for recent trades
        pdf.cell(25, 6, "Date", border=1, align='C')
        pdf.cell(20, 6, "Symbol", border=1, align='C')
        pdf.cell(18, 6, "Direction", border=1, align='C')
        pdf.cell(25, 6, "Entry", border=1, align='C')
        pdf.cell(25, 6, "Exit", border=1, align='C')
        pdf.cell(25, 6, "P&L", border=1, align='C')
        pdf.cell(20, 6, "Result", border=1, align='C', ln=1)

        # Table data for recent trades
        for _, trade in recent_trades.iterrows():
            result = "Win" if trade['pnl'] > 0 else "Loss"
            pdf.cell(25, 5, trade['date_formatted'], border=1, align='C')
            pdf.cell(20, 5, str(trade['symbol'])[:8], border=1, align='C')  # Truncate long symbols
            pdf.cell(18, 5, str(trade['direction'])[:6], border=1, align='C')
            pdf.cell(25, 5, safe_format_number(trade['entry_price'], "number", 2), border=1, align='C')
            pdf.cell(25, 5, safe_format_number(trade['exit_price'], "number", 2), border=1, align='C')
            pdf.cell(25, 5, trade['pnl_formatted'], border=1, align='C')
            pdf.cell(20, 5, result, border=1, align='C', ln=1)

    # Add new page for additional analysis
    pdf.add_page()

    # Trading Patterns Analysis
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Trading Patterns & Insights", ln=1)
    pdf.set_font("Arial", "", 10)

    if not filtered_df.empty:
        # Direction analysis
        direction_stats = filtered_df.groupby('direction').agg({
            'pnl': ['count', 'sum', lambda x: (x > 0).mean() * 100]
        }).round(2)
        direction_stats.columns = ['Trades', 'Total_PnL', 'Win_Rate']

        pdf.cell(0, 8, "Performance by Direction:", ln=1)
        for direction, row in direction_stats.iterrows():
            pdf.cell(0, 6, f"  {direction.upper()}: {int(row['Trades'])} trades, {safe_format_number(row['Total_PnL'], 'currency', 2)} P&L, {row['Win_Rate']:.1f}% win rate", ln=1)

        pdf.ln(5)

        # Monthly performance if data spans multiple months
        monthly_perf = filtered_df.copy()
        monthly_perf['month'] = pd.to_datetime(monthly_perf['exit_time']).dt.to_period('M')
        monthly_stats = monthly_perf.groupby('month')['pnl'].agg(['count', 'sum']).round(2)

        if len(monthly_stats) > 1:
            pdf.cell(0, 8, "Monthly Performance:", ln=1)
            for month, row in monthly_stats.head(6).iterrows():  # Show last 6 months
                pdf.cell(0, 6, f"  {month}: {int(row['count'])} trades, {safe_format_number(row['sum'], 'currency', 2)} P&L", ln=1)

    pdf.ln(10)

    # Risk Management Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Risk Management Summary", ln=1)
    pdf.set_font("Arial", "", 10)

    if not filtered_df.empty:
        # Calculate risk metrics
        losing_trades = filtered_df[filtered_df['pnl'] < 0]
        winning_trades = filtered_df[filtered_df['pnl'] > 0]

        risk_metrics = [
            ("Largest Loss", safe_format_number(filtered_df['pnl'].min(), "currency", 2)),
            ("Average Loss", safe_format_number(losing_trades['pnl'].mean(), "currency", 2) if not losing_trades.empty else "$0.00"),
            ("Largest Win", safe_format_number(filtered_df['pnl'].max(), "currency", 2)),
            ("Average Win", safe_format_number(winning_trades['pnl'].mean(), "currency", 2) if not winning_trades.empty else "$0.00"),
            ("Win/Loss Ratio", f"{len(winning_trades)}:{len(losing_trades)}" if not losing_trades.empty else f"{len(winning_trades)}:0")
        ]

        for label, value in risk_metrics:
            pdf.cell(95, 6, f"{label}:", border=0)
            pdf.cell(95, 6, value, border=0, ln=1)

    pdf.ln(10)

    # Footer
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Generated by TradeSense - Professional Trading Analytics Platform", ln=1, align='C')
    pdf.cell(0, 5, "This report contains confidential trading information and should be handled accordingly.", ln=1, align='C')

    return pdf.output(dest="S").encode("latin1")

st.set_page_config(page_title="TradeSense", layout="wide")

# Initialize session ID for feedback tracking
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())[:8]

# Header with feedback button
header_col1, header_col2 = st.columns([4, 1])

with header_col1:
    st.title("TradeSense")
    st.caption("Smarter Decisions. Safer Trades.")

with header_col2:
    if st.button("📝 Feedback", help="Report issues or suggest improvements"):
        st.session_state.show_feedback_modal = True

# Feedback Modal
if st.session_state.get('show_feedback_modal', False):
    with st.modal("📝 Feedback & Bug Reports"):
        st.write("**Help us improve TradeSense!**")
        st.write("Report bugs, suggest features, or share your experience.")

        # Determine current page context
        current_page = "Main"
        if st.session_state.get('current_tab'):
            current_page = st.session_state.current_tab
        elif selected_file:
            current_page = "Analytics"
        else:
            current_page = "Onboarding"

        st.info(f"Current page: {current_page}")

        feedback_text = st.text_area(
            "Your feedback:",
            placeholder="Describe the issue, suggestion, or your experience...",
            height=100
        )

        feedback_type = st.selectbox(
            "Type:",
            ["Bug Report", "Feature Request", "General Feedback", "UI/UX Issue", "Performance Issue"]
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Submit Feedback", type="primary"):
                if feedback_text.strip():
                    full_feedback = f"[{feedback_type}] {feedback_text}"
                    success = log_feedback(current_page, full_feedback)
                    if success:
                        st.success("✅ Feedback submitted! Thank you for helping us improve TradeSense.")
                        st.session_state.show_feedback_modal = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to submit feedback. Please try again.")
                else:
                    st.warning("Please enter your feedback before submitting.")

        with col2:
            if st.button("Cancel"):
                st.session_state.show_feedback_modal = False
                st.rerun()

# Onboarding message shown only on first load
if "show_tour" not in st.session_state:
    st.session_state.show_tour = True
if st.session_state.show_tour:
    with st.expander("Getting Started", expanded=True):
        st.markdown(
            "1. Upload a CSV/Excel file or use the sample data.\n"
            "2. Review performance metrics and risk stats.\n"
            "3. Filter trades and download reports."
        )
        if st.button("Got it", key="close_tour"):
            st.session_state.show_tour = False

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=1)
if theme == "Dark":
    st.markdown(
        """
        <style>
        /* Dark Theme - Global Styles */
        .stApp {
            background-color: #0e1117 !important;
            color: #fafafa !important;
        }
        .stApp *, .stApp div, .stApp span, .stApp p {
            color: #fafafa !important;
        }

        /* Headers and Titles */
        h1, h2, h3, h4, h5, h6, .stTitle, .stHeader, .stSubheader {
            color: #fafafa !important;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
            color: #fafafa !important;
        }

        /* Sidebar */
        .stSidebar {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        .stSidebar * {
            color: #fafafa !important;
        }
        .stSidebar .stSelectbox > div > div {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stSidebar .stSelectbox > div > div > div {
            color: #fafafa !important;
        }
        .stSidebar .stTextInput > div > div > input {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stSidebar .stNumberInput > div > div > input {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stSidebar .stCheckbox > label {
            color: #fafafa !important;
        }
        .stSidebar .stMultiSelect > label {
            color: #fafafa !important;
        }
        .stSidebar .stDateInput > label {
            color: #fafafa !important;
        }

        /* Form Elements */
        .stTextArea > div > div > textarea {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stSelectbox > div > div {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stTextInput > div > div > input {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stNumberInput > div > div > input {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }

        /* Labels and Text */
        label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label {
            color: #fafafa !important;
        }
        .stMarkdown, .stText {
            color: #fafafa !important;
        }
        .stCaption {
            color: #b3b3b3 !important;
        }

        /* Data and Tables */
        .stDataFrame {
            background-color: #262730 !important;
            color: #fafafa !important;
        }

        /* Metrics */
        .stMetric {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            padding: 10px !important;
            border-radius: 5px !important;
            border: 1px solid #4a4a4a !important;
        }
        .stMetric label, .stMetric div {
            color: #fafafa !important;
        }

        /* Expandable sections */
        .stExpander {
            background-color: #262730 !important;
            border: 1px solid #4a4a4a !important;
            color: #fafafa !important;
        }
        .stExpander * {
            color: #fafafa !important;
        }

        /* Buttons */
        .stButton > button {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
            border: 1px solid #4a4a4a !important;
        }
        .stButton > button:hover {
            background-color: #333333 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #262730 !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #fafafa !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #fafafa !important;
        }

        /* Charts */
        .js-plotly-plot .plotly text {
            fill: #fafafa !important;
        }

        /* Dropdown menus */
        .stSelectbox [data-baseweb="select"] {
            background-color: #1e1e1e !important;
            color: #fafafa !important;
        }
        .stSelectbox [data-baseweb="select"] > div {
            color: #fafafa !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        /* PROFESSIONAL SaaS DASHBOARD - LIGHT THEME */
        /* Inspired by Stripe, Linear, and Notion for maximum clarity and accessibility */

        /* ========== FOUNDATION STYLES ========== */
        
        /* Root Application - Pure White Background */
        .stApp {
            background-color: #ffffff !important;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        .main .block-container {
            background-color: #ffffff !important;
            padding-top: 2rem !important;
            max-width: 1200px !important;
        }

        /* ========== TYPOGRAPHY HIERARCHY ========== */
        
        /* Headers - Bold, Dark, Professional */
        h1, h2, h3, h4, h5, h6,
        [data-testid="stHeader"] h1,
        .stTitle, .stHeader, .stSubheader {
            color: #1a1a1a !important;
            font-weight: 700 !important;
            letter-spacing: -0.025em !important;
            line-height: 1.2 !important;
        }
        
        h1 {
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        h2 {
            font-size: 2rem !important;
            margin-bottom: 1rem !important;
            border-bottom: 2px solid #e5e7eb !important;
            padding-bottom: 0.5rem !important;
        }
        
        h3 {
            font-size: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }

        /* Body Text - High Contrast */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] div,
        [data-testid="stText"] div,
        .stMarkdown div,
        .stText div,
        .stMarkdown p {
            color: #1a1a1a !important;
            font-weight: 400 !important;
            line-height: 1.6 !important;
            font-size: 1rem !important;
        }

        /* Captions - Clear Hierarchy */
        [data-testid="stCaptionContainer"] p,
        .stCaption div,
        .stCaption {
            color: #4b5563 !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
        }

        /* ========== SIDEBAR - CLEAN NAVIGATION ========== */
        
        [data-testid="stSidebar"] {
            background-color: #f9fafb !important;
            border-right: 1px solid #e5e7eb !important;
            padding: 1rem !important;
        }
        
        [data-testid="stSidebar"] * {
            color: #1a1a1a !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #1a1a1a !important;
            font-weight: 700 !important;
            border-bottom: 1px solid #e5e7eb !important;
            padding-bottom: 0.5rem !important;
            margin-bottom: 1rem !important;
        }

        /* ========== FORM ELEMENTS - PROFESSIONAL INPUTS ========== */
        
        /* Input Fields */
        input[type="text"], 
        input[type="number"], 
        textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            border: 2px solid #d1d5db !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 12px 16px !important;
            font-size: 1rem !important;
            transition: all 0.2s ease !important;
        }
        
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
            outline: none !important;
        }

        /* Select Dropdowns */
        [data-baseweb="select"],
        [data-testid="stSidebar"] [data-baseweb="select"] {
            background-color: #ffffff !important;
            border: 2px solid #d1d5db !important;
            border-radius: 8px !important;
            min-height: 48px !important;
        }
        
        [data-baseweb="select"] > div {
            color: #1a1a1a !important;
            font-weight: 500 !important;
            padding: 12px 16px !important;
        }
        
        [data-baseweb="select"] svg {
            fill: #4b5563 !important;
        }

        /* Dropdown Menus */
        [data-baseweb="popover"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
        }
        
        [data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        
        [data-baseweb="menu"] li {
            background-color: #ffffff !important;
            color: #1a1a1a !important;
            font-weight: 500 !important;
            padding: 12px 16px !important;
            transition: background-color 0.15s ease !important;
        }
        
        [data-baseweb="menu"] li:hover {
            background-color: #f3f4f6 !important;
            color: #1a1a1a !important;
        }
        
        [data-baseweb="menu"] li[aria-selected="true"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Labels */
        label,
        [data-testid="stWidgetLabel"] label {
            color: #1a1a1a !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            margin-bottom: 0.5rem !important;
            display: block !important;
        }

        /* ========== BUTTONS - CLEAR CALL-TO-ACTION ========== */
        
        .stButton button,
        button {
            background-color: #ffffff !important;
            color: #374151 !important;
            border: 2px solid #d1d5db !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            font-size: 0.875rem !important;
            transition: all 0.2s ease !important;
            min-height: 48px !important;
        }
        
        .stButton button:hover,
        button:hover {
            background-color: #f9fafb !important;
            border-color: #9ca3af !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Primary Buttons */
        .stButton button[kind="primary"],
        button[data-testid*="primary"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-color: #2563eb !important;
        }
        
        .stButton button[kind="primary"]:hover {
            background-color: #1d4ed8 !important;
            border-color: #1d4ed8 !important;
            color: #ffffff !important;
        }

        /* ========== METRICS & KPI CARDS - DASHBOARD STYLE ========== */
        
        [data-testid="metric-container"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            padding: 24px !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) !important;
            transition: box-shadow 0.2s ease !important;
        }
        
        [data-testid="metric-container"]:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        }
        
        [data-testid="metric-container"] [data-testid="metric-value"] {
            color: #1a1a1a !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
            line-height: 1 !important;
        }
        
        [data-testid="metric-container"] [data-testid="metric-label"] {
            color: #6b7280 !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        
        [data-testid="metric-container"] [data-testid="metric-delta"] {
            font-weight: 600 !important;
            font-size: 0.875rem !important;
        }

        /* ========== TABS - CLEAN NAVIGATION ========== */
        
        [data-baseweb="tab-list"] {
            background-color: #f9fafb !important;
            border-bottom: 1px solid #e5e7eb !important;
            border-radius: 12px 12px 0 0 !important;
            padding: 0 8px !important;
        }
        
        [data-baseweb="tab"] {
            color: #6b7280 !important;
            font-weight: 500 !important;
            padding: 16px 24px !important;
            border-radius: 8px 8px 0 0 !important;
            transition: all 0.2s ease !important;
            margin: 8px 4px 0 4px !important;
        }
        
        [data-baseweb="tab"]:hover {
            color: #374151 !important;
            background-color: #f3f4f6 !important;
        }
        
        [data-baseweb="tab"][aria-selected="true"] {
            color: #2563eb !important;
            background-color: #ffffff !important;
            font-weight: 600 !important;
            border-bottom: 3px solid #2563eb !important;
            box-shadow: 0 -2px 4px 0 rgba(0, 0, 0, 0.05) !important;
        }

        /* ========== TABLES - DATA VISUALIZATION ========== */
        
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
        }
        
        [data-testid="stDataFrame"] table {
            border-collapse: separate !important;
            border-spacing: 0 !important;
            width: 100% !important;
        }
        
        [data-testid="stDataFrame"] th {
            background-color: #f9fafb !important;
            color: #1a1a1a !important;
            font-weight: 700 !important;
            font-size: 0.875rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            padding: 16px !important;
            border-bottom: 2px solid #e5e7eb !important;
        }
        
        [data-testid="stDataFrame"] td {
            color: #1a1a1a !important;
            font-weight: 500 !important;
            padding: 16px !important;
            border-bottom: 1px solid #f3f4f6 !important;
        }
        
        [data-testid="stDataFrame"] tr:nth-child(even) td {
            background-color: #f9fafb !important;
        }
        
        [data-testid="stDataFrame"] tr:hover td {
            background-color: #f3f4f6 !important;
        }

        /* ========== EXPANDABLE SECTIONS ========== */
        
        [data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            margin: 16px 0 !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
        }
        
        [data-testid="stExpander"] summary {
            color: #1a1a1a !important;
            font-weight: 600 !important;
            padding: 20px !important;
            background-color: #f9fafb !important;
            border-radius: 12px 12px 0 0 !important;
            cursor: pointer !important;
            transition: background-color 0.2s ease !important;
        }
        
        [data-testid="stExpander"] summary:hover {
            background-color: #f3f4f6 !important;
        }
        
        [data-testid="stExpander"] > div > div {
            padding: 20px !important;
        }

        /* ========== ALERTS & MESSAGES ========== */
        
        .stSuccess {
            background-color: #ecfdf5 !important;
            color: #065f46 !important;
            border: 1px solid #a7f3d0 !important;
            border-radius: 12px !important;
            padding: 16px !important;
            font-weight: 600 !important;
        }
        
        .stError {
            background-color: #fef2f2 !important;
            color: #991b1b !important;
            border: 1px solid #fecaca !important;
            border-radius: 12px !important;
            padding: 16px !important;
            font-weight: 600 !important;
        }
        
        .stWarning {
            background-color: #fffbeb !important;
            color: #92400e !important;
            border: 1px solid #fed7aa !important;
            border-radius: 12px !important;
            padding: 16px !important;
            font-weight: 600 !important;
        }
        
        .stInfo {
            background-color: #eff6ff !important;
            color: #1e40af !important;
            border: 1px solid #bfdbfe !important;
            border-radius: 12px !important;
            padding: 16px !important;
            font-weight: 600 !important;
        }

        /* ========== FILE UPLOADER ========== */
        
        [data-testid="stFileUploader"] section {
            background-color: #f9fafb !important;
            border: 2px dashed #d1d5db !important;
            border-radius: 12px !important;
            padding: 32px !important;
            text-align: center !important;
            transition: all 0.2s ease !important;
        }
        
        [data-testid="stFileUploader"] section:hover {
            border-color: #2563eb !important;
            background-color: #eff6ff !important;
        }
        
        [data-testid="stFileUploader"] button {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
        }

        /* ========== CHECKBOXES ========== */
        
        [data-testid="stCheckbox"] label {
            color: #1a1a1a !important;
            font-weight: 500 !important;
            cursor: pointer !important;
        }
        
        [data-testid="stCheckbox"] input[type="checkbox"] {
            accent-color: #2563eb !important;
            transform: scale(1.3) !important;
            margin-right: 8px !important;
        }

        /* ========== CHARTS - PROFESSIONAL STYLING ========== */
        
        .js-plotly-plot .plotly text {
            fill: #1a1a1a !important;
            font-weight: 500 !important;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }
        
        .js-plotly-plot .plotly .xtick text,
        .js-plotly-plot .plotly .ytick text {
            fill: #4b5563 !important;
            font-weight: 500 !important;
        }
        
        .js-plotly-plot .plotly .g-gtitle text {
            fill: #1a1a1a !important;
            font-weight: 700 !important;
            font-size: 18px !important;
        }

        /* ========== FOCUS STATES - ACCESSIBILITY ========== */
        
        button:focus,
        input:focus,
        textarea:focus,
        [data-baseweb="select"]:focus-within {
            outline: 3px solid #93c5fd !important;
            outline-offset: 2px !important;
        }

        /* ========== MOBILE RESPONSIVENESS ========== */
        
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            
            [data-testid="metric-container"] {
                padding: 16px !important;
            }
            
            .stButton button {
                padding: 16px 20px !important;
                font-size: 16px !important;
                min-height: 52px !important;
            }
            
            [data-baseweb="tab"] {
                padding: 12px 16px !important;
                font-size: 14px !important;
            }
            
            h1 {
                font-size: 2rem !important;
            }
            
            h2 {
                font-size: 1.5rem !important;
            }
        }

        /* ========== UTILITY OVERRIDES ========== */
        
        /* Ensure all text maintains proper contrast */
        .main * {
            color: #1a1a1a !important;
        }
        
        /* Sidebar text override */
        [data-testid="stSidebar"] * {
            color: #1a1a1a !important;
        }
        
        /* Header hierarchy override */
        h1, h2, h3, h4, h5, h6 {
            color: #1a1a1a !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.header("Upload Trade History")
st.sidebar.caption("We do not store or share your uploaded trade data.")

sample_file = "sample_data/futures_sample.csv"
use_sample = st.sidebar.checkbox("Use sample data", value=True)
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=['csv','xlsx','xls'])

if use_sample:
    selected_file = sample_file
elif uploaded_file is not None:
    selected_file = uploaded_file
else:
    selected_file = None

importer = FuturesImporter()

if selected_file:
    try:
        df = load_trade_data(selected_file)
    except Exception as e:
        st.error(
            "Failed to process file. Ensure it is a valid CSV or Excel file with the correct columns."
        )
        st.expander("Error details").write(str(e))
        st.stop()

    # Add tags column if it doesn't exist
    if 'tags' not in df.columns:
        df['tags'] = ''

    if importer.validate_columns(df):
        # Keep REQUIRED_COLUMNS plus tags if it exists
        columns_to_keep = REQUIRED_COLUMNS.copy()
        if 'tags' in df.columns:
            columns_to_keep.append('tags')
        df = df[[col for col in columns_to_keep if col in df.columns]]
    else:
        st.warning('Columns do not match required fields. Map them below:')
        mapping: Dict[str, str] = {}
        for col in REQUIRED_COLUMNS:
            mapping[col] = st.selectbox(f"Column for {col}", options=df.columns, key=col)
        try:
            df = importer.map_columns(df, mapping)
        except Exception as e:
            st.error(str(e))
            st.stop()

    # Parse datetimes with coercion and ISO8601 format
    df['entry_time'] = pd.to_datetime(
        df['entry_time'], errors='coerce', format='ISO8601'
    )
    df['exit_time'] = pd.to_datetime(
        df['exit_time'], errors='coerce', format='ISO8601'
    )

    if df['entry_time'].isna().any() or df['exit_time'].isna().any():
        st.warning("Some rows had invalid dates and were dropped.")
        df = df.dropna(subset=['entry_time', 'exit_time'])

    if df.empty:
        st.error("No valid rows remain after cleaning.")
        st.stop()

    # Filters above dashboard for better visibility
    st.header("📊 Trade Filters")
    st.caption("Filter your trades to analyze specific subsets of your trading data")

    # Create filter columns
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        symbols = st.multiselect(
            'Symbols', 
            options=df['symbol'].unique().tolist(), 
            default=df['symbol'].unique().tolist(),
            help="Select which symbols to include in analysis"
        )

    with filter_col2:
        directions = st.multiselect(
            'Directions', 
            options=df['direction'].unique().tolist(), 
            default=df['direction'].unique().tolist(),
            help="Filter by trade direction (long/short)"
        )

    with filter_col3:
        # Extract unique tags from the tags column (if it exists)
        all_tags = set()
        if 'tags' in df.columns:
            for tag_string in df['tags'].dropna():
                if tag_string and str(tag_string).strip():
                    tags_list = [tag.strip() for tag in str(tag_string).split(',')]
                    all_tags.update(tags_list)

        all_tags = sorted([tag for tag in all_tags if tag])  # Remove empty tags and sort

        selected_tags = st.multiselect(
            'Tags',
            options=all_tags,
            default=all_tags,
            help="Filter by trade tags (e.g., scalp, swing, breakout)"
        )

    with filter_col4:
        date_range = st.date_input(
            'Date Range',
            value=[df['entry_time'].min().date(), df['exit_time'].max().date()],
            help="Select date range for analysis"
        )

    # Apply filters
    filtered_df = df[
        df['symbol'].isin(symbols)
        & df['direction'].isin(directions)
        & (df['entry_time'].dt.date >= date_range[0])
        & (df['exit_time'].dt.date <= date_range[1])
    ]

    # Apply tag filter if tags column exists and tags are selected
    if 'tags' in df.columns and selected_tags:
        def has_selected_tag(tag_string):
            if pd.isna(tag_string) or not str(tag_string).strip():
                return False
            trade_tags = [tag.strip() for tag in str(tag_string).split(',')]
            return any(tag in selected_tags for tag in trade_tags)

        filtered_df = filtered_df[filtered_df['tags'].apply(has_selected_tag)]

    # Remove broker filter since it's not always available in manual entries
    # Keep it in sidebar for uploaded files
    if 'broker' in df.columns:
        st.sidebar.subheader("Additional Filters")
        brokers = st.sidebar.multiselect('Broker', options=df['broker'].unique().tolist(), default=df['broker'].unique().tolist())
        filtered_df = filtered_df[filtered_df['broker'].isin(brokers)]

    # Show filter results
    st.info(f"📈 Showing {len(filtered_df)} of {len(df)} total trades after applying filters")

    st.divider()

    # Ensure PnL is numeric for all analytics
    filtered_df = filtered_df.copy()
    filtered_df['pnl'] = pd.to_numeric(filtered_df['pnl'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['pnl'])

    if filtered_df.empty:
        st.error("No valid trade data found after filtering. Please check your data.")
        st.stop()

    stats = compute_basic_stats(filtered_df)
    perf = performance_over_time(filtered_df, freq='M')

    # Calculate and display KPIs at the top of the dashboard
    kpis = calculate_kpis(filtered_df, commission_per_trade=3.5)

    st.subheader('📊 Key Performance Indicators')
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    kpi_col1.metric(
        label='Total Trades', 
        value=f"{kpis['total_trades']:,}",
        help="Total number of completed trades"
    )
    kpi_col1.metric(
        label='Win Rate', 
        value=f"{kpis['win_rate_percent']:.1f}%",
        help="Percentage of profitable trades"
    )
    kpi_col2.metric(
        label='Average R:R', 
        value=f"{kpis['average_rr']:.2f}" if kpis['average_rr'] != np.inf else "∞",
        help="Average reward-to-risk ratio"
    )
    kpi_col2.metric(
        label='Net P&L (After Commission)', 
        value=f"${kpis['net_pnl_after_commission']:,.2f}",
        delta=f"${kpis['gross_pnl'] - kpis['net_pnl_after_commission']:,.2f} commission",
        help="Total profit/loss after $3.50 commission per trade"
    )
    kpi_col3.metric(
        label='Best Trade', 
        value=f"${kpis['max_single_trade_win']:,.2f}",
        help="Largest single winning trade"
    )
    kpi_col3.metric(
        label='Worst Trade', 
        value=f"${kpis['max_single_trade_loss']:,.2f}",
        help="Largest single losing trade"
    )

    # Show commission breakdown in expandable section
    with st.expander("💰 Commission Breakdown"):
        col_a, col_b, col_c = st.columns(3)
        col_a.metric('Gross P&L', f"${kpis['gross_pnl']:,.2f}")
        col_b.metric('Total Commission', f"${kpis['total_commission']:,.2f}")
        col_c.metric('Commission per Trade', "$3.50")

    # Daily Loss Limit Section
    st.subheader('📊 Daily Loss Limit Analysis')

    # User input for daily loss limit
    daily_loss_limit = st.number_input(
        'Daily Loss Limit ($)', 
        min_value=0.0, 
        value=1000.0, 
        step=50.0,
        help="Set your maximum acceptable loss per day"
    )

    # Calculate daily PnL and violations
    daily_pnl = filtered_df.groupby(filtered_df['exit_time'].dt.date)['pnl'].sum().reset_index()
    daily_pnl.columns = ['date', 'net_pnl']
    daily_pnl['violation'] = daily_pnl['net_pnl'] < -daily_loss_limit

    # Count violation days
    violation_days = len(daily_pnl[daily_pnl['violation']])
    total_trading_days = len(daily_pnl)

    # Display KPI
    violation_col1, violation_col2 = st.columns(2)
    violation_col1.metric(
        label='Daily Loss Limit Violations', 
        value=f"{violation_days}",
        delta=f"out of {total_trading_days} trading days",
        help=f"Days where net loss exceeded ${daily_loss_limit:,.2f}"
    )

    if violation_days > 0:
        violation_percentage = (violation_days / total_trading_days) * 100
        violation_col2.metric(
            label='Violation Rate', 
            value=f"{violation_percentage:.1f}%",
            help="Percentage of trading days with losses exceeding limit"
        )

    # Display violation details if any exist
    if violation_days > 0:
        st.subheader('🚨 Daily Loss Limit Violations')
        st.caption(f'Days where net loss exceeded ${daily_loss_limit:,.2f}')

        violation_details = daily_pnl[daily_pnl['violation']].copy()
        violation_details['net_pnl_formatted'] = violation_details['net_pnl'].apply(lambda x: f"${x:,.2f}")
        violation_details['excess_loss'] = violation_details['net_pnl'] + daily_loss_limit
        violation_details['excess_loss_formatted'] = violation_details['excess_loss'].apply(lambda x: f"${x:,.2f}")

        # Display violations table
        display_violations = violation_details[['date', 'net_pnl_formatted', 'excess_loss_formatted']].copy()
        display_violations.columns = ['Date', 'Net P&L', 'Excess Loss']
        display_violations = display_violations.sort_values('Date', ascending=False)

        st.dataframe(display_violations, use_container_width=True, hide_index=True)

        # Summary stats for violations
        worst_day_loss = violation_details['net_pnl'].min()
        total_excess_loss = violation_details['excess_loss'].sum()

        viol_col1, viol_col2 = st.columns(2)
        viol_col1.metric('Worst Day Loss', f"${worst_day_loss:,.2f}")
        viol_col2.metric('Total Excess Loss', f"${total_excess_loss:,.2f}")
    else:
        st.success(f"✅ No days exceeded the daily loss limit of ${daily_loss_limit:,.2f}")

    st.divider()

    overview_tab, symbol_tab, drawdown_tab, calendar_tab, journal_tab = st.tabs(
        ["Overview", "Symbols", "Drawdowns", "Calendar", "Journal"]
    )

    # Track current tab for feedback context
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 'Overview'

    with overview_tab:
        st.session_state.current_tab = 'Overview'

        st.subheader('Additional Performance Metrics')
        col1, col2, col3 = st.columns(3)
        col1.metric('Win Rate %', f"{stats['win_rate']:.2f}")
        col1.metric('Profit Factor', f"{stats['profit_factor']:.2f}")
        col2.metric('Expectancy', f"{stats['expectancy']:.2f}")
        col2.metric('Max Drawdown', f"{stats['max_drawdown']:.2f}")
        col3.metric('Sharpe Ratio', f"{stats['sharpe_ratio']:.2f}")
        col3.metric('Reward:Risk', f"{stats['reward_risk']:.2f}")

        st.subheader('Equity Curve')

        # Create Plotly equity curve with timestamps
        equity_df = filtered_df.copy().sort_values('exit_time')
        equity_df['cumulative_pnl'] = equity_df['pnl'].cumsum()

        # Choose colors based on theme
        if theme == "Light":
            equity_color = '#2563eb'  # Professional blue for light theme
            chart_bg = '#ffffff'
            text_color = '#1a1a1a'
        else:
            equity_color = '#00cc96'  # Keep existing color for dark theme
            chart_bg = '#0e1117'
            text_color = '#fafafa'

        fig_equity = px.line(
            equity_df, 
            x='exit_time', 
            y='cumulative_pnl',
            title='Cumulative P&L Over Time (Equity Curve)',
            labels={
                'exit_time': 'Date',
                'cumulative_pnl': 'Cumulative P&L ($)'
            }
        )
        fig_equity.update_layout(
            xaxis_title='Date',
            yaxis_title='Cumulative P&L ($)',
            hovermode='x unified',
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color=text_color),
            title_font_color=text_color,
            xaxis=dict(
                color=text_color, 
                gridcolor='#e5e7eb' if theme == "Light" else '#4a4a4a',
                gridwidth=1,
                showgrid=True,
                linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                linewidth=2
            ),
            yaxis=dict(
                color=text_color, 
                gridcolor='#e5e7eb' if theme == "Light" else '#4a4a4a',
                gridwidth=1,
                showgrid=True,
                linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                linewidth=2
            ),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        fig_equity.update_traces(
            line=dict(color=equity_color, width=3),
            hovertemplate='<b>Date:</b> %{x}<br><b>Cumulative P&L:</b> $%{y:,.2f}<extra></extra>'
        )

        st.plotly_chart(fig_equity, use_container_width=True)

        st.subheader('Performance Over Time')
        st.bar_chart(perf.set_index('period')['pnl'])

        st.subheader('Trading Activity - Trades Per Week')

        # Create weekly trade count chart
        trades_per_week = filtered_df.copy()
        trades_per_week['week'] = trades_per_week['exit_time'].dt.to_period('W').dt.start_time
        weekly_counts = trades_per_week.groupby('week').size().reset_index(name='trade_count')

        if not weekly_counts.empty:
            # Choose colors based on theme
            if theme == "Light":
                bar_color = '#2563eb'  # Professional blue for light theme
                chart_bg = '#ffffff'
                text_color = '#1a1a1a'
            else:
                bar_color = '#636EFA'  # Keep existing color for dark theme
                chart_bg = '#0e1117'
                text_color = '#fafafa'

            fig_weekly = px.bar(
                weekly_counts,
                x='week',
                y='trade_count',
                title='Number of Trades Per Week',
                labels={
                    'week': 'Week Starting',
                    'trade_count': 'Number of Trades'
                }
            )
            fig_weekly.update_layout(
                xaxis_title='Week Starting',
                yaxis_title='Number of Trades',
                showlegend=False,
                plot_bgcolor=chart_bg,
                paper_bgcolor=chart_bg,
                font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color=text_color),
                title_font_color=text_color,
                xaxis=dict(
                    color=text_color, 
                    gridcolor='#e5e7eb' if theme == "Light" else '#4a4a4a',
                    gridwidth=1,
                    showgrid=True,
                    linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                    linewidth=2
                ),
                yaxis=dict(
                    color=text_color, 
                    gridcolor='#e5e7eb' if theme == "Light" else '#4a4a4a',
                    gridwidth=1,
                    showgrid=True,
                    linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                    linewidth=2
                ),
                margin=dict(l=60, r=60, t=60, b=60)
            )
            fig_weekly.update_traces(
                marker_color=bar_color,
                hovertemplate='<b>Week:</b> %{x}<br><b>Trades:</b> %{y}<extra></extra>'
            )

            st.plotly_chart(fig_weekly, use_container_width=True)
        else:
            st.info("No weekly trade data available.")

        med = median_results(filtered_df)
        st.subheader('Median Results')
        st.write(med)

        pf_sym = profit_factor_by_symbol(filtered_df)
        st.subheader('Profit Factor by Symbol')
        st.dataframe(pf_sym, use_container_width=True)

        duration = trade_duration_stats(filtered_df)
        st.subheader('Trade Duration Stats (minutes)')
        st.write(duration)

        streak = max_streaks(filtered_df)
        st.subheader('Max Streaks')
        st.write(streak)

        rolling = rolling_metrics(filtered_df, window=10)
        if not rolling.empty:
            st.subheader('Rolling Metrics (10 trades)')
            st.line_chart(rolling.set_index('end_index')[['win_rate', 'profit_factor']])

        st.subheader('Trades')
        table_df = compute_trade_result(filtered_df)

        # Calculate Risk-Reward ratio for conditional formatting
        table_df_formatted = table_df.copy()

        # Calculate RR ratio (Risk = entry_price - stop_loss for long, stop_loss - entry_price for short)
        # Reward = exit_price - entry_price for long, entry_price - exit_price for short
        def calculate_rr(row):
            entry = float(row['entry_price'])
            exit = float(row['exit_price'])
            stop = float(row.get('stop_loss', 0))
            direction = row['direction']

            if stop == 0:
                return 0  # No stop loss set

            if direction == 'long':
                risk = abs(entry - stop)
                reward = abs(exit - entry)
            else:  # short
                risk = abs(stop - entry)
                reward = abs(entry - exit)

            return reward / risk if risk > 0 else 0

        table_df_formatted['rr_ratio'] = table_df_formatted.apply(calculate_rr, axis=1)

        # Create styled dataframe with conditional formatting
        def style_trades(df):
            def highlight_row(row):
                styles = [''] * len(row)

                # Get PnL value (handle string values from CSV)
                pnl_val = pd.to_numeric(row['pnl'], errors='coerce')

                # Get RR value and ensure it's numeric
                rr_val = row.get('rr_ratio', 0)
                if isinstance(rr_val, str):
                    try:
                        rr_val = float(rr_val) if rr_val != "N/A" else 0
                    except (ValueError, TypeError):
                        rr_val = 0

                # Highlight entire row based on conditions
                if not pd.isna(pnl_val) and pnl_val > 100:
                    # Green for high P&L trades
                    styles = ['background-color: #d4edda; color: #155724'] * len(row)
                elif rr_val > 0 and rr_val < 1:
                    # Red for poor RR trades
                    styles = ['background-color: #f8d7da; color: #721c24'] * len(row)

                return styles

            return df.style.apply(highlight_row, axis=1)

        # Display formatted table
        st.subheader('Trades with Conditional Formatting')
        st.caption('🟢 Green: Net P&L > $100 | 🔴 Red: Risk-Reward < 1.0')

        # Prepare display columns
        display_cols = ['symbol', 'direction', 'entry_price', 'exit_price', 'stop_loss', 
                       'pnl', 'rr_ratio', 'trade_result', 'entry_time', 'exit_time']
        display_df = table_df_formatted[[col for col in display_cols if col in table_df_formatted.columns]]

        # Format numeric columns properly to avoid pandas warnings
        if 'rr_ratio' in display_df.columns:
            display_df = display_df.copy()
            display_df['rr_ratio'] = display_df['rr_ratio'].apply(lambda x: f"{x:.2f}" if x > 0 else "N/A")
        if 'pnl' in display_df.columns:
            display_df = display_df.copy()
            pnl_numeric = pd.to_numeric(display_df['pnl'], errors='coerce')
            display_df['pnl'] = pnl_numeric.apply(lambda x: f"${x:.2f}" if not pd.isna(x) else "$0.00")

        # Apply styling and display
        styled_df = style_trades(display_df)
        st.dataframe(styled_df, use_container_width=True)

        # Original interactive grid for selection
        st.subheader('Interactive Trades Table')
        options = get_grid_options(table_df)
        grid = AgGrid(
            table_df,
            gridOptions=options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
        )

        if grid['selected_rows']:
            row = pd.Series(grid['selected_rows'][0])
            details = trade_detail(row)
            with st.modal('Trade Details'):
                chart_df = pd.DataFrame({
                    'time': [row['entry_time'], row['exit_time']],
                    'price': [row['entry_price'], row['exit_price']],
                })
                st.line_chart(chart_df.set_index('time'))
                st.write(f"Duration: {details['duration']}")
                st.write(f"MAE: {details['mae']}  MFE: {details['mfe']}")
                if details['notes']:
                    st.write(details['notes'])

    with symbol_tab:
        st.session_state.current_tab = 'Symbols'
        # Convert PnL to numeric to handle string values from CSV uploads
        symbol_df = filtered_df.copy()
        symbol_df['pnl'] = pd.to_numeric(symbol_df['pnl'], errors='coerce')
        symbol_df = symbol_df.dropna(subset=['pnl'])

        if not symbol_df.empty:
            grp = symbol_df.groupby('symbol')
            symbol_stats = pd.DataFrame({
                'Trades': grp['pnl'].count(),
                'Total PnL': grp['pnl'].sum(),
                'Avg PnL': grp['pnl'].mean(),
                'Win Rate %': grp['pnl'].apply(lambda x: (x > 0).mean() * 100),
            })
            st.dataframe(symbol_stats, use_container_width=True)
        else:
            st.warning("No valid PnL data found for symbol analysis.")

    with drawdown_tab:
        st.session_state.current_tab = 'Drawdowns'
        equity = stats['equity_curve']
        drawdown = equity.cummax() - equity
        # Choose colors based on theme
        if theme == "Light":
            area_color = '#dc2626'  # Professional red for drawdown in light theme
            chart_bg = '#ffffff'
            text_color = '#1a1a1a'
        else:
            area_color = '#ff6b6b'  # Keep existing red-ish for dark theme
            chart_bg = '#0e1117'
            text_color = '#fafafa'

        fig = px.area(x=drawdown.index, y=drawdown.values,
                      labels={'x': 'Trade', 'y': 'Drawdown'},
                      title='Drawdown Analysis')
        fig.update_layout(
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color=text_color),
            title_font_color=text_color,
            xaxis=dict(
                color=text_color, 
                gridcolor='#e5e7eb' if theme == "Light" else '#4a4a4a',
                gridwidth=1,
                showgrid=True,
                linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                linewidth=2,
                title='Trade Number'
            ),
            yaxis=dict(
                color=text_color, 
                gridcolor='#e5e7eb' if theme == "Light" else '#4a4a4a',
                gridwidth=1,
                showgrid=True,
                linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                linewidth=2,
                title='Drawdown ($)'
            ),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        fig.update_traces(fill='tonexty', fillcolor=area_color, line_color=area_color)
        st.plotly_chart(fig, use_container_width=True)

    with calendar_tab:
        st.session_state.current_tab = 'Calendar'
        daily_pnl = filtered_df.groupby(filtered_df['exit_time'].dt.date)['pnl'].sum()
        cal_df = daily_pnl.reset_index()
        cal_df.columns = ['date', 'pnl']
        cal_df['date'] = pd.to_datetime(cal_df['date'])
        cal_df['month'] = cal_df['date'].dt.month
        cal_df['day'] = cal_df['date'].dt.day
        pivot = cal_df.pivot(index='day', columns='month', values='pnl')
        # Choose color scale based on theme
        if theme == "Light":
            color_scale = [[0.0, '#dc2626'], [0.5, '#f3f4f6'], [1.0, '#059669']]  # Professional red-gray-green scale
            chart_bg = '#ffffff'
            text_color = '#1a1a1a'
        else:
            color_scale = 'RdYlGn'  # Same scale works for dark theme
            chart_bg = '#0e1117'
            text_color = '#fafafa'

        fig = px.imshow(pivot, 
                        labels={'x': 'Month', 'y': 'Day', 'color': 'PnL'},
                        aspect='auto',
                        color_continuous_scale=color_scale,
                        title='Daily P&L Calendar Heatmap')
        fig.update_layout(
            plot_bgcolor=chart_bg,
            paper_bgcolor=chart_bg,
            font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color=text_color),
            title_font_color=text_color,
            xaxis=dict(
                color=text_color,
                linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                linewidth=2
            ),
            yaxis=dict(
                color=text_color,
                linecolor='#d1d5db' if theme == "Light" else '#4a4a4a',
                linewidth=2
            ),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        st.plotly_chart(fig, use_container_width=True)

    with journal_tab:
        st.session_state.current_tab = 'Journal'
        if 'journal_entries' not in st.session_state:
            st.session_state.journal_entries = []
        note = st.text_area('New Journal Entry', key='journal_input')
        if st.button('Add Entry'):
            if note:
                st.session_state.journal_entries.append({
                    'date': pd.Timestamp.now().date(),
                    'note': note,
                })
                st.success('Entry added')
        if st.session_state.journal_entries:
            st.dataframe(pd.DataFrame(st.session_state.journal_entries))

    st.subheader('Risk Assessment')

    if 'account_size' not in st.session_state:
        st.session_state.account_size = 10000.0
    if 'risk_per_trade' not in st.session_state:
        st.session_state.risk_per_trade = 0.01
    if 'max_daily_loss' not in st.session_state:
        st.session_state.max_daily_loss = 500.0

    account_size = st.number_input('Account Size', value=st.session_state.account_size, key='account_size')
    risk_per_trade = st.number_input('Risk % per Trade', value=st.session_state.risk_per_trade, key='risk_per_trade')
    max_daily_loss = st.number_input('Max Daily Loss', value=st.session_state.max_daily_loss, key='max_daily_loss')

    risk = {}
    if st.button('Assess Risk'):
        risk = assess_risk(filtered_df, account_size, risk_per_trade, max_daily_loss)
        if risk['risk_alert']:
            st.error(risk['risk_alert'])
        st.write(risk)

    if risk:
        pdf_bytes = generate_pdf(stats, risk)
        st.download_button('Download Analytics Report', pdf_bytes, 'analytics_report.pdf')

    # Download buttons
    col_download1, col_download2, col_download3 = st.columns(3)

    with col_download1:
        st.download_button(
            'Download All Trades CSV', 
            df.to_csv(index=False), 
            'all_trades.csv',
            help="Download complete trade dataset"
        )

    with col_download2:
        st.download_button(
            'Download Filtered Trades CSV', 
            filtered_df.to_csv(index=False), 
            'filtered_trades.csv',
            help=f"Download {len(filtered_df)} filtered trades"
        )

    with col_download3:
        # Generate comprehensive PDF report
        try:
            comprehensive_pdf_bytes = generate_comprehensive_pdf(filtered_df, kpis, stats)
            st.download_button(
                '📄 Download PDF Report',
                comprehensive_pdf_bytes,
                f'tradesense_report_{pd.Timestamp.now().strftime("%Y%m%d_%H%M")}.pdf',
                help=f"Download comprehensive PDF report with {len(filtered_df)} filtered trades, KPIs, and analytics",
                type="primary"
            )
        except Exception as e:
            st.error(f"Error generating PDF report: {str(e)}")
            # Fallback to basic PDF
            if risk:
                pdf_bytes = generate_pdf(stats, risk)
                st.download_button('📄 Download Basic PDF Report', pdf_bytes, 'basic_analytics_report.pdf')

    # Trade Entry Form
    st.subheader('Manual Trade Entry')
    with st.form("trade_entry_form"):
        col1, col2 = st.columns(2)

        with col1:
            symbol = st.text_input('Symbol', placeholder='e.g. AAPL, TSLA')
            entry_price = st.number_input('Entry Price', min_value=0.0, step=0.01, format="%.2f")
            exit_price = st.number_input('Exit Price', min_value=0.0, step=0.01, format="%.2f")
            stop_loss = st.number_input('Stop Loss', min_value=0.0, step=0.01, format="%.2f")

        with col2:
            trade_size = st.number_input('Trade Size', min_value=0.0, step=0.01, format="%.2f")
            direction = st.selectbox('Direction', options=['long', 'short'])
            result = st.selectbox('Result', options=['win', 'loss'])

        notes = st.text_area('Notes', placeholder='Enter any trade notes...')

        # Enhanced Tags system with suggestions and custom tags
        col_tag1, col_tag2 = st.columns([2, 1])

        with col_tag1:
            # Predefined tag suggestions
            suggested_tags = ['scalp', 'swing', 'breakout', 'reversal', 'momentum', 'support', 'resistance', 'earnings', 'news', 'gap', 'pullback', 'bounce', 'trend', 'counter-trend']

            # Get existing tags from current trades if file exists
            existing_tags = set(suggested_tags)
            trades_file = 'trades.csv'
            if pd.io.common.file_exists(trades_file):
                try:
                    existing_trades = pd.read_csv(trades_file)
                    if 'tags' in existing_trades.columns:
                        for tag_string in existing_trades['tags'].dropna():
                            if tag_string and str(tag_string).strip():
                                existing_tag_list = [tag.strip() for tag in str(tag_string).split(',')]
                                existing_tags.update(existing_tag_list)
                except:
                    pass

            available_tags = sorted([tag for tag in existing_tags if tag])

            tags = st.multiselect(
                'Tags', 
                options=available_tags,
                help="Select existing tags or add custom ones below"
            )

        with col_tag2:
            custom_tag = st.text_input(
                'Add Custom Tag',
                placeholder='e.g., crypto, forex',
                help="Enter a new tag and it will be added to your selection"
            )

            if custom_tag and custom_tag.strip():
                clean_tag = custom_tag.strip().lower().replace(' ', '-')
                if clean_tag not in tags:
                    tags.append(clean_tag)
                    st.success(f"Added '{clean_tag}' to tags")

        submitted = st.form_submit_button("Submit Trade")

        if submitted:
            # Comprehensive validation with specific error messages
            validation_errors = []

            # Check symbol
            if not symbol or symbol.strip() == '':
                validation_errors.append("❌ Symbol is required and cannot be empty")
            elif len(symbol.strip()) < 1:
                validation_errors.append("❌ Symbol must be at least 1 character long")

            # Check entry price
            if entry_price <= 0:
                validation_errors.append("❌ Entry price must be greater than 0")
            elif entry_price > 1000000:
                validation_errors.append("❌ Entry price seems unrealistically high (> $1,000,000)")

            # Check exit price
            if exit_price <= 0:
                validation_errors.append("❌ Exit price must be greater than 0")
            elif exit_price > 1000000:
                validation_errors.append("❌ Exit price seems unrealistically high (> $1,000,000)")

            # Check stop loss
            if stop_loss < 0:
                validation_errors.append("❌ Stop loss cannot be negative")
            elif stop_loss > 1000000:
                validation_errors.append("❌ Stop loss seems unrealistically high (> $1,000,000)")

            # Check trade size
            if trade_size <= 0:
                validation_errors.append("❌ Trade size must be greater than 0")
            elif trade_size > 1000000:
                validation_errors.append("❌ Trade size seems unrealistically high (> 1,000,000 shares/contracts)")

            # Check direction
            if direction not in ['long', 'short']:
                validation_errors.append("❌ Direction must be either 'long' or 'short'")

            # Check result
            if result not in ['win', 'loss']:
                validation_errors.append("❌ Result must be either 'win' or 'loss'")

            # Logical validation checks
            if entry_price > 0 and exit_price > 0:
                if direction == 'long' and exit_price < entry_price and result == 'win':
                    validation_errors.append("❌ Long position with exit price lower than entry price should be marked as 'loss', not 'win'")
                elif direction == 'short' and exit_price > entry_price and result == 'win':
                    validation_errors.append("❌ Short position with exit price higher than entry price should be marked as 'loss', not 'win'")
                elif direction == 'long' and exit_price > entry_price and result == 'loss':
                    validation_errors.append("❌ Long position with exit price higher than entry price should be marked as 'win', not 'loss'")
                elif direction == 'short' and exit_price < entry_price and result == 'loss':
                    validation_errors.append("❌ Short position with exit price lower than entry price should be marked as 'win', not 'loss'")

            # Stop loss validation
            if stop_loss > 0 and entry_price > 0:
                if direction == 'long' and stop_loss > entry_price:
                    validation_errors.append("❌ For long positions, stop loss should be below entry price")
                elif direction == 'short' and stop_loss < entry_price:
                    validation_errors.append("❌ For short positions, stop loss should be above entry price")

            # Display validation errors
            if validation_errors:
                st.error("❌ **TRADE SUBMISSION FAILED**")
                st.error(f"Found {len(validation_errors)} validation error(s). Please fix the following issues:")
                for i, error in enumerate(validation_errors, 1):
                    st.error(f"{i}. {error}")
                st.warning("💡 **Tip**: Double-check your entry/exit prices match your trade direction and result.")
            else:
                # All validation passed, proceed with saving
                st.info("✅ **Validation passed** - Processing trade submission...")

                # Calculate PnL based on direction
                if direction == 'long':
                    pnl = (exit_price - entry_price) * trade_size
                else:  # short
                    pnl = (entry_price - exit_price) * trade_size

                # Calculate RR ratio for the new trade
                if stop_loss > 0:
                    if direction == 'long':
                        risk = abs(entry_price - stop_loss)
                        reward = abs(exit_price - entry_price)
                    else:  # short
                        risk = abs(stop_loss - entry_price)
                        reward = abs(entry_price - exit_price)
                    rr_ratio = reward / risk if risk > 0 else 0
                else:
                    rr_ratio = 0

                # Store the trade entry with current datetime and RR ratio
                trade_entry = {
                    'datetime': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': symbol.strip().upper(),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'stop_loss': stop_loss,
                    'trade_size': trade_size,
                    'direction': direction,
                    'result': result,
                    'pnl': pnl,
                    'rr_ratio': rr_ratio,
                    'notes': notes.strip() if notes else '',
                    'tags': ', '.join(tags) if tags else ''
                }

                # Save to CSV file
                trades_file = 'trades.csv'
                try:
                    # Check if file exists
                    file_existed = pd.io.common.file_exists(trades_file)

                    if not file_existed:
                        # Create new file with headers
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, index=False)
                        st.info(f"📁 Created new trades file: {trades_file}")
                    else:
                        # Append to existing file
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, mode='a', header=False, index=False)
                        st.info(f"📝 Appended to existing file: {trades_file}")

                    # Success message with comprehensive details
                    st.success("🎉 **TRADE SUBMISSION SUCCESSFUL!**")

                    # Trade summary
                    rr_status = f"{rr_ratio:.3f}" if rr_ratio > 0 else "N/A (No Stop Loss)"
                    rr_flag = " 🚨 Poor Risk/Reward" if 0 < rr_ratio < 1 else " ✅ Good Risk/Reward" if rr_ratio >= 1 else ""

                    st.success(f"**Trade Details:**")
                    st.success(f"• Symbol: {symbol.strip().upper()}")
                    st.success(f"• Direction: {direction.upper()}")
                    st.success(f"• P&L: ${pnl:.2f}")
                    st.success(f"• Risk/Reward Ratio: {rr_status}{rr_flag}")
                    st.success(f"• Tags: {', '.join(tags) if tags else 'None'}")

                    # File save confirmation
                    st.success(f"**Saved to:** {trades_file}")
                    st.success(f"**Timestamp:** {trade_entry['datetime']}")

                    # Show trade data in expandable section
                    with st.expander("📋 View Complete Trade Data"):
                        st.json(trade_entry)

                    # Rule-based feedback logic
                    feedback_messages = []

                    # Rule 1: Check RR ratio
                    if 0 < rr_ratio < 1:
                        feedback_messages.append("⚠️ **Low RR**: Consider setting better reward targets. Your current Risk/Reward ratio is below 1.0.")

                    # Rule 2: Check win rate for last 20 trades
                    try:
                        # Read existing trades to calculate recent win rate
                        if pd.io.common.file_exists(trades_file):
                            existing_trades = pd.read_csv(trades_file)
                            if len(existing_trades) >= 20:  # Only check if we have at least 20 trades
                                # Get last 20 trades (including the one we just added)
                                last_20_trades = existing_trades.tail(20)
                                last_20_trades['pnl'] = pd.to_numeric(last_20_trades['pnl'], errors='coerce')
                                last_20_trades = last_20_trades.dropna(subset=['pnl'])

                                if len(last_20_trades) >= 20:
                                    winning_trades = len(last_20_trades[last_20_trades['pnl'] > 0])
                                    recent_win_rate = (winning_trades / len(last_20_trades)) * 100

                                    if recent_win_rate < 50:
                                        feedback_messages.append(f"📊 **Low Recent Win Rate**: Your win rate over the last 20 trades is {recent_win_rate:.1f}%. Consider reviewing your losing trades to identify patterns.")
                    except Exception:
                        pass  # Silently skip win rate analysis if there's an error

                    # Display feedback messages
                    if feedback_messages:
                        st.subheader("🤖 Trading Feedback")
                        for message in feedback_messages:
                            st.warning(message)
                    else:
                        # Positive feedback when rules pass
                        positive_feedback = []
                        if rr_ratio >= 1:
                            positive_feedback.append("✅ **Good Risk/Reward**: Your R:R ratio meets the 1:1 minimum threshold.")

                        if positive_feedback:
                            st.subheader("🤖 Trading Feedback")
                            for message in positive_feedback:
                                st.success(message)

                except FileNotFoundError as e:
                    st.error("❌ **SAVE FAILED - File System Error**")
                    st.error(f"**Reason:** Could not access the trades file location")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)

                except PermissionError as e:
                    st.error("❌ **SAVE FAILED - Permission Denied**")
                    st.error(f"**Reason:** Insufficient permissions to write to {trades_file}")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)

                except pd.errors.EmptyDataError as e:
                    st.error("❌ **SAVE FAILED - Data Format Error**")
                    st.error(f"**Reason:** Issue with trade data format")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)

                except Exception as e:
                    st.error("❌ **SAVE FAILED - Unexpected Error**")
                    st.error(f"**Reason:** An unexpected error occurred while saving")
                    st.error(f"**Error Type:** {type(e).__name__}")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)
                    st.error("**Troubleshooting:** Try refreshing the page or contact support if the issue persists.")

else:
    st.info('Upload a trade history file to begin.')

    # Check if trades.csv exists and display the trades
    trades_file = 'trades.csv'
    file_exists = pd.io.common.file_exists(trades_file)
    trades_empty = True

    if file_exists:
        try:
            # Read the trades from CSV
            manual_trades_df = pd.read_csv(trades_file)
            trades_empty = manual_trades_df.empty

            if not trades_empty:
                # Parse datetime to timestamp column
                manual_trades_df['timestamp'] = pd.to_datetime(manual_trades_df['datetime'], errors='coerce')

                # Ensure tags column exists for filtering
                if 'tags' not in manual_trades_df.columns:
                    manual_trades_df['tags'] = ''

                st.subheader('Your Manual Trades')
                st.write(f"Found {len(manual_trades_df)} manually entered trades:")

                # Display the trades in a nice format
                display_df = manual_trades_df.copy()
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:.2f}")

                # Reorder columns for better display
                column_order = ['timestamp', 'symbol', 'direction', 'entry_price', 'exit_price', 
                               'trade_size', 'pnl', 'result', 'stop_loss', 'tags', 'notes']
                display_df = display_df[[col for col in column_order if col in display_df.columns]]

                st.dataframe(display_df, use_container_width=True)

                # Show basic stats for manual trades
                total_pnl = manual_trades_df['pnl'].sum()
                win_trades = len(manual_trades_df[manual_trades_df['pnl'] > 0])
                total_trades = len(manual_trades_df)
                win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric('Total Trades', total_trades)
                col2.metric('Total P&L', f"${total_pnl:.2f}")
                col3.metric('Win Rate', f"{win_rate:.1f}%")

                # Option to download the manual trades
                st.download_button(
                    'Download Manual Trades CSV', 
                    manual_trades_df.to_csv(index=False), 
                    'manual_trades.csv'
                )

        except Exception as e:
            st.error(f"Error reading trades.csv: {str(e)}")
            trades_empty = True

    # Show onboarding card if file doesn't exist or is empty
    if not file_exists or trades_empty:
        st.subheader('🚀 Welcome to TradeSense!')

        # Onboarding card with sample trade
        with st.container():
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px;">
                <h3 style="color: white; margin-top: 0;">📈 Start Your Trading Journey</h3>
                <p style="color: #f0f0f0; font-size: 16px; margin-bottom: 15px;">
                    Track, analyze, and improve your trades with powerful analytics. 
                    Enter your first trade below to unlock insights!
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Sample trade example
            with st.expander("💡 See Sample Trade Example", expanded=True):
                st.markdown("**Here's what a profitable trade entry looks like:**")

                sample_cols = st.columns(3)
                with sample_cols[0]:
                    st.info("**📊 Trade Details**\n- Symbol: AAPL\n- Direction: Long\n- Entry: $150.00\n- Exit: $155.50")

                with sample_cols[1]:
                    st.success("**💰 Risk Management**\n- Stop Loss: $147.50\n- Trade Size: 100 shares\n- Risk/Reward: 2.2:1")

                with sample_cols[2]:
                    st.warning("**🏷️ Results**\n- P&L: +$550.00\n- Result: Win\n- Tags: breakout, momentum")

                st.markdown("""
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
                    <strong>🎯 Pro Tip:</strong> Good trades have clear entry/exit rules, proper risk management, 
                    and detailed notes for future analysis!
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 👇 Ready to start? Enter your first trade below!")

    # Show trade entry form even when no file is uploaded
    st.subheader('Manual Trade Entry')
    with st.form("trade_entry_form"):
        col1, col2 = st.columns(2)

        with col1:
            symbol = st.text_input('Symbol', placeholder='e.g. AAPL, TSLA')
            entry_price = st.number_input('Entry Price', min_value=0.0, step=0.01, format="%.2f")
            exit_price = st.number_input('Exit Price', min_value=0.0, step=0.01, format="%.2f")
            stop_loss = st.number_input('Stop Loss', min_value=0.0, step=0.01, format="%.2f")

        with col2:
            trade_size = st.number_input('Trade Size', min_value=0.0, step=0.01, format="%.2f")
            direction = st.selectbox('Direction', options=['long', 'short'])
            result = st.selectbox('Result', options=['win', 'loss'])

        notes = st.text_area('Notes', placeholder='Enter any trade notes...')

        # Enhanced Tags system with suggestions and custom tags
        col_tag1, col_tag2 = st.columns([2, 1])

        with col_tag1:
            # Predefined tag suggestions
            suggested_tags = ['scalp', 'swing', 'breakout', 'reversal', 'momentum', 'support', 'resistance', 'earnings', 'news', 'gap', 'pullback', 'bounce', 'trend', 'counter-trend']

            # Get existing tags from current trades if file exists
            existing_tags = set(suggested_tags)
            trades_file = 'trades.csv'
            if pd.io.common.file_exists(trades_file):
                try:
                    existing_trades = pd.read_csv(trades_file)
                    if 'tags' in existing_trades.columns:
                        for tag_string in existing_trades['tags'].dropna():
                            if tag_string and str(tag_string).strip():
                                existing_tag_list = [tag.strip() for tag in str(tag_string).split(',')]
                                existing_tags.update(existing_tag_list)
                except:
                    pass

            available_tags = sorted([tag for tag in existing_tags if tag])

            tags = st.multiselect(
                'Tags', 
                options=available_tags,
                help="Select existing tags or add custom ones below"
            )

        with col_tag2:
            custom_tag = st.text_input(
                'Add Custom Tag',
                placeholder='e.g., crypto, forex',
                help="Enter a new tag and it will be added to your selection"
            )

            if custom_tag and custom_tag.strip():
                clean_tag = custom_tag.strip().lower().replace(' ', '-')
                if clean_tag not in tags:
                    tags.append(clean_tag)
                    st.success(f"Added '{clean_tag}' to tags")

        submitted = st.form_submit_button("Submit Trade")

        if submitted:
            # Comprehensive validation with specific error messages
            validation_errors = []

            # Check symbol
            if not symbol or symbol.strip() == '':
                validation_errors.append("❌ Symbol is required and cannot be empty")
            elif len(symbol.strip()) < 1:
                validation_errors.append("❌ Symbol must be at least 1 character long")

            # Check entry price
            if entry_price <= 0:
                validation_errors.append("❌ Entry price must be greater than 0")
            elif entry_price > 1000000:
                validation_errors.append("❌ Entry price seems unrealistically high (> $1,000,000)")

            # Check exit price
            if exit_price <= 0:
                validation_errors.append("❌ Exit price must be greater than 0")
            elif exit_price > 1000000:
                validation_errors.append("❌ Exit price seems unrealistically high (> $1,000,000)")

            # Check stop loss
            if stop_loss < 0:
                validation_errors.append("❌ Stop loss cannot be negative")
            elif stop_loss > 1000000:
                validation_errors.append("❌ Stop loss seems unrealistically high (> $1,000,000)")

            # Check trade size
            if trade_size <= 0:
                validation_errors.append("❌ Trade size must be greater than 0")
            elif trade_size > 1000000:
                validation_errors.append("❌ Trade size seems unrealistically high (> 1,000,000 shares/contracts)")

            # Check direction
            if direction not in ['long', 'short']:
                validation_errors.append("❌ Direction must be either 'long' or 'short'")

            # Check result
            if result not in ['win', 'loss']:
                validation_errors.append("❌ Result must be either 'win' or 'loss'")

            # Logical validation checks
            if entry_price > 0 and exit_price > 0:
                if direction == 'long' and exit_price < entry_price and result == 'win':
                    validation_errors.append("❌ Long position with exit price lower than entry price should be marked as 'loss', not 'win'")
                elif direction == 'short' and exit_price > entry_price and result == 'win':
                    validation_errors.append("❌ Short position with exit price higher than entry price should be marked as 'loss', not 'win'")
                elif direction == 'long' and exit_price > entry_price and result == 'loss':
                    validation_errors.append("❌ Long position with exit price higher than entry price should be marked as 'win', not 'loss'")
                elif direction == 'short' and exit_price < entry_price and result == 'loss':
                    validation_errors.append("❌ Short position with exit price lower than entry price should be marked as 'win', not 'loss'")

            # Stop loss validation
            if stop_loss > 0 and entry_price > 0:
                if direction == 'long' and stop_loss > entry_price:
                    validation_errors.append("❌ For long positions, stop loss should be below entry price")
                elif direction == 'short' and stop_loss < entry_price:
                    validation_errors.append("❌ For short positions, stop loss should be above entry price")

            # Display validation errors
            if validation_errors:
                st.error("❌ **TRADE SUBMISSION FAILED**")
                st.error(f"Found {len(validation_errors)} validation error(s). Please fix the following issues:")
                for i, error in enumerate(validation_errors, 1):
                    st.error(f"{i}. {error}")
                st.warning("💡 **Tip**: Double-check your entry/exit prices match your trade direction and result.")
            else:
                # All validation passed, proceed with saving
                st.info("✅ **Validation passed** - Processing trade submission...")

                # Calculate PnL based on direction
                if direction == 'long':
                    pnl = (exit_price - entry_price) * trade_size
                else:  # short
                    pnl = (entry_price - exit_price) * trade_size

                # Calculate RR ratio for the new trade
                if stop_loss > 0:
                    if direction == 'long':
                        risk = abs(entry_price - stop_loss)
                        reward = abs(exit_price - entry_price)
                    else:  # short
                        risk = abs(stop_loss - entry_price)
                        reward = abs(entry_price - exit_price)
                    rr_ratio = reward / risk if risk > 0 else 0
                else:
                    rr_ratio = 0

                # Store the trade entry with current datetime and RR ratio
                trade_entry = {
                    'datetime': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': symbol.strip().upper(),
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'stop_loss': stop_loss,
                    'trade_size': trade_size,
                    'direction': direction,
                    'result': result,
                    'pnl': pnl,
                    'rr_ratio': rr_ratio,
                    'notes': notes.strip() if notes else '',
                    'tags': ', '.join(tags) if tags else ''
                }

                # Save to CSV file
                trades_file = 'trades.csv'
                try:
                    # Check if file exists
                    file_existed = pd.io.common.file_exists(trades_file)

                    if not file_existed:
                        # Create new file with headers
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, index=False)
                        st.info(f"📁 Created new trades file: {trades_file}")
                    else:
                        # Append to existing file
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, mode='a', header=False, index=False)
                        st.info(f"📝 Appended to existing file: {trades_file}")

                    # Success message with comprehensive details
                    st.success("🎉 **TRADE SUBMISSION SUCCESSFUL!**")

                    # Trade summary
                    rr_status = f"{rr_ratio:.3f}" if rr_ratio > 0 else "N/A (No Stop Loss)"
                    rr_flag = " 🚨 Poor Risk/Reward" if 0 < rr_ratio < 1 else " ✅ Good Risk/Reward" if rr_ratio >= 1 else ""

                    st.success(f"**Trade Details:**")
                    st.success(f"• Symbol: {symbol.strip().upper()}")
                    st.success(f"• Direction: {direction.upper()}")
                    st.success(f"• P&L: ${pnl:.2f}")
                    st.success(f"• Risk/Reward Ratio: {rr_status}{rr_flag}")
                    st.success(f"• Tags: {', '.join(tags) if tags else 'None'}")

                    # File save confirmation
                    st.success(f"**Saved to:** {trades_file}")
                    st.success(f"**Timestamp:** {trade_entry['datetime']}")

                    # Show trade data in expandable section
                    with st.expander("📋 View Complete Trade Data"):
                        st.json(trade_entry)

                    # Rule-based feedback logic
                    feedback_messages = []

                    # Rule 1: Check RR ratio
                    if 0 < rr_ratio < 1:
                        feedback_messages.append("⚠️ **Low RR**: Consider setting better reward targets. Your current Risk/Reward ratio is below 1.0.")

                    # Rule 2: Check win rate for last 20 trades
                    try:
                        # Read existing trades to calculate recent win rate
                        if pd.io.common.file_exists(trades_file):
                            existing_trades = pd.read_csv(trades_file)
                            if len(existing_trades) >= 20:  # Only check if we have at least 20 trades
                                # Get last 20 trades (including the one we just added)
                                last_20_trades = existing_trades.tail(20)
                                last_20_trades['pnl'] = pd.to_numeric(last_20_trades['pnl'], errors='coerce')
                                last_20_trades = last_20_trades.dropna(subset=['pnl'])

                                if len(last_20_trades) >= 20:
                                    winning_trades = len(last_20_trades[last_20_trades['pnl'] > 0])
                                    recent_win_rate = (winning_trades / len(last_20_trades)) * 100

                                    if recent_win_rate < 50:
                                        feedback_messages.append(f"📊 **Low Recent Win Rate**: Your win rate over the last 20 trades is {recent_win_rate:.1f}%. Consider reviewing your losing trades to identify patterns.")
                    except Exception:
                        pass  # Silently skip win rate analysis if there's an error

                    # Display feedback messages
                    if feedback_messages:
                        st.subheader("🤖 Trading Feedback")
                        for message in feedback_messages:
                            st.warning(message)
                    else:
                        # Positive feedback when rules pass
                        positive_feedback = []
                        if rr_ratio >= 1:
                            positive_feedback.append("✅ **Good Risk/Reward**: Your R:R ratio meets the 1:1 minimum threshold.")

                        if positive_feedback:
                            st.subheader("🤖 Trading Feedback")
                            for message in positive_feedback:
                                st.success(message)

                except FileNotFoundError as e:
                    st.error("❌ **SAVE FAILED - File System Error**")
                    st.error(f"**Reason:** Could not access the trades file location")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)

                except PermissionError as e:
                    st.error("❌ **SAVE FAILED - Permission Denied**")
                    st.error(f"**Reason:** Insufficient permissions to write to {trades_file}")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)

                except pd.errors.EmptyDataError as e:
                    st.error("❌ **SAVE FAILED - Data Format Error**")
                    st.error(f"**Reason:** Issue with trade data format")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)

                except Exception as e:
                    st.error("❌ **SAVE FAILED - Unexpected Error**")
                    st.error(f"**Reason:** An unexpected error occurred while saving")
                    st.error(f"**Error Type:** {type(e).__name__}")
                    st.error(f"**Technical Details:** {str(e)}")
                    st.error("**Your trade data:** (Copy this as backup)")
                    st.json(trade_entry)
                    st.error("**Troubleshooting:** Try refreshing the page or contact support if the issue persists.")