
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from documentation.auto_support import AutoSupportSystem

class ErrorNotificationUI:
    """Enhanced error notification and troubleshooting interface."""
    
    def __init__(self):
        self.auto_support = AutoSupportSystem()
    
    def render_error_interface(self):
        """Render the main error notification interface."""
        st.title("🛠️ TradeSense Support Center")
        
        # Quick status check
        self._render_system_status()
        
        # Main support tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🆘 Get Help", "📋 Known Issues", "💬 Contact Support", "📚 Troubleshooting"
        ])
        
        with tab1:
            self._render_help_interface()
        with tab2:
            self._render_known_issues()
        with tab3:
            self._render_contact_support()
        with tab4:
            self._render_troubleshooting_guide()
    
    def _render_system_status(self):
        """Render system status indicator."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 🟢 System Status: Operational")
        
        with col2:
            if st.button("🔄 Refresh Status"):
                st.rerun()
        
        with col3:
            if st.button("📊 Status Page"):
                st.info("🔗 Full status page: https://status.tradesense.app")
    
    def _render_help_interface(self):
        """Render interactive help interface."""
        st.header("🆘 Describe Your Issue")
        
        # Issue description form
        with st.form("support_form"):
            issue_type = st.selectbox(
                "What type of issue are you experiencing?",
                [
                    "Data upload problems",
                    "Login/authentication issues", 
                    "Analytics not working",
                    "Broker connection problems",
                    "Performance issues",
                    "Report generation errors",
                    "General questions",
                    "Other"
                ]
            )
            
            error_message = st.text_area(
                "Any error messages you're seeing?",
                placeholder="Paste any error messages here...",
                height=100
            )
            
            description = st.text_area(
                "Describe what you were trying to do:",
                placeholder="I was trying to...",
                height=100
            )
            
            submitted = st.form_submit_button("🔍 Get Help")
            
            if submitted:
                self._process_support_request(issue_type, error_message, description)
    
    def _process_support_request(self, issue_type: str, error_message: str, description: str):
        """Process support request and provide automated suggestions."""
        st.subheader("💡 Suggested Solutions")
        
        # Get automated suggestions
        suggestion = self.auto_support.analyze_issue(error_message, description)
        
        if suggestion:
            # Display confidence level
            confidence_color = "🟢" if suggestion.confidence >= 0.8 else "🟡" if suggestion.confidence >= 0.6 else "🔴"
            st.markdown(f"{confidence_color} **Confidence:** {suggestion.confidence:.0%}")
            
            # Display solution steps
            st.markdown(f"**Issue Type:** {suggestion.issue_type}")
            
            for i, step in enumerate(suggestion.solution_steps, 1):
                st.markdown(f"{i}. {step}")
            
            # Display additional resources
            if suggestion.additional_resources:
                st.subheader("📚 Additional Resources")
                for resource in suggestion.additional_resources:
                    st.markdown(f"• [{resource['title']}]({resource['url']})")
            
            # Feedback on suggestion
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 This helped"):
                    st.success("Thanks for your feedback!")
            with col2:
                if st.button("👎 Still need help"):
                    self._render_escalation_form()
        else:
            # No automated solution found
            st.warning("🤔 We couldn't find an automatic solution.")
            st.info("Let's connect you with our support team.")
            self._render_escalation_form()
    
    def _render_escalation_form(self):
        """Render form to escalate to human support."""
        st.subheader("📞 Contact Human Support")
        
        with st.form("escalation_form"):
            priority = st.selectbox(
                "Priority Level",
                ["Low - General question", "Medium - Issue affecting work", "High - Critical system down"]
            )
            
            contact_method = st.selectbox(
                "Preferred Contact Method",
                ["Email", "Live Chat", "Phone Call"]
            )
            
            additional_info = st.text_area(
                "Additional Information",
                placeholder="Any other details that might help...",
                height=80
            )
            
            if st.form_submit_button("📨 Submit Support Request"):
                st.success("✅ Support request submitted! We'll get back to you within 24 hours.")
                
                # Store in session for follow-up
                if 'support_requests' not in st.session_state:
                    st.session_state.support_requests = []
                
                st.session_state.support_requests.append({
                    'timestamp': datetime.now().isoformat(),
                    'priority': priority,
                    'contact_method': contact_method,
                    'additional_info': additional_info
                })
    
    def _render_known_issues(self):
        """Render known issues and their status."""
        st.header("📋 Known Issues & Updates")
        
        known_issues = [
            {
                "title": "PDF Export Performance",
                "description": "Large reports may take longer to generate",
                "status": "🔧 In Progress",
                "eta": "Next Update",
                "workaround": "Export smaller date ranges for faster processing"
            },
            {
                "title": "Interactive Brokers Connection",
                "description": "Occasional timeout during market hours",
                "status": "🟡 Monitoring", 
                "eta": "Under Investigation",
                "workaround": "Retry connection or use manual data upload"
            },
            {
                "title": "Mobile Browser Display",
                "description": "Some charts may not display properly on mobile",
                "status": "📋 Planned",
                "eta": "Q2 2024",
                "workaround": "Use desktop browser for best experience"
            }
        ]
        
        for issue in known_issues:
            with st.expander(f"{issue['status']} {issue['title']}"):
                st.write(f"**Description:** {issue['description']}")
                st.write(f"**ETA:** {issue['eta']}")
                
                if issue['workaround']:
                    st.info(f"**Workaround:** {issue['workaround']}")
    
    def _render_contact_support(self):
        """Render contact support options."""
        st.header("💬 Contact Support")
        
        # Support options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📧 Email Support
            **General:** support@tradesense.app  
            **Technical:** tech@tradesense.app  
            **Billing:** billing@tradesense.app
            
            *Response time: 4-24 hours*
            """)
        
        with col2:
            st.markdown("""
            ### 💬 Live Chat
            Available during business hours  
            Monday-Friday: 9 AM - 6 PM EST
            
            *Average response: < 5 minutes*
            """)
            
            if st.button("🗨️ Start Live Chat"):
                st.info("Live chat would open here")
        
        with col3:
            st.markdown("""
            ### 📞 Phone Support
            **US/Canada:** +1 (555) 123-TRADE  
            **International:** +1 (555) 123-4567
            
            *Business hours only*
            """)
    
    def _render_troubleshooting_guide(self):
        """Render comprehensive troubleshooting guide."""
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
                    "Trades not appearing",
                    "Incorrect trade data",
                    "Missing recent trades",
                    "Duplicate trade entries"
                ],
                "solutions": [
                    "Refresh the connection to your broker",
                    "Check the date range settings",
                    "Verify trade status with your broker",
                    "Use manual data upload as backup",
                    "Contact support if data appears corrupted"
                ]
            },
            {
                "title": "📈 Analytics & Reports",
                "problems": [
                    "Charts not loading",
                    "Incorrect calculations",
                    "Report generation fails",
                    "Export not working"
                ],
                "solutions": [
                    "Clear your browser cache and cookies",
                    "Try refreshing the page",
                    "Check if you have sufficient trade data",
                    "Ensure date ranges are valid",
                    "Try exporting smaller datasets"
                ]
            },
            {
                "title": "⚡ Performance Issues",
                "problems": [
                    "App loading slowly",
                    "Timeouts during analysis",
                    "Browser freezing",
                    "Charts taking long to render"
                ],
                "solutions": [
                    "Close unnecessary browser tabs",
                    "Clear browser cache",
                    "Reduce the amount of data being analyzed",
                    "Try using a different browser",
                    "Check your internet connection speed"
                ]
            }
        ]

        for section in troubleshooting_sections:
            with st.expander(section["title"]):
                st.markdown("**Common Problems:**")
                for problem in section["problems"]:
                    st.markdown(f"• {problem}")
                
                st.markdown("**Solutions:**")
                for i, solution in enumerate(section["solutions"], 1):
                    st.markdown(f"{i}. {solution}")
        
        # Quick fixes section
        st.subheader("⚡ Quick Fixes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Clear Browser Cache"):
                st.info("""
                **How to clear cache:**
                1. Press Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
                2. Select "Cached images and files"
                3. Click "Clear data"
                4. Refresh TradeSense
                """)
        
        with col2:
            if st.button("🆕 Force Refresh Page"):
                st.info("""
                **Force refresh:**
                1. Press Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
                2. Or hold Shift and click the refresh button
                3. This bypasses the cache completely
                """)
        
        # Browser compatibility
        st.subheader("🌐 Browser Compatibility")
        
        compatibility_data = {
            "Browser": ["Chrome", "Firefox", "Safari", "Edge", "Mobile Safari", "Mobile Chrome"],
            "Status": ["✅ Recommended", "✅ Supported", "✅ Supported", "✅ Supported", "⚠️ Limited", "⚠️ Limited"],
            "Version": ["Latest", "Latest", "Latest", "Latest", "iOS 14+", "Android 10+"]
        }
        
        compatibility_df = pd.DataFrame(compatibility_data)
        st.dataframe(compatibility_df, use_container_width=True)
        
        # System requirements
        st.subheader("💻 System Requirements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Minimum Requirements:**
            - 4GB RAM
            - Modern browser (last 2 versions)
            - Stable internet connection
            - JavaScript enabled
            """)
        
        with col2:
            st.markdown("""
            **Recommended:**
            - 8GB+ RAM  
            - Latest Chrome or Firefox
            - High-speed internet
            - Large monitor for best experience
            """)

def render_error_notification_interface():
    """Main function to render error notification interface."""
    error_ui = ErrorNotificationUI()
    error_ui.render_error_interface()

# Enhanced error handling decorator
def handle_errors(func):
    """Decorator to handle and display errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            
            # Show error details in expander
            with st.expander("🔍 Error Details"):
                st.code(f"Error: {str(e)}")
                st.code(f"Function: {func.__name__}")
                
                # Quick solutions
                st.markdown("**Quick Solutions:**")
                st.markdown("1. Refresh the page")
                st.markdown("2. Clear browser cache")
                st.markdown("3. Try again in a few minutes")
                
                if st.button("📞 Contact Support"):
                    error_ui = ErrorNotificationUI()
                    error_ui._render_escalation_form()
    
    return wrapper
