import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Dict
import psutil
import gc
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
from connectors import load_connectors, ConnectorRegistry
from connectors.registry import registry
from connectors.loader import get_available_connectors, test_connector
from data_validation import DataValidator, create_data_correction_interface
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


@st.cache_data(max_entries=3)  # Limit cache entries to prevent memory buildup
def process_trade_dataframe(df_hash, df_data):
    """Cache expensive data processing operations with graceful handling of missing columns."""
    # Safety check for empty data
    if not df_data:
        raise ValueError("No data provided for processing")

    df = pd.DataFrame(df_data)

    # Safety check for empty DataFrame
    if df.empty:
        raise ValueError("Empty DataFrame after conversion from records")

    # Check which datetime columns are available
    datetime_cols = ['entry_time', 'exit_time']
    available_datetime_cols = [col for col in datetime_cols if col in df.columns]

    # Process available datetime columns with error handling
    try:
        for col in available_datetime_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # Only remove rows with invalid datetime data if we have datetime columns
        if available_datetime_cols:
            original_rows = len(df)
            df = df.dropna(subset=available_datetime_cols)

            if len(df) == 0 and original_rows > 0:
                raise ValueError("No valid datetime data found after processing")

            if len(df) < original_rows:
                # Log information about removed rows
                removed_rows = original_rows - len(df)
                print(f"Removed {removed_rows} rows with invalid datetime data")

        # Calculate P&L if missing but we have price and quantity data
        if 'pnl' not in df.columns:
            required_for_pnl = ['entry_price', 'exit_price', 'qty', 'direction']
            if all(col in df.columns for col in required_for_pnl):
                def calc_pnl(row):
                    try:
                        entry = float(row['entry_price'])
                        exit_price = float(row['exit_price'])
                        qty = float(row['qty'])
                        direction = str(row['direction']).lower()

                        if direction in ['long', 'buy']:
                            return (exit_price - entry) * qty
                        elif direction in ['short', 'sell']:
                            return (entry - exit_price) * qty
                        else:
                            return 0
                    except:
                        return 0

                df['pnl'] = df.apply(calc_pnl, axis=1)

        return df

    except Exception as e:
        raise ValueError(f"Error processing data: {str(e)}")


@st.cache_data(max_entries=3)  # Limit cache entries to prevent memory buildup
def compute_cached_analytics(filtered_df_hash, filtered_df_data):
    """Cache all expensive analytics computations with graceful handling of missing columns."""
    filtered_df = pd.DataFrame(filtered_df_data)

    # Only process P&L if it exists
    if 'pnl' in filtered_df.columns:
        filtered_df['pnl'] = pd.to_numeric(filtered_df['pnl'], errors='coerce')
        filtered_df = filtered_df.dropna(subset=['pnl'])

    if filtered_df.empty:
        return None

    result = {}

    # Compute basic stats if P&L is available
    try:
        if 'pnl' in filtered_df.columns:
            result['stats'] = compute_basic_stats(filtered_df)
        else:
            result['stats'] = {'total_trades': len(filtered_df)}
    except Exception as e:
        result['stats'] = {'total_trades': len(filtered_df), 'error': str(e)}

    # Compute performance over time if datetime columns are available
    try:
        if 'exit_time' in filtered_df.columns and 'pnl' in filtered_df.columns:
            result['perf'] = performance_over_time(filtered_df, freq='M')
        else:
            result['perf'] = pd.DataFrame()
    except Exception as e:
        result['perf'] = pd.DataFrame()

    # Compute KPIs if P&L is available
    try:
        if 'pnl' in filtered_df.columns:
            result['kpis'] = calculate_kpis(filtered_df, commission_per_trade=3.5)
        else:
            result['kpis'] = {'total_trades': len(filtered_df)}
    except Exception as e:
        result['kpis'] = {'total_trades': len(filtered_df), 'error': str(e)}

    return result


def clear_memory_cache():
    """Clear Streamlit cache and force aggressive memory cleanup."""
    try:
        # Get memory before cleanup
        memory_before = None
        try:
            memory_before = psutil.virtual_memory().percent
        except:
            pass
        
        # Clear all Streamlit caches
        st.cache_data.clear()
        
        # Clear session state of large data objects
        keys_to_clear = [
            'merged_df', 'processed_df', 'cached_analytics', 
            'journal_entries', 'show_feedback_modal', 'data_updated'
        ]
        cleared_keys = []
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
                cleared_keys.append(key)
        
        # Clear any cached dataframes or large objects from globals
        import sys
        for name, obj in list(sys.modules[__name__].__dict__.items()):
            if isinstance(obj, pd.DataFrame) and len(obj) > 100:
                del sys.modules[__name__].__dict__[name]
        
        # Multiple rounds of garbage collection
        for _ in range(3):
            gc.collect()
        
        # Get memory after cleanup
        memory_after = None
        try:
            memory_after = psutil.virtual_memory().percent
        except:
            pass
        
        # Calculate memory freed (if available)
        if memory_before is not None and memory_after is not None:
            memory_freed = memory_before - memory_after
            if memory_freed > 0:
                st.sidebar.success(f"✅ Freed {memory_freed:.1f}% memory")
            else:
                st.sidebar.info("✅ Cache cleared (system memory unchanged)")
        else:
            st.sidebar.success("✅ Cache and session data cleared")
        
        # Show what was cleared
        if cleared_keys:
            st.sidebar.info(f"Cleared: {', '.join(cleared_keys)}")
        
        return True
    except Exception as e:
        st.sidebar.error(f"Error clearing cache: {str(e)}")
        return False

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

    # Handle fpdf2 output properly
    try:
        output = pdf.output()
        if isinstance(output, (bytes, bytearray)):
            return bytes(output)
        else:
            return output.encode("latin1")
    except Exception:
        # Fallback for older fpdf versions
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
        pdf.cell(0, 10, "Performance by Symbol", new_x="LMARGIN", new_y="NEXT")
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
        pdf.cell(30, 8, "Win Rate %", border=1, align='C', new_x="LMARGIN", new_y="NEXT")

        # Table data
        for _, row in symbol_stats.head(10).iterrows():  # Limit to top 10 symbols
            pdf.cell(30, 6, str(row['symbol']), border=1, align='C')
            pdf.cell(25, 6, str(int(row['Trades'])), border=1, align='C')
            pdf.cell(35, 6, safe_format_number(row['Total_PnL'], "currency", 2), border=1, align='C')
            pdf.cell(35, 6, safe_format_number(row['Avg_PnL'], "currency", 2), border=1, align='C')
            pdf.cell(30, 6, f"{row['Win_Rate']:.1f}%", border=1, align='C', new_x="LMARGIN", new_y="NEXT")

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

    # Handle fpdf2 output properly
    try:
        output = pdf.output()
        if isinstance(output, (bytes, bytearray)):
            return bytes(output)
        else:
            return output.encode("latin1")
    except Exception:
        # Fallback for older fpdf versions
        return pdf.output(dest="S").encode("latin1")

st.set_page_config(page_title="TradeSense", layout="wide")

# Session ID already initialized above

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

# Initialize session state variables safely
if "show_tour" not in st.session_state:
    st.session_state.show_tour = True

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())[:8]

# Onboarding message shown only on first load
if st.session_state.get("show_tour", True):
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

# Memory monitoring with management controls
try:
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    
    # Always show memory info and cleanup button
    st.sidebar.metric(
        "Memory Usage", 
        f"{memory_usage:.1f}%",
        help=f"RAM: {memory_info.used / (1024**3):.1f}GB / {memory_info.total / (1024**3):.1f}GB"
    )
    
    # Always show cleanup button, but make it more prominent when needed
    if memory_usage > 50:
        if st.sidebar.button("🧹 Clear Cache", help="Clear cache to free memory", key="clear_cache", type="primary"):
            clear_memory_cache()  # Function now handles its own feedback
            st.rerun()
    else:
        if st.sidebar.button("🧹 Clear Cache", help="Clear cache to free memory", key="clear_cache_normal"):
            clear_memory_cache()  # Function now handles its own feedback
            st.rerun()
        
    # Warning for high memory usage
    if memory_usage > 80:
        st.sidebar.error("⚠️ High memory usage! Consider clearing cache.")
    elif memory_usage > 60:
        st.sidebar.warning("⚠️ Memory usage getting high.")
        
except:
    # Fallback cleanup button if psutil not available
    if st.sidebar.button("🧹 Clear Cache", help="Clear cache to free memory", key="clear_cache_fallback"):
        clear_memory_cache()  # Function now handles its own feedback
        st.rerun()

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
        # Check if we have merged data from external CSV upload
        if st.session_state.get('data_updated', False) and 'merged_df' in st.session_state:
            df = st.session_state['merged_df']
            st.session_state['data_updated'] = False  # Reset flag
            st.info(f"📊 **Using merged dataset:** {len(df)} total trades")
        else:
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

    # Analyze column availability instead of blocking
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    available_columns = [col for col in REQUIRED_COLUMNS if col in df.columns]

    if missing_columns:
        # Show warning but continue processing
        st.warning(f"⚠️ **Missing columns:** {', '.join(missing_columns)}")
        st.info(f"📊 **Available columns:** {', '.join(available_columns)}")

        # Show what analytics will be affected
        affected_features = []
        if 'entry_time' not in df.columns or 'exit_time' not in df.columns:
            affected_features.extend(['Time-series analysis', 'Duration analysis', 'Calendar view'])
        if 'pnl' not in df.columns and not all(col in df.columns for col in ['entry_price', 'exit_price', 'qty']):
            affected_features.extend(['P&L analytics', 'Performance metrics'])
        if 'symbol' not in df.columns:
            affected_features.extend(['Symbol-based analysis'])
        if 'direction' not in df.columns:
            affected_features.extend(['Direction-based analysis'])

        if affected_features:
            st.warning(f"📉 **Limited analytics:** {', '.join(affected_features)} will be unavailable.")

        # Offer column mapping option
        with st.expander("🔧 Map Your Columns (Optional)", expanded=False):
            st.write("Map your existing columns to the expected format:")
            mapping: Dict[str, str] = {}

            col_map1, col_map2 = st.columns(2)

            for i, req_col in enumerate(missing_columns):
                with col_map1 if i % 2 == 0 else col_map2:
                    mapping[req_col] = st.selectbox(
                        f"Map '{req_col}' to:", 
                        options=["(Skip)"] + list(df.columns),
                        key=f"map_{req_col}"
                    )

            if st.button("Apply Column Mapping", key="apply_column_mapping"):
                try:
                    # Apply valid mappings
                    for req_col, selected_col in mapping.items():
                        if selected_col != "(Skip)" and selected_col in df.columns:
                            df[req_col] = df[selected_col]

                    # Update missing columns list
                    new_missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
                    if len(new_missing) < len(missing_columns):
                        st.success(f"✅ Successfully mapped {len(missing_columns) - len(new_missing)} columns!")
                        st.rerun()
                    else:
                        st.info("No new columns were mapped.")

                except Exception as e:
                    st.error(f"Error applying mapping: {str(e)}")

    # Keep available columns plus optional ones
    columns_to_keep = [col for col in REQUIRED_COLUMNS if col in df.columns]
    if 'tags' in df.columns:
        columns_to_keep.append('tags')
    if 'notes' in df.columns:
        columns_to_keep.append('notes')

    # Also keep any unmapped columns that might be useful
    useful_columns = ['stop_loss', 'target', 'commission', 'fees', 'spread']
    for col in useful_columns:
        if col in df.columns and col not in columns_to_keep:
            columns_to_keep.append(col)

    df = df[[col for col in columns_to_keep if col in df.columns]]

    if df.empty:
        st.error("❌ No usable data found in the uploaded file.")
        st.stop()

    # Debug: Show initial DataFrame info
    st.write(f"**Debug Info:** Initial DataFrame shape: {df.shape}")
    if not df.empty:
        st.write(f"**Initial columns:** {list(df.columns)}")
    else:
        st.error("❌ **Critical Error:** DataFrame is empty after initial loading!")
        st.error("This suggests an issue with the data loading process.")
        st.stop()

    # Check for datetime columns - warn but don't stop if missing
    datetime_cols_available = [col for col in ['entry_time', 'exit_time'] if col in df.columns]
    missing_datetime_cols = [col for col in ['entry_time', 'exit_time'] if col not in df.columns]

    if missing_datetime_cols:
        st.warning(f"⚠️ **Missing datetime columns:** {', '.join(missing_datetime_cols)}")
        st.info("Time-based analytics will be limited or unavailable.")

        # If both datetime columns are missing, create dummy ones for basic processing
        if not datetime_cols_available:
            st.info("🔧 Creating dummy timestamps to enable basic analytics...")
            df['entry_time'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
            df['exit_time'] = df['entry_time'] + pd.Timedelta(hours=1)
            datetime_cols_available = ['entry_time', 'exit_time']

    # Data Validation and Correction System
    st.subheader("🔍 Data Quality Check")

    validator = DataValidator()

    # Quick quality check with error handling
    with st.spinner("Checking data quality..."):
        try:
            cleaned_df_preview, quick_report = validator.validate_and_clean_data(df.copy(), interactive=False)
            # Don't replace original df yet, just get the report
        except Exception as e:
            st.error(f"❌ **Data validation error:** {str(e)}")
            st.error("Proceeding with original data...")
            quick_report = {
                'data_quality_score': 50.0,
                'issues_found': [f"Validation error: {str(e)}"],
                'corrections_made': [],
                'original_rows': len(df),
                'final_rows': len(df)
            }

    quality_score = quick_report['data_quality_score']

    # Show quality status
    if quality_score >= 90:
        st.success(f"✅ **Excellent Data Quality** ({quality_score:.1f}%) - Ready for analysis!")
        show_validation = st.checkbox("🔧 Advanced Validation Options", value=False)
    elif quality_score >= 70:
        st.warning(f"⚠️ **Good Data Quality** ({quality_score:.1f}%) - Minor issues detected")
        show_validation = st.checkbox("🔧 Review and Fix Issues", value=True)
    else:
        st.error(f"❌ **Data Quality Issues** ({quality_score:.1f}%) - Validation recommended")
        show_validation = st.checkbox("🔧 Fix Data Issues (Recommended)", value=True)

    if show_validation:
        try:
            validated_df = create_data_correction_interface(df, validator)
            # Only update if validation didn't empty the DataFrame and has required columns
            if (not validated_df.empty and 
                len(validated_df.columns) > 0 and 
                all(col in validated_df.columns for col in ['entry_time', 'exit_time'])):
                df = validated_df
                st.success("✅ Data validation complete. Proceeding with analysis...")
            else:
                st.warning("⚠️ Validation resulted in empty DataFrame or missing required columns. Using original data.")
        except Exception as e:
            st.error(f"❌ **Validation error:** {str(e)}")
            st.warning("Using original data instead.")

    # Critical data integrity checks before processing
    if df.empty:
        st.error("❌ **Critical Error:** DataFrame is empty!")
        st.error("**Possible causes:**")
        st.error("• No data was loaded from the file")
        st.error("• Data validation removed all rows")
        st.error("• File format is not compatible")
        st.stop()

    if len(df.columns) == 0:
        st.error("❌ **Critical Error:** DataFrame has no columns!")
        st.error("**Possible causes:**")
        st.error("• File is empty or corrupted")
        st.error("• Data processing removed all columns")
        st.stop()

    # Check for required columns before processing
    required_processing_cols = ['entry_time', 'exit_time']
    missing_cols = [col for col in required_processing_cols if col not in df.columns]

    if missing_cols:
        st.error(f"❌ **Required columns missing:** {', '.join(missing_cols)}")
        st.error(f"**Available columns:** {list(df.columns)}")
        st.error("**Required for analysis:** entry_time, exit_time")
        st.error("Please ensure your data contains the required datetime columns.")
        st.stop()

    st.write(f"**Debug Info:** Final DataFrame shape before processing: {df.shape}")
    st.write(f"**Final columns:** {list(df.columns)}")

    # Optimize data processing with cached operations
    with st.spinner("Processing available data..."):
        try:
            # Use cached data processing with graceful handling
            df_hash = hash(df.to_string())
            df = process_trade_dataframe(df_hash, df.to_dict('records'))

            if df.empty:
                st.error("❌ **No valid rows remain after data processing.**")
                st.error("**Common causes:**")
                st.error("• Invalid data formats in available columns")
                st.error("• All values are missing or invalid")
                st.stop()

        except ValueError as e:
            st.error(f"❌ **Data processing error:** {str(e)}")
            st.error("**Proceeding with limited analytics using available data...**")
            # Continue with original data if processing fails
            pass

    # Simplified filters - only show available columns
    st.header("📊 Filters")
    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        # Symbol filter (only if symbol column exists)
        if 'symbol' in df.columns:
            symbols = st.multiselect('Symbols', options=df['symbol'].unique().tolist(), default=df['symbol'].unique().tolist())
        else:
            symbols = []
            st.info("ℹ️ Symbol filter unavailable (missing 'symbol' column)")

        # Date range filter (only if datetime columns exist)
        if 'entry_time' in df.columns and 'exit_time' in df.columns:
            try:
                min_date = df['entry_time'].min().date() if pd.notna(df['entry_time'].min()) else pd.Timestamp.now().date()
                max_date = df['exit_time'].max().date() if pd.notna(df['exit_time'].max()) else pd.Timestamp.now().date()
                date_range = st.date_input('Date Range', value=[min_date, max_date])
            except:
                date_range = [pd.Timestamp.now().date(), pd.Timestamp.now().date()]
        else:
            date_range = []
            st.info("ℹ️ Date filter unavailable (missing datetime columns)")

    with filter_col2:
        # Direction filter (only if direction column exists)
        if 'direction' in df.columns:
            directions = st.multiselect('Directions', options=df['direction'].unique().tolist(), default=df['direction'].unique().tolist())
        else:
            directions = []
            st.info("ℹ️ Direction filter unavailable (missing 'direction' column)")

        # Tags filter (only if tags column exists)
        if 'tags' in df.columns:
            all_tags = set()
            for tag_string in df['tags'].dropna():
                if tag_string and str(tag_string).strip():
                    all_tags.update([tag.strip() for tag in str(tag_string).split(',')])
            selected_tags = st.multiselect('Tags', options=sorted(all_tags), default=sorted(all_tags))
        else:
            selected_tags = []

    # Apply filters only for available columns
    filtered_df = df.copy()

    # Apply symbol filter
    if 'symbol' in df.columns and symbols:
        filtered_df = filtered_df[filtered_df['symbol'].isin(symbols)]

    # Apply direction filter
    if 'direction' in df.columns and directions:
        filtered_df = filtered_df[filtered_df['direction'].isin(directions)]

    # Apply date range filter
    if 'entry_time' in df.columns and 'exit_time' in df.columns and date_range:
        try:
            filtered_df = filtered_df[
                (filtered_df['entry_time'].dt.date >= date_range[0])
                & (filtered_df['exit_time'].dt.date <= date_range[1])
            ]
        except:
            # Skip date filtering if there's an error
            pass

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

    # Show filter results and merged data notification
    if st.session_state.get('merged_df') is not None:
        st.success(f"🔄 **Analytics Updated:** Showing {len(filtered_df)} of {len(df)} total trades (including imported data)")
    else:
        st.info(f"📈 Showing {len(filtered_df)} of {len(df)} total trades after applying filters")

    st.divider()

    # Use cached expensive calculations with graceful P&L handling
    filtered_df_hash = hash(f"{len(filtered_df)}_{hash(str(symbols))}_{hash(str(directions))}")

    with st.spinner("Computing available analytics..."):
        # Only process P&L if the column exists
        if 'pnl' in filtered_df.columns:
            filtered_df['pnl'] = pd.to_numeric(filtered_df['pnl'], errors='coerce')
            filtered_df = filtered_df.dropna(subset=['pnl'])
        else:
            st.warning("⚠️ P&L column missing - Financial analytics will be limited")

        if filtered_df.empty:
            st.error("No valid trade data found after filtering.")
            st.stop()

        # Use cached analytics computation with error handling
        try:
            cached_results = compute_cached_analytics(filtered_df_hash, filtered_df.to_dict('records'))

            if cached_results is None:
                # Create minimal stats if cached computation fails
                cached_results = {
                    'stats': {'total_trades': len(filtered_df)},
                    'perf': pd.DataFrame(),
                    'kpis': {'total_trades': len(filtered_df)}
                }

            stats = cached_results['stats']
            perf = cached_results['perf']
            kpis = cached_results['kpis']
        except Exception as e:
            st.warning(f"⚠️ Some analytics unavailable due to missing data: {str(e)}")
            # Create basic fallback stats
            stats = {'total_trades': len(filtered_df)}
            perf = pd.DataFrame()
            kpis = {'total_trades': len(filtered_df)}

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

        # Enhanced equity curve generation with robust data cleaning
        try:
            equity_df = filtered_df.copy()

            # Step 1: Ultra-thorough data cleaning
            original_rows = len(equity_df)

            # Clean PnL data with multiple validation layers
            equity_df['pnl'] = pd.to_numeric(equity_df['pnl'], errors='coerce')
            equity_df = equity_df.dropna(subset=['pnl'])

            # Remove infinite, NaN, and extreme values with multiple checks
            equity_df = equity_df[np.isfinite(equity_df['pnl'])]
            equity_df = equity_df[~np.isinf(equity_df['pnl'])]
            equity_df = equity_df[~np.isnan(equity_df['pnl'])]
            equity_df = equity_df[equity_df['pnl'] != np.inf]
            equity_df = equity_df[equity_df['pnl'] != -np.inf]
            equity_df = equity_df[equity_df['pnl'] != float('inf')]
            equity_df = equity_df[equity_df['pnl'] != float('-inf')]

            # Cap extreme values to prevent infinite accumulation
            max_single_trade = 100000  # Cap single trade at $100k
            equity_df['pnl'] = equity_df['pnl'].clip(-max_single_trade, max_single_trade)

            # Step 2: Clean and validate exit_time
            if 'exit_time' in equity_df.columns:
                equity_df['exit_time'] = pd.to_datetime(equity_df['exit_time'], errors='coerce')
                equity_df = equity_df.dropna(subset=['exit_time'])

                # Remove invalid dates with more strict validation
                current_time = pd.Timestamp.now()
                min_valid_date = pd.Timestamp('2000-01-01')
                max_valid_date = current_time + pd.Timedelta(days=7)  # Allow up to 1 week in future

                valid_date_mask = (
                    (equity_df['exit_time'] >= min_valid_date) & 
                    (equity_df['exit_time'] <= max_valid_date) &
                    (equity_df['exit_time'].notna())
                )
                equity_df = equity_df[valid_date_mask]

            # Step 3: Ensure we have valid data for charting
            if equity_df.empty:
                st.warning("⚠️ Unable to display equity curve: No valid trade data after cleaning")
                st.info(f"Started with {original_rows} trades, all were removed during data cleaning")
                st.info("**Common causes:** Invalid P&L values, missing dates, extreme outliers")
            elif len(equity_df) < 2:
                st.warning("⚠️ Unable to display equity curve: Need at least 2 valid trades")
                st.info(f"Available trades after cleaning: {len(equity_df)} of {original_rows}")
            else:
                # Step 4: Sort and create cumulative PnL with additional safety
                equity_df = equity_df.sort_values('exit_time')
                equity_df = equity_df.reset_index(drop=True)

                # Calculate cumulative PnL with overflow protection
                running_total = 0
                cumulative_values = []

                for pnl in equity_df['pnl']:
                    running_total += pnl
                    # Check for overflow/underflow
                    if abs(running_total) > 1e10:  # 10 billion limit
                        running_total = np.sign(running_total) * 1e10
                    cumulative_values.append(running_total)

                equity_df['cumulative_pnl'] = cumulative_values

                # Final validation of cumulative values
                equity_df = equity_df[np.isfinite(equity_df['cumulative_pnl'])]
                equity_df = equity_df[~np.isinf(equity_df['cumulative_pnl'])]

                if not equity_df.empty and len(equity_df) >= 2:
                    # Step 5: Create chart data with additional safety measures
                    chart_data = equity_df.set_index('exit_time')['cumulative_pnl']

                    # Remove any remaining infinite values
                    chart_data = chart_data[np.isfinite(chart_data)]
                    chart_data = chart_data[~np.isinf(chart_data)]

                    # Handle duplicate timestamps by keeping the last value
                    chart_data = chart_data[~chart_data.index.duplicated(keep='last')]

                    # Ensure index is properly formatted datetime
                    chart_data.index = pd.to_datetime(chart_data.index)

                    # Final check before plotting
                    if len(chart_data) >= 2 and chart_data.index.notna().all():
                        # Display summary info
                        starting_value = chart_data.iloc[0]
                        ending_value = chart_data.iloc[-1]
                        total_return = ending_value - starting_value

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Starting P&L", f"${starting_value:,.2f}")
                        col2.metric("Ending P&L", f"${ending_value:,.2f}")
                        col3.metric("Total Return", f"${total_return:,.2f}")

                        # Plot the equity curve
                        st.line_chart(chart_data, height=400)

                        st.caption(f"📊 Equity curve based on {len(equity_df)} valid trades")
                    else:
                        st.warning("⚠️ Unable to display equity curve: Invalid chart data after final validation")
                        st.info(f"Chart data points: {len(chart_data)}")
                else:
                    st.warning("⚠️ Unable to display equity curve: No valid cumulative P&L data")
                    st.info(f"Trades before cumulative calculation: {len(equity_df)}")

        except Exception as e:
            st.error(f"❌ Error generating equity curve: {str(e)}")
            st.info("**Troubleshooting:** Try using the data validation tool above to clean your data")
            # Log the error for debugging
            import traceback
            st.expander("Technical Details").code(traceback.format_exc())

        st.subheader('Performance Over Time')
        try:
            if not perf.empty and len(perf) >= 2:
                # Clean the performance data more thoroughly
                clean_perf = perf.copy()
                clean_perf['pnl'] = pd.to_numeric(clean_perf['pnl'], errors='coerce')
                clean_perf = clean_perf.dropna(subset=['pnl'])
                clean_perf = clean_perf[np.isfinite(clean_perf['pnl'])]
                clean_perf = clean_perf[clean_perf['pnl'] != np.inf]
                clean_perf = clean_perf[clean_perf['pnl'] != -np.inf]

                if not clean_perf.empty and len(clean_perf) >= 2:
                    chart_data = clean_perf.set_index('period')['pnl']
                    st.bar_chart(chart_data)
                else:
                    st.warning("⚠️ Unable to display performance chart: Insufficient valid data points after cleaning")
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

        # Rolling metrics with better validation
        min_trades_for_rolling = 15  # Need more than the window size for meaningful analysis
        if len(filtered_df) >= min_trades_for_rolling:
            rolling = rolling_metrics(filtered_df, window=10)
            try:
                if not rolling.empty and len(rolling) >= 2:
                    st.subheader('Rolling Metrics (10-trade windows)')

                    # Display metrics summary
                    col_r1, col_r2, col_r3 = st.columns(3)
                    col_r1.metric('Rolling Periods', len(rolling))
                    if not rolling.empty:
                        avg_win_rate = rolling['win_rate'].mean()
                        avg_pf = rolling['profit_factor'].mean()
                        col_r2.metric('Avg Rolling Win Rate', f"{avg_win_rate:.1f}%")
                        col_r3.metric('Avg Rolling PF', f"{avg_pf:.2f}")

                    # Clean chart data
                    chart_data = rolling.set_index('end_index')[['win_rate', 'profit_factor']].copy()

                    # Replace infinite values and clean data
                    chart_data = chart_data.replace([np.inf, -np.inf], np.nan)
                    chart_data = chart_data.dropna()

                    if not chart_data.empty and len(chart_data) >= 2:
                        st.line_chart(chart_data, height=400)
                    else:
                        st.warning("⚠️ Unable to display rolling metrics chart: Insufficient valid data points after cleaning")
                        st.info(f"Rolling data generated: {len(rolling)} periods, Chart data after cleaning: {len(chart_data)}")
                else:
                    st.warning(f"⚠️ Unable to generate rolling metrics: Generated {len(rolling)} rolling periods (need at least 2)")
                    st.info(f"Available trades: {len(filtered_df)}, Required for rolling analysis: {min_trades_for_rolling}")

            except Exception as e:
                st.error(f"❌ Error generating rolling metrics chart: {str(e)}")
                logger.error(f"Rolling metrics error: {str(e)}")
        else:
            st.info(f"ℹ️ Rolling metrics analysis requires at least {min_trades_for_rolling} trades. You have {len(filtered_df)} trades.")
            st.caption("Add more trades to see rolling performance analysis over 10-trade windows.")

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

    # Connector Management Section
    st.subheader('🔌 Data Connectors')
    
    # Load available connectors
    if 'connectors_loaded' not in st.session_state:
        with st.spinner("Loading connectors..."):
            load_results = load_connectors()
            st.session_state.connectors_loaded = True
            if load_results['errors']:
                st.warning(f"⚠️ {len(load_results['errors'])} connector loading errors")
                with st.expander("View Errors"):
                    for error in load_results['errors']:
                        st.error(f"File: {error['file']} - {error['error']}")
    
    # Connector selection and management
    with st.expander("🔧 Connector Manager", expanded=False):
        available_connectors = get_available_connectors()
        
        if available_connectors:
            st.write(f"**Available Connectors:** {len(available_connectors)}")
            
            connector_options = [f"{conn['name']} ({conn.get('type', 'unknown')})" 
                               for conn in available_connectors if 'error' not in conn]
            
            if connector_options:
                selected_connector = st.selectbox(
                    "Select Connector:",
                    options=[""] + connector_options,
                    help="Choose a connector to import trade data"
                )
                
                if selected_connector:
                    connector_name = selected_connector.split(' (')[0]
                    
                    # Get connector instance for configuration
                    try:
                        instance = registry.create_instance(connector_name)
                        metadata = instance.get_metadata()
                        
                        st.write(f"**Connector Type:** {metadata['type']}")
                        st.write(f"**Supported Formats:** {', '.join(metadata['supported_formats'])}")
                        
                        # Configuration form
                        if metadata['config_required']:
                            st.write("**Required Configuration:**")
                            config = {}
                            
                            for config_key in metadata['config_required']:
                                if config_key == 'file_path':
                                    uploaded_file = st.file_uploader(
                                        f"Upload {metadata['supported_formats'][0].upper()} file",
                                        type=metadata['supported_formats'],
                                        key=f"connector_{connector_name}_file"
                                    )
                                    if uploaded_file:
                                        # Save uploaded file temporarily
                                        import tempfile
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                                            tmp_file.write(uploaded_file.getvalue())
                                            config['file_path'] = tmp_file.name
                                else:
                                    config[config_key] = st.text_input(
                                        f"{config_key.replace('_', ' ').title()}:",
                                        key=f"connector_{connector_name}_{config_key}",
                                        type="password" if "secret" in config_key.lower() or "key" in config_key.lower() else "default"
                                    )
                            
                            # Test connection and import data
                            col_test, col_import = st.columns(2)
                            
                            with col_test:
                                if st.button("🔍 Test Connection", key=f"test_{connector_name}"):
                                    if all(config.values()):
                                        with st.spinner("Testing connection..."):
                                            # Authenticate
                                            auth_success = instance.authenticate(config)
                                            if auth_success:
                                                # Test data quality
                                                test_result = test_connector(connector_name, config)
                                                
                                                if test_result['connection_status'] == 'ok':
                                                    st.success("✅ Connection successful!")
                                                    
                                                    quality = test_result['quality_report']
                                                    if quality['status'] == 'success':
                                                        st.success(f"📊 Sample data: {quality['sample_size']} trades")
                                                        if quality['missing_required']:
                                                            st.warning(f"⚠️ Missing columns: {', '.join(quality['missing_required'])}")
                                                    else:
                                                        st.error(f"❌ Data quality issue: {quality.get('message', 'Unknown error')}")
                                                else:
                                                    st.error("❌ Connection failed")
                                            else:
                                                st.error("❌ Authentication failed")
                                    else:
                                        st.warning("Please fill in all required configuration fields")
                            
                            with col_import:
                                if st.button("📥 Import Data", key=f"import_{connector_name}", type="primary"):
                                    if all(config.values()):
                                        with st.spinner("Importing trade data..."):
                                            try:
                                                # Authenticate and fetch data
                                                auth_success = instance.authenticate(config)
                                                if auth_success:
                                                    raw_trades = instance.fetch_trades()
                                                    if raw_trades:
                                                        normalized_df = instance.normalize_data(raw_trades)
                                                        
                                                        if not normalized_df.empty:
                                                            # Clear old cache
                                                            st.cache_data.clear()
                                                            
                                                            # Merge with existing data if available
                                                            if 'merged_df' in st.session_state or not df.empty:
                                                                existing_df = st.session_state.get('merged_df', df)
                                                                merged_df = pd.concat([existing_df, normalized_df], ignore_index=True)
                                                                st.session_state['merged_df'] = merged_df
                                                            else:
                                                                st.session_state['merged_df'] = normalized_df
                                                            
                                                            st.session_state['data_updated'] = True
                                                            
                                                            st.success(f"🎉 Imported {len(normalized_df)} trades from {connector_name}")
                                                            st.info("🔄 Page will refresh to show updated analytics...")
                                                            st.rerun()
                                                        else:
                                                            st.warning("No valid trade data found after normalization")
                                                    else:
                                                        st.warning("No trade data available from connector")
                                                else:
                                                    st.error("Authentication failed")
                                            except Exception as e:
                                                st.error(f"Import error: {str(e)}")
                                    else:
                                        st.warning("Please complete configuration first")
                        else:
                            st.info("No configuration required for this connector")
                            
                    except Exception as e:
                        st.error(f"Error loading connector: {str(e)}")
            else:
                st.warning("No working connectors available")
        else:
            st.warning("No connectors found. Check connector loading errors above.")
    
    # External CSV Upload Section
    st.subheader('📂 Import External CSV Trades')

    with st.expander("Import CSV Trade Data", expanded=False):
        st.write("Upload a CSV file with your trade history to merge with existing data.")

        external_csv = st.file_uploader(
            "Choose CSV file", 
            type=['csv'], 
            key="external_csv_upload",
            help="Upload CSV with columns: symbol, entry_time, exit_time, entry_price, exit_price, qty, direction, pnl, trade_type, broker"
        )

        if external_csv is not None:
            try:
                # Load and validate external CSV
                external_df = pd.read_csv(external_csv)

                st.write(f"📊 **File loaded:** {len(external_df)} rows found")

                # Perform data quality analysis first
                quality_report = importer.validate_data_quality(external_df)

                if quality_report['issues']:
                    st.error("**🚨 Critical Data Issues Found:**")
                    for issue in quality_report['issues']:
                        st.error(f"• {issue}")
                    st.stop()

                if quality_report['warnings']:
                    st.warning("**⚠️ Data Quality Warnings:**")
                    for warning in quality_report['warnings']:
                        st.warning(f"• {warning}")

                    estimated_valid = quality_report['valid_rows']
                    total_rows = quality_report['total_rows']
                    if estimated_valid < total_rows:
                        st.info(f"📈 **Estimated valid trades after cleaning:** {estimated_valid} of {total_rows} ({(estimated_valid/total_rows*100):.1f}%)")

                st.write("**Column validation:**")

                # Check for required columns
                missing_cols = []
                for col in REQUIRED_COLUMNS:
                    if col in external_df.columns:
                        st.success(f"✅ {col}")
                    else:
                        st.error(f"❌ {col} - Missing")
                        missing_cols.append(col)

                if missing_cols:
                    st.warning(f"**Missing required columns:** {', '.join(missing_cols)}")
                    st.write("**Available columns in your file:**")
                    st.write(list(external_df.columns))

                    # Allow column mapping
                    st.write("**Map your columns to required format:**")
                    column_mapping = {}

                    map_col1, map_col2 = st.columns(2)

                    with map_col1:
                        for i, req_col in enumerate(missing_cols[:5]):  # First 5 missing
                            column_mapping[req_col] = st.selectbox(
                                f"Map '{req_col}' to:", 
                                options=[""] + list(external_df.columns),
                                key=f"map_{req_col}"
                            )

                    with map_col2:
                        for i, req_col in enumerate(missing_cols[5:]):  # Remaining missing
                            column_mapping[req_col] = st.selectbox(
                                f"Map '{req_col}' to:", 
                                options=[""] + list(external_df.columns),
                                key=f"map_{req_col}"
                            )

                    # Apply column mapping
                    if st.button("Apply Column Mapping", key="apply_mapping"):
                        if all(mapping for mapping in column_mapping.values()):
                            try:
                                # Rename columns based on mapping
                                external_df = external_df.rename(columns={v: k for k, v in column_mapping.items() if v})

                                # Recheck validation
                                if importer.validate_columns(external_df):
                                    st.success("✅ Column mapping successful!")
                                    missing_cols = []  # Clear missing columns
                                else:
                                    still_missing = [col for col in REQUIRED_COLUMNS if col not in external_df.columns]
                                    st.error(f"❌ Still missing: {', '.join(still_missing)}")
                            except Exception as e:
                                st.error(f"Error applying mapping: {str(e)}")
                        else:
                            st.warning("Please map all missing columns before proceeding.")

                # If validation passes, proceed with data processing
                if not missing_cols:
                    # Clean and standardize external data
                    try:
                        # Store original row count for reporting
                        original_rows = len(external_df)

                        # Keep only required columns plus optional ones
                        columns_to_keep = REQUIRED_COLUMNS.copy()
                        if 'tags' in external_df.columns:
                            columns_to_keep.append('tags')
                        if 'notes' in external_df.columns:
                            columns_to_keep.append('notes')

                        external_df = external_df[[col for col in columns_to_keep if col in external_df.columns]]

                        # Add missing optional columns
                        if 'tags' not in external_df.columns:
                            external_df['tags'] = ''
                        if 'notes' not in external_df.columns:
                            external_df['notes'] = ''

                        # Data quality check and cleaning
                        st.write("**🔍 Data Quality Analysis:**")

                        # Check for missing values in required columns
                        missing_data_report = []
                        for col in REQUIRED_COLUMNS:
                            if col in external_df.columns:
                                null_count = external_df[col].isna().sum()
                                empty_count = (external_df[col] == '').sum() if external_df[col].dtype == 'object' else 0
                                total_missing = null_count + empty_count
                                if total_missing > 0:
                                    missing_data_report.append(f"• {col}: {total_missing} missing values ({(total_missing/len(external_df)*100):.1f}%)")

                        if missing_data_report:
                            st.warning("**⚠️ Found missing data:**")
                            for report in missing_data_report:
                                st.write(report)
                        else:
                            st.success("✅ No missing data detected in required columns")

                        # Clean and validate data step by step
                        cleaning_steps = []

                        # 1. Clean symbol column
                        if 'symbol' in external_df.columns:
                            before_symbol = len(external_df)
                            external_df = external_df[external_df['symbol'].notna() & (external_df['symbol'] != '')]
                            external_df['symbol'] = external_df['symbol'].astype(str).str.strip().str.upper()
                            after_symbol = len(external_df)
                            if before_symbol != after_symbol:
                                cleaning_steps.append(f"Removed {before_symbol - after_symbol} rows with missing symbols")

                        # 2. Process and validate dates
                        if 'entry_time' in external_df.columns and 'exit_time' in external_df.columns:
                            before_dates = len(external_df)
                            external_df['entry_time'] = pd.to_datetime(external_df['entry_time'], errors='coerce')
                            external_df['exit_time'] = pd.to_datetime(external_df['exit_time'], errors='coerce')
                            external_df = external_df.dropna(subset=['entry_time', 'exit_time'])

                            # Remove trades where exit time is before entry time
                            invalid_dates = external_df['exit_time'] <= external_df['entry_time']
                            external_df = external_df[~invalid_dates]
                            after_dates = len(external_df)

                            if before_dates != after_dates:
                                cleaning_steps.append(f"Removed {before_dates - after_dates} rows with invalid dates")

                        # 3. Clean price data
                        price_columns = ['entry_price', 'exit_price']
                        for col in price_columns:
                            if col in external_df.columns:
                                before_price = len(external_df)
                                external_df[col] = pd.to_numeric(external_df[col], errors='coerce')
                                external_df = external_df[external_df[col] > 0]  # Prices must be positive
                                after_price = len(external_df)
                                if before_price != after_price:
                                    cleaning_steps.append(f"Removed {before_price - after_price} rows with invalid {col}")

                        # 4. Clean quantity data
                        if 'qty' in external_df.columns:
                            before_qty = len(external_df)
                            external_df['qty'] = pd.to_numeric(external_df['qty'], errors='coerce')
                            external_df = external_df[external_df['qty'] > 0]  # Quantity must be positive
                            after_qty = len(external_df)
                            if before_qty != after_qty:
                                cleaning_steps.append(f"Removed {before_qty - after_qty} rows with invalid quantity")

                        # 5. Validate direction
                        if 'direction' in external_df.columns:
                            before_direction = len(external_df)
                            external_df['direction'] = external_df['direction'].astype(str).str.lower().str.strip()
                            valid_directions = external_df['direction'].isin(['long', 'short', 'buy', 'sell'])
                            external_df = external_df[valid_directions]
                            # Standardize direction values
                            external_df['direction'] = external_df['direction'].replace({'buy': 'long', 'sell': 'short'})
                            after_direction = len(external_df)
                            if before_direction != after_direction:
                                cleaning_steps.append(f"Removed {before_direction - after_direction} rows with invalid direction")

                        # 6. Clean PnL data (if present, otherwise calculate it)
                        if 'pnl' in external_df.columns:
                            before_pnl = len(external_df)
                            external_df['pnl'] = pd.to_numeric(external_df['pnl'], errors='coerce')
                            external_df = external_df.dropna(subset=['pnl'])
                            # Remove infinite values
                            external_df = external_df[np.isfinite(external_df['pnl'])]
                            after_pnl = len(external_df)
                            if before_pnl != after_pnl:
                                cleaning_steps.append(f"Removed {before_pnl - after_pnl} rows with invalid P&L")
                        else:
                            # Calculate P&L if missing
                            if all(col in external_df.columns for col in ['entry_price', 'exit_price', 'qty', 'direction']):
                                def calculate_pnl(row):
                                    if row['direction'] == 'long':
                                        return (row['exit_price'] - row['entry_price']) * row['qty']
                                    else:  # short
                                        return (row['entry_price'] - row['exit_price']) * row['qty']

                                external_df['pnl'] = external_df.apply(calculate_pnl, axis=1)
                                cleaning_steps.append("Calculated P&L from price and quantity data")

                        # 7. Fill missing optional fields with defaults
                        if 'trade_type' not in external_df.columns or external_df['trade_type'].isna().all():
                            external_df['trade_type'] = 'manual'
                            cleaning_steps.append("Set trade_type to 'manual' for missing values")

                        if 'broker' not in external_df.columns or external_df['broker'].isna().all():
                            external_df['broker'] = 'imported'
                            cleaning_steps.append("Set broker to 'imported' for missing values")

                        # Report cleaning results
                        final_rows = len(external_df)
                        rows_removed = original_rows - final_rows

                        if rows_removed > 0:
                            st.warning(f"⚠️ **Data Cleaning Results:** Removed {rows_removed} of {original_rows} rows ({(rows_removed/original_rows*100):.1f}%)")
                            if cleaning_steps:
                                st.write("**Cleaning steps performed:**")
                                for step in cleaning_steps:
                                    st.write(f"• {step}")
                        else:
                            st.success("✅ **All data passed validation** - No rows removed")

                        if final_rows == 0:
                            st.error("❌ **No valid trades remaining after data cleaning**")
                            st.error("**Common issues to check:**")
                            st.error("• Ensure dates are in a recognizable format (YYYY-MM-DD or MM/DD/YYYY)")
                            st.error("• Verify prices and quantities are positive numbers")
                            st.error("• Check that direction is 'long', 'short', 'buy', or 'sell'")
                            st.error("• Make sure entry_time is before exit_time")
                            st.stop()

                        st.success(f"✅ **Data cleaned:** {final_rows} valid trades ready for import")

                        # Show preview with data quality indicators
                        st.write("**Preview of cleaned data:**")
                        preview_df = external_df.head(10).copy()

                        # Add data quality indicators to preview
                        if len(preview_df) > 0:
                            st.dataframe(preview_df, use_container_width=True)

                            # Show data types for verification
                            with st.expander("📋 Data Types Verification"):
                                st.write("**Column data types after cleaning:**")
                                for col in external_df.columns:
                                    if col in REQUIRED_COLUMNS:
                                        dtype_info = f"• {col}: {external_df[col].dtype}"
                                        if col in ['entry_time', 'exit_time']:
                                            dtype_info += f" (Valid dates: {external_df[col].notna().sum()})"
                                        elif col in ['entry_price', 'exit_price', 'qty', 'pnl']:
                                            dtype_info += f" (Valid numbers: {external_df[col].notna().sum()})"
                                        st.write(dtype_info)

                        # Merge with existing data
                        if st.button("🔄 Merge with Existing Trades", key="merge_data", type="primary"):
                            try:
                                # Create a unique identifier for duplicate detection
                                def create_trade_id(row):
                                    return f"{row['symbol']}_{row['entry_time']}_{row['exit_time']}_{row['entry_price']}_{row['exit_price']}"

                                # Add IDs to both dataframes
                                external_df['trade_id'] = external_df.apply(create_trade_id, axis=1)
                                df['trade_id'] = df.apply(create_trade_id, axis=1)

                                # Find duplicates
                                duplicates = external_df[external_df['trade_id'].isin(df['trade_id'])]
                                unique_external = external_df[~external_df['trade_id'].isin(df['trade_id'])]

                                if len(duplicates) > 0:
                                    st.warning(f"⚠️ Found {len(duplicates)} duplicate trades (will be skipped)")
                                    with st.expander("View Duplicates"):
                                        st.dataframe(duplicates[['symbol', 'entry_time', 'exit_time', 'pnl']], use_container_width=True)

                                if len(unique_external) > 0:
                                    # Merge unique trades
                                    merged_df = pd.concat([df.drop('trade_id', axis=1), unique_external.drop('trade_id', axis=1)], ignore_index=True)

                                    st.success(f"🎉 **Merge Complete!**")
                                    st.success(f"• Added {len(unique_external)} new trades")
                                    st.success(f"• Skipped {len(duplicates)} duplicates") 
                                    st.success(f"• Total trades: {len(merged_df)}")

                                    # Clear old cache before saving new data
                                    st.cache_data.clear()
                                    
                                    # Save merged data to session state to trigger re-analysis
                                    st.session_state['merged_df'] = merged_df
                                    st.session_state['data_updated'] = True

                                    # Force garbage collection after data operations
                                    gc.collect()

                                    st.info("🔄 **Page will refresh to show updated analytics...**")
                                    st.rerun()

                                else:
                                    st.warning("❌ No new trades to add (all were duplicates)")

                            except Exception as e:
                                st.error(f"❌ Error during merge: {str(e)}")
                                st.error("Please check your data format and try again.")

                    except Exception as e:
                        st.error(f"❌ Error processing external data: {str(e)}")
                        st.write("Please check your CSV format and data types.")

            except Exception as e:
                st.error(f"❌ Error loading CSV file: {str(e)}")
                st.write("Please ensure your file is a valid CSV format.")

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