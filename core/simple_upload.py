
import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def simple_file_upload():
    """Simple file upload with basic processing."""
    st.subheader("📁 Upload Your Trade Data")
    
    uploaded_file = st.file_uploader(
        "Select your trading data file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files with your trading data"
    )
    
    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Store in session state
            st.session_state.trade_data = df
            
            # Show success message and preview
            st.success(f"✅ Successfully uploaded {uploaded_file.name}")
            st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
            
            # Show preview
            with st.expander("📊 Data Preview", expanded=True):
                st.dataframe(df.head(), use_container_width=True)
                
            st.info("Go to the Analytics tab to view your trading performance!")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            logger.error(f"File upload error: {e}")
