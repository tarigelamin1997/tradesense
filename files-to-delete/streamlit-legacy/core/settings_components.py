
#!/usr/bin/env python3
"""
Settings Components
Renders application settings and configuration
"""

import streamlit as st

def render_settings():
    """Render settings page."""
    st.markdown("## ⚙️ Settings")
    
    # Session management
    st.markdown("### 🗂️ Session Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clear Session Data"):
            _clear_session_data()
    
    with col2:
        if st.button("🔄 Reload Application"):
            st.rerun()
    
    # System information
    st.markdown("### 🔧 System Information")
    
    # Session state info
    with st.expander("Session State", expanded=False):
        session_info = {
            'authenticated': st.session_state.get('authenticated', False),
            'data_uploaded': st.session_state.get('trade_data') is not None,
            'analysis_complete': st.session_state.get('analysis_complete', False),
            'total_session_keys': len(st.session_state.keys())
        }
        st.json(session_info)
    
    # Data info
    if st.session_state.get('trade_data') is not None:
        trade_data = st.session_state.trade_data
        with st.expander("Data Information", expanded=False):
            data_info = {
                'rows': len(trade_data),
                'columns': list(trade_data.columns),
                'memory_usage': f"{trade_data.memory_usage(deep=True).sum() / 1024:.1f} KB"
            }
            st.json(data_info)

def _clear_session_data():
    """Clear session data with confirmation."""
    # Keep essential authentication data
    essential_keys = ['authenticated', 'user_id']
    
    keys_to_remove = [key for key in st.session_state.keys() if key not in essential_keys]
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    st.success("✅ Session data cleared (authentication preserved)")
    st.rerun()
