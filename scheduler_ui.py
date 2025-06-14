
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from scheduler import job_scheduler, JobStatus, JobType
from connectors.loader import get_available_connectors
from auth import require_auth

def render_job_management_interface(current_user: Dict):
    """Render the job management interface in Streamlit."""
    st.subheader("🕐 Background Jobs & Sync Scheduler")
    
    if not current_user:
        st.warning("Please login to manage background jobs")
        return
    
    user_id = current_user['id']
    
    # Start scheduler if not running
    if not job_scheduler.scheduler.running:
        job_scheduler.start()
    
    # Tabs for different job management sections
    job_tabs = st.tabs(["Active Jobs", "Schedule New Job", "Job History", "Settings"])
    
    with job_tabs[0]:
        render_active_jobs(user_id)
    
    with job_tabs[1]:
        render_schedule_new_job(user_id, current_user.get('partner_id'))
    
    with job_tabs[2]:
        render_job_history(user_id)
    
    with job_tabs[3]:
        render_job_settings(user_id)

def render_active_jobs(user_id: int):
    """Render active jobs table."""
    st.write("**Your Active Background Jobs**")
    
    try:
        jobs = job_scheduler.get_user_jobs(user_id)
        
        if not jobs:
            st.info("No scheduled jobs found. Create your first sync job below!")
            return
        
        # Convert to DataFrame for better display
        jobs_df = pd.DataFrame(jobs)
        
        # Add status indicators
        def format_status(status):
            status_icons = {
                'pending': '⏳ Pending',
                'running': '🏃 Running',
                'completed': '✅ Completed',
                'failed': '❌ Failed',
                'cancelled': '🚫 Cancelled'
            }
            return status_icons.get(status, status)
        
        jobs_df['status_display'] = jobs_df['status'].apply(format_status)
        
        # Format dates
        for date_col in ['scheduled_at', 'last_run', 'next_run']:
            if date_col in jobs_df.columns:
                jobs_df[date_col] = pd.to_datetime(jobs_df[date_col], errors='coerce')
                jobs_df[f'{date_col}_display'] = jobs_df[date_col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display jobs with actions
        for idx, job in jobs_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{job['type'].replace('_', ' ').title()}**")
                    st.caption(f"ID: {job['id'][:20]}...")
                
                with col2:
                    st.write(job['status_display'])
                    if job['error_count'] > 0:
                        st.caption(f"⚠️ {job['error_count']} errors")
                
                with col3:
                    if job['next_run_display']:
                        st.write(f"Next: {job['next_run_display']}")
                    if job['last_run_display']:
                        st.caption(f"Last: {job['last_run_display']}")
                
                with col4:
                    if job['is_active']:
                        if st.button("🚫 Cancel", key=f"cancel_{job['id']}", help="Cancel this job"):
                            if job_scheduler.cancel_job(job['id']):
                                st.success("Job cancelled!")
                                st.rerun()
                            else:
                                st.error("Failed to cancel job")
                    else:
                        st.caption("Inactive")
                
                # Show error details if any
                if job['last_error']:
                    with st.expander(f"🔍 Error Details - {job['id'][:10]}"):
                        st.error(job['last_error'])
                
                st.divider()
    
    except Exception as e:
        st.error(f"Error loading jobs: {str(e)}")

def render_schedule_new_job(user_id: int, partner_id: Optional[str]):
    """Render form to schedule new background jobs."""
    st.write("**Schedule New Background Job**")
    
    job_type = st.selectbox(
        "Job Type",
        options=[
            ("Connector Sync", "connector_sync"),
            ("Manual Sync (One-time)", "manual_sync")
        ],
        format_func=lambda x: x[0],
        help="Choose the type of background job to schedule"
    )
    
    job_type_value = job_type[1]
    
    if job_type_value in ['connector_sync', 'manual_sync']:
        render_connector_sync_form(user_id, partner_id, job_type_value)

def render_connector_sync_form(user_id: int, partner_id: Optional[str], job_type: str):
    """Render form for connector sync jobs."""
    
    # Get available connectors
    available_connectors = get_available_connectors()
    
    if not available_connectors:
        st.warning("No connectors available. Please check connector configuration.")
        return
    
    working_connectors = [conn for conn in available_connectors if 'error' not in conn]
    
    if not working_connectors:
        st.error("No working connectors found. Please check connector setup.")
        return
    
    with st.form("schedule_sync_job"):
        st.write(f"**Configure {job_type.replace('_', ' ').title()}**")
        
        # Connector selection
        connector_options = [(conn['name'], conn['name']) for conn in working_connectors]
        selected_connector = st.selectbox(
            "Select Connector:",
            options=connector_options,
            format_func=lambda x: x[1],
            help="Choose which connector to sync data from"
        )
        
        connector_name = selected_connector[1] if selected_connector else None
        
        # Get connector metadata for configuration
        if connector_name:
            try:
                connector_metadata = next(conn for conn in working_connectors if conn['name'] == connector_name)
                
                st.write(f"**Connector Type:** {connector_metadata.get('type', 'Unknown')}")
                st.write(f"**Supported Formats:** {', '.join(connector_metadata.get('supported_formats', []))}")
                
                # Sync frequency (only for recurring sync)
                if job_type == 'connector_sync':
                    sync_interval = st.selectbox(
                        "Sync Frequency:",
                        options=[
                            (15, "Every 15 minutes"),
                            (30, "Every 30 minutes"),
                            (60, "Every hour"),
                            (180, "Every 3 hours"),
                            (360, "Every 6 hours"),
                            (720, "Every 12 hours"),
                            (1440, "Daily")
                        ],
                        format_func=lambda x: x[1],
                        help="How often should this sync run?"
                    )
                    sync_interval_minutes = sync_interval[0]
                else:
                    sync_interval_minutes = 0  # One-time execution
                
                # Additional configuration
                with st.expander("🔧 Advanced Configuration", expanded=False):
                    config_json = st.text_area(
                        "Connector Config (JSON):",
                        value="{}",
                        help="Additional configuration for the connector in JSON format"
                    )
                
                # Submit button
                submit_label = "🔄 Schedule Recurring Sync" if job_type == 'connector_sync' else "▶️ Run Manual Sync Now"
                
                if st.form_submit_button(submit_label, type="primary"):
                    try:
                        # Parse config
                        import json
                        config = json.loads(config_json) if config_json.strip() else {}
                        
                        # Schedule the job
                        if job_type == 'connector_sync':
                            job_id = job_scheduler.schedule_connector_sync(
                                user_id=user_id,
                                connector_name=connector_name,
                                sync_interval_minutes=sync_interval_minutes,
                                partner_id=partner_id,
                                config=config
                            )
                            
                            st.success(f"✅ **Sync Job Scheduled!**")
                            st.success(f"**Connector:** {connector_name}")
                            st.success(f"**Frequency:** {sync_interval[1]}")
                            st.success(f"**Job ID:** {job_id}")
                            st.info("Your data will be automatically synced in the background. Check the 'Active Jobs' tab to monitor progress.")
                        
                        else:  # manual_sync
                            job_id = job_scheduler.execute_manual_sync(
                                user_id=user_id,
                                connector_name=connector_name,
                                config=config
                            )
                            
                            st.success(f"✅ **Manual Sync Started!**")
                            st.success(f"**Connector:** {connector_name}")
                            st.success(f"**Job ID:** {job_id}")
                            st.info("Your sync is running now. Check the 'Active Jobs' tab to monitor progress.")
                        
                        # Auto-refresh to show new job
                        st.rerun()
                    
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON in connector configuration")
                    except Exception as e:
                        st.error(f"❌ Error scheduling job: {str(e)}")
            
            except Exception as e:
                st.error(f"Error loading connector metadata: {str(e)}")

def render_job_history(user_id: int):
    """Render job execution history."""
    st.write("**Job Execution History**")
    
    try:
        jobs = job_scheduler.get_user_jobs(user_id)
        
        if not jobs:
            st.info("No job history available.")
            return
        
        # Let user select a job to view history
        job_options = [(job['id'], f"{job['type']} - {job['id'][:10]}...") for job in jobs]
        
        selected_job = st.selectbox(
            "Select Job to View History:",
            options=job_options,
            format_func=lambda x: x[1]
        )
        
        if selected_job:
            job_id = selected_job[0]
            history = job_scheduler.get_job_history(job_id, limit=20)
            
            if history:
                st.write(f"**Execution History for Job:** {job_id[:20]}...")
                
                history_df = pd.DataFrame(history)
                
                # Format times
                for time_col in ['start_time', 'end_time']:
                    if time_col in history_df.columns:
                        history_df[time_col] = pd.to_datetime(history_df[time_col], errors='coerce')
                        history_df[f'{time_col}_display'] = history_df[time_col].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Add status formatting
                def format_status(status):
                    status_icons = {
                        'completed': '✅ Completed',
                        'failed': '❌ Failed',
                        'running': '🏃 Running'
                    }
                    return status_icons.get(status, status)
                
                history_df['status_display'] = history_df['status'].apply(format_status)
                
                # Display execution records
                for idx, execution in history_df.iterrows():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                        
                        with col1:
                            st.write(execution['status_display'])
                        
                        with col2:
                            st.write(f"Started: {execution['start_time_display']}")
                        
                        with col3:
                            if execution['end_time_display']:
                                st.write(f"Ended: {execution['end_time_display']}")
                        
                        with col4:
                            if execution['records_processed']:
                                st.write(f"📊 {execution['records_processed']} records")
                        
                        # Show error details if any
                        if execution['error_message']:
                            with st.expander(f"🔍 Error Details - {execution['start_time_display']}"):
                                st.error(execution['error_message'])
                        
                        st.divider()
            else:
                st.info("No execution history found for this job.")
    
    except Exception as e:
        st.error(f"Error loading job history: {str(e)}")

def render_job_settings(user_id: int):
    """Render job management settings."""
    st.write("**Job Management Settings**")
    
    # Global settings
    st.write("**Scheduler Status**")
    if job_scheduler.scheduler.running:
        st.success("✅ Background scheduler is running")
        
        if st.button("🛑 Stop Scheduler", help="Stop all background jobs"):
            job_scheduler.stop()
            st.warning("Scheduler stopped. Jobs will not run until restarted.")
            st.rerun()
    else:
        st.warning("⚠️ Background scheduler is stopped")
        
        if st.button("▶️ Start Scheduler", help="Start background job processing"):
            job_scheduler.start()
            st.success("Scheduler started!")
            st.rerun()
    
    st.divider()
    
    # Bulk actions
    st.write("**Bulk Actions**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Failed Jobs", help="Remove all failed jobs"):
            try:
                # This would need to be implemented in the scheduler
                st.info("Feature coming soon!")
            except Exception as e:
                st.error(f"Error clearing failed jobs: {str(e)}")
    
    with col2:
        if st.button("📊 Export Job Data", help="Download job history as CSV"):
            try:
                jobs = job_scheduler.get_user_jobs(user_id)
                if jobs:
                    jobs_df = pd.DataFrame(jobs)
                    csv = jobs_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Jobs CSV",
                        csv,
                        f"job_history_{user_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No job data to export")
            except Exception as e:
                st.error(f"Error exporting job data: {str(e)}")
    
    st.divider()
    
    # Statistics
    st.write("**Job Statistics**")
    
    try:
        jobs = job_scheduler.get_user_jobs(user_id)
        
        if jobs:
            total_jobs = len(jobs)
            active_jobs = len([job for job in jobs if job['is_active']])
            failed_jobs = len([job for job in jobs if job['status'] == 'failed'])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Jobs", total_jobs)
            
            with col2:
                st.metric("Active Jobs", active_jobs)
            
            with col3:
                st.metric("Failed Jobs", failed_jobs)
            
            # Job type breakdown
            job_types = {}
            for job in jobs:
                job_type = job['type']
                job_types[job_type] = job_types.get(job_type, 0) + 1
            
            if job_types:
                st.write("**Job Types:**")
                for job_type, count in job_types.items():
                    st.write(f"• {job_type.replace('_', ' ').title()}: {count}")
        else:
            st.info("No job statistics available.")
    
    except Exception as e:
        st.error(f"Error loading job statistics: {str(e)}")

def render_sync_status_widget():
    """Render a compact sync status widget for the sidebar."""
    if 'current_user' not in st.session_state or not st.session_state.current_user:
        return
    
    user_id = st.session_state.current_user['id']
    
    try:
        jobs = job_scheduler.get_user_jobs(user_id)
        active_jobs = [job for job in jobs if job['is_active']]
        
        if active_jobs:
            st.sidebar.write("**🔄 Background Sync**")
            
            running_jobs = [job for job in active_jobs if job['status'] == 'running']
            if running_jobs:
                st.sidebar.success(f"✅ {len(running_jobs)} sync(s) running")
            
            failed_jobs = [job for job in active_jobs if job['status'] == 'failed']
            if failed_jobs:
                st.sidebar.error(f"❌ {len(failed_jobs)} sync(s) failed")
            
            # Quick manual sync button
            if st.sidebar.button("🔄 Quick Sync", help="Run manual sync now"):
                st.session_state.show_manual_sync = True
                st.rerun()
    
    except Exception:
        pass  # Silently handle errors in widget
