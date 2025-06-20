import streamlit as st
from typing import Dict, List, Any, Optional
from notification_system import NotificationManager, UserNotification, NotificationType, NotificationPriority
from datetime import datetime

class ErrorNotificationUI:
    """Specialized UI components for error notifications and troubleshooting."""

    def __init__(self):
        self.notification_manager = NotificationManager()

    def render_error_banner(self, error_type: str, error_message: str, 
                           action_steps: List[str] = None):
        """Render a prominent error banner with actionable steps."""
        st.error(f"🚨 **{error_type}**")

        with st.container():
            st.write(f"**Issue:** {error_message}")

            if action_steps:
                st.write("**What to do:**")
                for i, step in enumerate(action_steps, 1):
                    st.write(f"{i}. {step}")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("🔄 Retry Now", type="primary"):
                    st.info("Retrying operation...")
                    # Add retry logic here

            with col2:
                if st.button("📚 Get Help"):
                    self.show_help_modal(error_type)

            with col3:
                if st.button("✕ Dismiss"):
                    st.success("Error dismissed")

    def render_connectivity_status(self, integrations: List[Dict]):
        """Render connectivity status for all integrations."""
        st.subheader("🌐 Connection Status")

        if not integrations:
            st.info("No integrations configured")
            return

        # Group by status
        status_groups = {
            'connected': [],
            'error': [],
            'pending': []
        }

        for integration in integrations:
            status = integration.get('status', 'unknown')
            if status in status_groups:
                status_groups[status].append(integration)
            else:
                status_groups['error'].append(integration)

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "✅ Connected", 
                len(status_groups['connected']),
                help="Integrations working normally"
            )

        with col2:
            st.metric(
                "❌ Issues", 
                len(status_groups['error']),
                help="Integrations with errors"
            )

        with col3:
            st.metric(
                "⏳ Pending", 
                len(status_groups['pending']),
                help="Integrations being set up"
            )

        # Detailed status
        if status_groups['error']:
            st.subheader("🚨 Issues Requiring Attention")

            for integration in status_groups['error']:
                self.render_integration_error_card(integration)

        if status_groups['connected']:
            with st.expander("✅ Working Integrations"):
                for integration in status_groups['connected']:
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**{integration['display_name']}**")

                    with col2:
                        last_sync = integration.get('last_sync', 'Never')
                        st.caption(f"Last sync: {last_sync}")

                    with col3:
                        st.success("✅")

    def render_integration_error_card(self, integration: Dict):
        """Render an error card for a problematic integration."""
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.error(f"**{integration['display_name']}**")

                error_details = integration.get('error_details', {})
                error_message = error_details.get('message', 'Unknown error occurred')
                st.write(f"**Error:** {error_message}")

                # Show specific help based on error type
                error_type = self.classify_error(error_message)
                if error_type:
                    st.caption(f"**Type:** {error_type}")

                # Show last attempt
                last_error = integration.get('last_error_time')
                if last_error:
                    st.caption(f"**Last failed:** {last_error}")

            with col2:
                if st.button(f"🔧 Fix", key=f"fix_{integration['id']}"):
                    self.show_fix_modal(integration)

                if st.button(f"🔄 Retry", key=f"retry_{integration['id']}"):
                    st.info("Retrying connection...")

    def classify_error(self, error_message: str) -> str:
        """Classify error type for better user guidance."""
        if not error_message:
            return "Unknown"

        error_lower = error_message.lower()

        if any(word in error_lower for word in ['auth', 'login', 'credential', 'token']):
            return "Authentication Issue"
        elif any(word in error_lower for word in ['connection', 'network', 'timeout']):
            return "Connection Problem"
        elif any(word in error_lower for word in ['rate', 'limit', 'quota']):
            return "Rate Limiting"
        elif any(word in error_lower for word in ['permission', 'forbidden', 'access']):
            return "Permission Error"
        else:
            return "Technical Error"

    def show_fix_modal(self, integration: Dict):
        """Show detailed fix instructions in a modal."""
        with st.modal(f"Fix {integration['display_name']}"):
            error_message = integration.get('error_details', {}).get('message', '')
            error_type = self.classify_error(error_message)

            st.write(f"**Issue Type:** {error_type}")
            st.write(f"**Error Message:** {error_message}")

            # Provide specific instructions based on error type
            if error_type == "Authentication Issue":
                st.subheader("🔐 Authentication Fix Steps")
                st.write("1. Go to your broker's website and verify your login works")
                st.write("2. Check if your password was recently changed")
                st.write("3. Ensure API access is enabled in your broker account")
                st.write("4. Click 'Reconnect' below to enter new credentials")

                if st.button("🔗 Reconnect Integration", type="primary"):
                    st.success("Redirecting to reconnection flow...")

            elif error_type == "Connection Problem":
                st.subheader("🌐 Connection Troubleshooting")
                st.write("1. Check your internet connection")
                st.write("2. Verify the broker's services are operational")
                st.write("3. Try again in a few minutes")
                st.write("4. Contact support if the issue persists")

                if st.button("🔄 Test Connection", type="primary"):
                    st.info("Testing connection...")

            elif error_type == "Rate Limiting":
                st.subheader("⚡ Rate Limit Solutions")
                st.write("1. Wait 1 hour before trying again")
                st.write("2. Reduce sync frequency in settings")
                st.write("3. Check if other apps are using the same credentials")

                if st.button("⏰ Schedule Retry", type="primary"):
                    st.success("Will retry automatically in 1 hour")

            else:
                st.subheader("🛠️ General Troubleshooting")
                st.write("1. Try disconnecting and reconnecting the integration")
                st.write("2. Check for any recent changes to your broker account")
                st.write("3. Contact support with the error details above")

                if st.button("📞 Contact Support", type="primary"):
                    st.info("Support contact information will be provided")

    def show_help_modal(self, error_type: str):
        """Show general help information."""
        with st.modal(f"Help: {error_type}"):
            st.write("Detailed help information would go here based on the error type.")

            # Add links to documentation, FAQ, support, etc.
            st.write("**Useful Resources:**")
            st.write("• [FAQ and Common Issues](#)")
            st.write("• [Integration Setup Guide](#)")
            st.write("• [Contact Support](#)")

    def render_sync_progress_indicator(self, active_syncs: List[Dict]):
        """Render a progress indicator for active syncs."""
        if not active_syncs:
            return

        st.write("**🔄 Active Sync Operations**")

        for sync in active_syncs:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.write(f"**{sync['provider_name']}**")

            with col2:
                # Show progress bar or spinner
                if sync['status'] == 'running':
                    progress = min(1.0, sync.get('progress', 0.5))
                    st.progress(progress)
                else:
                    st.write(f"Status: {sync['status']}")

            with col3:
                if st.button("⏹️", key=f"stop_{sync['job_id']}", help="Cancel"):
                    st.warning("Cancelling sync...")

def render_error_troubleshooting_guide():
    """Render comprehensive error troubleshooting guide."""
    st.subheader("🆘 Troubleshooting Guide")

    troubleshooting_sections = [
        {
            "title": "🔐 Login & Authentication Issues",
            "problems": [
                "Can't connect to broker account",
                "Authentication failed",
                "Invalid credentials error",
                "Token expired messages"
            ],
            "solutions": [
                "Verify your username and password on the broker's website",
                "Check if 2FA is required and properly configured",
                "Ensure API access is enabled in your broker account settings",
                "Try generating new API keys if applicable",
                "Contact your broker if account is locked or suspended"
            ]
        },
        {
            "title": "🌐 Connection Problems",
            "problems": [
                "Connection timeout errors",
                "Unable to reach broker servers",
                "Network connection failed",
                "Server unavailable messages"
            ],
            "solutions": [
                "Check your internet connection",
                "Verify broker's service status page",
                "Try connecting during off-peak hours",
                "Disable VPN if using one",
                "Contact your network administrator if on corporate network"
            ]
        },
        {
            "title": "📊 Data Sync Issues",
            "problems": [
                "No trades showing up",
                "Incomplete trade data",
                "Wrong trade counts",
                "Missing recent trades"
            ],
            "solutions": [
                "Check the date range settings",
                "Verify account permissions include trade history access",
                "Try syncing smaller date ranges",
                "Contact broker about API data availability",
                "Check if there are account-specific restrictions"
            ]
        },
        {
            "title": "⚡ Performance Issues",
            "problems": [
                "Sync taking too long",
                "Application running slowly",
                "Frequent timeouts",
                "Rate limit exceeded"
            ],
            "solutions": [
                "Reduce sync frequency",
                "Sync smaller date ranges",
                "Close other applications using the same broker API",
                "Wait and retry during off-peak hours",
                "Contact support about API rate limits"
            ]
        }
    ]

    for section in troubleshooting_sections:
        with st.expander(section["title"]):
            st.write("**Common Problems:**")
            for problem in section["problems"]:
                st.write(f"• {problem}")

            st.write("**Solutions:**")
            for solution in section["solutions"]:
                st.write(f"• {solution}")

def render_error_notification_with_context(error_details: Dict, show_troubleshooting: bool = True):
    """Render error notification with context and auto-support."""
    st.error(f"❌ **Error:** {error_details.get('message', 'Unknown error occurred')}")

    # Auto-support suggestion
    from documentation.auto_support import render_auto_support_widget
    error_message = error_details.get('message', '')

    st.markdown("---")
    st.subheader("🤖 Instant Help")
    render_auto_support_widget(error_message=error_message)

    # Error details
    with st.expander("🔍 Error Details", expanded=False):
        if error_details.get('error_type'):
            st.write(f"**Type:** {error_details['error_type']}")
        if error_details.get('timestamp'):
            st.write(f"**Time:** {error_details['timestamp']}")
        if error_details.get('context'):
            st.write(f"**Context:** {error_details['context']}")

    if show_troubleshooting:
        render_error_troubleshooting_guide()

# Global error notification UI instance
error_ui = ErrorNotificationUI()