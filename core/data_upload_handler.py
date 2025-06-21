"""Complete, functional version of the modified code."""
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
                # Display file info with enhanced styling
                st.markdown("### 📄 **File Information**")

                info_col1, info_col2, info_col3 = st.columns(3)

                with info_col1:
                    st.metric("📁 File Name", uploaded_file.name)

                with info_col2:
                    file_size = len(uploaded_file.getvalue()) / 1024
                    st.metric("📏 File Size", f"{file_size:.1f} KB")

                with info_col3:
                    st.metric("📊 Total Rows", len(df))

                # Enhanced data preview
                with st.expander("📊 Data Preview & Analysis", expanded=True):
                    preview_col1, preview_col2 = st.columns([2, 1])

                    with preview_col1:
                        st.markdown("**Sample Data:**")
                        st.dataframe(df.head(), use_container_width=True)

                    with preview_col2:
                        st.markdown("**Columns Found:**")
                        for col in df.columns:
                            st.write(f"• {col}")

                        # Quick data quality check
                        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                        if missing_pct > 0:
                            st.warning(f"⚠️ {missing_pct:.1f}% missing data")
                        else:
                            st.success("✅ No missing data")

                # Process the data
                _process_uploaded_data(df, uploaded_file.name)

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
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
    """Process uploaded data with enhanced feedback."""
    try:
        # Store data in session state for analytics
        st.session_state.trade_data = df
        st.session_state.data_source = filename

        # Success message with metrics
        total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
        win_rate = (len(df[df['pnl'] > 0]) / len(df) * 100) if 'pnl' in df.columns and len(df) > 0 else 0

        # Modern success banner with refined styling
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin: 1.5rem 0;
            color: white;
            font-weight: 600;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                <span style="font-size: 1.1rem;">✅ File processed successfully</span>
                <div style="display: flex; gap: 2rem; font-size: 0.95rem; opacity: 0.95;">
                    <span><strong>{rows:,}</strong> trades</span>
                    <span>P&L: <strong>${pnl:,.2f}</strong></span>
                    <span>Win Rate: <strong>{win_rate:.1f}%</strong></span>
                </div>
            </div>
        </div>
        """.format(rows=len(df), pnl=total_pnl, win_rate=win_rate), unsafe_allow_html=True)

        # Validate required columns
        required_cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.warning(f"⚠️ Missing recommended columns: {', '.join(missing_cols)}")
            st.info("The analytics will work with available data, but some features may be limited.")
        else:
            st.success("✅ All recommended columns found! Full analytics available.")

        st.info("💡 Navigate to the **Analytics** tab to explore your trading performance!")

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        logger.error(f"Data processing error: {str(e)}")

def handle_file_upload():
    """Enhanced file upload handler with modern UI."""
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

            # Modern success banner with refined styling
            st.markdown("""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin: 1.5rem 0;
            color: white;
            font-weight: 600;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.1);
        ">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                <span style="font-size: 1.1rem;">✅ File processed successfully</span>
                <div style="display: flex; gap: 2rem; font-size: 0.95rem; opacity: 0.95;">
                    <span><strong>{rows:,}</strong> trades</span>
                    <span>P&L: <strong>${pnl:,.2f}</strong></span>
                    <span>Win Rate: <strong>{win_rate:.1f}%</strong></span>
                </div>
            </div>
        </div>
        """.format(rows=len(df), pnl=total_pnl, win_rate=win_rate), unsafe_allow_html=True)

            # Advanced data preview with analytics insights
            st.markdown("### 📊 **Data Intelligence Dashboard**")

            # Create metric cards
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    color: white;
                    margin-bottom: 1rem;
                ">
                    <h3 style="margin: 0; font-size: 1.5rem;">{}</h3>
                    <p style="margin: 0;">Total Trades</p>
                </div>
                """.format(len(df)), unsafe_allow_html=True)

            with col2:
                total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    color: white;
                    margin-bottom: 1rem;
                ">
                    <h3 style="margin: 0; font-size: 1.5rem;">${:.2f}</h3>
                    <p style="margin: 0;">Total P&L</p>
                </div>
                """.format(total_pnl), unsafe_allow_html=True)

            with col3:
                unique_symbols = df['symbol'].nunique() if 'symbol' in df.columns else 0
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    color: white;
                    margin-bottom: 1rem;
                ">
                    <h3 style="margin: 0; font-size: 1.5rem;">{}</h3>
                    <p style="margin: 0;">Symbols Traded</p>
                </div>
                """.format(unique_symbols), unsafe_allow_html=True)

            with col4:
                data_quality = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                quality_color = "#00ff88" if data_quality > 95 else "#ffaa00" if data_quality > 85 else "#ff4444"
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, {color} 0%, {color}80 100%);
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    color: white;
                    margin-bottom: 1rem;
                ">
                    <h3 style="margin: 0; font-size: 1.5rem;">{:.1f}%</h3>
                    <p style="margin: 0;">Data Quality</p>
                </div>
                """.format(data_quality, color=quality_color), unsafe_allow_html=True)

            # Interactive data preview with styling
            st.markdown("### 🔍 **Interactive Data Preview**")

            preview_col1, preview_col2 = st.columns([2, 1])

            with preview_col1:
                st.markdown("**📋 Sample Records**")
                # Style the dataframe
                display_df = df.head(5)
                st.dataframe(display_df, use_container_width=True, hide_index=True)

            with preview_col2:
                st.markdown("**📈 Quick Analytics**")

                if 'pnl' in df.columns:
                    win_rate = (df[df['pnl'] > 0].shape[0] / len(df)) * 100
                    st.metric("Win Rate", f"{win_rate:.1f}%")

                    avg_win = df[df['pnl'] > 0]['pnl'].mean()
                    avg_loss = df[df['pnl'] < 0]['pnl'].mean()
                    st.metric("Avg Win", f"${avg_win:.2f}")
                    st.metric("Avg Loss", f"${avg_loss:.2f}")

                st.info(f"**Columns:** {len(df.columns)}")

                # Column health check
                missing_cols = []
                expected_cols = ['symbol', 'entry_time', 'exit_time', 'pnl', 'direction']
                for col in expected_cols:
                    if col not in df.columns:
                        missing_cols.append(col)

                if missing_cols:
                    st.warning(f"⚠️ Missing: {', '.join(missing_cols)}")
                else:
                    st.success("✅ All key columns present")

            # Data validation alerts
            if df.empty:
                st.error("⚠️ The uploaded file appears to be empty.")
                return None

            missing_data_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            if missing_data_pct > 20:
                st.warning(f"⚠️ High missing data detected ({missing_data_pct:.1f}%). Consider data cleanup.")

            # Store in session state
            st.session_state.trade_data = df
            st.session_state.data_source = uploaded_file.name

            return df

        except Exception as e:
            st.error(f"❌ **Error processing file:** {str(e)}")
            st.info("💡 **Troubleshooting tips:**\n- Ensure your file is not corrupted\n- Check that column headers are in the first row\n- Verify the file format is supported")
            return None

    return None
st.markdown("""
                <style>
                :root {
                    --bg-primary: #ffffff;
                    --bg-secondary: #f8fafc;
                    --bg-gradient: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
                    --border-color: #e2e8f0;
                    --text-primary: #1e293b;
                    --text-secondary: #64748b;
                    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }

                @media (prefers-color-scheme: dark) {
                    :root {
                        --bg-primary: #1e293b;
                        --bg-secondary: #334155;
                        --bg-gradient: linear-gradient(145deg, #1e293b 0%, #334155 100%);
                        --border-color: #475569;
                        --text-primary: #f1f5f9;
                        --text-secondary: #cbd5e1;
                        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
                    }
                }

                .file-info-card {
                    background: var(--bg-gradient);
                    border: 1px solid var(--border-color);
                    border-radius: 16px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    box-shadow: var(--shadow);
                    transition: all 0.2s ease;
                }
                .file-info-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.1);
                }
                .file-stat {
                    text-align: center;
                    padding: 0.75rem;
                }
                .file-stat-value {
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: var(--text-primary);
                    margin-bottom: 0.25rem;
                }
                .file-stat-label {
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                    font-weight: 500;
                }
                </style>""", unsafe_allow_html=True)