"""
Email service for sending verification and notification emails
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging
from jinja2 import Template

from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_username or "noreply@tradesense.io"
        self.app_name = "TradeSense"
        self.app_url = os.getenv("APP_URL", "http://localhost:5173")
        
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send an email using SMTP"""
        try:
            # Check if email is configured
            if not self.smtp_server or not self.smtp_username or not self.smtp_password:
                logger.warning("Email service not configured. Skipping email send.")
                logger.info(f"Would have sent email to {to_email}: {subject}")
                return True
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.app_name} <{self.from_email}>"
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def generate_verification_token(self, user_id: int, email: str) -> str:
        """Generate a verification token for email confirmation"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'type': 'email_verification'
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode a verification token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get('type') != 'email_verification':
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("Verification token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.error("Invalid verification token")
            return None
    
    def send_verification_email(self, user_id: int, email: str, username: str) -> bool:
        """Send email verification link to user"""
        token = self.generate_verification_token(user_id, email)
        verification_url = f"{self.app_url}/verify-email?token={token}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background: #f5f5f5; padding: 30px; border-radius: 0 0 8px 8px; }
                .button { display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; font-size: 0.875rem; color: #666; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {{ app_name }}!</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ username }},</h2>
                    <p>Thanks for signing up! Please confirm your email address by clicking the button below:</p>
                    <p style="text-align: center;">
                        <a href="{{ verification_url }}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: white; padding: 10px; border-radius: 4px;">
                        {{ verification_url }}
                    </p>
                    <p>This link will expire in 24 hours for security reasons.</p>
                    <p>If you didn't create an account with {{ app_name }}, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            app_name=self.app_name,
            username=username,
            verification_url=verification_url,
            year=datetime.now().year
        )
        
        subject = f"Verify your {self.app_name} account"
        return self._send_email(email, subject, html_content)
    
    def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email after successful verification"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background: #f5f5f5; padding: 30px; border-radius: 0 0 8px 8px; }
                .button { display: inline-block; background: #10b981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .feature { margin: 15px 0; padding-left: 20px; }
                .footer { margin-top: 30px; font-size: 0.875rem; color: #666; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {{ app_name }}!</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ username }},</h2>
                    <p>Your email has been verified! You're all set to start tracking and improving your trading performance.</p>
                    
                    <h3>Here's what you can do next:</h3>
                    <div class="feature">✅ Import your trading history via CSV</div>
                    <div class="feature">📊 View detailed analytics and performance metrics</div>
                    <div class="feature">📝 Keep a trading journal to track your thoughts</div>
                    <div class="feature">🎯 Build playbooks for consistent strategies</div>
                    
                    <p style="text-align: center;">
                        <a href="{{ app_url }}/dashboard" class="button">Go to Dashboard</a>
                    </p>
                    
                    <p>Need help getting started? Check out our <a href="{{ app_url }}/docs">documentation</a> or reach out to support.</p>
                </div>
                <div class="footer">
                    <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            app_name=self.app_name,
            username=username,
            app_url=self.app_url,
            year=datetime.now().year
        )
        
        subject = f"Welcome to {self.app_name}!"
        return self._send_email(email, subject, html_content)
    
    def send_password_reset_email(self, email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.app_url}/reset-password?token={reset_token}"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #dc2626; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background: #f5f5f5; padding: 30px; border-radius: 0 0 8px 8px; }
                .button { display: inline-block; background: #dc2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
                .footer { margin-top: 30px; font-size: 0.875rem; color: #666; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {{ username }},</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{{ reset_url }}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: white; padding: 10px; border-radius: 4px;">
                        {{ reset_url }}
                    </p>
                    <p><strong>This link will expire in 1 hour for security reasons.</strong></p>
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password won't be changed.</p>
                </div>
                <div class="footer">
                    <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            app_name=self.app_name,
            username=username,
            reset_url=reset_url,
            year=datetime.now().year
        )
        
        subject = f"Reset your {self.app_name} password"
        return self._send_email(email, subject, html_content)