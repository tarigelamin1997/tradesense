
import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import threading
import queue
from logging_manager import log_info, log_warning, LogCategory
from sync_engine import sync_engine, SyncStatus
from integration_manager import IntegrationManager

class NotificationType(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    SYNC_STATUS = "sync_status"

class NotificationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class UserNotification:
    """Represents a user notification with all necessary details."""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    action_steps: Optional[List[str]] = None
    timestamp: datetime = None
    dismissible: bool = True
    auto_dismiss_seconds: Optional[int] = None
    category: str = "general"
    user_id: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class NotificationManager:
    """Manages user notifications and real-time status updates."""
    
    def __init__(self):
        self.notifications: Dict[str, UserNotification] = {}
        self.notification_queue = queue.Queue()
        self.sync_status_cache = {}
        self.integration_manager = IntegrationManager()
        
    def add_notification(self, notification: UserNotification):
        """Add a new notification."""
        self.notifications[notification.id] = notification
        self.notification_queue.put(notification)
        
        log_info(f"Notification added: {notification.title}",
                details={'type': notification.type.value, 'priority': notification.priority.value},
                category=LogCategory.USER_ACTION)
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification."""
        if notification_id in self.notifications:
            del self.notifications[notification_id]
    
    def get_active_notifications(self, user_id: Optional[int] = None) -> List[UserNotification]:
        """Get active notifications for a user."""
        notifications = []
        current_time = datetime.now()
        
        for notification in list(self.notifications.values()):
            # Filter by user if specified
            if user_id and notification.user_id and notification.user_id != user_id:
                continue
            
            # Auto-dismiss expired notifications
            if (notification.auto_dismiss_seconds and 
                current_time > notification.timestamp + timedelta(seconds=notification.auto_dismiss_seconds)):
                self.dismiss_notification(notification.id)
                continue
                
            notifications.append(notification)
        
        # Sort by priority and timestamp
        return sorted(notifications, 
                     key=lambda x: (x.priority.value, x.timestamp), 
                     reverse=True)
    
    def create_sync_notification(self, sync_job_id: str, status: SyncStatus, 
                               provider_name: str, user_id: int,
                               error_message: str = None) -> UserNotification:
        """Create a sync-specific notification."""
        notification_id = f"sync_{sync_job_id}"
        
        if status == SyncStatus.RUNNING:
            return UserNotification(
                id=notification_id,
                type=NotificationType.INFO,
                priority=NotificationPriority.LOW,
                title="🔄 Sync in Progress",
                message=f"Syncing data from {provider_name}...",
                category="sync",
                user_id=user_id,
                auto_dismiss_seconds=300  # Auto-dismiss after 5 minutes
            )
        
        elif status == SyncStatus.SUCCESS:
            return UserNotification(
                id=notification_id,
                type=NotificationType.SUCCESS,
                priority=NotificationPriority.MEDIUM,
                title="✅ Sync Completed",
                message=f"Successfully synced data from {provider_name}",
                category="sync",
                user_id=user_id,
                auto_dismiss_seconds=10
            )
        
        elif status == SyncStatus.ERROR:
            error_details, action_steps = self._analyze_sync_error(error_message, provider_name)
            
            return UserNotification(
                id=notification_id,
                type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH,
                title="❌ Sync Failed",
                message=f"Failed to sync data from {provider_name}",
                details=error_details,
                action_steps=action_steps,
                category="sync",
                user_id=user_id,
                dismissible=True
            )
        
        elif status == SyncStatus.CANCELLED:
            return UserNotification(
                id=notification_id,
                type=NotificationType.WARNING,
                priority=NotificationPriority.LOW,
                title="⏹️ Sync Cancelled",
                message=f"Sync cancelled for {provider_name}",
                category="sync",
                user_id=user_id,
                auto_dismiss_seconds=5
            )
    
    def _analyze_sync_error(self, error_message: str, provider_name: str) -> tuple:
        """Analyze sync error and provide helpful details and action steps."""
        error_details = {"raw_error": error_message}
        action_steps = []
        
        if not error_message:
            return error_details, ["Contact support for assistance"]
        
        error_lower = error_message.lower()
        
        # Authentication errors
        if any(keyword in error_lower for keyword in ['auth', 'credential', 'login', 'token', 'unauthorized']):
            error_details.update({
                "category": "Authentication Error",
                "description": "Your login credentials for this broker/platform have expired or are invalid.",
                "common_causes": [
                    "Password was changed on the broker platform",
                    "API keys have expired",
                    "Two-factor authentication is required",
                    "Account was locked or suspended"
                ]
            })
            action_steps = [
                "1. Go to the Integrations page",
                "2. Click 'Reconnect' for this integration",
                "3. Enter your current credentials",
                "4. Ensure 2FA is properly configured if required",
                "5. Contact your broker if account issues persist"
            ]
        
        # Connection errors
        elif any(keyword in error_lower for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            error_details.update({
                "category": "Connection Error",
                "description": "Unable to connect to the broker's servers.",
                "common_causes": [
                    "Broker server maintenance",
                    "Internet connectivity issues",
                    "Firewall blocking connections",
                    "Broker API rate limits exceeded"
                ]
            })
            action_steps = [
                "1. Check your internet connection",
                "2. Wait 5-10 minutes and try again",
                "3. Check broker's status page for maintenance",
                "4. Contact support if issue persists"
            ]
        
        # Rate limiting
        elif any(keyword in error_lower for keyword in ['rate limit', 'quota', 'too many requests']):
            error_details.update({
                "category": "Rate Limit Exceeded",
                "description": "Too many requests sent to the broker's API.",
                "common_causes": [
                    "Multiple sync operations running simultaneously",
                    "Broker has strict API limits",
                    "Other applications using the same credentials"
                ]
            })
            action_steps = [
                "1. Wait 1 hour before trying again",
                "2. Reduce sync frequency in settings",
                "3. Ensure no other apps are using the same API keys",
                "4. Contact broker to increase API limits if needed"
            ]
        
        # Data format errors
        elif any(keyword in error_lower for keyword in ['format', 'parse', 'invalid data', 'schema']):
            error_details.update({
                "category": "Data Format Error",
                "description": "The broker returned data in an unexpected format.",
                "common_causes": [
                    "Broker changed their data format",
                    "Corrupted data transmission",
                    "Connector needs updating"
                ]
            })
            action_steps = [
                "1. Try syncing again in a few minutes",
                "2. Check if there are any app updates available",
                "3. Contact support - this may require a connector update"
            ]
        
        # Permission errors
        elif any(keyword in error_lower for keyword in ['permission', 'forbidden', 'access denied']):
            error_details.update({
                "category": "Permission Error",
                "description": "Your account doesn't have permission to access trade data.",
                "common_causes": [
                    "Account type doesn't support API access",
                    "Trade data access not enabled",
                    "API permissions were revoked"
                ]
            })
            action_steps = [
                "1. Check your account settings with the broker",
                "2. Ensure API access is enabled for your account type",
                "3. Contact your broker to enable trade data access",
                "4. Verify your subscription includes API features"
            ]
        
        # Generic error fallback
        else:
            error_details.update({
                "category": "Unknown Error",
                "description": "An unexpected error occurred during sync.",
                "technical_details": error_message[:500]  # Limit length
            })
            action_steps = [
                "1. Try syncing again in a few minutes",
                "2. Check the integration status page",
                "3. Contact support with the error details below"
            ]
        
        return error_details, action_steps
    
    def create_system_notification(self, title: str, message: str, 
                                 notification_type: NotificationType = NotificationType.INFO,
                                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                                 action_steps: List[str] = None) -> UserNotification:
        """Create a system-wide notification."""
        return UserNotification(
            id=f"system_{int(time.time())}",
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            action_steps=action_steps,
            category="system"
        )

# Global notification manager
notification_manager = NotificationManager()

def render_notification_center(user_id: Optional[int] = None):
    """Render the main notification center in the sidebar."""
    with st.sidebar:
        st.subheader("🔔 Notifications")
        
        notifications = notification_manager.get_active_notifications(user_id)
        
        if not notifications:
            st.success("✅ All caught up!")
            return
        
        # Show notification count by priority
        critical_count = len([n for n in notifications if n.priority == NotificationPriority.CRITICAL])
        high_count = len([n for n in notifications if n.priority == NotificationPriority.HIGH])
        
        if critical_count > 0:
            st.error(f"🚨 {critical_count} critical issue(s)")
        elif high_count > 0:
            st.warning(f"⚠️ {high_count} important issue(s)")
        
        # Display notifications
        for notification in notifications[:5]:  # Show top 5
            render_notification_item(notification)
        
        if len(notifications) > 5:
            st.caption(f"... and {len(notifications) - 5} more")

def render_notification_item(notification: UserNotification):
    """Render a single notification item."""
    # Choose icon and color based on type
    type_config = {
        NotificationType.SUCCESS: {"icon": "✅", "color": "success"},
        NotificationType.WARNING: {"icon": "⚠️", "color": "warning"},
        NotificationType.ERROR: {"icon": "❌", "color": "error"},
        NotificationType.INFO: {"icon": "ℹ️", "color": "info"},
        NotificationType.SYNC_STATUS: {"icon": "🔄", "color": "info"}
    }
    
    config = type_config.get(notification.type, {"icon": "📢", "color": "info"})
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if notification.type == NotificationType.SUCCESS:
                st.success(f"{config['icon']} {notification.title}")
            elif notification.type == NotificationType.WARNING:
                st.warning(f"{config['icon']} {notification.title}")
            elif notification.type == NotificationType.ERROR:
                st.error(f"{config['icon']} {notification.title}")
            else:
                st.info(f"{config['icon']} {notification.title}")
            
            st.caption(notification.message)
        
        with col2:
            if notification.dismissible:
                if st.button("✕", key=f"dismiss_{notification.id}", help="Dismiss"):
                    notification_manager.dismiss_notification(notification.id)
                    st.rerun()

def render_detailed_notification_modal(notification: UserNotification):
    """Render detailed notification view in a modal."""
    with st.modal(f"{notification.title}"):
        st.write(f"**Message:** {notification.message}")
        
        if notification.details:
            st.subheader("📋 Details")
            
            details = notification.details
            
            if "category" in details:
                st.write(f"**Error Type:** {details['category']}")
            
            if "description" in details:
                st.write(f"**Description:** {details['description']}")
            
            if "common_causes" in details:
                st.write("**Common Causes:**")
                for cause in details["common_causes"]:
                    st.write(f"• {cause}")
            
            if "technical_details" in details:
                with st.expander("🔧 Technical Details"):
                    st.code(details["technical_details"])
        
        if notification.action_steps:
            st.subheader("🛠️ How to Fix")
            for step in notification.action_steps:
                st.write(step)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Mark as Resolved", type="primary"):
                notification_manager.dismiss_notification(notification.id)
                st.success("Notification dismissed!")
                st.rerun()
        
        with col2:
            if st.button("📞 Contact Support"):
                st.info("Support contact information will be displayed here")

def render_real_time_sync_status(user_id: int):
    """Render real-time sync status widget."""
    st.subheader("🔄 Real-time Sync Status")
    
    # Get active sync jobs
    active_jobs = []
    if sync_engine.running:
        for job_id, job in sync_engine.active_jobs.items():
            if job.user_id == user_id:
                job_info = sync_engine.get_sync_status(job_id)
                if job_info:
                    active_jobs.append(job_info)
    
    if not active_jobs:
        st.success("✅ No active sync operations")
        return
    
    st.write(f"**{len(active_jobs)} active sync operation(s)**")
    
    for job in active_jobs:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                status_icons = {
                    'pending': '⏳',
                    'running': '🔄',
                    'success': '✅',
                    'error': '❌',
                    'cancelled': '⏹️'
                }
                
                icon = status_icons.get(job['status'], '❓')
                st.write(f"{icon} **{job['provider_name']}**")
                
                if job['status'] == 'running' and job['started_at']:
                    started = datetime.fromisoformat(job['started_at'])
                    duration = datetime.now() - started
                    st.caption(f"Running for {duration.seconds//60}m {duration.seconds%60}s")
            
            with col2:
                if job['status'] == 'running':
                    # Show progress bar for running jobs
                    progress = min(1.0, (time.time() % 30) / 30)  # Simulated progress
                    st.progress(progress)
                elif job['records_processed'] > 0:
                    st.write(f"{job['records_processed']} records")
            
            with col3:
                if job['status'] in ['pending', 'running']:
                    if st.button("❌", key=f"cancel_{job['job_id']}", help="Cancel"):
                        if sync_engine.cancel_sync_job(job['job_id']):
                            st.success("Sync cancelled")
                            st.rerun()

def show_error_help_center():
    """Show comprehensive error help center."""
    st.subheader("🆘 Error Help Center")
    
    st.write("**Common Issues and Solutions:**")
    
    help_sections = {
        "🔐 Authentication Problems": {
            "description": "Login or credential issues with your broker accounts",
            "solutions": [
                "Check if your password was recently changed",
                "Verify 2FA settings are correctly configured",
                "Ensure API access is enabled on your broker account",
                "Try disconnecting and reconnecting the integration"
            ]
        },
        "🌐 Connection Issues": {
            "description": "Problems connecting to broker servers",
            "solutions": [
                "Check your internet connection",
                "Wait for broker server maintenance to complete",
                "Try syncing during off-peak hours",
                "Contact your broker's technical support"
            ]
        },
        "⚡ Rate Limiting": {
            "description": "Too many API requests sent too quickly",
            "solutions": [
                "Reduce sync frequency in settings",
                "Wait before retrying failed syncs",
                "Ensure no other apps are using the same credentials",
                "Contact broker to discuss API limits"
            ]
        },
        "📊 Data Format Issues": {
            "description": "Problems processing trade data from your broker",
            "solutions": [
                "Update to the latest version of the app",
                "Try syncing again after a few minutes",
                "Contact support if the issue persists",
                "Check if your broker recently changed their data format"
            ]
        }
    }
    
    for title, info in help_sections.items():
        with st.expander(title):
            st.write(info["description"])
            st.write("**Solutions:**")
            for solution in info["solutions"]:
                st.write(f"• {solution}")

def create_sync_status_notification(job_id: str, status: SyncStatus, 
                                  provider_name: str, user_id: int,
                                  error_message: str = None):
    """Create and add a sync status notification."""
    notification = notification_manager.create_sync_notification(
        job_id, status, provider_name, user_id, error_message
    )
    notification_manager.add_notification(notification)

def create_system_alert(title: str, message: str, 
                       notification_type: NotificationType = NotificationType.INFO,
                       priority: NotificationPriority = NotificationPriority.MEDIUM,
                       action_steps: List[str] = None):
    """Create and add a system alert."""
    notification = notification_manager.create_system_notification(
        title, message, notification_type, priority, action_steps
    )
    notification_manager.add_notification(notification)

# Integration with existing sync engine
def setup_sync_notifications():
    """Setup sync notifications integration."""
    def sync_callback(job, result):
        """Callback for sync job completion."""
        if result:
            if result.get('status') == 'success':
                create_sync_status_notification(
                    job.job_id, SyncStatus.SUCCESS, 
                    job.provider_name, job.user_id
                )
            elif result.get('status') == 'error':
                create_sync_status_notification(
                    job.job_id, SyncStatus.ERROR,
                    job.provider_name, job.user_id,
                    result.get('error')
                )
    
    sync_engine.register_sync_callback(sync_callback)

# Initialize sync notifications
setup_sync_notifications()
import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import threading
import queue

class NotificationType(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    SYNC_STATUS = "sync_status"

class NotificationPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class UserNotification:
    """Represents a user notification with all necessary details."""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    action_steps: Optional[List[str]] = None
    timestamp: datetime = None
    dismissible: bool = True
    auto_dismiss_seconds: Optional[int] = None
    category: str = "general"
    user_id: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class NotificationManager:
    """Manages user notifications and real-time status updates."""
    
    def __init__(self):
        self.notifications: Dict[str, UserNotification] = {}
        self.notification_queue = queue.Queue()
        
    def add_notification(self, notification: UserNotification):
        """Add a new notification."""
        self.notifications[notification.id] = notification
        self.notification_queue.put(notification)
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss a notification."""
        if notification_id in self.notifications:
            del self.notifications[notification_id]
    
    def get_active_notifications(self, user_id: Optional[int] = None) -> List[UserNotification]:
        """Get active notifications for a user."""
        notifications = []
        current_time = datetime.now()
        
        for notification in list(self.notifications.values()):
            # Filter by user if specified
            if user_id and notification.user_id and notification.user_id != user_id:
                continue
            
            # Auto-dismiss expired notifications
            if (notification.auto_dismiss_seconds and 
                current_time > notification.timestamp + timedelta(seconds=notification.auto_dismiss_seconds)):
                self.dismiss_notification(notification.id)
                continue
                
            notifications.append(notification)
        
        # Sort by priority and timestamp
        return sorted(notifications, 
                     key=lambda x: (x.priority.value, x.timestamp), 
                     reverse=True)
    
    def create_system_notification(self, title: str, message: str, 
                                 notification_type: NotificationType = NotificationType.INFO,
                                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                                 action_steps: List[str] = None) -> UserNotification:
        """Create a system-wide notification."""
        return UserNotification(
            id=f"system_{int(time.time())}",
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            action_steps=action_steps,
            category="system"
        )

# Global notification manager
notification_manager = NotificationManager()

def render_notification_center(user_id: Optional[int] = None):
    """Render the main notification center in the sidebar."""
    with st.sidebar:
        st.subheader("🔔 Notifications")
        
        notifications = notification_manager.get_active_notifications(user_id)
        
        if not notifications:
            st.success("✅ All caught up!")
            return
        
        # Show notification count by priority
        critical_count = len([n for n in notifications if n.priority == NotificationPriority.CRITICAL])
        high_count = len([n for n in notifications if n.priority == NotificationPriority.HIGH])
        
        if critical_count > 0:
            st.error(f"🚨 {critical_count} critical issue(s)")
        elif high_count > 0:
            st.warning(f"⚠️ {high_count} important issue(s)")
        
        # Display notifications
        for notification in notifications[:5]:  # Show top 5
            render_notification_item(notification)
        
        if len(notifications) > 5:
            st.caption(f"... and {len(notifications) - 5} more")

def render_notification_item(notification: UserNotification):
    """Render a single notification item."""
    # Choose icon and color based on type
    type_config = {
        NotificationType.SUCCESS: {"icon": "✅", "color": "success"},
        NotificationType.WARNING: {"icon": "⚠️", "color": "warning"},
        NotificationType.ERROR: {"icon": "❌", "color": "error"},
        NotificationType.INFO: {"icon": "ℹ️", "color": "info"},
        NotificationType.SYNC_STATUS: {"icon": "🔄", "color": "info"}
    }
    
    config = type_config.get(notification.type, {"icon": "📢", "color": "info"})
    
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if notification.type == NotificationType.SUCCESS:
                st.success(f"{config['icon']} {notification.title}")
            elif notification.type == NotificationType.WARNING:
                st.warning(f"{config['icon']} {notification.title}")
            elif notification.type == NotificationType.ERROR:
                st.error(f"{config['icon']} {notification.title}")
            else:
                st.info(f"{config['icon']} {notification.title}")
            
            st.caption(notification.message)
        
        with col2:
            if notification.dismissible:
                if st.button("✕", key=f"dismiss_{notification.id}", help="Dismiss"):
                    notification_manager.dismiss_notification(notification.id)
                    st.rerun()

def create_system_alert(title: str, message: str, 
                       notification_type: NotificationType = NotificationType.INFO,
                       priority: NotificationPriority = NotificationPriority.MEDIUM,
                       action_steps: List[str] = None):
    """Create and add a system alert."""
    notification = notification_manager.create_system_notification(
        title, message, notification_type, priority, action_steps
    )
    notification_manager.add_notification(notification)
