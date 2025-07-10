
import streamlit as st
import pandas as pd
import sys
import traceback
import logging
from datetime import datetime
import json

def show_debug_console():
    """Display comprehensive debug console."""
    st.title("🔧 Debug Console")
    st.markdown("---")
    
    # System Information
    st.subheader("📊 System Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Python Version", sys.version.split()[0])
        st.metric("Streamlit Version", st.__version__)
    
    with col2:
        st.metric("Pandas Version", pd.__version__)
        try:
            import psutil
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent:.1f}%")
        except:
            st.metric("Memory Usage", "N/A")
    
    with col3:
        st.metric("Session State Keys", len(st.session_state))
        st.metric("Cache Entries", "Unknown")
    
    # Error Log Viewer
    st.subheader("🚨 Recent Errors")
    
    error_sources = [
        ("Application Log", "logs/tradesense.log"),
        ("Error Log", "logs/tradesense_errors.log"),
        ("System Log", "logs/application.log")
    ]
    
    for log_name, log_path in error_sources:
        with st.expander(f"📄 {log_name}"):
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-20:]  # Last 20 lines
                
                if recent_lines:
                    for line in recent_lines:
                        if 'ERROR' in line or 'CRITICAL' in line:
                            st.error(line.strip())
                        elif 'WARNING' in line:
                            st.warning(line.strip())
                        else:
                            st.text(line.strip())
                else:
                    st.info("No recent entries")
                    
            except FileNotFoundError:
                st.info(f"Log file {log_path} not found")
            except Exception as e:
                st.error(f"Error reading {log_path}: {str(e)}")
    
    # Session State Inspector
    st.subheader("🔍 Session State Inspector")
    
    if st.button("Refresh Session State"):
        st.rerun()
    
    # Filter session state for large objects
    filtered_state = {}
    large_objects = {}
    
    for key, value in st.session_state.items():
        try:
            size = sys.getsizeof(value)
            if size > 1024:  # Objects larger than 1KB
                large_objects[key] = f"{size:,} bytes"
            else:
                filtered_state[key] = str(value)[:200]  # Truncate long strings
        except:
            filtered_state[key] = "Unable to inspect"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Small Objects:**")
        st.json(filtered_state)
    
    with col2:
        st.write("**Large Objects:**")
        for key, size in large_objects.items():
            st.write(f"• `{key}`: {size}")
    
    # Cache Management
    st.subheader("🧹 Cache Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Clear Data Cache", type="primary"):
            st.cache_data.clear()
            st.success("Data cache cleared")
    
    with col2:
        if st.button("Clear Session State"):
            keys_to_remove = [k for k in st.session_state.keys() if k != 'session_id']
            for key in keys_to_remove:
                del st.session_state[key]
            st.success("Session state cleared")
    
    with col3:
        if st.button("Force Garbage Collection"):
            import gc
            collected = gc.collect()
            st.success(f"Collected {collected} objects")
    
    # Error Simulation for Testing
    st.subheader("⚠️ Error Testing")
    st.warning("Use these buttons to test error handling:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Simulate KeyError"):
            raise KeyError("Test key error for debugging")
    
    with col2:
        if st.button("Simulate ValueError"):
            raise ValueError("Test value error for debugging")
    
    with col3:
        if st.button("Simulate Memory Error"):
            # Create a large list to trigger memory issues
            large_list = [0] * (10**7)
            st.write("Large list created")

if __name__ == "__main__":
    show_debug_console()
