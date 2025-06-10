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
        /* Light Theme - Root Application */
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        .main .block-container {
            background-color: #ffffff !important;
        }

        /* Fix main title and all headers */
        [data-testid="stHeader"] h1 {
            color: #262730 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #262730 !important;
        }
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6 {
            color: #262730 !important;
        }

        /* Fix all text content */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] div,
        [data-testid="stText"] div,
        .stMarkdown div,
        .stText div {
            color: #262730 !important;
        }

        /* Fix caption text */
        [data-testid="stCaptionContainer"] p,
        .stCaption div {
            color: #666666 !important;
        }

        /* Sidebar comprehensive styling */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6 !important;
        }
        [data-testid="stSidebar"] * {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {
            color: #262730 !important;
        }

        /* Sidebar form elements */
        [data-testid="stSidebar"] [data-baseweb="select"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] span {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            fill: #262730 !important;
        }
        [data-testid="stSidebar"] input {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }

        /* Fix dropdown menus in sidebar */
        [data-testid="stSidebar"] [data-baseweb="popover"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stSidebar"] [data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        [data-testid="stSidebar"] [data-baseweb="menu"] li {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="menu"] li:hover {
            background-color: #e3f2fd !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="menu"] li[aria-selected="true"] {
            background-color: #bbdefb !important;
            color: #262730 !important;
        }

        /* Main content form elements */
        [data-baseweb="select"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        [data-baseweb="select"] span {
            color: #262730 !important;
        }
        [data-baseweb="select"] div {
            color: #262730 !important;
        }
        [data-baseweb="select"] svg {
            fill: #262730 !important;
        }
        input[type="text"], input[type="number"], textarea {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }

        /* Fix all labels */
        label {
            color: #262730 !important;
        }

        /* Fix metrics */
        [data-testid="metric-container"] {
            background-color: #f8f9fa !important;
            color: #262730 !important;
            border: 1px solid #e9ecef !important;
        }
        [data-testid="metric-container"] * {
            color: #262730 !important;
        }

        /* Fix tabs */
        [data-baseweb="tab-list"] {
            background-color: #f0f2f6 !important;
        }
        [data-baseweb="tab"] {
            color: #262730 !important;
        }
        [data-baseweb="tab"][aria-selected="true"] {
            color: #262730 !important;
            background-color: #ffffff !important;
        }

        /* Fix buttons */
        .stButton button {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        .stButton button:hover {
            background-color: #f8f9fa !important;
            color: #262730 !important;
        }

        /* Fix expanders */
        [data-testid="stExpander"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stExpander"] * {
            color: #262730 !important;
        }

        /* Fix dataframes */
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
        }
        [data-testid="stDataFrame"] * {
            color: #262730 !important;
        }

        /* Fix charts */
        .js-plotly-plot .plotly text {
            fill: #262730 !important;
        }

        /* CRITICAL FIX: Dropdown options with proper contrast */
        [data-baseweb="popover"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        [data-baseweb="menu"] {
            background-color: #ffffff !important;
        }
        [data-baseweb="menu"] li {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-baseweb="menu"] li:hover {
            background-color: #e3f2fd !important;
            color: #262730 !important;
        }
        [data-baseweb="menu"] li[aria-selected="true"] {
            background-color: #bbdefb !important;
            color: #262730 !important;
        }

        /* Fix multi-select tags/pills */
        [data-baseweb="tag"] {
            background-color: #e9ecef !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        [data-baseweb="tag"] span {
            color: #262730 !important;
        }
        [data-baseweb="tag"] svg {
            fill: #262730 !important;
        }

        /* Fix multi-select container and input */
        [data-baseweb="select"] [data-baseweb="input"] {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-baseweb="select"] [data-baseweb="input"] input {
            color: #262730 !important;
        }

        /* Fix multi-select dropdown options */
        [data-baseweb="list"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-baseweb="list-item"] {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-baseweb="list-item"]:hover {
            background-color: #e3f2fd !important;
            color: #262730 !important;
        }
        [data-baseweb="list-item"][aria-selected="true"] {
            background-color: #bbdefb !important;
            color: #262730 !important;
        }

        /* Fix checkbox in multi-select */
        [data-baseweb="checkbox"] {
            border-color: #cccccc !important;
            background-color: #ffffff !important;
        }
        [data-baseweb="checkbox"]:checked {
            background-color: #007bff !important;
            border-color: #007bff !important;
        }
        [data-baseweb="checkbox"] svg {
            fill: #ffffff !important;
        }

        /* Fix single select dropdown options */
        [data-baseweb="popover"] [data-baseweb="list"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-baseweb="popover"] [data-baseweb="list-item"] {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-baseweb="popover"] [data-baseweb="list-item"]:hover {
            background-color: #e3f2fd !important;
            color: #262730 !important;
        }
        [data-baseweb="popover"] [data-baseweb="list-item"][aria-selected="true"] {
            background-color: #bbdefb !important;
            color: #262730 !important;
        }

        /* File uploader - Fix drag and drop area */
        [data-testid="stFileUploader"] {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stFileUploader"] * {
            color: #262730 !important;
        }
        [data-testid="stFileUploader"] section {
            background-color: #f8f9fa !important;
            border: 2px dashed #cccccc !important;
            color: #262730 !important;
        }
        [data-testid="stFileUploader"] section * {
            color: #262730 !important;
        }
        [data-testid="stFileUploader"] button {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }

        /* Checkbox */
        [data-testid="stCheckbox"] label {
            color: #262730 !important;
        }
        [data-testid="stCheckbox"] input[type="checkbox"] {
            accent-color: #007bff !important;
        }

        /* Fix clear buttons and X buttons */
        button[aria-label*="Clear"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        button[aria-label*="Clear"]:hover {
            background-color: #f8f9fa !important;
            color: #262730 !important;
        }
        [data-baseweb="tag"] button {
            color: #262730 !important;
        }
        [data-baseweb="tag"] button:hover {
            background-color: #dee2e6 !important;
            color: #262730 !important;
        }

        /* Additional overrides for BaseWeb components */
        div[data-baseweb="base-input"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        div[data-baseweb="base-input"] input {
            color: #262730 !important;
        }

        /* Fix for theme selector specifically */
        [data-testid="stSidebar"] div[role="listbox"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stSidebar"] div[role="option"] {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] div[role="option"]:hover {
            background-color: #e3f2fd !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] div[role="option"][aria-selected="true"] {
            background-color: #bbdefb !important;
            color: #262730 !important;
        }

        /* CRITICAL: Fix BaseWeb dropdown visibility issues */
        /* Target all BaseWeb popover content globally */
        [data-baseweb="popover"] [data-baseweb="popover-content"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }

        /* Target BaseWeb select dropdowns specifically */
        [data-baseweb="select"] [data-baseweb="popover"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-baseweb="select"] [data-baseweb="popover"] * {
            color: #262730 !important;
        }

        /* Fix dropdown arrow and controls */
        [data-baseweb="select"] [data-baseweb="select-arrow"] {
            fill: #262730 !important;
        }
        [data-baseweb="select"] [data-baseweb="select-arrow"] svg {
            fill: #262730 !important;
        }
        [data-baseweb="select"] button {
            color: #262730 !important;
            background-color: transparent !important;
        }

        /* Fix multiselect clear button and controls */
        [data-baseweb="select"] [data-baseweb="tag"] button {
            color: #262730 !important;
            background-color: transparent !important;
        }
        [data-baseweb="select"] [data-baseweb="tag"] button:hover {
            background-color: #f0f0f0 !important;
            color: #262730 !important;
        }
        [data-baseweb="select"] [data-baseweb="tag"] button svg {
            fill: #262730 !important;
        }

        /* Clear all button for multiselect */
        [data-baseweb="select"] button[aria-label*="Clear all"] {
            color: #262730 !important;
            background-color: transparent !important;
        }
        [data-baseweb="select"] button[aria-label*="Clear all"]:hover {
            background-color: #f0f0f0 !important;
            color: #262730 !important;
        }
        [data-baseweb="select"] button[aria-label*="Clear all"] svg {
            fill: #262730 !important;
        }

        /* Generic button fixes for select components */
        [data-baseweb="select"] [role="button"] {
            color: #262730 !important;
        }
        [data-baseweb="select"] [role="button"] svg {
            fill: #262730 !important;
        }

        /* Fix sidebar select component specifically */
        [data-testid="stSidebar"] [data-baseweb="select"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] button {
            color: #262730 !important;
            background-color: transparent !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] button svg {
            fill: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="select-arrow"] {
            fill: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="select-arrow"] svg {
            fill: #262730 !important;
        }

        /* Ensure dropdown text is always visible */
        [data-baseweb="popover"] span,
        [data-baseweb="popover"] div,
        [data-baseweb="popover"] li,
        [data-baseweb="menu"] span,
        [data-baseweb="menu"] div,
        [data-baseweb="list"] span,
        [data-baseweb="list"] div,
        [data-baseweb="list-item"] span {
            color: #262730 !important;
        }

        /* Force visibility on all interactive elements */
        [data-baseweb] button {
            color: #262730 !important;
        }
        [data-baseweb] button svg {
            fill: #262730 !important;
        }
        [data-baseweb] [role="button"] {
            color: #262730 !important;
        }
        [data-baseweb] [role="button"] svg {
            fill: #262730 !important;
        }

        /* ULTRA-SPECIFIC FIX for Theme dropdown - nuclear option */
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="input"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="input"] > div {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="input"] input {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="input"] span {
            background-color: #ffffff !important;
            color: #262730 !important;
        }

        /* Fix the actual display text in select boxes */
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="single-value"] {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="single-value"] span {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="single-value"] div {
            color: #262730 !important;
        }

        /* Ultra-specific targeting for Streamlit's selectbox container */
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div > div {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div > div > div {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border: 1px solid #cccccc !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] span {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] div {
            color: #262730 !important;
        }

        /* Target any remaining BaseWeb elements in sidebar with brute force */
        [data-testid="stSidebar"] div[class*="baseweb"] {
            background-color: #ffffff !important;
            color: #262730 !important;
        }
        [data-testid="stSidebar"] div[class*="baseweb"] span {
            color: #262730 !important;
        }
        [data-testid="stSidebar"] div[class*="baseweb"] div {
            color: #262730 !important;
        }

        /* Emergency override - target everything in sidebar selectbox */
        [data-testid="stSidebar"] div[data-baseweb] * {
            background-color: #ffffff !important;
            color: #262730 !important;
        }

        /* Final override for any remaining invisible elements */
        [data-testid="stSidebar"] * {
            color: #262730 !important;
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
    
    st.divider()

    overview_tab, symbol_tab, drawdown_tab, calendar_tab, journal_tab = st.tabs(
        ["Overview", "Symbols", "Drawdowns", "Calendar", "Journal"]
    )

    with overview_tab:
        
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
            hovermode='x unified'
        )
        fig_equity.update_traces(
            line=dict(color='#00cc96', width=2),
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
                showlegend=False
            )
            fig_weekly.update_traces(
                marker_color='#636EFA',
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
                rr_val = row.get('rr_ratio', 0)
                
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
        
        # Format numeric columns
        if 'rr_ratio' in display_df.columns:
            display_df['rr_ratio'] = display_df['rr_ratio'].apply(lambda x: f"{x:.2f}" if x > 0 else "N/A")
        if 'pnl' in display_df.columns:
            display_df['pnl'] = pd.to_numeric(display_df['pnl'], errors='coerce')
            display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:.2f}" if not pd.isna(x) else "$0.00")
        
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

        # Tags multi-select
        available_tags = ['scalp', 'swing', 'breakout', 'reversal', 'momentum', 'support', 'resistance', 'earnings', 'news']
        tags = st.multiselect('Tags', options=available_tags)

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
                st.error("Please fix the following issues before submitting:")
                for error in validation_errors:
                    st.error(error)
            else:
                # All validation passed, proceed with saving
                # Calculate PnL based on direction
                if direction == 'long':
                    pnl = (exit_price - entry_price) * trade_size
                else:  # short
                    pnl = (entry_price - exit_price) * trade_size

                # Store the trade entry with current datetime
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
                    'notes': notes.strip() if notes else '',
                    'tags': ', '.join(tags) if tags else ''
                }

                # Save to CSV file
                trades_file = 'trades.csv'
                try:
                    # Check if file exists
                    if not pd.io.common.file_exists(trades_file):
                        # Create new file with headers
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, index=False)
                    else:
                        # Append to existing file
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, mode='a', header=False, index=False)

                    st.success(f"✅ Trade submitted successfully! Calculated PnL: ${pnl:.2f}")
                    st.success(f"💾 Trade saved to {trades_file}")
                    st.json(trade_entry)
                except Exception as e:
                    st.error(f"💥 Error saving trade to file: {str(e)}")
                    st.json(trade_entry)

else:
    st.info('Upload a trade history file to begin.')
    
    # Check if trades.csv exists and display the trades
    trades_file = 'trades.csv'
    if pd.io.common.file_exists(trades_file):
        try:
            # Read the trades from CSV
            manual_trades_df = pd.read_csv(trades_file)
            
            # Parse datetime to timestamp column
            manual_trades_df['timestamp'] = pd.to_datetime(manual_trades_df['datetime'], errors='coerce')
            
            if not manual_trades_df.empty:
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

        # Tags multi-select
        available_tags = ['scalp', 'swing', 'breakout', 'reversal', 'momentum', 'support', 'resistance', 'earnings', 'news']
        tags = st.multiselect('Tags', options=available_tags)

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
                st.error("Please fix the following issues before submitting:")
                for error in validation_errors:
                    st.error(error)
            else:
                # All validation passed, proceed with saving
                # Calculate PnL based on direction
                if direction == 'long':
                    pnl = (exit_price - entry_price) * trade_size
                else:  # short
                    pnl = (entry_price - exit_price) * trade_size

                # Store the trade entry with current datetime
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
                    'notes': notes.strip() if notes else '',
                    'tags': ', '.join(tags) if tags else ''
                }

                # Save to CSV file
                trades_file = 'trades.csv'
                try:
                    # Check if file exists
                    if not pd.io.common.file_exists(trades_file):
                        # Create new file with headers
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, index=False)
                    else:
                        # Append to existing file
                        trade_df = pd.DataFrame([trade_entry])
                        trade_df.to_csv(trades_file, mode='a', header=False, index=False)

                    st.success(f"✅ Trade submitted successfully! Calculated PnL: ${pnl:.2f}")
                    st.success(f"💾 Trade saved to {trades_file}")
                    st.json(trade_entry)
                except Exception as e:
                    st.error(f"💥 Error saving trade to file: {str(e)}")
                    st.json(trade_entry)