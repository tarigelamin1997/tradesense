import streamlit as st
import pandas as pd
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
)
from risk_tool import assess_risk
from payment import PaymentGateway


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

st.set_page_config(page_title="TradeSense", layout="wide")
st.title("TradeSense")
st.caption("Smarter Decisions. Safer Trades.")

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

theme = st.sidebar.selectbox("Theme", ["Light", "Dark"], index=0)
if theme == "Dark":
    st.markdown(
        "<style>body {background-color: #111;color: #eee;}</style>",
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

    if importer.validate_columns(df):
        df = df[REQUIRED_COLUMNS]
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

    st.sidebar.subheader("Filters")
    symbols = st.sidebar.multiselect('Symbol', options=df['symbol'].unique().tolist(), default=df['symbol'].unique().tolist())
    directions = st.sidebar.multiselect('Direction', options=df['direction'].unique().tolist(), default=df['direction'].unique().tolist())
    brokers = st.sidebar.multiselect('Broker', options=df['broker'].unique().tolist(), default=df['broker'].unique().tolist())
    date_range = st.sidebar.date_input(
        'Date range',
        value=[df['entry_time'].min().date(), df['exit_time'].max().date()],
    )

    filtered_df = df[
        df['symbol'].isin(symbols)
        & df['direction'].isin(directions)
        & df['broker'].isin(brokers)
        & (df['entry_time'].dt.date >= date_range[0])
        & (df['exit_time'].dt.date <= date_range[1])
    ]

    stats = compute_basic_stats(filtered_df)
    perf = performance_over_time(filtered_df, freq='M')

    overview_tab, symbol_tab, drawdown_tab, calendar_tab, journal_tab = st.tabs(
        ["Overview", "Symbols", "Drawdowns", "Calendar", "Journal"]
    )

    with overview_tab:
        st.subheader('Performance Metrics')
        col1, col2, col3 = st.columns(3)
        col1.metric('Win Rate %', f"{stats['win_rate']:.2f}")
        col1.metric('Profit Factor', f"{stats['profit_factor']:.2f}")
        col2.metric('Expectancy', f"{stats['expectancy']:.2f}")
        col2.metric('Max Drawdown', f"{stats['max_drawdown']:.2f}")
        col3.metric('Sharpe Ratio', f"{stats['sharpe_ratio']:.2f}")
        col3.metric('Reward:Risk', f"{stats['reward_risk']:.2f}")

        st.subheader('Equity Curve')
        st.line_chart(stats['equity_curve'])

        st.subheader('Performance Over Time')
        st.bar_chart(perf.set_index('period')['pnl'])

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
        grp = filtered_df.groupby('symbol')
        symbol_stats = pd.DataFrame({
            'Trades': grp['pnl'].count(),
            'Total PnL': grp['pnl'].sum(),
            'Avg PnL': grp['pnl'].mean(),
            'Win Rate %': grp.apply(lambda g: (g['pnl'] > 0).mean() * 100),
        })
        st.dataframe(symbol_stats, use_container_width=True)

    with drawdown_tab:
        equity = stats['equity_curve']
        drawdown = equity.cummax() - equity
        fig = px.area(x=drawdown.index, y=drawdown.values,
                      labels={'x': 'Trade', 'y': 'Drawdown'})
        st.plotly_chart(fig, use_container_width=True)

    with calendar_tab:
        daily_pnl = filtered_df.groupby(filtered_df['exit_time'].dt.date)['pnl'].sum()
        cal_df = daily_pnl.reset_index()
        cal_df.columns = ['date', 'pnl']
        cal_df['date'] = pd.to_datetime(cal_df['date'])
        cal_df['month'] = cal_df['date'].dt.month
        cal_df['day'] = cal_df['date'].dt.day
        pivot = cal_df.pivot(index='day', columns='month', values='pnl')
        fig = px.imshow(pivot, labels={'x': 'Month', 'y': 'Day', 'color': 'PnL'},
                        aspect='auto')
        st.plotly_chart(fig, use_container_width=True)

    with journal_tab:
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

    st.download_button('Download Cleaned CSV', df.to_csv(index=False), 'cleaned_trades.csv')
else:
    st.info('Upload a trade history file to begin.')

