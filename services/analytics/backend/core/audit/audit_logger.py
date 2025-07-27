"""
Enhanced Audit Logging System for Compliance and Security

Provides comprehensive audit logging with search, retention, and compliance features
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from sqlalchemy import Column, String, DateTime, JSON, Text, Index, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import asyncio
from contextlib import contextmanager

from core.db.connection_pool import get_db
from core.logging_config import get_logger
from core.security_config import get_data_encryption
from core.cache.redis_cache import get_cache, CacheNamespace
from core.monitoring.datadog_apm import get_apm

logger = get_logger(__name__)

Base = declarative_base()


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"
    MFA_ENABLED = "auth.mfa.enabled"
    MFA_DISABLED = "auth.mfa.disabled"
    
    # Authorization events
    PERMISSION_GRANTED = "authz.permission.granted"
    PERMISSION_DENIED = "authz.permission.denied"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REMOVED = "authz.role.removed"
    
    # Data access events
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    
    # API events
    API_CALL = "api.call"
    API_ERROR = "api.error"
    API_RATE_LIMIT = "api.rate_limit"
    
    # Trading events
    TRADE_CREATED = "trade.created"
    TRADE_EXECUTED = "trade.executed"
    TRADE_CANCELLED = "trade.cancelled"
    TRADE_MODIFIED = "trade.modified"
    
    # Financial events
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    
    # Security events
    SECURITY_VIOLATION = "security.violation"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    IP_BLOCKED = "security.ip_blocked"
    ACCOUNT_LOCKED = "security.account_locked"
    
    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    CONFIG_CHANGE = "system.config.change"
    BACKUP_CREATED = "system.backup.created"
    BACKUP_RESTORED = "system.backup.restored"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    """Audit log database model"""
    __tablename__ = "audit_logs"
    
    # Primary fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    event_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, default=AuditSeverity.INFO.value)
    
    # Actor information
    user_id = Column(String, index=True)
    username = Column(String, index=True)
    ip_address = Column(String, index=True)
    user_agent = Column(String)
    session_id = Column(String, index=True)
    
    # Event details
    resource_type = Column(String, index=True)  # e.g., "trade", "user", "payment"
    resource_id = Column(String, index=True)
    action = Column(String, nullable=False)  # e.g., "create", "read", "update", "delete"
    result = Column(String, nullable=False)  # "success" or "failure"
    
    # Additional context
    metadata = Column(JSON)  # Additional event-specific data
    error_message = Column(Text)
    
    # Compliance fields
    data_classification = Column(String)  # e.g., "public", "internal", "confidential", "restricted"
    compliance_tags = Column(JSON)  # e.g., ["gdpr", "pci", "sox"]
    
    # Security fields
    risk_score = Column(Integer, default=0)  # 0-100
    encrypted_data = Column(Text)  # For sensitive data
    data_hash = Column(String)  # For integrity verification
    
    # Retention
    retention_date = Column(DateTime, index=True)
    archived = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_audit_timestamp_event', 'timestamp', 'event_type'),
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_compliance', 'data_classification', 'timestamp'),
    )


class AuditEvent(BaseModel):
    """Audit event model"""
    event_type: AuditEventType
    severity: AuditSeverity = AuditSeverity.INFO
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: str
    result: str = "success"
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    data_classification: str = "internal"
    compliance_tags: List[str] = Field(default_factory=list)
    risk_score: int = Field(0, ge=0, le=100)


class AuditLogger:
    """Enhanced audit logging system"""
    
    def __init__(self):
        self.encryption = get_data_encryption()
        self.cache = get_cache()
        self.apm = get_apm()
        
        # Batch settings
        self.batch_size = 100
        self.batch_timeout = 5.0  # seconds
        self._batch: List[AuditLog] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task = None
    
    def log(self, event: AuditEvent, db: Session = None) -> str:
        """Log an audit event"""
        try:
            # Create audit log entry
            audit_log = self._create_audit_log(event)
            
            # Log immediately if critical
            if event.severity == AuditSeverity.CRITICAL:
                self._persist_log(audit_log, db)
            else:
                # Add to batch
                asyncio.create_task(self._add_to_batch(audit_log))
            
            # Record metrics
            self._record_metrics(event)
            
            # Check for security alerts
            self._check_security_alerts(event)
            
            return audit_log.id
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            raise
    
    async def log_async(self, event: AuditEvent) -> str:
        """Async version of log"""
        return self.log(event)
    
    def _create_audit_log(self, event: AuditEvent) -> AuditLog:
        """Create audit log entry"""
        # Calculate retention date based on classification
        retention_days = {
            "public": 90,
            "internal": 365,
            "confidential": 2555,  # 7 years
            "restricted": 3650  # 10 years
        }.get(event.data_classification, 365)
        
        retention_date = datetime.utcnow() + timedelta(days=retention_days)
        
        # Encrypt sensitive data if present
        encrypted_data = None
        if event.metadata and event.data_classification in ["confidential", "restricted"]:
            sensitive_fields = ["password", "ssn", "credit_card", "api_key"]
            sensitive_data = {
                k: v for k, v in event.metadata.items()
                if any(field in k.lower() for field in sensitive_fields)
            }
            if sensitive_data:
                encrypted_data = self.encryption.encrypt_dict(sensitive_data)
                # Remove from regular metadata
                for key in sensitive_data:
                    event.metadata.pop(key)
        
        # Calculate data hash for integrity
        data_str = json.dumps({
            "event_type": event.event_type,
            "user_id": event.user_id,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "action": event.action,
            "result": event.result,
            "timestamp": datetime.utcnow().isoformat()
        }, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        return AuditLog(
            event_type=event.event_type,
            severity=event.severity,
            user_id=event.user_id,
            username=event.username,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            session_id=event.session_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            result=event.result,
            metadata=event.metadata,
            error_message=event.error_message,
            data_classification=event.data_classification,
            compliance_tags=event.compliance_tags,
            risk_score=event.risk_score,
            encrypted_data=encrypted_data,
            data_hash=data_hash,
            retention_date=retention_date
        )
    
    async def _add_to_batch(self, audit_log: AuditLog):
        """Add log to batch for bulk insert"""
        async with self._batch_lock:
            self._batch.append(audit_log)
            
            if len(self._batch) >= self.batch_size:
                await self._flush_batch()
            elif not self._batch_task:
                # Schedule batch flush
                self._batch_task = asyncio.create_task(self._batch_timer())
    
    async def _batch_timer(self):
        """Timer for batch timeout"""
        await asyncio.sleep(self.batch_timeout)
        async with self._batch_lock:
            if self._batch:
                await self._flush_batch()
            self._batch_task = None
    
    async def _flush_batch(self):
        """Flush batch to database"""
        if not self._batch:
            return
        
        batch_to_insert = self._batch
        self._batch = []
        
        try:
            db = next(get_db())
            db.bulk_save_objects(batch_to_insert)
            db.commit()
            
            logger.info(f"Flushed {len(batch_to_insert)} audit logs to database")
        except Exception as e:
            logger.error(f"Failed to flush audit batch: {e}")
            # Re-add to batch for retry
            self._batch.extend(batch_to_insert)
        finally:
            db.close()
    
    def _persist_log(self, audit_log: AuditLog, db: Session = None):
        """Persist single log immediately"""
        if db:
            db.add(audit_log)
            db.commit()
        else:
            db = next(get_db())
            try:
                db.add(audit_log)
                db.commit()
            finally:
                db.close()
    
    def _record_metrics(self, event: AuditEvent):
        """Record audit metrics"""
        if self.apm:
            tags = {
                "event_type": event.event_type,
                "severity": event.severity,
                "result": event.result,
                "resource_type": event.resource_type or "unknown"
            }
            
            # Count events
            self.apm.record_metric(
                "audit.event",
                1,
                "counter",
                tags
            )
            
            # Track risk scores
            if event.risk_score > 0:
                self.apm.record_metric(
                    "audit.risk_score",
                    event.risk_score,
                    "gauge",
                    tags
                )
    
    def _check_security_alerts(self, event: AuditEvent):
        """Check if event should trigger security alerts"""
        # High risk events
        if event.risk_score >= 80:
            logger.critical(
                f"High risk audit event: {event.event_type} "
                f"(risk_score={event.risk_score}, user={event.user_id})"
            )
            # TODO: Send to security team
        
        # Failed login tracking
        if event.event_type == AuditEventType.LOGIN_FAILURE:
            cache_key = f"failed_logins:{event.ip_address}"
            count = self.cache.get(CacheNamespace.TEMP, cache_key, 0)
            count += 1
            self.cache.set(CacheNamespace.TEMP, cache_key, count, ttl=300)
            
            if count >= 5:
                # Log security event
                self.log(AuditEvent(
                    event_type=AuditEventType.IP_BLOCKED,
                    severity=AuditSeverity.WARNING,
                    ip_address=event.ip_address,
                    action="block",
                    metadata={"failed_attempts": count},
                    risk_score=70
                ))
    
    def search(
        self,
        db: Session,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Search audit logs"""
        query = db.query(AuditLog)
        
        if event_types:
            query = query.filter(AuditLog.event_type.in_(event_types))
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if severity:
            query = query.filter(AuditLog.severity == severity)
        
        # Order by timestamp descending
        query = query.order_by(AuditLog.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_user_activity(
        self,
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity summary"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= start_date
        ).all()
        
        # Summarize activity
        activity = {
            "total_events": len(logs),
            "event_types": {},
            "resources_accessed": set(),
            "failed_actions": 0,
            "risk_events": 0,
            "ip_addresses": set()
        }
        
        for log in logs:
            # Count by event type
            activity["event_types"][log.event_type] = \
                activity["event_types"].get(log.event_type, 0) + 1
            
            # Track resources
            if log.resource_type and log.resource_id:
                activity["resources_accessed"].add(
                    f"{log.resource_type}:{log.resource_id}"
                )
            
            # Count failures
            if log.result == "failure":
                activity["failed_actions"] += 1
            
            # Count risk events
            if log.risk_score > 50:
                activity["risk_events"] += 1
            
            # Track IPs
            if log.ip_address:
                activity["ip_addresses"].add(log.ip_address)
        
        # Convert sets to lists for JSON serialization
        activity["resources_accessed"] = list(activity["resources_accessed"])
        activity["ip_addresses"] = list(activity["ip_addresses"])
        
        return activity
    
    def export_logs(
        self,
        db: Session,
        format: str = "json",
        **search_kwargs
    ) -> Union[str, bytes]:
        """Export audit logs"""
        logs = self.search(db, **search_kwargs)
        
        if format == "json":
            data = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "severity": log.severity,
                    "user_id": log.user_id,
                    "username": log.username,
                    "ip_address": log.ip_address,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "action": log.action,
                    "result": log.result,
                    "metadata": log.metadata,
                    "risk_score": log.risk_score
                }
                data.append(log_dict)
            
            return json.dumps(data, indent=2)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "ID", "Timestamp", "Event Type", "Severity",
                "User ID", "Username", "IP Address",
                "Resource Type", "Resource ID", "Action",
                "Result", "Risk Score"
            ])
            
            # Data
            for log in logs:
                writer.writerow([
                    log.id, log.timestamp, log.event_type, log.severity,
                    log.user_id, log.username, log.ip_address,
                    log.resource_type, log.resource_id, log.action,
                    log.result, log.risk_score
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def archive_old_logs(self, db: Session, days: int = 365):
        """Archive old audit logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find logs to archive
        logs_to_archive = db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff_date,
            AuditLog.archived == False,
            AuditLog.data_classification.in_(["public", "internal"])
        ).all()
        
        # Archive logs (in production, would move to cold storage)
        for log in logs_to_archive:
            log.archived = True
        
        db.commit()
        
        logger.info(f"Archived {len(logs_to_archive)} audit logs older than {days} days")
        
        return len(logs_to_archive)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    
    return _audit_logger


# Decorator for automatic audit logging
def audit_action(
    event_type: AuditEventType,
    resource_type: Optional[str] = None,
    extract_resource_id: Optional[Callable] = None,
    severity: AuditSeverity = AuditSeverity.INFO,
    risk_score: int = 0
):
    """Decorator to automatically log actions"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            
            # Extract context
            request = kwargs.get("request") or (args[0] if args else None)
            user_id = getattr(request.state, "user_id", None) if request else None
            
            # Extract resource ID
            resource_id = None
            if extract_resource_id:
                resource_id = extract_resource_id(*args, **kwargs)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                audit_logger.log(AuditEvent(
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    result="success",
                    risk_score=risk_score
                ))
                
                return result
                
            except Exception as e:
                # Log failure
                audit_logger.log(AuditEvent(
                    event_type=event_type,
                    severity=AuditSeverity.ERROR,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    result="failure",
                    error_message=str(e),
                    risk_score=min(risk_score + 20, 100)
                ))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            
            # Extract context
            request = kwargs.get("request") or (args[0] if args else None)
            user_id = getattr(request.state, "user_id", None) if request else None
            
            # Extract resource ID
            resource_id = None
            if extract_resource_id:
                resource_id = extract_resource_id(*args, **kwargs)
            
            try:
                result = func(*args, **kwargs)
                
                # Log success
                audit_logger.log(AuditEvent(
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    result="success",
                    risk_score=risk_score
                ))
                
                return result
                
            except Exception as e:
                # Log failure
                audit_logger.log(AuditEvent(
                    event_type=event_type,
                    severity=AuditSeverity.ERROR,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    result="failure",
                    error_message=str(e),
                    risk_score=min(risk_score + 20, 100)
                ))
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator