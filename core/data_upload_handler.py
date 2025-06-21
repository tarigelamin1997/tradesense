
#!/usr/bin/env python3
"""
Data Upload Handler - Modern UI Implementation
Handles file upload with enhanced visuals and interactive features
"""

import streamlit as st
import pandas as pd
import logging
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

logger = logging.getLogger(__name__)

def render_data_upload_section(unique_key="default_upload"):
    """Render the modern data upload section with enhanced UI."""
    
    # Modern header with gradient background
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    ">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">📁 Upload Trade Data</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Transform your trading history into actionable insights
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Upload area with modern styling
    st.markdown("""
    <div style="
        background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
        transition: all 0.3s ease;
    " id="upload-zone">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
        <h3 style="color: #475569; margin-bottom: 0.5rem;">Drag & Drop or Click to Upload</h3>
        <p style="color: #64748b; margin: 0;">Supported formats: CSV, XLSX, XLS (Max 200MB)</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose your trade data file",
        type=['csv', 'xlsx', 'xls'],
        help="Supported formats: CSV, Excel (.xlsx, .xls). Max file size: 200MB",
        accept_multiple_files=False,
        key=f"trade_data_uploader_{unique_key}",
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        try:
            # Read and process the file
            df = _read_uploaded_file(uploaded_file)
            
            if df is not None:
                # Modern success animation
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
                    animation: slideIn 0.5s ease-out;
                ">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
                        <span style="font-size: 1.1rem;">✅ File processed successfully!</span>
                    </div>
                </div>
                <style>
                @keyframes slideIn {
                    from { opacity: 0; transform: translateY(-20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Enhanced file information cards
                _render_file_info_cards(uploaded_file, df)
                
                # Interactive data preview
                _render_interactive_data_preview(df)
                
                # Process and store data
                _process_uploaded_data(df, uploaded_file.name)

        except Exception as e:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                padding: 1.5rem;
                border-radius: 12px;
                color: white;
                margin: 1rem 0;
            ">
                <h4 style="margin: 0 0 0.5rem 0;">❌ Error Processing File</h4>
                <p style="margin: 0; opacity: 0.9;">""" + str(e) + """</p>
            </div>
            """, unsafe_allow_html=True)
            logger.error(f"File upload error: {str(e)}")

def _read_uploaded_file(uploaded_file):
    """Read uploaded file with enhanced error handling."""
    try:
        if uploaded_file.name.endswith('.csv'):
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

def _render_file_info_cards(uploaded_file, df):
    """Render modern file information cards."""
    file_size = len(uploaded_file.getvalue()) / 1024
    
    st.markdown("### 📊 **File Intelligence Dashboard**")
    
    # Create metric cards with modern styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            transition: transform 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📁</div>
            <h3 style="margin: 0; font-size: 1.2rem; font-weight: 600;">{uploaded_file.name}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">File Name</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: transform 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📏</div>
            <h3 style="margin: 0; font-size: 1.2rem; font-weight: 600;">{file_size:.1f} KB</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">File Size</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
            transition: transform 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <h3 style="margin: 0; font-size: 1.2rem; font-weight: 600;">{len(df):,}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">Total Trades</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        data_quality = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        quality_color = "#10b981" if data_quality > 95 else "#f59e0b" if data_quality > 85 else "#ef4444"
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {quality_color} 0%, {quality_color}cc 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            transition: transform 0.2s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
            <h3 style="margin: 0; font-size: 1.2rem; font-weight: 600;">{data_quality:.1f}%</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">Data Quality</p>
        </div>
        """, unsafe_allow_html=True)

def _render_interactive_data_preview(df):
    """Render interactive data preview with modern styling."""
    st.markdown("### 🔍 **Interactive Data Preview**")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Table View", "📈 Quick Stats", "🔍 Column Analysis"])
    
    with tab1:
        # Enhanced table with search and filter capabilities
        st.markdown("**Enhanced Data Table**")
        
        # Search functionality
        search_term = st.text_input("🔍 Search data", placeholder="Search across all columns...")
        
        if search_term:
            # Filter dataframe based on search term
            mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            filtered_df = df[mask]
            st.write(f"Found {len(filtered_df)} rows matching '{search_term}'")
        else:
            filtered_df = df
        
        # Interactive table with styling
        st.markdown("""
        <style>
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .dataframe thead th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            border: none;
        }
        .dataframe tbody tr:hover {
            background-color: #f1f5f9;
            transition: all 0.2s ease;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Show preview with pagination
        rows_per_page = st.selectbox("Rows per page", [5, 10, 25, 50], index=1)
        
        if len(filtered_df) > rows_per_page:
            page = st.number_input("Page", min_value=1, max_value=(len(filtered_df) // rows_per_page) + 1, value=1)
            start_idx = (page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page
            display_df = filtered_df.iloc[start_idx:end_idx]
        else:
            display_df = filtered_df.head(rows_per_page)
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab2:
        # Quick statistics with visualizations
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if 'pnl' in df.columns:
                # P&L metrics
                total_pnl = df['pnl'].sum()
                avg_pnl = df['pnl'].mean()
                win_rate = (len(df[df['pnl'] > 0]) / len(df) * 100) if len(df) > 0 else 0
                
                st.markdown("**Performance Metrics**")
                st.metric("Total P&L", f"${total_pnl:,.2f}")
                st.metric("Average P&L", f"${avg_pnl:.2f}")
                st.metric("Win Rate", f"{win_rate:.1f}%")
                
                # Simple P&L distribution chart
                fig = px.histogram(df, x='pnl', nbins=30, title="P&L Distribution")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True, key=f"pnl_hist_{id(df)}")
        
        with col2:
            st.markdown("**Data Overview**")
            st.metric("Total Rows", f"{len(df):,}")
            st.metric("Total Columns", len(df.columns))
            
            # Missing data visualization
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                fig = px.bar(x=missing_data.index, y=missing_data.values, title="Missing Data by Column")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True, key=f"missing_data_{id(df)}")
            else:
                st.success("✅ No missing data detected")
    
    with tab3:
        # Column analysis
        st.markdown("**Column Analysis**")
        
        for i, col in enumerate(df.columns):
            with st.expander(f"📊 {col} - {df[col].dtype}"):
                col_data = df[col]
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**Unique values:** {col_data.nunique()}")
                    st.write(f"**Missing values:** {col_data.isnull().sum()}")
                
                with col_info2:
                    if pd.api.types.is_numeric_dtype(col_data):
                        st.write(f"**Min:** {col_data.min()}")
                        st.write(f"**Max:** {col_data.max()}")
                        st.write(f"**Mean:** {col_data.mean():.2f}")
                
                # Sample values
                sample_values = col_data.dropna().head(5).tolist()
                st.write(f"**Sample values:** {sample_values}")

def _process_uploaded_data(df, filename):
    """Process uploaded data with enhanced feedback."""
    try:
        # Store data in session state
        st.session_state.trade_data = df
        st.session_state.data_source = filename
        
        # Enhanced success metrics
        total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
        win_rate = (len(df[df['pnl'] > 0]) / len(df) * 100) if 'pnl' in df.columns and len(df) > 0 else 0
        
        # Success summary with beautiful metrics
        st.markdown("### 🎉 **Processing Complete!**")
        
        metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
        
        with metrics_col1:
            st.metric("📊 Total Trades", f"{len(df):,}")
        with metrics_col2:
            if total_pnl != 0:
                st.metric("💰 Total P&L", f"${total_pnl:,.2f}")
        with metrics_col3:
            if win_rate > 0:
                st.metric("🎯 Win Rate", f"{win_rate:.1f}%")
        with metrics_col4:
            unique_symbols = df['symbol'].nunique() if 'symbol' in df.columns else 0
            st.metric("🏷️ Symbols", unique_symbols)
        
        # Data validation with visual indicators
        st.markdown("### ✅ **Data Validation Results**")
        
        required_cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'direction']
        missing_cols = [col for col in required_cols if col not in df.columns]
        present_cols = [col for col in required_cols if col in df.columns]
        
        validation_col1, validation_col2 = st.columns(2)
        
        with validation_col1:
            if present_cols:
                st.markdown("**✅ Present Columns:**")
                for col in present_cols:
                    st.markdown(f"• ✅ {col}")
        
        with validation_col2:
            if missing_cols:
                st.markdown("**⚠️ Missing Columns:**")
                for col in missing_cols:
                    st.markdown(f"• ⚠️ {col}")
            else:
                st.success("🎉 All recommended columns found!")
        
        # Navigation call-to-action
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            margin: 2rem 0;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        ">
            <h3 style="margin: 0 0 0.5rem 0;">🚀 Ready for Analytics!</h3>
            <p style="margin: 0; opacity: 0.9;">Navigate to the Analytics tab to explore your trading performance</p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        logger.error(f"Data processing error: {str(e)}")

# Add custom CSS for enhanced interactivity
st.markdown("""
<style>
/* Enhanced hover effects */
.element-container:hover {
    transform: translateY(-2px);
    transition: all 0.2s ease;
}

/* Modern button styling */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

/* Enhanced file uploader styling */
.stFileUploader > div > div {
    border-radius: 12px;
    border: 2px dashed #cbd5e1;
    transition: all 0.3s ease;
}

.stFileUploader > div > div:hover {
    border-color: #667eea;
    background-color: #f8fafc;
}

/* Modern metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}

/* Enhanced dataframe styling */
.dataframe {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
}
</style>
""", unsafe_allow_html=True)
