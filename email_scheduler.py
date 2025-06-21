#!/usr/bin/env python3
"""
Email Scheduler
Automated weekly trading report email system with enhanced UI
"""

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, Any
import json
import sqlite3

logger = logging.getLogger(__name__)

class EmailScheduler:
    """Handle automated email scheduling for trading reports with database storage."""

    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.scheduler_running = False
        self.db_path = 'tradesense.db'
        self._init_email_tables()

    def _init_email_tables(self):
        """Initialize email scheduling tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    email_address TEXT NOT NULL,
                    report_day TEXT NOT NULL,
                    report_time TEXT DEFAULT '09:00',
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    email_address TEXT,
                    status TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error initializing email tables: {e}")

    def save_email_schedule(self, user_id: int, email_address: str, report_day: str, 
                           report_time: str = '09:00', enabled: bool = True):
        """Save email schedule settings to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if schedule exists
            cursor.execute("""
                SELECT id FROM email_schedules WHERE user_id = ?
            """, (user_id,))

            existing = cursor.fetchone()

            if existing:
                # Update existing schedule
                cursor.execute("""
                    UPDATE email_schedules 
                    SET email_address = ?, report_day = ?, report_time = ?, 
                        enabled = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (email_address, report_day, report_time, enabled, user_id))
            else:
                # Create new schedule
                cursor.execute("""
                    INSERT INTO email_schedules (user_id, email_address, report_day, report_time, enabled)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, email_address, report_day, report_time, enabled))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error saving email schedule: {e}")
            return False

    def get_email_schedule(self, user_id: int):
        """Get email schedule for user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT email_address, report_day, report_time, enabled
                FROM email_schedules WHERE user_id = ?
            """, (user_id,))

            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'email_address': result[0],
                    'report_day': result[1],
                    'report_time': result[2],
                    'enabled': bool(result[3])
                }
            return None

        except Exception as e:
            logger.error(f"Error getting email schedule: {e}")
            return None

    def send_weekly_report(self, user_email: str, report_data: Dict[str, Any], user_id: int = None):
        """Send weekly trading report via email with enhanced template."""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = user_email
            msg['Subject'] = f"📊 TradeSense Weekly Report - {datetime.now().strftime('%B %d, %Y')}"

            # Create email body
            html_body = self._create_enhanced_email_body(report_data)
            text_body = self._create_text_email_body(report_data)

            # Attach both text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send email (mock for demo - replace with actual SMTP)
            if self.email_user and self.email_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.email_user, self.email_password)
                text = msg.as_string()
                server.sendmail(self.email_user, user_email, text)
                server.quit()

                # Log success
                self._log_email_send(user_id, user_email, 'success')
                logger.info(f"Weekly report sent to {user_email}")
                return True
            else:
                # Demo mode - just log
                self._log_email_send(user_id, user_email, 'demo_mode')
                logger.info(f"Demo: Weekly report would be sent to {user_email}")
                return True

        except Exception as e:
            self._log_email_send(user_id, user_email, 'failed', str(e))
            logger.error(f"Failed to send email to {user_email}: {e}")
            return False

    def _log_email_send(self, user_id: int, email_address: str, status: str, error_message: str = None):
        """Log email send attempt."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO email_logs (user_id, email_address, status, error_message)
                VALUES (?, ?, ?, ?)
            """, (user_id, email_address, status, error_message))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error logging email send: {e}")

    def _create_enhanced_email_body(self, report_data: Dict[str, Any]) -> str:
        """Create enhanced HTML email body for weekly report."""
        win_rate = report_data.get('win_rate', 0)
        total_pnl = report_data.get('total_pnl', 0)
        profit_factor = report_data.get('profit_factor', 0)

        # Performance badge
        if win_rate > 60 and profit_factor > 2.0:
            performance_badge = "🏆 Excellent"
            badge_color = "#10b981"
        elif win_rate > 50 and profit_factor > 1.5:
            performance_badge = "⭐ Good"
            badge_color = "#3b82f6"
        else:
            performance_badge = "📈 Improving"
            badge_color = "#f59e0b"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TradeSense Weekly Report</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">

                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">📊 TradeSense</h1>
                    <p style="color: rgba(255, 255, 255, 0.9); margin: 5px 0 0 0; font-size: 16px;">Weekly Trading Report</p>
                </div>

                <!-- Performance Badge -->
                <div style="text-align: center; padding: 20px;">
                    <div style="display: inline-block; background-color: {badge_color}; color: white; padding: 10px 20px; border-radius: 25px; font-weight: 600;">
                        {performance_badge} Performance
                    </div>
                </div>

                <!-- Metrics Grid -->
                <div style="padding: 0 30px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">

                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; border-left: 4px solid #667eea;">
                            <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Total Trades</div>
                            <div style="font-size: 28px; font-weight: 700; color: #1e293b;">{report_data.get('total_trades', 0):,}</div>
                        </div>

                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; border-left: 4px solid {'#10b981' if win_rate > 50 else '#ef4444'};">
                            <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Win Rate</div>
                            <div style="font-size: 28px; font-weight: 700; color: {'#10b981' if win_rate > 50 else '#ef4444'};">{win_rate:.1f}%</div>
                        </div>

                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; border-left: 4px solid {'#10b981' if total_pnl > 0 else '#ef4444'};">
                            <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Net P&L</div>
                            <div style="font-size: 28px; font-weight: 700; color: {'#10b981' if total_pnl > 0 else '#ef4444'};">{'+ ' if total_pnl > 0 else ''}${total_pnl:,.2f}</div>
                        </div>

                        <div style="background-color: #f8fafc; padding: 20px; border-radius: 12px; text-align: center; border-left: 4px solid {'#10b981' if profit_factor > 1.5 else '#ef4444'};">
                            <div style="font-size: 14px; color: #64748b; margin-bottom: 5px;">Profit Factor</div>
                            <div style="font-size: 28px; font-weight: 700; color: {'#10b981' if profit_factor > 1.5 else '#ef4444'};">{'∞' if profit_factor == float('inf') else f'{profit_factor:.2f}'}</div>
                        </div>

                    </div>
                </div>

                <!-- Insights Section -->
                <div style="padding: 0 30px 30px;">
                    <h3 style="color: #1e293b; margin-bottom: 15px;">📊 Weekly Insights</h3>
                    <div style="background-color: #f1f5f9; padding: 20px; border-radius: 12px; border-left: 4px solid #3b82f6;">
                        <p style="margin: 0; color: #475569; line-height: 1.6;">
                            {self._generate_insight_text(report_data)}
                        </p>
                    </div>
                </div>

                <!-- CTA Button -->
                <div style="text-align: center; padding: 0 30px 30px;">
                    <a href="https://tradesense.app" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                        View Detailed Analytics →
                    </a>
                </div>

                <!-- Footer -->
                <div style="background-color: #f8fafc; padding: 20px 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; font-size: 12px; color: #64748b;">
                        This automated report was generated by TradeSense Analytics Platform<br>
                        Report generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}
                    </p>
                </div>

            </div>
        </body>
        </html>
        """

    def _create_text_email_body(self, report_data: Dict[str, Any]) -> str:
        """Create plain text email body for weekly report."""
        return f"""
TradeSense Weekly Trading Report
{datetime.now().strftime('%B %d, %Y')}

PERFORMANCE SUMMARY
===================
Total Trades: {report_data.get('total_trades', 0):,}
Win Rate: {report_data.get('win_rate', 0):.1f}%
Net P&L: ${report_data.get('total_pnl', 0):,.2f}
Profit Factor: {report_data.get('profit_factor', 0):.2f}

View your complete analytics dashboard at: https://tradesense.app

This is an automated report from TradeSense Analytics Platform.
        """

    def _generate_insight_text(self, report_data: Dict[str, Any]) -> str:
        """Generate personalized insight text based on performance."""
        win_rate = report_data.get('win_rate', 0)
        total_pnl = report_data.get('total_pnl', 0)
        profit_factor = report_data.get('profit_factor', 0)
        total_trades = report_data.get('total_trades', 0)

        if win_rate > 60 and profit_factor > 2.0:
            return f"Outstanding week! Your {win_rate:.1f}% win rate and strong profit factor of {profit_factor:.2f} demonstrate excellent trading discipline. Consider scaling your strategy while maintaining current risk parameters."
        elif win_rate > 50 and total_pnl > 0:
            return f"Good performance this week with {total_trades} trades and a {win_rate:.1f}% win rate. Your strategy is showing positive momentum. Focus on consistency and risk management."
        elif total_pnl > 0:
            return f"Profitable week despite a {win_rate:.1f}% win rate. This suggests good risk-reward management. Consider improving trade selection to increase win rate."
        else:
            return f"This week presented challenges with a {win_rate:.1f}% win rate. Review your recent trades to identify areas for improvement. Consider adjusting position sizing or entry criteria."

# Global scheduler instance
email_scheduler = EmailScheduler()

def render_email_scheduling_ui():
    """Render enhanced email scheduling UI in settings."""
    st.subheader("📧 Weekly Report Email")

    # Get current user
    user_id = st.session_state.get('user_id', 1)  # Default for demo
    current_schedule = email_scheduler.get_email_schedule(user_id)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Email settings
        enable_emails = st.checkbox(
            "📨 Enable Weekly Email Reports",
            value=current_schedule.get('enabled', False) if current_schedule else False,
            key="enable_weekly_emails",
            help="Receive automated weekly trading performance reports every week"
        )

        if enable_emails:
            email_address = st.text_input(
                "📬 Email Address",
                value=current_schedule.get('email_address', st.session_state.get('user_email', '')) if current_schedule else st.session_state.get('user_email', ''),
                help="Email address to receive weekly reports",
                placeholder="your.email@example.com"
            )

            col_day, col_time = st.columns(2)

            with col_day:
                report_day = st.selectbox(
                    "📅 Report Day",
                    options=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                    index=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(
                        current_schedule.get('report_day', 'Monday')
                    ) if current_schedule else 0,
                    help="Day of the week to receive reports"
                )

            with col_time:
                report_time = st.selectbox(
                    "🕘 Report Time",
                    options=['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'],
                    index=['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'].index(
                        current_schedule.get('report_time', '09:00')
                    ) if current_schedule else 0,
                    help="Time to receive reports (24-hour format)"
                )

            # Save button
            if st.button("💾 Save Email Settings", type="primary", use_container_width=True):
                if email_address:
                    success = email_scheduler.save_email_schedule(
                        user_id, email_address, report_day, report_time, enable_emails
                    )

                    if success:
                        st.success("✅ Email settings saved successfully!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to save email settings")
                else:
                    st.error("Please enter a valid email address")

    with col2:
        # Preview and test section
        st.markdown("### 📋 Email Preview")

        if enable_emails and email_address:
            st.info(f"""
            **Schedule Summary:**
            📧 **Email:** {email_address}  
            📅 **Day:** {report_day}  
            🕘 **Time:** {report_time}  
            ✅ **Status:** Active
            """)

            # Test email button
            if st.button("📧 Send Test Email", use_container_width=True):
                try:
                    # Generate test data
                    test_data = {
                        'total_trades': 47,
                        'win_rate': 63.8,
                        'total_pnl': 8750.25,
                        'profit_factor': 2.3,
                        'best_trade': 1250.00,
                        'worst_trade': -450.00
                    }

                    with st.spinner("Sending test email..."):
                        success = email_scheduler.send_weekly_report(
                            email_address, test_data, user_id
                        )

                    if success:
                        st.success("✅ Test email sent successfully!")
                    else:
                        st.error("❌ Failed to send test email")

                except Exception as e:
                    st.error(f"Error sending test email: {e}")
        else:
            st.info("📝 Enable email reports and enter your email address to see preview")

def start_email_scheduler():
    """Start the email scheduler background service."""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    if not email_scheduler.scheduler_running:
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        email_scheduler.scheduler_running = True
        logger.info("Email scheduler started")

# Auto-start scheduler
start_email_scheduler()