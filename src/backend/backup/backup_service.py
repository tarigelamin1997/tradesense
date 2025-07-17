"""
Automated backup service for TradeSense.
Handles scheduled backups, retention policies, and disaster recovery.
"""

import os
import json
import asyncio
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import aiofiles
import gzip
import shutil
from pathlib import Path
import schedule
import time

from app.core.config import settings
from app.core.db.session import get_db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.email_service import email_service
from src.backend.monitoring.metrics import backup_metrics


class BackupType:
    """Types of backups supported."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupDestination:
    """Backup storage destinations."""
    LOCAL = "local"
    S3 = "s3"
    GOOGLE_CLOUD = "gcs"
    AZURE = "azure"


class BackupStatus:
    """Backup job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackupService:
    """Manages automated backups for TradeSense."""
    
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIRECTORY or "/var/backups/tradesense")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # S3 configuration
        self.s3_client = None
        if settings.AWS_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        
        self.retention_policies = {
            'daily': 7,      # Keep daily backups for 7 days
            'weekly': 4,     # Keep weekly backups for 4 weeks
            'monthly': 12,   # Keep monthly backups for 12 months
            'yearly': 5      # Keep yearly backups for 5 years
        }
        
        self.backup_schedule = {
            'database': {'frequency': 'daily', 'time': '02:00'},
            'files': {'frequency': 'daily', 'time': '03:00'},
            'full': {'frequency': 'weekly', 'day': 'sunday', 'time': '04:00'}
        }
    
    async def backup_database(self, backup_type: str = BackupType.FULL) -> Dict[str, Any]:
        """Backup PostgreSQL database."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f"db_backup_{backup_type}_{timestamp}"
        
        try:
            # Record backup start
            backup_id = await self._record_backup_start(
                backup_name=backup_name,
                backup_type="database",
                backup_subtype=backup_type
            )
            
            # Create backup file path
            backup_file = self.backup_dir / f"{backup_name}.sql.gz"
            
            # PostgreSQL backup command
            pg_dump_cmd = [
                'pg_dump',
                f'--dbname={settings.DATABASE_URL}',
                '--no-owner',
                '--no-acl',
                '--clean',
                '--if-exists'
            ]
            
            if backup_type == BackupType.INCREMENTAL:
                # For incremental, only backup changed data (requires WAL archiving)
                pg_dump_cmd.extend(['--incremental', '--from-snapshot', self._get_last_snapshot()])
            
            # Execute backup
            process = subprocess.Popen(
                pg_dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Compress on the fly
            with gzip.open(backup_file, 'wb') as gz_file:
                for line in process.stdout:
                    gz_file.write(line)
            
            process.wait()
            
            if process.returncode != 0:
                error_msg = process.stderr.read().decode()
                raise Exception(f"pg_dump failed: {error_msg}")
            
            # Get file size
            file_size = backup_file.stat().st_size
            
            # Upload to remote storage
            remote_path = None
            if settings.BACKUP_TO_S3:
                remote_path = await self._upload_to_s3(backup_file, backup_name)
            
            # Record success
            await self._record_backup_complete(
                backup_id=backup_id,
                file_path=str(backup_file),
                file_size=file_size,
                remote_path=remote_path
            )
            
            # Update metrics
            backup_metrics.backup_completed.labels(
                backup_type='database',
                destination='s3' if remote_path else 'local'
            ).inc()
            backup_metrics.backup_size_bytes.labels(
                backup_type='database'
            ).observe(file_size)
            
            return {
                'backup_id': backup_id,
                'backup_name': backup_name,
                'file_path': str(backup_file),
                'file_size': file_size,
                'remote_path': remote_path,
                'duration': (datetime.utcnow() - datetime.strptime(timestamp, '%Y%m%d_%H%M%S')).total_seconds()
            }
            
        except Exception as e:
            # Record failure
            if 'backup_id' in locals():
                await self._record_backup_failure(backup_id, str(e))
            
            # Update metrics
            backup_metrics.backup_failures.labels(
                backup_type='database',
                reason=type(e).__name__
            ).inc()
            
            raise
    
    async def backup_files(self, include_patterns: List[str] = None) -> Dict[str, Any]:
        """Backup application files and user uploads."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f"files_backup_{timestamp}"
        
        try:
            # Record backup start
            backup_id = await self._record_backup_start(
                backup_name=backup_name,
                backup_type="files",
                backup_subtype="full"
            )
            
            # Default patterns
            if not include_patterns:
                include_patterns = [
                    settings.UPLOAD_DIRECTORY,
                    settings.EXPORT_STORAGE_PATH,
                    '/app/config',  # Application configuration
                    '/app/scripts'  # Custom scripts
                ]
            
            # Create tar archive
            backup_file = self.backup_dir / f"{backup_name}.tar.gz"
            
            tar_cmd = ['tar', '-czf', str(backup_file)]
            
            # Add include patterns
            for pattern in include_patterns:
                if os.path.exists(pattern):
                    tar_cmd.append(pattern)
            
            # Execute backup
            result = subprocess.run(tar_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar failed: {result.stderr}")
            
            # Get file size
            file_size = backup_file.stat().st_size
            
            # Upload to remote storage
            remote_path = None
            if settings.BACKUP_TO_S3:
                remote_path = await self._upload_to_s3(backup_file, backup_name)
            
            # Record success
            await self._record_backup_complete(
                backup_id=backup_id,
                file_path=str(backup_file),
                file_size=file_size,
                remote_path=remote_path
            )
            
            return {
                'backup_id': backup_id,
                'backup_name': backup_name,
                'file_path': str(backup_file),
                'file_size': file_size,
                'remote_path': remote_path
            }
            
        except Exception as e:
            if 'backup_id' in locals():
                await self._record_backup_failure(backup_id, str(e))
            raise
    
    async def backup_full(self) -> Dict[str, Any]:
        """Perform full system backup (database + files)."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f"full_backup_{timestamp}"
        
        results = {
            'backup_name': backup_name,
            'timestamp': timestamp,
            'components': {}
        }
        
        # Backup database
        try:
            db_result = await self.backup_database(BackupType.FULL)
            results['components']['database'] = db_result
        except Exception as e:
            results['components']['database'] = {'error': str(e)}
        
        # Backup files
        try:
            files_result = await self.backup_files()
            results['components']['files'] = files_result
        except Exception as e:
            results['components']['files'] = {'error': str(e)}
        
        # Create manifest
        manifest_file = self.backup_dir / f"{backup_name}_manifest.json"
        async with aiofiles.open(manifest_file, 'w') as f:
            await f.write(json.dumps(results, indent=2, default=str))
        
        # Upload manifest
        if settings.BACKUP_TO_S3:
            await self._upload_to_s3(manifest_file, f"{backup_name}_manifest")
        
        # Send notification
        await self._send_backup_notification(results)
        
        return results
    
    async def restore_database(self, backup_id: str, target_db: Optional[str] = None) -> Dict[str, Any]:
        """Restore database from backup."""
        # Get backup info
        backup_info = await self._get_backup_info(backup_id)
        if not backup_info:
            raise ValueError(f"Backup {backup_id} not found")
        
        # Download from S3 if needed
        backup_file = Path(backup_info['file_path'])
        if not backup_file.exists() and backup_info.get('remote_path'):
            backup_file = await self._download_from_s3(backup_info['remote_path'])
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Create restore point
        restore_point = await self.backup_database(BackupType.FULL)
        
        try:
            # Prepare psql command
            psql_cmd = [
                'psql',
                f'--dbname={target_db or settings.DATABASE_URL}'
            ]
            
            # Decompress and restore
            with gzip.open(backup_file, 'rb') as gz_file:
                process = subprocess.Popen(
                    psql_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = process.communicate(gz_file.read())
                
                if process.returncode != 0:
                    raise Exception(f"psql restore failed: {stderr.decode()}")
            
            # Record restore
            await self._record_restore(
                backup_id=backup_id,
                restore_point_id=restore_point['backup_id'],
                status='completed'
            )
            
            return {
                'status': 'completed',
                'backup_id': backup_id,
                'restore_point_id': restore_point['backup_id'],
                'restored_at': datetime.utcnow()
            }
            
        except Exception as e:
            # Record failure
            await self._record_restore(
                backup_id=backup_id,
                restore_point_id=restore_point['backup_id'],
                status='failed',
                error=str(e)
            )
            raise
    
    async def cleanup_old_backups(self) -> Dict[str, int]:
        """Clean up old backups based on retention policy."""
        deleted_counts = {
            'local': 0,
            'remote': 0
        }
        
        # Get all backups
        async with get_db() as db:
            result = await db.execute(
                text("""
                    SELECT id, backup_name, file_path, remote_path, created_at,
                           backup_type, backup_frequency
                    FROM backups
                    WHERE status = 'completed'
                    ORDER BY created_at DESC
                """)
            )
            
            backups = result.fetchall()
        
        # Group by frequency
        backups_by_freq = {}
        for backup in backups:
            freq = backup.backup_frequency or 'daily'
            if freq not in backups_by_freq:
                backups_by_freq[freq] = []
            backups_by_freq[freq].append(backup)
        
        # Apply retention policies
        for frequency, retention_days in self.retention_policies.items():
            if frequency not in backups_by_freq:
                continue
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            for backup in backups_by_freq[frequency]:
                if backup.created_at < cutoff_date:
                    # Delete local file
                    if backup.file_path and Path(backup.file_path).exists():
                        Path(backup.file_path).unlink()
                        deleted_counts['local'] += 1
                    
                    # Delete from S3
                    if backup.remote_path:
                        await self._delete_from_s3(backup.remote_path)
                        deleted_counts['remote'] += 1
                    
                    # Mark as deleted in database
                    await self._mark_backup_deleted(backup.id)
        
        # Update metrics
        backup_metrics.backups_deleted.labels(location='local').inc(deleted_counts['local'])
        backup_metrics.backups_deleted.labels(location='remote').inc(deleted_counts['remote'])
        
        return deleted_counts
    
    async def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup integrity."""
        backup_info = await self._get_backup_info(backup_id)
        if not backup_info:
            raise ValueError(f"Backup {backup_id} not found")
        
        verification_results = {
            'backup_id': backup_id,
            'verified_at': datetime.utcnow(),
            'checks': {}
        }
        
        # Check file exists
        backup_file = Path(backup_info['file_path'])
        verification_results['checks']['file_exists'] = backup_file.exists()
        
        if backup_file.exists():
            # Check file size
            actual_size = backup_file.stat().st_size
            verification_results['checks']['file_size_match'] = actual_size == backup_info['file_size']
            
            # Check file integrity
            if backup_info['backup_type'] == 'database':
                # Test database backup integrity
                try:
                    with gzip.open(backup_file, 'rb') as f:
                        # Read first few lines to check format
                        header = f.read(1024).decode('utf-8', errors='ignore')
                        verification_results['checks']['valid_sql'] = 'PostgreSQL' in header
                except Exception as e:
                    verification_results['checks']['valid_sql'] = False
                    verification_results['checks']['error'] = str(e)
        
        # Check S3 backup
        if backup_info.get('remote_path'):
            try:
                s3_exists = await self._check_s3_exists(backup_info['remote_path'])
                verification_results['checks']['s3_exists'] = s3_exists
            except Exception as e:
                verification_results['checks']['s3_exists'] = False
                verification_results['checks']['s3_error'] = str(e)
        
        # Overall status
        all_checks_passed = all(
            v for k, v in verification_results['checks'].items() 
            if not k.endswith('_error')
        )
        verification_results['status'] = 'passed' if all_checks_passed else 'failed'
        
        # Update database
        await self._update_backup_verification(backup_id, verification_results)
        
        return verification_results
    
    async def schedule_backups(self):
        """Schedule automated backups."""
        # Database backup - daily at 2 AM
        schedule.every().day.at("02:00").do(lambda: asyncio.create_task(self.backup_database()))
        
        # Files backup - daily at 3 AM
        schedule.every().day.at("03:00").do(lambda: asyncio.create_task(self.backup_files()))
        
        # Full backup - weekly on Sunday at 4 AM
        schedule.every().sunday.at("04:00").do(lambda: asyncio.create_task(self.backup_full()))
        
        # Cleanup - weekly on Monday at 5 AM
        schedule.every().monday.at("05:00").do(lambda: asyncio.create_task(self.cleanup_old_backups()))
        
        # Verification - daily at 6 AM
        schedule.every().day.at("06:00").do(lambda: asyncio.create_task(self._verify_recent_backups()))
        
        # Run scheduler
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    # Helper methods
    async def _upload_to_s3(self, local_file: Path, s3_key: str) -> str:
        """Upload file to S3."""
        if not self.s3_client:
            raise ValueError("S3 client not configured")
        
        s3_path = f"backups/{s3_key}"
        
        try:
            self.s3_client.upload_file(
                str(local_file),
                settings.S3_BACKUP_BUCKET,
                s3_path,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost savings
                }
            )
            
            return f"s3://{settings.S3_BACKUP_BUCKET}/{s3_path}"
            
        except ClientError as e:
            raise Exception(f"S3 upload failed: {e}")
    
    async def _download_from_s3(self, s3_path: str) -> Path:
        """Download file from S3."""
        if not self.s3_client:
            raise ValueError("S3 client not configured")
        
        # Parse S3 path
        bucket, key = s3_path.replace('s3://', '').split('/', 1)
        
        # Local file path
        local_file = self.backup_dir / Path(key).name
        
        try:
            self.s3_client.download_file(bucket, key, str(local_file))
            return local_file
        except ClientError as e:
            raise Exception(f"S3 download failed: {e}")
    
    async def _record_backup_start(self, backup_name: str, backup_type: str, backup_subtype: str) -> str:
        """Record backup start in database."""
        async with get_db() as db:
            result = await db.execute(
                text("""
                    INSERT INTO backups (
                        backup_name, backup_type, backup_subtype,
                        status, started_at
                    ) VALUES (
                        :backup_name, :backup_type, :backup_subtype,
                        'running', NOW()
                    )
                    RETURNING id
                """),
                {
                    "backup_name": backup_name,
                    "backup_type": backup_type,
                    "backup_subtype": backup_subtype
                }
            )
            await db.commit()
            return str(result.scalar())
    
    async def _record_backup_complete(
        self, 
        backup_id: str, 
        file_path: str, 
        file_size: int, 
        remote_path: Optional[str] = None
    ):
        """Record backup completion."""
        async with get_db() as db:
            await db.execute(
                text("""
                    UPDATE backups
                    SET status = 'completed',
                        completed_at = NOW(),
                        file_path = :file_path,
                        file_size = :file_size,
                        remote_path = :remote_path
                    WHERE id = :backup_id
                """),
                {
                    "backup_id": backup_id,
                    "file_path": file_path,
                    "file_size": file_size,
                    "remote_path": remote_path
                }
            )
            await db.commit()
    
    async def _send_backup_notification(self, results: Dict[str, Any]):
        """Send backup completion notification."""
        # Check for failures
        has_failures = any(
            'error' in component 
            for component in results.get('components', {}).values()
        )
        
        subject = f"TradeSense Backup {'Failed' if has_failures else 'Completed'}"
        
        body = f"""Backup Status Report
        
Backup Name: {results['backup_name']}
Timestamp: {results['timestamp']}
Status: {'Failed' if has_failures else 'Success'}

Components:
"""
        
        for component, result in results.get('components', {}).items():
            if 'error' in result:
                body += f"\n{component}: FAILED - {result['error']}"
            else:
                body += f"\n{component}: SUCCESS - {result.get('file_size', 0) / 1024 / 1024:.1f} MB"
        
        await email_service.send_admin_email(subject, body)


# Initialize service
backup_service = BackupService()