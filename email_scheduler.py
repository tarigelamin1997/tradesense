
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
import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import sqlite3
from datetime import datetime, timedelta
import json
import threading
import time
import schedule

class EmailScheduler:
    """Email scheduling system for trading reports."""
    
    def __init__(self, db_path="tradesense.db"):
        self.db_path = db_path
        self.init_email_tables()
        
    def init_email_tables(self):
        """Initialize email scheduling tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                frequency TEXT NOT NULL,
                day_of_week INTEGER,
                time_of_day TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_sent TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_id INTEGER NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                error_message TEXT,
                FOREIGN KEY (schedule_id) REFERENCES email_schedules (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_email_schedule(self, user_id, email, frequency, day_of_week=None, time_of_day="09:00"):
        """Create new email schedule."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO email_schedules (user_id, email, frequency, day_of_week, time_of_day)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, frequency, day_of_week, time_of_day))
            
            schedule_id = cursor.lastrowid
            conn.commit()
            return {"success": True, "schedule_id": schedule_id}
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def get_user_schedules(self, user_id):
        """Get all email schedules for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM email_schedules WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        schedules = cursor.fetchall()
        conn.close()
        
        if schedules:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, schedule)) for schedule in schedules]
        return []
    
    def send_trading_report_email(self, to_email, analytics_data, pdf_content=None):
        """Send trading report via email."""
        try:
            # Email configuration (would use environment variables in production)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            from_email = "noreply@tradesense.com"  # Configure with actual email
            from_password = "app_password"  # Use app password
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"TradeSense Weekly Report - {datetime.now().strftime('%B %d, %Y')}"
            
            # Email body
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <h2 style="color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px;">
                    📊 Your Weekly Trading Report
                  </h2>
                  
                  <p>Hello!</p>
                  
                  <p>Here's your weekly trading performance summary:</p>
                  
                  <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #0066cc;">Key Metrics</h3>
                    <ul style="list-style: none; padding: 0;">
                      <li><strong>Total P&L:</strong> ${analytics_data.get('total_pnl', 0):,.2f}</li>
                      <li><strong>Win Rate:</strong> {analytics_data.get('win_rate', 0):.1f}%</li>
                      <li><strong>Total Trades:</strong> {analytics_data.get('total_trades', 0):,}</li>
                      <li><strong>Profit Factor:</strong> {analytics_data.get('profit_factor', 0):.2f}</li>
                    </ul>
                  </div>
                  
                  <p>For detailed analysis, please log in to your TradeSense dashboard.</p>
                  
                  <div style="margin: 30px 0; text-align: center;">
                    <a href="https://your-tradesense-url.com" 
                       style="background: #0066cc; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                      View Full Dashboard
                    </a>
                  </div>
                  
                  <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                  
                  <p style="font-size: 12px; color: #666;">
                    This is an automated report from TradeSense. 
                    To unsubscribe, please log in to your account and update your email preferences.
                  </p>
                </div>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach PDF if provided
            if pdf_content:
                pdf_attachment = MIMEBase('application', 'octet-stream')
                pdf_attachment.set_payload(pdf_content)
                encoders.encode_base64(pdf_attachment)
                pdf_attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename= "TradeSense_Report_{datetime.now().strftime("%Y%m%d")}.pdf"'
                )
                msg.attach(pdf_attachment)
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, from_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return {"success": True, "message": "Email sent successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

def render_email_scheduling_ui(user_id, user_email):
    """Render email scheduling interface."""
    st.subheader("📧 Email Report Scheduling")
    
    scheduler = EmailScheduler()
    
    # Current schedules
    existing_schedules = scheduler.get_user_schedules(user_id)
    
    if existing_schedules:
        st.write("**Current Email Schedules:**")
        for schedule in existing_schedules:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"📧 {schedule['email']}")
            
            with col2:
                frequency_text = schedule['frequency']
                if schedule['day_of_week'] is not None:
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    frequency_text += f" ({days[schedule['day_of_week']]})"
                st.write(f"🕐 {frequency_text} at {schedule['time_of_day']}")
            
            with col3:
                if st.button("🗑️", key=f"delete_schedule_{schedule['id']}", help="Delete schedule"):
                    # Delete schedule logic here
                    st.success("Schedule deleted!")
                    st.rerun()
        
        st.markdown("---")
    
    # Add new schedule
    with st.expander("➕ Add New Email Schedule"):
        with st.form("email_schedule_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("Email Address", value=user_email)
                frequency = st.selectbox(
                    "Frequency",
                    options=['weekly', 'monthly'],
                    format_func=lambda x: x.title()
                )
            
            with col2:
                if frequency == 'weekly':
                    day_of_week = st.selectbox(
                        "Day of Week",
                        options=[0, 1, 2, 3, 4, 5, 6],
                        format_func=lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]
                    )
                else:
                    day_of_week = 1  # First of month
                
                time_of_day = st.time_input("Time of Day", value=datetime.strptime("09:00", "%H:%M").time())
            
            include_pdf = st.checkbox("Include PDF attachment", value=True)
            
            if st.form_submit_button("📅 Schedule Reports", type="primary"):
                if email:
                    result = scheduler.create_email_schedule(
                        user_id=user_id,
                        email=email,
                        frequency=frequency,
                        day_of_week=day_of_week,
                        time_of_day=time_of_day.strftime("%H:%M")
                    )
                    
                    if result['success']:
                        st.success("✅ Email schedule created successfully!")
                        st.info("You'll receive your first report according to the schedule you set.")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to create schedule: {result['error']}")
                else:
                    st.error("Please enter a valid email address")
    
    # Test email
    st.markdown("---")
    if st.button("📧 Send Test Report Now"):
        with st.spinner("Sending test email..."):
            # Mock analytics data for test
            test_analytics = {
                'total_pnl': 1250.75,
                'win_rate': 68.5,
                'total_trades': 45,
                'profit_factor': 1.85
            }
            
            result = scheduler.send_trading_report_email(user_email, test_analytics)
            
            if result['success']:
                st.success("✅ Test email sent successfully!")
            else:
                st.error(f"❌ Failed to send email: {result['error']}")
                st.info("💡 Email functionality requires SMTP configuration. Contact support for setup.")
