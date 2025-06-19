#!/usr/bin/env python3
"""
Trade Data Components
Renders trade data table and filters
"""

import streamlit as st
import pandas as pd
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def render_trade_data():
    """Render trade data table and management."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("💼 Trade Data")
    with col2:
        if st.session_state.get('data_uploaded', False):
            trade_data = st.session_state.get('trade_data')
            if trade_data is not None and isinstance(trade_data, pd.DataFrame):
                csv_data = trade_data.to_csv(index=False)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv_data,
                    file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="trade_data_export"
                )

    if not st.session_state.get('data_uploaded', False):
        st.info("👆 Please upload trade data first")
        return

    trade_data = st.session_state.get('trade_data')
    if trade_data is not None:
        # Show basic info
        st.subheader("📊 Data Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", len(trade_data))
        with col2:
            if 'pnl' in trade_data.columns or 'profit_loss' in trade_data.columns:
                pnl_col = 'pnl' if 'pnl' in trade_data.columns else 'profit_loss'
                total_pnl = trade_data[pnl_col].sum()
                st.metric("Total P&L", f"${total_pnl:,.2f}")
        with col3:
            st.metric("Data Points", len(trade_data.columns))

        # Display the data table
        st.subheader("📋 Trade Records")
        st.dataframe(trade_data, use_container_width=True)
    else:
        st.warning("No trade data available")