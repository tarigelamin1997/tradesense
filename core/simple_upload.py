import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def simple_file_upload(unique_key="simple_default"):
    """Simple file upload component."""
    st.subheader("📁 Upload Trade Data")

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        key=f"simple_uploader_{unique_key}"
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
#!/usr/bin/env python3
"""
Simple file upload fallback
"""

import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def simple_file_upload(unique_key="simple_upload"):
    """Simple file upload interface."""
    st.subheader("📁 Upload Trade Data")
    
    uploaded_file = st.file_uploader(
        "Choose your trade data file",
        type=['csv', 'xlsx', 'xls'],
        key=unique_key
    )
    
    if uploaded_file is not None:
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! {len(df)} rows loaded.")
            
            # Store in session state
            st.session_state.trade_data = df
            
            # Show preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            return df
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            st.error(f"Error reading file: {e}")
            return None
    
    return None
