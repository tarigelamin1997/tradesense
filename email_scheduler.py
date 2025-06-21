
import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import schedule
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
import logging
from auth import AuthManager

logger = logging.getLogger(__name__)

class EmailScheduler:
    """Handle scheduled email reports for users."""
    
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"  # Configure based on your email provider
        self.smtp_port = 587
        self.sender_email = "reports@tradesense.com"  # Configure your email
        self.sender_password = "your_app_password"  # Use app password
        
    def schedule_weekly_report(self, user_email: str, day_of_week: str):
        """Schedule weekly email reports for a user."""
        try:
            # Store user preference in database
            auth_manager = AuthManager()
            current_user = auth_manager.get_current_user()
            
            if current_user:
                # Update user preferences (implement in your auth system)
                self._update_user_email_preferences(current_user['id'], user_email, day_of_week)
                return True
                
        except Exception as e:
            logger.error(f"Email scheduling error: {e}")
            return False
    
    def send_weekly_report(self, user_email: str, analytics_data: dict):
        """Send weekly analytics report via email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = user_email
            msg['Subject'] = f"Your Weekly Trading Report - {datetime.now().strftime('%B %d, %Y')}"
            
            # Create HTML email content
            html_content = self._create_email_template(analytics_data)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, user_email, text)
            server.quit()
            
            logger.info(f"Weekly report sent to {user_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return False
    
    def _create_email_template(self, analytics_data: dict) -> str:
        """Create professional HTML email template."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .metric {{ background: #f8fafc; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .footer {{ background: #f8fafc; padding: 20px; text-align: center; color: #6b7280; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Your Weekly Trading Report</h1>
                    <p>Performance summary for {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="content">
                    <h2>Performance Highlights</h2>
                    
                    <div class="metric">
                        <div>Total P&L</div>
                        <div class="metric-value">${analytics_data.get('total_pnl', 0):,.2f}</div>
                    </div>
                    
                    <div class="metric">
                        <div>Win Rate</div>
                        <div class="metric-value">{analytics_data.get('win_rate', 0):.1f}%</div>
                    </div>
                    
                    <div class="metric">
                        <div>Total Trades</div>
                        <div class="metric-value">{analytics_data.get('total_trades', 0):,}</div>
                    </div>
                    
                    <div class="metric">
                        <div>Profit Factor</div>
                        <div class="metric-value">{analytics_data.get('profit_factor', 0):.2f}</div>
                    </div>
                    
                    <p>View your complete analytics dashboard at <a href="https://tradesense.replit.app">TradeSense</a></p>
                </div>
                
                <div class="footer">
                    <p>This is an automated report from TradeSense</p>
                    <p>To unsubscribe, visit your account settings</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _update_user_email_preferences(self, user_id: int, email: str, day_of_week: str):
        """Update user email preferences in database."""
        # Implementation depends on your database schema
        pass


def render_email_scheduler_ui():
    """Render email scheduling interface."""
    st.subheader("📧 Email Reports")
    
    auth_manager = AuthManager()
    current_user = auth_manager.get_current_user()
    
    if not current_user:
        st.warning("Please login to configure email reports")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Weekly Analytics Reports**")
        st.write("Receive a summary of your trading performance every week")
        
        enable_emails = st.checkbox(
            "Enable weekly email reports", 
            value=st.session_state.get('email_reports_enabled', False),
            key="email_reports_enabled"
        )
        
        if enable_emails:
            email_address = st.text_input(
                "Email Address", 
                value=current_user.get('email', ''),
                key="report_email"
            )
            
            day_of_week = st.selectbox(
                "Send reports on:",
                options=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                index=0,
                key="report_day"
            )
            
            time_of_day = st.time_input(
                "Time of day:",
                value=datetime.strptime("09:00", "%H:%M").time(),
                key="report_time"
            )
    
    with col2:
        if enable_emails:
            if st.button("💾 Save Email Settings", type="primary", use_container_width=True):
                scheduler = EmailScheduler()
                success = scheduler.schedule_weekly_report(
                    st.session_state.report_email,
                    st.session_state.report_day
                )
                
                if success:
                    show_toast("Email settings saved successfully!")
                    st.success(f"Weekly reports will be sent to {st.session_state.report_email} every {st.session_state.report_day}")
                else:
                    st.error("Failed to save email settings")
            
            st.markdown("---")
            
            if st.button("📧 Send Test Email", use_container_width=True):
                with st.spinner("Sending test email..."):
                    scheduler = EmailScheduler()
                    test_analytics = {
                        'total_pnl': 1250.50,
                        'win_rate': 67.3,
                        'total_trades': 45,
                        'profit_factor': 1.8
                    }
                    
                    success = scheduler.send_weekly_report(
                        st.session_state.report_email,
                        test_analytics
                    )
                    
                    if success:
                        show_toast("Test email sent successfully!")
                    else:
                        st.error("Failed to send test email")
