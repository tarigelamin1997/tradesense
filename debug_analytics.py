
import streamlit as st
import pandas as pd
from trade_entry_manager import TradeEntryManager
from analytics import compute_basic_stats, calculate_kpis
import numpy as np

def debug_analytics():
    """Debug analytics issues."""
    st.title("🔍 Analytics Debug Tool")
    
    manager = TradeEntryManager()
    
    # Show data status
    st.subheader("Data Status")
    
    try:
        df = manager.get_unified_dataframe()
        st.write(f"**Total rows:** {len(df)}")
        st.write(f"**Columns:** {list(df.columns)}")
        
        if not df.empty:
            st.write("**Data types:**")
            st.write(df.dtypes)
            
            st.write("**Sample data:**")
            st.write(df.head())
            
            # Check PnL column specifically
            if 'pnl' in df.columns:
                st.write("**PnL Analysis:**")
                st.write(f"- PnL data type: {df['pnl'].dtype}")
                st.write(f"- Non-null PnL values: {df['pnl'].notna().sum()}")
                st.write(f"- Null PnL values: {df['pnl'].isna().sum()}")
                
                # Try to convert to numeric
                pnl_numeric = pd.to_numeric(df['pnl'], errors='coerce')
                st.write(f"- Valid numeric PnL: {pnl_numeric.notna().sum()}")
                st.write(f"- Infinite values: {np.isinf(pnl_numeric).sum()}")
                
                if pnl_numeric.notna().sum() > 0:
                    st.write(f"- PnL range: {pnl_numeric.min():.2f} to {pnl_numeric.max():.2f}")
            else:
                st.error("❌ PnL column not found!")
                
        else:
            st.warning("⚠️ No data found")
            
    except Exception as e:
        st.error(f"❌ Error getting data: {str(e)}")
        st.exception(e)
    
    # Test analytics functions
    st.subheader("Analytics Test")
    
    if st.button("Test Analytics"):
        try:
            analytics = manager.get_unified_analytics()
            st.success("✅ Analytics computed successfully")
            st.json(analytics)
        except Exception as e:
            st.error(f"❌ Analytics failed: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    debug_analytics()
