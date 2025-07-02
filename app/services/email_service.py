
"""
Email Service
Complete implementation for email scheduling and notifications
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime, time
import os
import sqlite3
from app.config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Complete email service implementation"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.db_path = 'tradesense.db'
        self._init_email_tables()
    
    def _init_email_tables(self):
        """Initialize email scheduling tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS email_schedules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        email_type TEXT NOT NULL,
                        schedule_time TEXT NOT NULL,
                        enabled BOOLEAN DEFAULT 1,
                        recipients TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init email tables: {e}")
    
    async def create_schedule(self, user_id: int, email_type: str, schedule_time: time, 
                            enabled: bool = True, recipients: Optional[List[str]] = None):
        """Create new email schedule"""
        try:
            recipients_str = ','.join(recipients) if recipients else ''
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO email_schedules (user_id, email_type, schedule_time, enabled, recipients)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, email_type, schedule_time.strftime('%H:%M:%S'), enabled, recipients_str))
                
                schedule_id = cursor.lastrowid
                conn.commit()
                
                return {"id": schedule_id, "user_id": user_id, "email_type": email_type}
        except Exception as e:
            logger.error(f"Create schedule failed: {e}")
            raise
    
    async def get_user_schedules(self, user_id: int):
        """Get user's email schedules"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, email_type, schedule_time, enabled, recipients, created_at
                    FROM email_schedules WHERE user_id = ?
                """, (user_id,))
                
                schedules = []
                for row in cursor.fetchall():
                    schedules.append({
                        "id": row[0],
                        "email_type": row[1],
                        "schedule_time": row[2],
                        "enabled": bool(row[3]),
                        "recipients": row[4].split(',') if row[4] else [],
                        "created_at": row[5]
                    })
                
                return schedules
        except Exception as e:
            logger.error(f"Get schedules failed: {e}")
            return []
    
    async def update_schedule(self, schedule_id: int, user_id: int, **kwargs):
        """Update existing email schedule"""
        try:
            set_clauses = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['email_type', 'enabled']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                elif key == 'schedule_time':
                    set_clauses.append("schedule_time = ?")
                    values.append(value.strftime('%H:%M:%S') if hasattr(value, 'strftime') else value)
                elif key == 'recipients':
                    set_clauses.append("recipients = ?")
                    values.append(','.join(value) if isinstance(value, list) else value)
            
            if not set_clauses:
                return None
                
            values.extend([schedule_id, user_id])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE email_schedules SET {', '.join(set_clauses)}
                    WHERE id = ? AND user_id = ?
                """, values)
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Update schedule failed: {e}")
            return False
    
    async def delete_schedule(self, schedule_id: int, user_id: int):
        """Delete email schedule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM email_schedules WHERE id = ? AND user_id = ?
                """, (schedule_id, user_id))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Delete schedule failed: {e}")
            return False
    
    async def send_performance_report(self, user_id: int, report_type: str, 
                                    recipient_email: str, include_charts: bool = True):
        """Send performance report via email"""
        try:
            # Generate report content
            subject = f"TradeSense {report_type.replace('_', ' ').title()} Report"
            
            html_content = f"""
            <html>
                <body>
                    <h2>Your TradeSense {report_type.replace('_', ' ').title()} Report</h2>
                    <p>This is your automated trading performance report.</p>
                    <p>Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <br>
                    <p>Login to TradeSense for detailed analytics: <a href="https://tradesense.replit.app">https://tradesense.replit.app</a></p>
                </body>
            </html>
            """
            
            return await self._send_email(recipient_email, subject, html_content)
        except Exception as e:
            logger.error(f"Send performance report failed: {e}")
            return False
    
    async def send_test_email(self, recipient_email: str, username: str):
        """Send test email"""
        try:
            subject = "TradeSense Test Email"
            html_content = f"""
            <html>
                <body>
                    <h2>Hello {username}!</h2>
                    <p>This is a test email from TradeSense.</p>
                    <p>Your email settings are working correctly.</p>
                    <p>Time sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </body>
            </html>
            """
            
            return await self._send_email(recipient_email, subject, html_content)
        except Exception as e:
            logger.error(f"Send test email failed: {e}")
            return False
    
    async def get_templates(self):
        """Get available email templates"""
        return [
            {
                "id": "daily_report",
                "name": "Daily Performance Report",
                "subject": "Daily Trading Summary",
                "template_html": "<h2>Daily Report</h2><p>Your trading summary for today.</p>"
            },
            {
                "id": "weekly_summary",
                "name": "Weekly Performance Summary", 
                "subject": "Weekly Trading Summary",
                "template_html": "<h2>Weekly Report</h2><p>Your trading summary for this week.</p>"
            },
            {
                "id": "performance_alert",
                "name": "Performance Alert",
                "subject": "Trading Performance Alert",
                "template_html": "<h2>Performance Alert</h2><p>Important update about your trading performance.</p>"
            }
        ]
    
    async def _send_email(self, recipient: str, subject: str, html_content: str):
        """Send email via SMTP"""
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Send email failed: {e}")
            return False
