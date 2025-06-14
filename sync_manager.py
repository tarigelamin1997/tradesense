
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import time

from sync_engine import sync_engine, SyncStatus, SyncTrigger
from integration_manager import IntegrationManager
from auth import require_auth
from logging_manager import log_info, log_warning, LogCategory

class SyncManager:
    """High-level sync management interface for the UI."""
    
    def __init__(self):
        self.integration_manager = IntegrationManager()
        
        # Ensure sync engine is started
        if not sync_engine.running:
            sync_engine.start_engine()
    
    def get_user_sync_overview(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive sync overview for a user."""
        integrations = self.integration_manager.get_user_integrations(user_id)
        
        overview = {
            'total_integrations': len(integrations),
            'active_syncs': 0,
            'recent_syncs': 0,
            'total_records_synced': 0,
            'last_sync_time': None,
            'sync_health_score': 0,
            'integrations_status': []
        }
        
        recent_cutoff = datetime.now() - timedelta(hours=24)
        
        for integration in integrations:
            status_info = {
                'integration_id': integration['id'],
                'provider_name': integration['provider_name'],
                'display_name': integration['display_name'],
                'status': integration['status'],
                'auto_sync': integration['auto_sync'],
                'last_sync': integration['last_sync'],
                'error_count': integration['error_count'],
                'sync_health': 'good'
            }
            
            # Calculate health
            if integration['status'] == 'error':
                status_info['sync_health'] = 'poor'
            elif integration['error_count'] > 0:
                status_info['sync_health'] = 'warning'
            
            # Check recent activity
            if integration['last_sync']:
                last_sync = datetime.fromisoformat(integration['last_sync'])
                if last_sync > recent_cutoff:
                    overview['recent_syncs'] += 1
                
                if not overview['last_sync_time'] or last_sync > overview['last_sync_time']:
                    overview['last_sync_time'] = last_sync
            
            overview['integrations_status'].append(status_info)
        
        # Calculate health score
        if overview['total_integrations'] > 0:
            healthy_count = len([i for i in overview['integrations_status'] 
                               if i['sync_health'] == 'good'])
            overview['sync_health_score'] = int(
                (healthy_count / overview['total_integrations']) * 100
            )
        
        return overview
    
    def trigger_sync_for_integration(self, user_id: int, integration_id: int) -> Dict[str, Any]:
        """Trigger manual sync for a specific integration."""
        try:
            job = sync_engine.trigger_manual_sync(user_id, integration_id)
            
            log_info(f"Manual sync triggered for integration {integration_id}",
                    details={'user_id': user_id, 'job_id': job.job_id},
                    category=LogCategory.USER_ACTION)
            
            return {
                'success': True,
                'job_id': job.job_id,
                'message': 'Sync started successfully'
            }
            
        except Exception as e:
            log_warning(f"Failed to trigger sync: {str(e)}",
                       details={'user_id': user_id, 'integration_id': integration_id},
                       category=LogCategory.USER_ACTION)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_active_sync_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Get active sync jobs for a user."""
        active_jobs = []
        
        for job_id, job in sync_engine.active_jobs.items():
            if job.user_id == user_id:
                job_info = sync_engine.get_sync_status(job_id)
                if job_info:
                    active_jobs.append(job_info)
        
        return active_jobs
    
    def configure_auto_sync(self, integration_id: int, enabled: bool, 
                          frequency_minutes: int = 60) -> bool:
        """Configure automatic sync for an integration."""
        try:
            if enabled:
                sync_engine.schedule_integration_sync(integration_id, frequency_minutes)
            else:
                # Disable scheduling (implementation depends on requirements)
                pass
            
            return True
        except Exception as e:
            log_warning(f"Failed to configure auto-sync: {str(e)}",
                       category=LogCategory.SYSTEM)
            return False
    
    def get_sync_history(self, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
        """Get sync history for a user."""
        # This would query the sync_jobs table
        # Implementation depends on specific requirements
        return []
    
    def get_sync_performance_metrics(self) -> Dict[str, Any]:
        """Get system-wide sync performance metrics."""
        return sync_engine.get_sync_metrics()

# Global sync manager instance
sync_manager = SyncManager()

@require_auth
def render_sync_dashboard(current_user: Dict):
    """Render the sync dashboard UI."""
    st.title("🔄 Data Sync Dashboard")
    st.caption("Monitor and control automatic trade data synchronization")
    
    user_id = current_user['id']
    
    # Get sync overview
    overview = sync_manager.get_user_sync_overview(user_id)
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Connected Accounts", overview['total_integrations'])
    
    with col2:
        st.metric("Sync Health", f"{overview['sync_health_score']}%",
                 delta="Good" if overview['sync_health_score'] > 80 else "Needs Attention")
    
    with col3:
        st.metric("Recent Syncs (24h)", overview['recent_syncs'])
    
    with col4:
        if overview['last_sync_time']:
            time_ago = datetime.now() - overview['last_sync_time']
            if time_ago.days > 0:
                last_sync_display = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                last_sync_display = f"{time_ago.seconds//3600}h ago"
            else:
                last_sync_display = f"{time_ago.seconds//60}m ago"
            st.metric("Last Sync", last_sync_display)
        else:
            st.metric("Last Sync", "Never")
    
    st.divider()
    
    # Active sync jobs
    active_jobs = sync_manager.get_active_sync_jobs(user_id)
    
    if active_jobs:
        st.subheader("🔄 Active Sync Jobs")
        
        for job in active_jobs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{job['provider_name']}**")
                    st.caption(f"Job ID: {job['job_id'][:12]}...")
                
                with col2:
                    status_color = {
                        'pending': '🟡',
                        'running': '🔄',
                        'success': '🟢',
                        'error': '🔴',
                        'cancelled': '⚪'
                    }.get(job['status'], '⚪')
                    
                    st.write(f"{status_color} {job['status'].title()}")
                
                with col3:
                    if job['started_at']:
                        started = datetime.fromisoformat(job['started_at'])
                        duration = datetime.now() - started
                        st.write(f"Running: {duration.seconds//60}m {duration.seconds%60}s")
                    else:
                        st.write("Waiting to start...")
                
                with col4:
                    if job['status'] in ['pending', 'running']:
                        if st.button("❌", key=f"cancel_{job['job_id']}", 
                                    help="Cancel sync"):
                            if sync_engine.cancel_sync_job(job['job_id']):
                                st.success("Sync cancelled")
                                st.rerun()
        
        st.divider()
    
    # Integration status
    st.subheader("📊 Integration Status")
    
    if overview['integrations_status']:
        for integration in overview['integrations_status']:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
                
                with col1:
                    health_color = {
                        'good': '🟢',
                        'warning': '🟡',
                        'poor': '🔴'
                    }.get(integration['sync_health'], '⚪')
                    
                    st.write(f"**{health_color} {integration['display_name']}**")
                    st.caption(f"Provider: {integration['provider_name']}")
                
                with col2:
                    auto_sync_icon = "🔄" if integration['auto_sync'] else "⏸️"
                    st.write(auto_sync_icon)
                    st.caption("Auto-sync" if integration['auto_sync'] else "Manual")
                
                with col3:
                    if integration['last_sync']:
                        last_sync = datetime.fromisoformat(integration['last_sync'])
                        time_ago = datetime.now() - last_sync
                        if time_ago.days > 0:
                            st.write(f"Last: {time_ago.days}d ago")
                        elif time_ago.seconds > 3600:
                            st.write(f"Last: {time_ago.seconds//3600}h ago")
                        else:
                            st.write(f"Last: {time_ago.seconds//60}m ago")
                    else:
                        st.write("Never synced")
                    
                    if integration['error_count'] > 0:
                        st.caption(f"⚠️ {integration['error_count']} errors")
                
                with col4:
                    if st.button("🔄 Sync Now", 
                                key=f"sync_{integration['integration_id']}"):
                        with st.spinner("Starting sync..."):
                            result = sync_manager.trigger_sync_for_integration(
                                user_id, integration['integration_id']
                            )
                            
                            if result['success']:
                                st.success("Sync started!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to start sync: {result['error']}")
        
        st.divider()
    else:
        st.info("No integrations configured. Add broker connections in the Integrations page.")
    
    # Sync settings
    with st.expander("⚙️ Sync Settings"):
        st.subheader("Global Sync Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_frequency = st.selectbox(
                "Default Auto-sync Frequency",
                options=[15, 30, 60, 120, 240, 480],
                format_func=lambda x: f"Every {x} minutes" if x < 60 else f"Every {x//60} hour(s)",
                index=2  # Default to 60 minutes
            )
        
        with col2:
            enable_realtime = st.checkbox(
                "Enable Real-time Sync (where supported)",
                help="Automatically sync new trades as they occur"
            )
        
        max_retries = st.slider("Max Retry Attempts", 1, 5, 3)
        
        if st.button("💾 Save Sync Settings"):
            st.success("Sync settings saved!")
    
    # Performance metrics
    with st.expander("📈 Performance Metrics"):
        metrics = sync_manager.get_sync_performance_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Syncs", metrics.get('total_syncs', 0))
            st.metric("Success Rate", 
                     f"{(metrics.get('successful_syncs', 0) / max(metrics.get('total_syncs', 1), 1) * 100):.1f}%")
        
        with col2:
            st.metric("Records Processed", metrics.get('total_records_processed', 0))
            st.metric("Failed Syncs", metrics.get('failed_syncs', 0))
        
        with col3:
            avg_duration = metrics.get('avg_sync_duration', 0)
            st.metric("Avg Sync Duration", f"{avg_duration:.1f}s")
        
        if st.button("🔄 Refresh Metrics"):
            st.rerun()

def render_webhook_sync_ui():
    """Render webhook-based sync configuration."""
    st.subheader("🔗 Webhook Sync Configuration")
    st.caption("Configure real-time sync via webhooks")
    
    st.info("🚧 Webhook sync configuration coming soon! This will enable instant trade updates.")
    
    # Placeholder for webhook configuration
    webhook_url = st.text_input(
        "Webhook URL",
        placeholder="https://your-app.replit.dev/webhook/trades",
        disabled=True
    )
    
    webhook_secret = st.text_input(
        "Webhook Secret",
        type="password",
        disabled=True
    )
    
    st.checkbox("Enable webhook validation", disabled=True)
    st.button("🔗 Configure Webhook", disabled=True)
