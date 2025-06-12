import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Dict
import psutil
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


@st.cache_data
def load_cached_trade_data(file_path_or_content):
    """Cached version of trade data loading."""
    if isinstance(file_path_or_content, str):
        # File path
        return load_trade_data(file_path_or_content)
    else:
        # File content - convert to string for hashing
        return load_trade_data(file_path_or_content)


@st.cache_data
def process_trade_dataframe(df_hash, df_data):
    """Cache expensive data processing operations."""
    df = pd.DataFrame(df_data)
    df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
    df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
    df = df.dropna(subset=['entry_time', 'exit_time'])
    return df


@st.cache_data
def compute_cached_analytics(filtered_df_hash, filtered_df_data):
    """Cache all expensive analytics computations."""
    filtered_df = pd.DataFrame(filtered_df_data)
    filtered_df['pnl'] = pd.to_numeric(filtered_df['pnl'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['pnl'])

    if filtered_df.empty:
        return None

    return {
        'stats': compute_basic_stats(filtered_df),
        'perf': performance_over_time(filtered_df, freq='M'),
        'kpis': calculate_kpis(filtered_df, commission_per_trade=3.5),
    }


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
    output = pdf.output(dest="S")
    return output if isinstance(output, bytes) else output.encode("latin1")


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

    output = pdf.output(dest="S")
    return output if isinstance(output, bytes) else output.encode("latin1")

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

# Simplified theme selection - remove heavy CSS
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=1)

st.sidebar.header("Upload Trade History")
st.sidebar.caption("We do not store or share your uploaded trade data.")

# Memory monitoring
try:
    memory_info = psutil.virtual_memory()
    st.sidebar.metric(
        "Memory Usage", 
        f"{memory_info.percent:.1f}%",
        help=f"RAM: {memory_info.used / (1024**3):.1f}GB / {memory_info.total / (1024**3):.1f}GB"
    )
except:
    pass  # Gracefully handle if psutil not available

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
        # Use cached data loading
        if isinstance(selected_file, str):
            df = load_cached_trade_data(selected_file)
        else:
            # For uploaded files, we need to cache based on content
            df = load_cached_trade_data(selected_file)
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

    # Optimize data processing with cached operations
    with st.spinner("Processing data..."):
        # Use cached data processing
        df_hash = hash(df.to_string())
        df = process_trade_dataframe(df_hash, df.to_dict('records'))

        if df.empty:
            st.error("No valid rows remain after cleaning.")
            st.stop()

    # Simplified filters
    st.header("📊 Filters")
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        symbols = st.multiselect('Symbols', options=df['symbol'].unique().tolist(), default=df['symbol'].unique().tolist())
        date_range = st.date_input('Date Range', value=[df['entry_time'].min().date(), df['exit_time'].max().date()])

    with filter_col2:
        directions = st.multiselect('Directions', options=df['direction'].unique().tolist(), default=df['direction'].unique().tolist())

        # Simplified tags
        if 'tags' in df.columns:
            all_tags = set()
            for tag_string in df['tags'].dropna():
                if tag_string and str(tag_string).strip():
                    all_tags.update([tag.strip() for tag in str(tag_string).split(',')])
            selected_tags = st.multiselect('Tags', options=sorted(all_tags), default=sorted(all_tags))
        else:
            selected_tags = []

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

    # Use cached expensive calculations
    filtered_df_hash = hash(f"{len(filtered_df)}_{hash(str(symbols))}_{hash(str(directions))}")

    with st.spinner("Computing analytics..."):
        filtered_df['pnl'] = pd.to_numeric(filtered_df['pnl'], errors='coerce')
        filtered_df = filtered_df.dropna(subset=['pnl'])

        if filtered_df.empty:
            st.error("No valid trade data found after filtering.")
            st.stop()

        # Use cached analytics computation
        cached_results = compute_cached_analytics(filtered_df_hash, filtered_df.to_dict('records'))

        if cached_results is None:
            st.error("No valid trade data found after filtering.")
            st.stop()

        stats = cached_results['stats']
        perf = cached_results['perf']
        kpis = cached_results['kpis']

    st.subheader('📊 Key Performance Indicators')
    
    # Import formatting functions
    from analytics import format_currency, format_percentage, format_number
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    kpi_col1.metric(
        label='Total Trades', 
        value=f"{kpis['total_trades']:,}" if kpis['total_trades'] > 0 else "–",
        help="Total number of completed trades"
    )
    kpi_col1.metric(
        label='Win Rate', 
        value=format_percentage(kpis['win_rate_percent']),
        help="Percentage of profitable trades"
    )
    kpi_col2.metric(
        label='Average R:R', 
        value=format_number(kpis['average_rr']) if kpis['average_rr'] != np.inf else "∞",
        help="Average reward-to-risk ratio"
    )
    kpi_col2.metric(
        label='Net P&L (After Commission)', 
        value=format_currency(kpis['net_pnl_after_commission']),
        delta=f"{format_currency(kpis['gross_pnl'] - kpis['net_pnl_after_commission'])} commission",
        help="Total profit/loss after commission"
    )
    kpi_col3.metric(
        label='Best Trade', 
        value=format_currency(kpis['max_single_trade_win']),
        help="Largest single winning trade"
    )
    kpi_col3.metric(
        label='Worst Trade', 
        value=format_currency(kpis['max_single_trade_loss']),
        help="Largest single losing trade"
    )

    # Show commission breakdown in expandable section
    with st.expander("💰 Commission Breakdown"):
        col_a, col_b, col_c = st.columns(3)
        col_a.metric('Gross P&L', format_currency(kpis['gross_pnl']))
        col_b.metric('Total Commission', format_currency(kpis['total_commission']))
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
        value=f"{violation_days}" if violation_days >= 0 else "–",
        delta=f"out of {total_trading_days} trading days",
        help=f"Days where net loss exceeded {format_currency(daily_loss_limit)}"
    )

    if violation_days > 0:
        violation_percentage = (violation_days / total_trading_days) * 100
        violation_col2.metric(
            label='Violation Rate', 
            value=format_percentage(violation_percentage),
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
        viol_col1.metric('Worst Day Loss', format_currency(worst_day_loss))
        viol_col2.metric('Total Excess Loss', format_currency(total_excess_loss))
    else:
        st.success(f"✅ No days exceeded the daily loss limit of {format_currency(daily_loss_limit)}")

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
        col1.metric('Win Rate', format_percentage(stats['win_rate']))
        col1.metric('Profit Factor', format_number(stats['profit_factor']))
        col2.metric('Expectancy', format_currency(stats['expectancy']))
        col2.metric('Max Drawdown', format_currency(stats['max_drawdown']))
        col3.metric('Sharpe Ratio', format_number(stats['sharpe_ratio']))
        col3.metric('Reward:Risk', format_number(stats['reward_risk']))

        st.subheader('Equity Curve')

        # Clean equity curve generation
        try:
            equity_df = filtered_df.copy()
            equity_df['pnl'] = pd.to_numeric(equity_df['pnl'], errors='coerce')
            equity_df = equity_df.dropna(subset=['pnl'])
            equity_df = equity_df[np.isfinite(equity_df['pnl'])]

            if not equity_df.empty and len(equity_df) >= 2:
                equity_df = equity_df.sort_values('exit_time')
                equity_df['cumulative_pnl'] = equity_df['pnl'].cumsum()

                # Remove infinite values from cumulative PnL
                equity_df = equity_df[np.isfinite(equity_df['cumulative_pnl'])]

                if not equity_df.empty and len(equity_df) >= 2:
                    chart_data = equity_df.set_index('exit_time')['cumulative_pnl']
                    if chart_data.index.dtype.kind in 'Mm' and len(chart_data) >= 2:
                        st.line_chart(chart_data, height=400)
                    else:
                        st.warning("⚠️ Unable to display equity curve: Invalid time series data")
                else:
                    st.warning("⚠️ Unable to display equity curve: Insufficient valid data points")
            else:
                st.warning("⚠️ Unable to display equity curve: Need at least 2 trades with valid P&L data")

        except Exception as e:
            st.error(f"❌ Error generating equity curve: {str(e)}")

        st.subheader('Performance Over Time')
        try:
            if not perf.empty and len(perf) >= 2:
                chart_data = perf.set_index('period')['pnl']
                chart_data = chart_data[np.isfinite(chart_data)]  # Remove infinite values

                if not chart_data.empty and len(chart_data) >= 2:
                    st.bar_chart(chart_data)
                else:
                    st.warning("⚠️ Unable to display performance chart: Insufficient valid data points")
            else:
                st.warning("⚠️ Unable to display performance chart: Need at least 2 periods of data")

        except Exception as e:
            st.error(f"❌ Error generating performance chart: {str(e)}")

        med = median_results(filtered_df)
        st.subheader('Median Results')
        
        med_col1, med_col2, med_col3 = st.columns(3)
        med_col1.metric('Median P&L', format_currency(med['median_pnl']))
        med_col2.metric('Median Win', format_currency(med['median_win']))
        med_col3.metric('Median Loss', format_currency(med['median_loss']))

        pf_sym = profit_factor_by_symbol(filtered_df)
        st.subheader('Profit Factor by Symbol')
        st.dataframe(pf_sym, use_container_width=True)

        duration = trade_duration_stats(filtered_df)
        st.subheader('Trade Duration Analysis')
        
        dur_col1, dur_col2, dur_col3, dur_col4 = st.columns(4)
        dur_col1.metric('Average Duration', f"{format_number(duration['average_minutes'], 0)} min")
        dur_col2.metric('Shortest Trade', f"{format_number(duration['min_minutes'], 0)} min")
        dur_col3.metric('Longest Trade', f"{format_number(duration['max_minutes'], 0)} min")
        dur_col4.metric('Median Duration', f"{format_number(duration['median_minutes'], 0)} min")

        streak = max_streaks(filtered_df)
        st.subheader('Streak Analysis')
        
        streak_col1, streak_col2 = st.columns(2)
        streak_col1.metric('Max Win Streak', f"{streak['max_win_streak']} trades")
        streak_col2.metric('Max Loss Streak', f"{streak['max_loss_streak']} trades")

        rolling = rolling_metrics(filtered_df, window=10)
        try:
            if not rolling.empty and len(rolling) >= 2:
                st.subheader('Rolling Metrics (10 trades)')

                # Clean chart data
                chart_data = rolling.set_index('end_index')[['win_rate', 'profit_factor']]
                chart_data = chart_data.replace([np.inf, -np.inf], np.nan).dropna()

                if not chart_data.empty and len(chart_data) >= 2:
                    st.line_chart(chart_data)
                else:
                    st.warning("⚠️ Unable to display rolling metrics chart: Insufficient valid data points")
            else:
                st.warning("⚠️ Unable to display rolling metrics: Need more trades for rolling window analysis")

        except Exception as e:
            st.error(f"❌ Error generating rolling metrics chart: {str(e)}")

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
        try:
            # Clean symbol data
            symbol_df = filtered_df.copy()
            symbol_df['pnl'] = pd.to_numeric(symbol_df['pnl'], errors='coerce')
            symbol_df = symbol_df.dropna(subset=['pnl'])
            symbol_df = symbol_df[np.isfinite(symbol_df['pnl'])]

            if not symbol_df.empty:
                grp = symbol_df.groupby('symbol')

                symbol_stats = pd.DataFrame({
                    'Trades': grp['pnl'].count(),
                    'Total PnL': grp['pnl'].sum().apply(format_currency),
                    'Avg PnL': grp['pnl'].mean().apply(format_currency),
                    'Win Rate': grp['pnl'].apply(lambda x: format_percentage((x > 0).mean() * 100)),
                })

                st.dataframe(symbol_stats, use_container_width=True)
            else:
                st.warning("⚠️ No valid PnL data found for symbol analysis.")

        except Exception as e:
            st.error(f"❌ Error analyzing symbols: {str(e)}")

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

        # Applying the provided change to the form submission button for mobile responsiveness.
        submitted = st.form_submit_button(
            "💾 Submit Trade", 
            use_container_width=True,
            type="primary"
        )

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