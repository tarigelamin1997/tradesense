"""
Monitoring API endpoints for TradeSense.
Provides health checks, metrics, and system status.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from sqlalchemy import text

from core.auth import get_current_user, require_admin
from core.db.session import get_db
from models.user import User
from monitoring import health_checker, alerting_system
from monitoring.metrics import (
    active_users, system_info, memory_usage, cpu_usage
)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tradesense-api"
    }


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    # Quick check of critical components
    try:
        # Check database
        async with get_db() as db:
            await db.execute(text("SELECT 1"))
        
        # Check Redis
        from core.cache import redis_client
        await redis_client.ping()
        
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe."""
    return {"status": "started"}


@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user)
):
    """Detailed health check with component status."""
    health_status = await health_checker.check_health(detailed=True)
    
    # Add user context
    health_status["checked_by"] = current_user.email
    
    return health_status


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    metrics = generate_latest()
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)


@router.get("/status")
async def system_status(
    current_user: User = Depends(require_admin)
):
    """Get comprehensive system status."""
    
    # Get health status
    health = await health_checker.check_health(detailed=True)
    
    # Get active alerts
    alerts = [
        {
            "name": alert.name,
            "severity": alert.severity,
            "message": alert.message,
            "fired_at": alert.fired_at.isoformat()
        }
        for alert in alerting_system.active_alerts.values()
    ]
    
    # Get system metrics
    async with get_db() as db:
        # Database stats
        db_stats_result = await db.execute(
            text("""
                SELECT 
                    (SELECT count(*) FROM users) as total_users,
                    (SELECT count(*) FROM trades) as total_trades,
                    (SELECT count(*) FROM user_sessions WHERE last_activity > NOW() - INTERVAL '1 hour') as active_sessions,
                    pg_database_size(current_database()) as database_size
            """)
        )
        db_stats = db_stats_result.first()
        
        # Recent activity
        activity_result = await db.execute(
            text("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as trades_created
                FROM trades
                WHERE created_at > NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
        )
        recent_activity = [
            {"date": row.date.isoformat(), "trades": row.trades_created}
            for row in activity_result
        ]
    
    return {
        "health": health,
        "alerts": alerts,
        "statistics": {
            "users": {
                "total": db_stats.total_users,
                "active_sessions": db_stats.active_sessions
            },
            "trades": {
                "total": db_stats.total_trades
            },
            "database": {
                "size_mb": db_stats.database_size / (1024 * 1024)
            }
        },
        "recent_activity": recent_activity,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin)
):
    """Get system alerts."""
    try:
        async with get_db() as db:
            query = """
                SELECT 
                    id, name, severity, status, message,
                    details, fired_at, resolved_at, acknowledged_at,
                    acknowledged_by, tags, runbook_url
                FROM alerts
                WHERE 1=1
            """
            params = {}
            
            if status:
                query += " AND status = :status"
                params["status"] = status
                
            if severity:
                query += " AND severity = :severity"
                params["severity"] = severity
            
            query += " ORDER BY fired_at DESC LIMIT :limit"
            params["limit"] = limit
            
            result = await db.execute(text(query), params)
            
            alerts = []
            for row in result:
                alerts.append({
                    "id": row.id,
                    "name": row.name,
                    "severity": row.severity,
                    "status": row.status,
                    "message": row.message,
                    "details": row.details,
                    "fired_at": row.fired_at.isoformat(),
                    "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
                    "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None,
                    "acknowledged_by": row.acknowledged_by,
                    "tags": row.tags,
                    "runbook_url": row.runbook_url
                })
            
            return {
                "alerts": alerts,
                "count": len(alerts),
                "active_count": len([a for a in alerts if a["status"] == "firing"])
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(require_admin)
):
    """Acknowledge an alert."""
    try:
        async with get_db() as db:
            # Update alert
            result = await db.execute(
                text("""
                    UPDATE alerts
                    SET status = 'acknowledged',
                        acknowledged_at = NOW(),
                        acknowledged_by = :user_email
                    WHERE id = :alert_id
                    RETURNING id
                """),
                {
                    "alert_id": alert_id,
                    "user_email": current_user.email
                }
            )
            
            if not result.first():
                raise HTTPException(status_code=404, detail="Alert not found")
            
            await db.commit()
            
            return {"message": "Alert acknowledged", "alert_id": alert_id}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def performance_metrics(
    period: str = Query("1h", description="Time period (1h, 24h, 7d)"),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics."""
    
    # Map period to hours
    period_hours = {
        "1h": 1,
        "24h": 24,
        "7d": 168
    }.get(period, 1)
    
    since = datetime.utcnow() - timedelta(hours=period_hours)
    
    try:
        async with get_db() as db:
            # Response time percentiles
            response_times = await db.execute(
                text("""
                    SELECT 
                        percentile_cont(0.5) WITHIN GROUP (ORDER BY response_time_ms) as p50,
                        percentile_cont(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95,
                        percentile_cont(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99,
                        AVG(response_time_ms) as avg,
                        COUNT(*) as count
                    FROM api_requests
                    WHERE created_at > :since
                """),
                {"since": since}
            )
            
            response_time_data = response_times.first()
            
            # Error rate
            error_rate = await db.execute(
                text("""
                    SELECT 
                        COUNT(CASE WHEN status_code >= 500 THEN 1 END)::float / COUNT(*) as error_rate
                    FROM api_requests
                    WHERE created_at > :since
                """),
                {"since": since}
            )
            
            error_rate_value = error_rate.scalar() or 0
            
            # Top slow endpoints
            slow_endpoints = await db.execute(
                text("""
                    SELECT 
                        endpoint,
                        AVG(response_time_ms) as avg_time,
                        COUNT(*) as count
                    FROM api_requests
                    WHERE created_at > :since
                    GROUP BY endpoint
                    ORDER BY avg_time DESC
                    LIMIT 10
                """),
                {"since": since}
            )
            
            return {
                "period": period,
                "response_times": {
                    "p50": response_time_data.p50,
                    "p95": response_time_data.p95,
                    "p99": response_time_data.p99,
                    "average": response_time_data.avg,
                    "total_requests": response_time_data.count
                },
                "error_rate": error_rate_value,
                "slow_endpoints": [
                    {
                        "endpoint": row.endpoint,
                        "avg_response_time_ms": row.avg_time,
                        "request_count": row.count
                    }
                    for row in slow_endpoints
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None, description="Log level filter"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin)
):
    """Get application logs."""
    try:
        async with get_db() as db:
            query = """
                SELECT 
                    timestamp, level, logger, message, context
                FROM application_logs
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """
            params = {"limit": limit}
            
            if level:
                query += " AND level = :level"
                params["level"] = level
                
            if search:
                query += " AND message ILIKE :search"
                params["search"] = f"%{search}%"
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            
            result = await db.execute(text(query), params)
            
            logs = []
            for row in result:
                logs.append({
                    "timestamp": row.timestamp.isoformat(),
                    "level": row.level,
                    "logger": row.logger,
                    "message": row.message,
                    "context": row.context
                })
            
            return {
                "logs": logs,
                "count": len(logs)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-alert")
async def test_alert(
    severity: str = Query("info", description="Alert severity"),
    current_user: User = Depends(require_admin)
):
    """Send a test alert."""
    from monitoring.alerting import Alert, AlertSeverity, AlertStatus
    
    alert = Alert(
        id=f"test-{datetime.utcnow().timestamp()}",
        name="test_alert",
        severity=AlertSeverity(severity),
        status=AlertStatus.FIRING,
        message=f"Test alert triggered by {current_user.email}",
        details={
            "triggered_by": current_user.email,
            "timestamp": datetime.utcnow().isoformat()
        },
        fired_at=datetime.utcnow(),
        tags=["test"]
    )
    
    await alerting_system._send_notifications(alert)
    
    return {
        "message": "Test alert sent",
        "alert": {
            "id": alert.id,
            "severity": alert.severity,
            "message": alert.message
        }
    }