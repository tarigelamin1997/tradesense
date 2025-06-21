#!/usr/bin/env python3
"""
Data Upload Handler
Handles file upload and initial data processing
"""

import streamlit as st
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def render_data_upload_section(unique_key="default_upload"):
    """Render the data upload section."""
    st.subheader("📁 Upload Trade Data")
    st.write("Choose a CSV or Excel file containing your trading data")

    # File uploader with clear label
    uploaded_file = st.file_uploader(
        "Choose your trade data file",
        type=['csv', 'xlsx', 'xls'],
        help="Supported formats: CSV, XLSX, XLS (Max 200MB)",
        accept_multiple_files=False,
        key=f"trade_data_uploader_{unique_key}"
    )

    if uploaded_file is not None:
        try:
            # Read the file with better error handling
            df = _read_uploaded_file(uploaded_file)

            if df is not None:
                # Display file info
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Size:** {uploaded_file.size / 1024:.1f}KB")
                st.write(f"**Rows:** {len(df)}")
                st.write(f"**Columns:** {list(df.columns)}")

                # Show preview
                with st.expander("📄 Data Preview", expanded=False):
                    st.dataframe(df.head(), use_container_width=True)

                # Process the data
                _process_uploaded_data(df, uploaded_file.name)

        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            logger.error(f"File upload error: {str(e)}")

def _read_uploaded_file(uploaded_file):
    """Read uploaded file with error handling."""
    try:
        if uploaded_file.name.endswith('.csv'):
            # Try different encodings
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def _process_uploaded_data(df, filename):
    """Process uploaded data with fallback methods."""
    try:
        # Try full processing first
        from trade_entry_manager import trade_manager
        result = trade_manager.add_file_trades(df, f"file_{filename}")

        if result['status'] == 'success':
            st.success(f"✅ Successfully processed {result['trades_added']} trades")
            st.session_state.trade_data = trade_manager.get_all_trades_dataframe()
        else:
            _handle_processing_error(result, df)

    except Exception as e:
        # Fallback to simple validation
        _fallback_processing(df, str(e))

def _handle_processing_error(result, df):
    """Handle processing errors with helpful feedback."""
    st.error(f"Error processing file: {result['message']}")

    # Show column mapping suggestions
    required_cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction']
    st.info("**Required columns:** " + ", ".join(required_cols))
    st.info(f"**Your file has:** {', '.join(df.columns)}")

    # Suggest mappings
    suggestions = []
    for req_col in required_cols:
        for file_col in df.columns:
            if req_col.lower() in file_col.lower() or file_col.lower() in req_col.lower():
                suggestions.append(f"'{file_col}' might map to '{req_col}'")

    if suggestions:
        st.info("**Possible column mappings:**")
        for suggestion in suggestions:
            st.info(f"• {suggestion}")

def _fallback_processing(df, error):
    """Fallback processing when main system fails."""
    st.warning(f"🔧 Main processing failed: {error}")
    st.info("Trying simplified processing...")

    # Basic validation
    required_columns = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction']
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
    else:
        # Store raw data
        st.session_state.trade_data = df
        st.success("✅ File uploaded successfully! Limited analytics available.")

def handle_file_upload():
    """Handle file upload with enhanced preview and validation."""
    st.markdown("### 📁 **Upload Your Trade Data**")

    uploaded_file = st.file_uploader(
        "Choose your trading history file",
        type=['csv', 'xlsx', 'xls'],
        help="Supported formats: CSV, Excel (.xlsx, .xls). Max file size: 200MB",
        key="main_file_uploader"
    )

    if uploaded_file is not None:
        try:
            # Show file information with enhanced styling
            file_size = len(uploaded_file.getvalue()) / 1024  # KB

            with st.container():
                st.markdown("### 📄 **File Information**")

                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.metric("📁 File Name", uploaded_file.name)

                with info_col2:
                    st.metric("📏 File Size", f"{file_size:.1f} KB")

                with info_col3:
                    file_type = uploaded_file.name.split('.')[-1].upper()
                    st.metric("📋 Format", file_type)

            # Read the file based on its type
            with st.spinner("🔄 Processing your trading data..."):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

            # Enhanced success message with data preview
            st.success(f"✅ Successfully processed **{len(df):,} trades** from `{uploaded_file.name}`")

            # Quick data preview
            st.markdown("### 👀 **Data Preview**")

            preview_col1, preview_col2 = st.columns(2)

            with preview_col1:
                st.markdown("**📊 Dataset Dimensions**")
                st.info(f"**Rows:** {len(df):,} | **Columns:** {len(df.columns)}")

                st.markdown("**📋 Column Names**")
                columns_display = ", ".join([f"`{col}`" for col in df.columns[:5]])
                if len(df.columns) > 5:
                    columns_display += f" ... and {len(df.columns) - 5} more"
                st.info(columns_display)

            with preview_col2:
                st.markdown("**🔍 Sample Data**")
                st.dataframe(
                    df.head(3),
                    use_container_width=True,
                    hide_index=True
                )

            # Data validation alerts
            if df.empty:
                st.error("⚠️ The uploaded file appears to be empty.")
                return None

            missing_data_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            if missing_data_pct > 20:
                st.warning(f"⚠️ High missing data detected ({missing_data_pct:.1f}%). Consider data cleanup.")

            return df

        except Exception as e:
            st.error(f"❌ **Error processing file:** {str(e)}")
            st.info("💡 **Troubleshooting tips:**\n- Ensure your file is not corrupted\n- Check that column headers are in the first row\n- Verify the file format is supported")
            return None

    return None
```