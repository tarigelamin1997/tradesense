
#!/usr/bin/env python3
"""
Analysis Engine
Handles analysis execution and control
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_analysis_controls():
    """Render analysis control interface."""
    if st.session_state.get('analysis_complete', False):
        st.info("✅ Analysis completed! Results are displayed below.")
    elif st.session_state.get('trade_data') is not None:
        if st.button("🔄 Run Comprehensive Analysis", type="primary"):
            run_analysis()

def run_analysis():
    """Run comprehensive analysis with error handling."""
    try:
        with st.spinner("Running analysis..."):
            from trade_entry_manager import trade_manager
            
            # Get analytics
            analytics_result = trade_manager.get_unified_analytics()
            
            # Store results
            st.session_state.analytics_result = analytics_result
            st.session_state.analysis_complete = True
            
            st.success("✅ Analysis completed successfully!")
            st.rerun()
            
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        logger.error(f"Analysis error: {str(e)}")
        
        # Try basic analysis
        _run_basic_analysis()

def _run_basic_analysis():
    """Run basic analysis when full analysis fails."""
    try:
        trade_data = st.session_state.get('trade_data')
        if trade_data is not None and not trade_data.empty:
            import pandas as pd
            
            # Basic calculations
            total_trades = len(trade_data)
            if 'pnl' in trade_data.columns:
                pnl_data = pd.to_numeric(trade_data['pnl'], errors='coerce').dropna()
                total_pnl = pnl_data.sum()
                wins = len(pnl_data[pnl_data > 0])
                win_rate = (wins / len(pnl_data) * 100) if len(pnl_data) > 0 else 0
                
                # Store basic results
                basic_analytics = {
                    'basic_stats': {
                        'total_trades': total_trades,
                        'total_pnl': total_pnl,
                        'win_rate': win_rate,
                        'wins': wins,
                        'losses': len(pnl_data) - wins
                    }
                }
                
                st.session_state.analytics_result = basic_analytics
                st.session_state.analysis_complete = True
                st.success("✅ Basic analysis completed!")
                st.rerun()
            else:
                st.error("No P&L column found for analysis")
    except Exception as e:
        st.error(f"Basic analysis also failed: {str(e)}")
