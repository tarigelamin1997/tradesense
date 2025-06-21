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
    """Render enhanced trade data visualization with comprehensive insights."""
    # Enhanced header with file info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("💼 Trade Data Analytics Dashboard")
    with col2:
        if st.session_state.get('data_uploaded', False):
            trade_data = st.session_state.get('trade_data')
            if trade_data is not None and isinstance(trade_data, pd.DataFrame):
                csv_data = trade_data.to_csv(index=False)
                st.download_button(
                    label="📥 Export Enhanced CSV",
                    data=csv_data,
                    file_name=f"tradesense_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="trade_data_export",
                    help="Download your processed trade data"
                )

    if not st.session_state.get('data_uploaded', False):
        st.info("👆 Please upload trade data to unlock comprehensive analytics")
        return

    trade_data = st.session_state.get('trade_data')
    if trade_data is not None:
        # Enhanced data summary with visual appeal
        st.markdown("### 📊 **Dataset Overview**")
        
        # Create visually appealing metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📈 Total Trades", 
                value=f"{len(trade_data):,}",
                help="Total number of trades in your dataset"
            )
        
        with col2:
            if 'pnl' in trade_data.columns:
                total_pnl = pd.to_numeric(trade_data['pnl'], errors='coerce').sum()
                pnl_color = "normal" if total_pnl >= 0 else "inverse"
                st.metric(
                    label="💰 Total P&L", 
                    value=f"${total_pnl:,.2f}",
                    delta=f"{'Profitable' if total_pnl >= 0 else 'Loss'} Portfolio",
                    help="Total profit/loss across all trades"
                )
        
        with col3:
            # Calculate date range
            if 'entry_time' in trade_data.columns:
                try:
                    dates = pd.to_datetime(trade_data['entry_time'])
                    date_range = (dates.max() - dates.min()).days
                    st.metric(
                        label="📅 Trading Period", 
                        value=f"{date_range} days",
                        help="Time span covered by your trading data"
                    )
                except:
                    st.metric("📅 Trading Period", "N/A")
            else:
                st.metric("📅 Trading Period", "N/A")
        
        with col4:
            # Win rate calculation
            if 'pnl' in trade_data.columns:
                pnl_numeric = pd.to_numeric(trade_data['pnl'], errors='coerce')
                win_rate = (pnl_numeric > 0).mean() * 100
                st.metric(
                    label="🎯 Win Rate", 
                    value=f"{win_rate:.1f}%",
                    delta=f"{'Strong' if win_rate >= 60 else 'Good' if win_rate >= 50 else 'Needs Work'}",
                    help="Percentage of profitable trades"
                )

        # Data composition insights
        st.markdown("### 🔍 **Data Composition**")
        
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            # Symbol breakdown
            if 'symbol' in trade_data.columns:
                symbol_counts = trade_data['symbol'].value_counts().head(10)
                st.markdown("**📈 Top Symbols Traded**")
                
                # Create a more appealing chart
                import plotly.express as px
                fig = px.bar(
                    x=symbol_counts.values,
                    y=symbol_counts.index,
                    orientation='h',
                    title="Most Active Trading Symbols",
                    labels={'x': 'Number of Trades', 'y': 'Symbol'},
                    color=symbol_counts.values,
                    color_continuous_scale='viridis'
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True, key="symbol_breakdown")

        with insight_col2:
            # Direction breakdown
            if 'direction' in trade_data.columns:
                direction_counts = trade_data['direction'].value_counts()
                st.markdown("**📊 Trade Direction Split**")
                
                fig = px.pie(
                    values=direction_counts.values,
                    names=direction_counts.index,
                    title="Long vs Short Distribution",
                    color_discrete_sequence=['#00cc96', '#ff6692']
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True, key="direction_split")

        # Enhanced data quality indicators
        st.markdown("### ✅ **Data Quality Assessment**")
        
        qual_col1, qual_col2, qual_col3 = st.columns(3)
        
        with qual_col1:
            # Completeness check
            missing_data = trade_data.isnull().sum().sum()
            completeness = (1 - missing_data / (len(trade_data) * len(trade_data.columns))) * 100
            
            if completeness >= 95:
                quality_icon = "🟢"
                quality_status = "Excellent"
            elif completeness >= 85:
                quality_icon = "🟡"
                quality_status = "Good"
            else:
                quality_icon = "🔴"
                quality_status = "Needs Attention"
            
            st.metric(
                label=f"{quality_icon} Data Completeness",
                value=f"{completeness:.1f}%",
                delta=quality_status
            )
        
        with qual_col2:
            # Column coverage
            required_cols = ['symbol', 'entry_time', 'exit_time', 'pnl', 'direction']
            present_cols = [col for col in required_cols if col in trade_data.columns]
            coverage = len(present_cols) / len(required_cols) * 100
            
            st.metric(
                label="📋 Schema Coverage",
                value=f"{coverage:.0f}%",
                delta=f"{len(present_cols)}/{len(required_cols)} core fields"
            )
        
        with qual_col3:
            # Data freshness
            if 'exit_time' in trade_data.columns:
                try:
                    latest_trade = pd.to_datetime(trade_data['exit_time']).max()
                    days_since = (datetime.now() - latest_trade).days
                    freshness_status = "Fresh" if days_since <= 7 else "Recent" if days_since <= 30 else "Historical"
                    
                    st.metric(
                        label="🕐 Data Freshness",
                        value=f"{days_since} days ago",
                        delta=freshness_status
                    )
                except:
                    st.metric("🕐 Data Freshness", "Unknown")

        # Interactive data explorer
        st.markdown("### 🗃️ **Interactive Data Explorer**")
        
        # Add filtering options
        with st.expander("🔍 **Filter & Search Options**", expanded=False):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                # Symbol filter
                if 'symbol' in trade_data.columns:
                    unique_symbols = trade_data['symbol'].unique()
                    selected_symbols = st.multiselect(
                        "Filter by Symbols",
                        options=unique_symbols,
                        default=unique_symbols[:5] if len(unique_symbols) > 5 else unique_symbols,
                        key="symbol_filter"
                    )
                else:
                    selected_symbols = None
            
            with filter_col2:
                # Date range filter
                if 'entry_time' in trade_data.columns:
                    try:
                        dates = pd.to_datetime(trade_data['entry_time'])
                        date_range = st.date_input(
                            "Date Range",
                            value=(dates.min().date(), dates.max().date()),
                            min_value=dates.min().date(),
                            max_value=dates.max().date(),
                            key="date_filter"
                        )
                    except:
                        date_range = None
                else:
                    date_range = None
            
            with filter_col3:
                # P&L filter
                pnl_filter = st.selectbox(
                    "Trade Outcome",
                    options=['All Trades', 'Winners Only', 'Losers Only', 'Breakeven'],
                    key="pnl_filter"
                )

        # Apply filters and display enhanced table
        filtered_data = trade_data.copy()
        
        # Apply symbol filter
        if selected_symbols and 'symbol' in trade_data.columns:
            filtered_data = filtered_data[filtered_data['symbol'].isin(selected_symbols)]
        
        # Apply P&L filter
        if 'pnl' in filtered_data.columns and pnl_filter != 'All Trades':
            pnl_numeric = pd.to_numeric(filtered_data['pnl'], errors='coerce')
            if pnl_filter == 'Winners Only':
                filtered_data = filtered_data[pnl_numeric > 0]
            elif pnl_filter == 'Losers Only':
                filtered_data = filtered_data[pnl_numeric < 0]
            elif pnl_filter == 'Breakeven':
                filtered_data = filtered_data[pnl_numeric == 0]

        # Enhanced table display with styling
        st.markdown(f"**📋 Trade Records** ({len(filtered_data):,} trades displayed)")
        
        # Style the dataframe for better presentation
        if len(filtered_data) > 0:
            display_df = filtered_data.copy()
            
            # Format numeric columns for better readability
            if 'pnl' in display_df.columns:
                display_df['pnl'] = pd.to_numeric(display_df['pnl'], errors='coerce')
                display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
            
            if 'entry_price' in display_df.columns:
                display_df['entry_price'] = pd.to_numeric(display_df['entry_price'], errors='coerce')
                display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
            
            if 'exit_price' in display_df.columns:
                display_df['exit_price'] = pd.to_numeric(display_df['exit_price'], errors='coerce')
                display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Quick insights below the table
            st.markdown("### 💡 **Quick Insights**")
            
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                if 'pnl' in filtered_data.columns:
                    pnl_data = pd.to_numeric(filtered_data['pnl'], errors='coerce').dropna()
                    if len(pnl_data) > 0:
                        avg_trade = pnl_data.mean()
                        best_trade = pnl_data.max()
                        worst_trade = pnl_data.min()
                        
                        st.markdown(f"""
                        **📊 Performance Highlights:**
                        - Average trade: ${avg_trade:,.2f}
                        - Best trade: ${best_trade:,.2f}
                        - Worst trade: ${worst_trade:,.2f}
                        """)
            
            with insights_col2:
                if 'symbol' in filtered_data.columns:
                    most_traded = filtered_data['symbol'].mode().iloc[0] if len(filtered_data) > 0 else "N/A"
                    unique_symbols = filtered_data['symbol'].nunique()
                    
                    st.markdown(f"""
                    **🎯 Trading Focus:**
                    - Most traded symbol: {most_traded}
                    - Total symbols: {unique_symbols}
                    - Avg trades per symbol: {len(filtered_data) / unique_symbols:.1f}
                    """)
        else:
            st.warning("No trades match your current filters. Try adjusting the criteria above.")
    else:
        st.error("❌ No trade data available. Please check your upload.")