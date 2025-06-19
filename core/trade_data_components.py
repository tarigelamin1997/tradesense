
#!/usr/bin/env python3
"""
Trade Data Components
Renders trade data table and filters
"""

import streamlit as st

def render_trade_data():
    """Render trade data page."""
    trade_data = st.session_state.get('trade_data')
    if trade_data is not None and not trade_data.empty:
        st.markdown("## 📋 Trade Data")
        
        # Summary info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", len(trade_data))
        with col2:
            if 'pnl' in trade_data.columns:
                wins = len(trade_data[trade_data['pnl'] > 0])
                st.metric("Winning Trades", wins)
        with col3:
            if 'pnl' in trade_data.columns:
                total_pnl = trade_data['pnl'].sum()
                st.metric("Total P&L", f"${total_pnl:,.2f}")
        
        # Data table
        st.dataframe(trade_data, use_container_width=True)
        
        # Download option
        csv = trade_data.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="trade_data.csv",
            mime="text/csv"
        )
    else:
        st.info("No trade data available. Please upload a file first.")
