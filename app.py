import streamlit as st
import pandas as pd
from typing import Dict
from fpdf import FPDF

from data_import.futures_importer import FuturesImporter
from data_import.base_importer import REQUIRED_COLUMNS
from data_import.utils import load_trade_data
from analytics import (
    compute_basic_stats,
    performance_over_time,
    histogram_data,
    heatmap_data,
)
import plotly.express as px
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
    hist_df = histogram_data(filtered_df, 'pnl')
    heat_df = heatmap_data(filtered_df, 'symbol', 'direction')

    tab_metrics, tab_visuals, tab_risk = st.tabs(['Performance', 'Visuals', 'Risk'])

    with tab_metrics:
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

        st.subheader('Trades')
        st.dataframe(filtered_df, use_container_width=True)

    with tab_visuals:
        st.subheader('PnL Distribution')
        fig_hist = px.bar(hist_df, x='bin', y='count', labels={'bin': 'PnL', 'count': 'Count'})
        st.plotly_chart(fig_hist, use_container_width=True)

        st.subheader('Trades Heatmap')
        if not heat_df.empty:
            fig_heat = px.imshow(heat_df, text_auto=True, aspect='auto')
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info('Not enough data for heatmap')

    with tab_risk:
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

