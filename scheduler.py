
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import sqlite3
import json
import traceback
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import pandas as pd
import streamlit as st
from connectors.loader import get_available_connectors, test_connector
from connectors.registry import registry
from auth import AuthManager
from credential_manager import CredentialManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    CONNECTOR_SYNC = "connector_sync"
    DATA_CLEANUP = "data_cleanup"
    CREDENTIAL_ROTATION = "credential_rotation"
    REPORT_GENERATION = "report_generation"
    MANUAL_SYNC = "manual_sync"

@dataclass
class JobResult:
    job_id: str
    status: JobStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    records_processed: int = 0

class JobScheduler:
    """Background job scheduler for TradeSense operations."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.scheduler = BackgroundScheduler()
        self.credential_manager = CredentialManager()
        self.auth_manager = AuthManager()
        self._init_job_database()
        self._setup_event_listeners()
        
    def _init_job_database(self):
        """Initialize job tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                partner_id TEXT,
                config TEXT,
                status TEXT DEFAULT 'pending',
                scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                error_count INTEGER DEFAULT 0,
                last_error TEXT,
                result_data TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                execution_start TIMESTAMP,
                execution_end TIMESTAMP,
                status TEXT,
                records_processed INTEGER DEFAULT 0,
                error_message TEXT,
                result_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_event_listeners(self):
        """Setup scheduler event listeners for job tracking."""
        def job_listener(event):
            if event.exception:
                logger.error(f"Job {event.job_id} failed: {event.exception}")
                self._update_job_status(event.job_id, JobStatus.FAILED, str(event.exception))
            else:
                logger.info(f"Job {event.job_id} completed successfully")
                self._update_job_status(event.job_id, JobStatus.COMPLETED)
        
        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    
    def start(self):
        """Start the job scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")
            
            # Schedule default maintenance jobs
            self._schedule_default_jobs()
    
    def stop(self):
        """Stop the job scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler stopped")
    
    def _schedule_default_jobs(self):
        """Schedule default system maintenance jobs."""
        # Daily cleanup job
        self.scheduler.add_job(
            func=self._cleanup_old_jobs,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
            id="daily_cleanup",
            replace_existing=True
        )
        
        # Credential rotation check (weekly)
        self.scheduler.add_job(
            func=self._check_credential_expiry,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
            id="credential_check",
            replace_existing=True
        )
    
    def schedule_connector_sync(self, 
                              user_id: int,
                              connector_name: str,
                              sync_interval_minutes: int = 60,
                              partner_id: Optional[str] = None,
                              config: Dict[str, Any] = None) -> str:
        """Schedule recurring connector sync job."""
        job_id = f"sync_{connector_name}_{user_id}_{datetime.now().timestamp()}"
        
        # Store job configuration
        job_config = {
            'connector_name': connector_name,
            'user_id': user_id,
            'partner_id': partner_id,
            'config': config or {}
        }
        
        # Add to scheduler
        self.scheduler.add_job(
            func=self._execute_connector_sync,
            trigger=IntervalTrigger(minutes=sync_interval_minutes),
            args=[job_id, job_config],
            id=job_id,
            replace_existing=True
        )
        
        # Save to database
        self._save_job_to_db(
            job_id=job_id,
            job_type=JobType.CONNECTOR_SYNC,
            user_id=user_id,
            partner_id=partner_id,
            config=json.dumps(job_config),
            next_run=datetime.now() + timedelta(minutes=sync_interval_minutes)
        )
        
        logger.info(f"Scheduled connector sync job: {job_id}")
        return job_id
    
    def execute_manual_sync(self, 
                           user_id: int,
                           connector_name: str, 
                           config: Dict[str, Any] = None) -> str:
        """Execute immediate manual sync."""
        job_id = f"manual_sync_{connector_name}_{user_id}_{datetime.now().timestamp()}"
        
        job_config = {
            'connector_name': connector_name,
            'user_id': user_id,
            'config': config or {},
            'manual': True
        }
        
        # Execute immediately
        self.scheduler.add_job(
            func=self._execute_connector_sync,
            args=[job_id, job_config],
            id=job_id
        )
        
        # Save to database
        self._save_job_to_db(
            job_id=job_id,
            job_type=JobType.MANUAL_SYNC,
            user_id=user_id,
            config=json.dumps(job_config),
            next_run=datetime.now()
        )
        
        logger.info(f"Executing manual sync job: {job_id}")
        return job_id
    
    def _execute_connector_sync(self, job_id: str, config: Dict[str, Any]):
        """Execute connector synchronization."""
        start_time = datetime.now()
        self._update_job_status(job_id, JobStatus.RUNNING)
        
        try:
            connector_name = config['connector_name']
            user_id = config['user_id']
            
            logger.info(f"Starting connector sync: {connector_name} for user {user_id}")
            
            # Get user credentials
            credentials = self._get_user_credentials(user_id, connector_name)
            if not credentials:
                raise Exception(f"No credentials found for {connector_name}")
            
            # Create connector instance
            instance = registry.create_instance(connector_name, config.get('config', {}))
            
            # Authenticate
            if not instance.authenticate(credentials):
                raise Exception("Authentication failed")
            
            # Fetch new trade data
            raw_trades = instance.fetch_trades()
            
            if raw_trades:
                # Normalize data
                normalized_df = instance.normalize_data(raw_trades)
                
                # Save to user's data store
                records_processed = self._save_synced_data(user_id, normalized_df, connector_name)
                
                # Log success
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                self._log_job_execution(
                    job_id=job_id,
                    start_time=start_time,
                    end_time=end_time,
                    status=JobStatus.COMPLETED,
                    records_processed=records_processed
                )
                
                logger.info(f"Sync completed: {records_processed} records processed in {execution_time:.2f}s")
            else:
                logger.info(f"No new data found for {connector_name}")
                
                self._log_job_execution(
                    job_id=job_id,
                    start_time=start_time,
                    end_time=datetime.now(),
                    status=JobStatus.COMPLETED,
                    records_processed=0
                )
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sync job {job_id} failed: {error_msg}")
            
            # Increment error count and potentially retry
            self._handle_job_error(job_id, error_msg)
            
            self._log_job_execution(
                job_id=job_id,
                start_time=start_time,
                end_time=datetime.now(),
                status=JobStatus.FAILED,
                error_message=error_msg
            )
            
            raise
    
    def _get_user_credentials(self, user_id: int, connector_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve user credentials for connector."""
        try:
            # Try different credential types
            api_key = self.credential_manager.get_api_key(user_id, connector_name)
            if api_key:
                return {'api_key': api_key}
            
            broker_creds = self.credential_manager.get_broker_credentials(user_id, connector_name)
            if broker_creds:
                return broker_creds
            
            oauth_token = self.credential_manager.get_oauth_token(user_id, connector_name)
            if oauth_token:
                return oauth_token
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            return None
    
    def _save_synced_data(self, user_id: int, df: pd.DataFrame, source: str) -> int:
        """Save synchronized data to user's data store."""
        if df.empty:
            return 0
        
        # Add metadata
        df['user_id'] = user_id
        df['sync_source'] = source
        df['sync_timestamp'] = datetime.now()
        
        # Save to CSV or database
        data_file = f"synced_data_{user_id}_{source}.csv"
        
        try:
            # Check if file exists
            if os.path.exists(data_file):
                # Append new data
                existing_df = pd.read_csv(data_file)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                
                # Remove duplicates based on key columns
                key_columns = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price']
                available_key_columns = [col for col in key_columns if col in combined_df.columns]
                
                if available_key_columns:
                    combined_df = combined_df.drop_duplicates(subset=available_key_columns, keep='last')
                
                combined_df.to_csv(data_file, index=False)
                return len(df)
            else:
                # Create new file
                df.to_csv(data_file, index=False)
                return len(df)
        
        except Exception as e:
            logger.error(f"Error saving synced data: {e}")
            raise
    
    def _handle_job_error(self, job_id: str, error_message: str):
        """Handle job execution errors with retry logic."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Increment error count
        cursor.execute('''
            UPDATE scheduled_jobs 
            SET error_count = error_count + 1, 
                last_error = ?,
                status = 'failed'
            WHERE id = ?
        ''', (error_message, job_id))
        
        # Get current error count
        cursor.execute('SELECT error_count FROM scheduled_jobs WHERE id = ?', (job_id,))
        result = cursor.fetchone()
        
        if result:
            error_count = result[0]
            
            # Disable job after 5 consecutive failures
            if error_count >= 5:
                cursor.execute('UPDATE scheduled_jobs SET is_active = 0 WHERE id = ?', (job_id,))
                logger.warning(f"Job {job_id} disabled after 5 failures")
                
                # Remove from scheduler
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass
        
        conn.commit()
        conn.close()
    
    def _save_job_to_db(self, 
                       job_id: str,
                       job_type: JobType,
                       user_id: int,
                       config: str,
                       next_run: datetime,
                       partner_id: Optional[str] = None):
        """Save job configuration to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO scheduled_jobs 
            (id, job_type, user_id, partner_id, config, next_run, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (job_id, job_type.value, user_id, partner_id, config, next_run))
        
        conn.commit()
        conn.close()
    
    def _update_job_status(self, job_id: str, status: JobStatus, error_message: str = None):
        """Update job status in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if error_message:
            cursor.execute('''
                UPDATE scheduled_jobs 
                SET status = ?, last_error = ?, last_run = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status.value, error_message, job_id))
        else:
            cursor.execute('''
                UPDATE scheduled_jobs 
                SET status = ?, last_run = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status.value, job_id))
        
        conn.commit()
        conn.close()
    
    def _log_job_execution(self,
                          job_id: str,
                          start_time: datetime,
                          end_time: datetime,
                          status: JobStatus,
                          records_processed: int = 0,
                          error_message: str = None):
        """Log job execution details."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO job_history 
            (job_id, execution_start, execution_end, status, records_processed, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (job_id, start_time, end_time, status.value, records_processed, error_message))
        
        conn.commit()
        conn.close()
    
    def get_user_jobs(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all jobs for a specific user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, job_type, status, scheduled_at, last_run, next_run, 
                   error_count, last_error, is_active
            FROM scheduled_jobs 
            WHERE user_id = ? 
            ORDER BY scheduled_at DESC
        ''', (user_id,))
        
        jobs = []
        for row in cursor.fetchall():
            jobs.append({
                'id': row[0],
                'type': row[1],
                'status': row[2],
                'scheduled_at': row[3],
                'last_run': row[4],
                'next_run': row[5],
                'error_count': row[6],
                'last_error': row[7],
                'is_active': bool(row[8])
            })
        
        conn.close()
        return jobs
    
    def get_job_history(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get execution history for a specific job."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT execution_start, execution_end, status, records_processed, error_message
            FROM job_history 
            WHERE job_id = ? 
            ORDER BY execution_start DESC 
            LIMIT ?
        ''', (job_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'start_time': row[0],
                'end_time': row[1],
                'status': row[2],
                'records_processed': row[3],
                'error_message': row[4]
            })
        
        conn.close()
        return history
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        try:
            # Remove from scheduler
            self.scheduler.remove_job(job_id)
            
            # Update database
            self._update_job_status(job_id, JobStatus.CANCELLED)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE scheduled_jobs SET is_active = 0 WHERE id = ?', (job_id,))
            conn.commit()
            conn.close()
            
            logger.info(f"Job {job_id} cancelled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def _cleanup_old_jobs(self):
        """Clean up old job history records."""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM job_history WHERE created_at < ?', (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {deleted_count} old job history records")
    
    def _check_credential_expiry(self):
        """Check for expiring credentials and notify users."""
        # This would integrate with the credential manager
        # to check for credentials expiring soon
        logger.info("Checking credential expiry...")

# Global scheduler instance
job_scheduler = JobScheduler()
