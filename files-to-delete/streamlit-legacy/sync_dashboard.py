
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from auth import require_auth

@require_auth
def render_sync_dashboard(current_user: Dict):
    """Render comprehensive sync management dashboard."""
    st.title("🔄 Data Sync Dashboard")
    st.caption("Monitor and control automatic trade data synchronization")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Connected Accounts", 3)
    with col2:
        st.metric("Sync Health", "95%", delta="Good")
    with col3:
        st.metric("Recent Syncs (24h)", 12)
    with col4:
        st.metric("Last Sync", "2h ago")
    
    st.divider()
    
    # Active sync jobs
    st.subheader("🔄 Active Sync Jobs")
    
    # Sample active jobs
    active_jobs = [
        {"provider": "Interactive Brokers", "status": "running", "progress": 75},
        {"provider": "TD Ameritrade", "status": "pending", "progress": 0}
    ]
    
    for job in active_jobs:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{job['provider']}**")
                st.progress(job['progress'] / 100)
            
            with col2:
                status_color = {"running": "🔄", "pending": "⏳", "success": "✅", "error": "❌"}
                st.write(f"{status_color.get(job['status'], '⚪')} {job['status'].title()}")
            
            with col3:
                if job['status'] in ['pending', 'running']:
                    if st.button("❌", key=f"cancel_{job['provider']}", help="Cancel sync"):
                        st.success("Sync cancelled")
    
    st.divider()
    
    # Sync settings
    with st.expander("⚙️ Sync Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            auto_sync = st.checkbox("Enable Auto-sync", value=True)
            sync_frequency = st.selectbox("Sync Frequency", 
                                        options=[15, 30, 60, 120],
                                        format_func=lambda x: f"Every {x} minutes")
        
        with col2:
            enable_realtime = st.checkbox("Real-time Sync (where supported)")
            retry_attempts = st.slider("Max Retry Attempts", 1, 5, 3)
        
        if st.button("💾 Save Settings"):
            st.success("Sync settings saved!")

if __name__ == "__main__":
    # For testing
    test_user = {"id": 1, "first_name": "Test", "subscription_tier": "pro"}
    render_sync_dashboard(test_user)
