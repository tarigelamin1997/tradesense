import logging
import logging.handlers
import json
import sqlite3
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class LogLevel(Enum):
    """Log levels for categorizing different types of events."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Categories for different types of log entries."""
    USER_ACTION = "user_action"
    DATA_PROCESSING = "data_processing"
    SYNC_OPERATION = "sync_operation"
    AUTHENTICATION = "authentication"
    SYSTEM_ERROR = "system_error"
    BUSINESS_LOGIC = "business_logic"
    PERFORMANCE = "performance"

class CentralizedLogger:
    """Centralized logging system for TradeSense."""

    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_file_logging()
        self.critical_alerts_enabled = True

    def setup_database(self):
        """Initialize the logging database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                details JSON,
                user_id INTEGER,
                partner_id TEXT,
                session_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                stack_trace TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Error patterns table for tracking recurring issues
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT UNIQUE NOT NULL,
                first_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER DEFAULT 1,
                severity TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                description TEXT
            )
        ''')

        # User action logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                partner_id TEXT,
                action_type TEXT NOT NULL,
                action_details JSON,
                ip_address TEXT,
                user_agent TEXT,
                session_duration INTEGER,
                page_context TEXT
            )
        ''')

        # Sync operation logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                partner_id TEXT,
                sync_type TEXT NOT NULL,
                connector_name TEXT,
                status TEXT NOT NULL,
                records_processed INTEGER DEFAULT 0,
                records_success INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                error_details JSON,
                duration_seconds REAL,
                retry_count INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def setup_file_logging(self):
        """Setup file-based logging with rotation."""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        # Setup main application logger
        self.app_logger = logging.getLogger('tradesense_app')
        self.app_logger.setLevel(logging.DEBUG)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/tradesense.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )

        # Error file handler for errors and critical issues
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/tradesense_errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)

        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )

        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)

        # Add handlers
        self.app_logger.addHandler(file_handler)
        self.app_logger.addHandler(error_handler)

    def log_event(self, 
                  level: LogLevel, 
                  category: LogCategory, 
                  message: str,
                  details: Optional[Dict[str, Any]] = None,
                  user_id: Optional[int] = None,
                  partner_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  stack_trace: Optional[str] = None):
        """Log an event to both database and file."""

        # Get additional context from Streamlit session if available
        try:
            if not session_id and hasattr(st, 'session_state'):
                session_id = getattr(st.session_state, 'session_id', None)
        except:
            pass

        # Log to database
        self._log_to_database(
            level=level.value,
            category=category.value,
            message=message,
            details=details,
            user_id=user_id,
            partner_id=partner_id,
            session_id=session_id,
            stack_trace=stack_trace
        )

        # Log to file
        log_data = {
            'category': category.value,
            'user_id': user_id,
            'partner_id': partner_id,
            'session_id': session_id,
            'details': details
        }

        log_message = f"{message} | {json.dumps(log_data, default=str)}"

        if level == LogLevel.DEBUG:
            self.app_logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.app_logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.app_logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.app_logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.app_logger.critical(log_message)
            # Send critical alert
            if self.critical_alerts_enabled:
                self._send_critical_alert(message, details, stack_trace)

        # Track error patterns for recurring issues
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self._track_error_pattern(message, level, details)

    def _log_to_database(self, level: str, category: str, message: str,
                        details: Optional[Dict[str, Any]] = None,
                        user_id: Optional[int] = None,
                        partner_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        stack_trace: Optional[str] = None):
        """Log event to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO system_logs 
                (level, category, message, details, user_id, partner_id, 
                 session_id, stack_trace)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                level, category, message, 
                json.dumps(details, default=str) if details else None,
                user_id, partner_id, session_id, stack_trace
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            # Fallback to file logging if database fails
            self.app_logger.error(f"Failed to log to database: {str(e)}")

    def _track_error_pattern(self, message: str, level: LogLevel, details: Optional[Dict] = None):
        """Track recurring error patterns."""
        try:
            # Create error signature from message and key details
            error_signature = self._create_error_signature(message, details)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if pattern exists
            cursor.execute('''
                SELECT id, occurrence_count FROM error_patterns 
                WHERE error_signature = ?
            ''', (error_signature,))

            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                cursor.execute('''
                    UPDATE error_patterns 
                    SET last_occurrence = CURRENT_TIMESTAMP,
                        occurrence_count = occurrence_count + 1
                    WHERE id = ?
                ''', (existing[0],))
            else:
                # Create new pattern
                cursor.execute('''
                    INSERT INTO error_patterns 
                    (error_signature, severity, description)
                    VALUES (?, ?, ?)
                ''', (error_signature, level.value, message[:500]))

            conn.commit()
            conn.close()
        except Exception as e:
            self.app_logger.error(f"Failed to track error pattern: {str(e)}")

    def _create_error_signature(self, message: str, details: Optional[Dict] = None) -> str:
        """Create a unique signature for error pattern tracking."""
        # Use first 100 characters of message + error type if available
        signature_parts = [message[:100]]

        if details:
            if 'error_type' in details:
                signature_parts.append(details['error_type'])
            if 'function_name' in details:
                signature_parts.append(details['function_name'])

        return "|".join(signature_parts)

    def _send_critical_alert(self, message: str, details: Optional[Dict] = None, 
                           stack_trace: Optional[str] = None):
        """Send alert for critical issues."""
        try:
            # For now, log critical alerts to a special file
            # In production, you'd want to integrate with email/Slack/PagerDuty
            with open('logs/critical_alerts.log', 'a') as f:
                alert_data = {
                    'timestamp': datetime.now().isoformat(),
                    'message': message,
                    'details': details,
                    'stack_trace': stack_trace
                }
                f.write(json.dumps(alert_data, default=str) + '\n')

            # Store in session state for UI display
            if hasattr(st, 'session_state'):
                if 'critical_alerts' not in st.session_state:
                    st.session_state.critical_alerts = []

                st.session_state.critical_alerts.append({
                    'timestamp': datetime.now(),
                    'message': message,
                    'details': details
                })

        except Exception as e:
            self.app_logger.error(f"Failed to send critical alert: {str(e)}")

# Global logger instance
logger_instance = CentralizedLogger()

def log_error(message: str, details: Optional[Dict] = None, 
              user_id: Optional[int] = None, partner_id: Optional[str] = None,
              category: LogCategory = LogCategory.SYSTEM_ERROR):
    """Convenience function to log errors."""
    stack_trace = traceback.format_exc() if details and details.get('include_trace', True) else None
    logger_instance.log_event(
        level=LogLevel.ERROR,
        category=category,
        message=message,
        details=details,
        user_id=user_id,
        partner_id=partner_id,
        stack_trace=stack_trace
    )

def log_critical(message: str, details: Optional[Dict] = None,
                user_id: Optional[int] = None, partner_id: Optional[str] = None,
                category: LogCategory = LogCategory.SYSTEM_ERROR):
    """Convenience function to log critical issues."""
    stack_trace = traceback.format_exc()
    logger_instance.log_event(
        level=LogLevel.CRITICAL,
        category=category,
        message=message,
        details=details,
        user_id=user_id,
        partner_id=partner_id,
        stack_trace=stack_trace
    )

def log_warning(message: str, details: Optional[Dict] = None,
               user_id: Optional[int] = None, partner_id: Optional[str] = None,
               category: LogCategory = LogCategory.SYSTEM_ERROR):
    """Convenience function to log warnings."""
    logger_instance.log_event(
        level=LogLevel.WARNING,
        category=category,
        message=message,
        details=details,
        user_id=user_id,
        partner_id=partner_id
    )

def log_info(message: str, details: Optional[Dict] = None,
            user_id: Optional[int] = None, partner_id: Optional[str] = None,
            category: LogCategory = LogCategory.SYSTEM_ERROR):
    """Convenience function to log info events."""
    logger_instance.log_event(
        level=LogLevel.INFO,
        category=category,
        message=message,
        details=details,
        user_id=user_id,
        partner_id=partner_id
    )

def log_user_action(user_id: int, action: str, details: Optional[Dict] = None,
                   partner_id: Optional[str] = None, page_context: Optional[str] = None):
    """Convenience function to log user actions."""
    logger_instance.log_user_action(
        user_id=user_id,
        action_type=action,
        action_details=details,
        partner_id=partner_id,
        page_context=page_context
    )

def log_sync_result(user_id: int, sync_type: str, connector_name: str,
                   success: bool, records_processed: int = 0,
                   error_details: Optional[Dict] = None,
                   partner_id: Optional[str] = None,
                   duration_seconds: Optional[float] = None):
    """Convenience function to log sync operations."""
    status = 'success' if success else 'failed'
    records_success = records_processed if success else 0
    records_failed = 0 if success else records_processed

    logger_instance.log_sync_operation(
        user_id=user_id,
        sync_type=sync_type,
        connector_name=connector_name,
        status=status,
        records_processed=records_processed,
        records_success=records_success,
        records_failed=records_failed,
        error_details=error_details,
        duration_seconds=duration_seconds,
        partner_id=partner_id
    )