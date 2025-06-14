
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import sqlite3
import json
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from connectors.registry import registry
from connectors.loader import get_available_connectors
from integration_manager import IntegrationManager
from models.trade_model import UniversalTradeDataModel
from credential_manager import CredentialManager
from logging_manager import log_info, log_error, log_warning, LogCategory

class SyncStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"

class SyncTrigger(Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    REAL_TIME = "real_time"
    WEBHOOK = "webhook"

@dataclass
class SyncJob:
    """Represents a sync job for a specific integration."""
    job_id: str
    user_id: int
    integration_id: int
    provider_name: str
    trigger: SyncTrigger
    status: SyncStatus = SyncStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class TradeDataSyncEngine:
    """Comprehensive trade data sync engine for automated data pulling and normalization."""
    
    def __init__(self, db_path: str = "tradesense.db", max_workers: int = 5):
        self.db_path = db_path
        self.max_workers = max_workers
        self.integration_manager = IntegrationManager(db_path)
        self.credential_manager = CredentialManager(db_path)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Runtime state
        self.active_jobs: Dict[str, SyncJob] = {}
        self.sync_callbacks: List[Callable] = []
        self.running = False
        self.scheduler_thread = None
        
        # Performance tracking
        self.sync_metrics = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'total_records_processed': 0,
            'avg_sync_duration': 0.0
        }
        
        self.init_sync_tables()
        log_info("Trade Data Sync Engine initialized", category=LogCategory.SYSTEM_ERROR)
    
    def init_sync_tables(self):
        """Initialize sync engine database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sync jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_jobs (
                job_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                integration_id INTEGER NOT NULL,
                provider_name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                records_processed INTEGER DEFAULT 0,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                sync_duration REAL,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (integration_id) REFERENCES integrations (id)
            )
        ''')
        
        # Sync schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                integration_id INTEGER NOT NULL,
                frequency_minutes INTEGER NOT NULL,
                next_run TIMESTAMP NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (integration_id) REFERENCES integrations (id)
            )
        ''')
        
        # Real-time sync tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_sync_state (
                integration_id INTEGER PRIMARY KEY,
                last_trade_timestamp TIMESTAMP,
                last_sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cursor_position TEXT,
                is_active BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (integration_id) REFERENCES integrations (id)
            )
        ''')
        
        # Data normalization cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS normalization_cache (
                cache_key TEXT PRIMARY KEY,
                provider_name TEXT NOT NULL,
                raw_data_hash TEXT NOT NULL,
                normalized_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        # Performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT NOT NULL,
                sync_type TEXT NOT NULL,
                records_count INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                memory_usage_mb REAL,
                cpu_usage_percent REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_jobs_user_status ON sync_jobs (user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_jobs_integration ON sync_jobs (integration_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_schedules_next_run ON sync_schedules (next_run, enabled)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_realtime_sync_active ON realtime_sync_state (is_active)')
        
        conn.commit()
        conn.close()
    
    def start_engine(self):
        """Start the sync engine with scheduler."""
        if self.running:
            log_warning("Sync engine is already running", category=LogCategory.SYSTEM_ERROR)
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        log_info("Trade Data Sync Engine started", category=LogCategory.SYSTEM_ERROR)
    
    def stop_engine(self):
        """Stop the sync engine."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # Cancel pending jobs
        for job_id in list(self.active_jobs.keys()):
            self.cancel_sync_job(job_id)
        
        self.executor.shutdown(wait=True)
        log_info("Trade Data Sync Engine stopped", category=LogCategory.SYSTEM_ERROR)
    
    def _scheduler_loop(self):
        """Main scheduler loop that runs scheduled syncs."""
        while self.running:
            try:
                self._process_scheduled_syncs()
                self._cleanup_old_jobs()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                log_error(f"Scheduler loop error: {str(e)}", category=LogCategory.SYSTEM_ERROR)
                time.sleep(60)  # Wait longer on errors
    
    def _process_scheduled_syncs(self):
        """Process due scheduled syncs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ss.integration_id, i.user_id, i.provider_name, ss.frequency_minutes
            FROM sync_schedules ss
            JOIN integrations i ON ss.integration_id = i.id
            WHERE ss.enabled = TRUE 
            AND ss.next_run <= CURRENT_TIMESTAMP
            AND i.status = 'connected'
        ''')
        
        due_syncs = cursor.fetchall()
        conn.close()
        
        for integration_id, user_id, provider_name, frequency in due_syncs:
            # Create scheduled sync job
            job = self.create_sync_job(
                user_id=user_id,
                integration_id=integration_id,
                provider_name=provider_name,
                trigger=SyncTrigger.SCHEDULED
            )
            
            # Schedule next run
            self._update_next_run(integration_id, frequency)
    
    def create_sync_job(self, user_id: int, integration_id: int, 
                       provider_name: str, trigger: SyncTrigger) -> SyncJob:
        """Create and queue a new sync job."""
        job_id = f"{provider_name}_{user_id}_{integration_id}_{int(time.time())}"
        
        job = SyncJob(
            job_id=job_id,
            user_id=user_id,
            integration_id=integration_id,
            provider_name=provider_name,
            trigger=trigger
        )
        
        self.active_jobs[job_id] = job
        
        # Submit to executor
        future = self.executor.submit(self._execute_sync_job, job)
        future.add_done_callback(lambda f: self._job_completed(job_id, f))
        
        log_info(f"Sync job created: {job_id}", 
                details={'user_id': user_id, 'provider': provider_name},
                category=LogCategory.DATA_PROCESSING)
        
        return job
    
    def _execute_sync_job(self, job: SyncJob) -> Dict[str, Any]:
        """Execute a sync job."""
        start_time = time.time()
        
        try:
            job.status = SyncStatus.RUNNING
            job.started_at = datetime.now()
            self._save_job_state(job)
            
            log_info(f"Starting sync job: {job.job_id}", 
                    details={'provider': job.provider_name},
                    category=LogCategory.DATA_PROCESSING)
            
            # Get connector instance
            connector = self._get_connector_instance(job)
            if not connector:
                raise Exception("Failed to create connector instance")
            
            # Get credentials and authenticate
            credentials = self._get_integration_credentials(job)
            if not connector.authenticate(credentials):
                raise Exception("Authentication failed")
            
            # Fetch raw trade data
            raw_trades = self._fetch_trade_data(connector, job)
            
            # Normalize data
            normalized_model = self._normalize_trade_data(connector, raw_trades, job)
            
            # Store in user's trade database
            records_stored = self._store_normalized_trades(normalized_model, job)
            
            # Update job success
            job.status = SyncStatus.SUCCESS
            job.records_processed = records_stored
            job.completed_at = datetime.now()
            
            duration = time.time() - start_time
            
            # Update metrics
            self._update_sync_metrics(job, duration, True)
            
            # Update integration status
            self.integration_manager.record_sync_attempt(
                job.integration_id, 
                job.trigger.value, 
                'success', 
                records_stored,
                duration=duration
            )
            
            log_info(f"Sync job completed successfully: {job.job_id}", 
                    details={'records_processed': records_stored, 'duration': duration},
                    category=LogCategory.DATA_PROCESSING)
            
            return {
                'status': 'success',
                'records_processed': records_stored,
                'duration': duration
            }
            
        except Exception as e:
            job.status = SyncStatus.ERROR
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            duration = time.time() - start_time
            
            # Update metrics
            self._update_sync_metrics(job, duration, False)
            
            # Update integration status
            self.integration_manager.record_sync_attempt(
                job.integration_id,
                job.trigger.value,
                'error',
                0,
                str(e),
                duration
            )
            
            log_error(f"Sync job failed: {job.job_id} - {str(e)}", 
                     details={'provider': job.provider_name, 'user_id': job.user_id},
                     category=LogCategory.DATA_PROCESSING)
            
            # Retry logic
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = SyncStatus.PENDING
                
                # Exponential backoff
                delay = min(300, 30 * (2 ** job.retry_count))  # Max 5 minutes
                
                def retry_job():
                    time.sleep(delay)
                    if job.job_id in self.active_jobs:
                        self._execute_sync_job(job)
                
                threading.Thread(target=retry_job, daemon=True).start()
                
                log_info(f"Scheduling retry for job: {job.job_id} (attempt {job.retry_count + 1})",
                        category=LogCategory.DATA_PROCESSING)
            
            return {
                'status': 'error',
                'error': str(e),
                'duration': duration
            }
        
        finally:
            self._save_job_state(job)
    
    def _get_connector_instance(self, job: SyncJob):
        """Get connector instance for the job."""
        try:
            return registry.create_instance(job.provider_name)
        except Exception as e:
            log_error(f"Failed to create connector instance for {job.provider_name}: {str(e)}",
                     category=LogCategory.SYSTEM_ERROR)
            return None
    
    def _get_integration_credentials(self, job: SyncJob) -> Dict[str, str]:
        """Get integration credentials."""
        credential_id = f"broker_{job.provider_name}_{job.user_id}"
        credentials = self.credential_manager.get_broker_credentials(
            job.user_id, job.provider_name
        )
        
        if not credentials:
            raise Exception("No credentials found for integration")
        
        return credentials
    
    def _fetch_trade_data(self, connector, job: SyncJob) -> List[Dict[str, Any]]:
        """Fetch trade data using connector."""
        # Get last sync timestamp for incremental sync
        last_sync = self._get_last_sync_timestamp(job.integration_id)
        
        # Fetch trades since last sync
        if last_sync:
            raw_trades = connector.fetch_trades(start_date=last_sync)
        else:
            # First sync - get last 30 days
            start_date = datetime.now() - timedelta(days=30)
            raw_trades = connector.fetch_trades(start_date=start_date)
        
        return raw_trades or []
    
    def _normalize_trade_data(self, connector, raw_trades: List[Dict], 
                            job: SyncJob) -> UniversalTradeDataModel:
        """Normalize raw trade data to universal format."""
        if not raw_trades:
            return UniversalTradeDataModel()
        
        # Check cache first
        cache_key = self._generate_cache_key(job.provider_name, raw_trades)
        cached_model = self._get_cached_normalization(cache_key)
        
        if cached_model:
            log_info(f"Using cached normalization for {job.provider_name}",
                    category=LogCategory.DATA_PROCESSING)
            return cached_model
        
        # Normalize data
        normalized_model = connector.to_universal_model(raw_trades)
        
        # Validate data quality
        validation_report = normalized_model.validate_all()
        if validation_report['errors']:
            log_warning(f"Data validation issues: {validation_report['errors']}",
                       category=LogCategory.DATA_PROCESSING)
        
        # Remove duplicates
        duplicates_removed = normalized_model.remove_duplicates()
        if duplicates_removed > 0:
            log_info(f"Removed {duplicates_removed} duplicate trades",
                    category=LogCategory.DATA_PROCESSING)
        
        # Cache normalized data
        self._cache_normalization(cache_key, job.provider_name, normalized_model)
        
        return normalized_model
    
    def _store_normalized_trades(self, model: UniversalTradeDataModel, 
                               job: SyncJob) -> int:
        """Store normalized trades in user's database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create user trades table if not exists
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS user_{job.user_id}_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                qty REAL NOT NULL,
                direction TEXT NOT NULL,
                pnl REAL NOT NULL,
                trade_type TEXT NOT NULL,
                broker TEXT NOT NULL,
                notes TEXT,
                commission REAL,
                stop_loss REAL,
                take_profit REAL,
                tags TEXT,
                data_source TEXT NOT NULL,
                import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                integration_id INTEGER,
                FOREIGN KEY (integration_id) REFERENCES integrations (id)
            )
        ''')
        
        # Insert trades
        df = model.get_dataframe()
        records_stored = 0
        
        for _, trade in df.iterrows():
            try:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO user_{job.user_id}_trades 
                    (trade_id, symbol, entry_time, exit_time, entry_price, exit_price,
                     qty, direction, pnl, trade_type, broker, notes, commission,
                     stop_loss, take_profit, tags, data_source, integration_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade['trade_id'], trade['symbol'], trade['entry_time'],
                    trade['exit_time'], trade['entry_price'], trade['exit_price'],
                    trade['qty'], trade['direction'], trade['pnl'],
                    trade['trade_type'], trade['broker'], trade['notes'],
                    trade['commission'], trade['stop_loss'], trade['take_profit'],
                    trade['tags'], trade['data_source'], job.integration_id
                ))
                records_stored += 1
            except Exception as e:
                log_error(f"Failed to store trade {trade.get('trade_id', 'unknown')}: {str(e)}",
                         category=LogCategory.DATA_PROCESSING)
        
        # Update last sync timestamp
        self._update_last_sync_timestamp(job.integration_id)
        
        conn.commit()
        conn.close()
        
        return records_stored
    
    def _job_completed(self, job_id: str, future):
        """Handle job completion."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            
            # Trigger callbacks
            for callback in self.sync_callbacks:
                try:
                    callback(job, future.result() if not future.exception() else None)
                except Exception as e:
                    log_error(f"Sync callback error: {str(e)}", category=LogCategory.SYSTEM_ERROR)
            
            # Clean up job after some time
            def cleanup():
                time.sleep(300)  # Keep for 5 minutes
                self.active_jobs.pop(job_id, None)
            
            threading.Thread(target=cleanup, daemon=True).start()
    
    def get_sync_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a sync job."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                'job_id': job.job_id,
                'status': job.status.value,
                'provider_name': job.provider_name,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'records_processed': job.records_processed,
                'error_message': job.error_message,
                'retry_count': job.retry_count
            }
        return None
    
    def cancel_sync_job(self, job_id: str) -> bool:
        """Cancel a sync job."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = SyncStatus.CANCELLED
            self._save_job_state(job)
            
            log_info(f"Sync job cancelled: {job_id}", category=LogCategory.USER_ACTION)
            return True
        return False
    
    def schedule_integration_sync(self, integration_id: int, frequency_minutes: int):
        """Schedule regular syncs for an integration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        next_run = datetime.now() + timedelta(minutes=frequency_minutes)
        
        cursor.execute('''
            INSERT OR REPLACE INTO sync_schedules 
            (integration_id, frequency_minutes, next_run)
            VALUES (?, ?, ?)
        ''', (integration_id, frequency_minutes, next_run))
        
        conn.commit()
        conn.close()
        
        log_info(f"Scheduled sync for integration {integration_id} every {frequency_minutes} minutes",
                category=LogCategory.SYSTEM_ERROR)
    
    def enable_realtime_sync(self, integration_id: int):
        """Enable real-time sync for an integration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO realtime_sync_state 
            (integration_id, is_active, last_sync_timestamp)
            VALUES (?, TRUE, CURRENT_TIMESTAMP)
        ''', (integration_id,))
        
        conn.commit()
        conn.close()
        
        log_info(f"Real-time sync enabled for integration {integration_id}",
                category=LogCategory.SYSTEM_ERROR)
    
    def trigger_manual_sync(self, user_id: int, integration_id: int) -> SyncJob:
        """Trigger a manual sync for an integration."""
        # Get integration details
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT provider_name FROM integrations 
            WHERE id = ? AND user_id = ?
        ''', (integration_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise Exception("Integration not found")
        
        provider_name = result[0]
        
        return self.create_sync_job(
            user_id=user_id,
            integration_id=integration_id,
            provider_name=provider_name,
            trigger=SyncTrigger.MANUAL
        )
    
    def get_sync_metrics(self) -> Dict[str, Any]:
        """Get sync engine performance metrics."""
        return self.sync_metrics.copy()
    
    def register_sync_callback(self, callback: Callable):
        """Register a callback for sync events."""
        self.sync_callbacks.append(callback)
    
    # Helper methods
    def _save_job_state(self, job: SyncJob):
        """Save job state to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sync_jobs 
            (job_id, user_id, integration_id, provider_name, trigger_type,
             status, created_at, started_at, completed_at, records_processed,
             error_message, retry_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job.job_id, job.user_id, job.integration_id, job.provider_name,
            job.trigger.value, job.status.value, job.created_at,
            job.started_at, job.completed_at, job.records_processed,
            job.error_message, job.retry_count
        ))
        
        conn.commit()
        conn.close()
    
    def _update_next_run(self, integration_id: int, frequency_minutes: int):
        """Update next run time for scheduled sync."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        next_run = datetime.now() + timedelta(minutes=frequency_minutes)
        
        cursor.execute('''
            UPDATE sync_schedules 
            SET next_run = ?, last_run = CURRENT_TIMESTAMP
            WHERE integration_id = ?
        ''', (next_run, integration_id))
        
        conn.commit()
        conn.close()
    
    def _get_last_sync_timestamp(self, integration_id: int) -> Optional[datetime]:
        """Get last sync timestamp for incremental sync."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_sync_timestamp FROM realtime_sync_state 
            WHERE integration_id = ?
        ''', (integration_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return datetime.fromisoformat(result[0])
        return None
    
    def _update_last_sync_timestamp(self, integration_id: int):
        """Update last sync timestamp."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO realtime_sync_state 
            (integration_id, last_sync_timestamp)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (integration_id,))
        
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, provider_name: str, raw_trades: List[Dict]) -> str:
        """Generate cache key for normalization."""
        import hashlib
        
        data_str = json.dumps(raw_trades, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        
        return f"{provider_name}_{data_hash}"
    
    def _get_cached_normalization(self, cache_key: str) -> Optional[UniversalTradeDataModel]:
        """Get cached normalization result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT normalized_data FROM normalization_cache 
            WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (cache_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            try:
                # Deserialize cached model
                import pickle
                return pickle.loads(result[0].encode('latin1'))
            except Exception:
                return None
        
        return None
    
    def _cache_normalization(self, cache_key: str, provider_name: str, 
                           model: UniversalTradeDataModel):
        """Cache normalization result."""
        try:
            import pickle
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Serialize model
            serialized_data = pickle.dumps(model).decode('latin1')
            expires_at = datetime.now() + timedelta(hours=1)  # Cache for 1 hour
            
            cursor.execute('''
                INSERT OR REPLACE INTO normalization_cache 
                (cache_key, provider_name, raw_data_hash, normalized_data, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (cache_key, provider_name, cache_key.split('_')[-1], 
                  serialized_data, expires_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            log_error(f"Failed to cache normalization: {str(e)}", 
                     category=LogCategory.SYSTEM_ERROR)
    
    def _update_sync_metrics(self, job: SyncJob, duration: float, success: bool):
        """Update sync performance metrics."""
        self.sync_metrics['total_syncs'] += 1
        
        if success:
            self.sync_metrics['successful_syncs'] += 1
            self.sync_metrics['total_records_processed'] += job.records_processed
        else:
            self.sync_metrics['failed_syncs'] += 1
        
        # Update average duration
        total_syncs = self.sync_metrics['total_syncs']
        current_avg = self.sync_metrics['avg_sync_duration']
        self.sync_metrics['avg_sync_duration'] = (
            (current_avg * (total_syncs - 1) + duration) / total_syncs
        )
        
        # Store detailed metrics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sync_performance_metrics 
            (provider_name, sync_type, records_count, duration_seconds)
            VALUES (?, ?, ?, ?)
        ''', (job.provider_name, job.trigger.value, 
              job.records_processed, duration))
        
        conn.commit()
        conn.close()
    
    def _cleanup_old_jobs(self):
        """Clean up old job records."""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM sync_jobs 
            WHERE created_at < ? AND status IN ('success', 'error', 'cancelled')
        ''', (cutoff_time,))
        
        # Clean up old cache entries
        cursor.execute('''
            DELETE FROM normalization_cache 
            WHERE expires_at < CURRENT_TIMESTAMP
        ''', ())
        
        conn.commit()
        conn.close()

# Global sync engine instance
sync_engine = TradeDataSyncEngine()
