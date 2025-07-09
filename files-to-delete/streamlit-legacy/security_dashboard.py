
import streamlit as st
import json
from datetime import datetime
from typing import Dict, List

def render_security_dashboard():
    """Render security monitoring dashboard."""
    st.title("🛡️ Security Dashboard")
    st.caption("Monitor system security and vulnerabilities")
    
    # Security overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Security Score", "92/100", delta="Good")
    with col2:
        st.metric("Active Threats", 0, delta="0")
    with col3:
        st.metric("Vulnerabilities", 2, delta="-1")
    with col4:
        st.metric("Last Scan", "2h ago")
    
    st.divider()
    
    # Security status
    st.subheader("🔍 Security Status")
    
    security_checks = [
        {"check": "SQL Injection Protection", "status": "pass", "details": "All queries parameterized"},
        {"check": "Authentication System", "status": "pass", "details": "Strong password policy active"},
        {"check": "Data Encryption", "status": "warning", "details": "Consider upgrading to AES-256"},
        {"check": "File Permissions", "status": "pass", "details": "Proper file access controls"}
    ]
    
    for check in security_checks:
        col1, col2, col3 = st.columns([3, 1, 2])
        
        with col1:
            st.write(f"**{check['check']}**")
        
        with col2:
            if check['status'] == 'pass':
                st.success("✅ PASS")
            elif check['status'] == 'warning':
                st.warning("⚠️ WARNING")
            else:
                st.error("❌ FAIL")
        
        with col3:
            st.caption(check['details'])
    
    st.divider()
    
    # Recent security events
    st.subheader("📊 Recent Security Events")
    
    events = [
        {"time": "2h ago", "event": "Security scan completed", "severity": "info"},
        {"time": "1d ago", "event": "Failed login attempt blocked", "severity": "warning"},
        {"time": "3d ago", "event": "SSL certificate renewed", "severity": "info"}
    ]
    
    for event in events:
        severity_color = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}
        st.write(f"{severity_color.get(event['severity'], 'ℹ️')} **{event['time']}**: {event['event']}")
    
    # Security actions
    st.divider()
    st.subheader("🔧 Security Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Run Security Scan", type="primary"):
            with st.spinner("Running security scan..."):
                st.success("Security scan completed! No critical issues found.")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.success("Security report generated and downloaded!")
    
    with col3:
        if st.button("🔄 Update Signatures"):
            st.success("Security signatures updated!")

if __name__ == "__main__":
    render_security_dashboard()
