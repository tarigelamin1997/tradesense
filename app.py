import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict

from data_import.futures_importer import FuturesImporter
from data_import.base_importer import REQUIRED_COLUMNS
from analytics import compute_basic_stats
from risk_tool import assess_risk
from payment import PaymentGateway

st.set_page_config(page_title="TradeSense", layout="wide")
st.title("TradeSense")
st.caption("Smarter Decisions. Safer Trades.")

st.sidebar.header("Upload Trade History")

sample_file = Path('sample_data/futures_sample.csv')
if sample_file.exists():
    if st.sidebar.checkbox('Use sample data'):
        uploaded_file = open(sample_file, 'rb')
    else:
        uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=['csv','xlsx','xls'])
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel", type=['csv','xlsx','xls'])

importer = FuturesImporter()

if uploaded_file:
    try:
        df = importer.load(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    if not importer.validate_columns(df):
        st.warning('Columns do not match required fields. Map them below:')
        mapping: Dict[str, str] = {}
        for col in REQUIRED_COLUMNS:
            mapping[col] = st.selectbox(f"Column for {col}", options=df.columns, key=col)
        try:
            df = importer.map_columns(df, mapping)
        except Exception as e:
            st.error(str(e))
            st.stop()

    # Parse datetimes
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    stats = compute_basic_stats(df)

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

    st.subheader('Risk Assessment')
    account_size = st.number_input('Account Size', value=10000.0)
    risk_per_trade = st.number_input('Risk % per Trade', value=0.01)
    max_daily_loss = st.number_input('Max Daily Loss', value=500.0)
    if st.button('Assess Risk'):
        risk = assess_risk(df, account_size, risk_per_trade, max_daily_loss)
        st.write(risk)

    st.download_button('Download Cleaned CSV', df.to_csv(index=False), 'cleaned_trades.csv')
else:
    st.info('Upload a trade history file to begin or use the sample data.')

