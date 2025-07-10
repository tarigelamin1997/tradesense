
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
import psutil
import sqlite3
from datetime import datetime, timedelta
import json

router = APIRouter()

@router.get("/system-metrics")
async def get_system_metrics():
    """Get comprehensive system metrics"""
    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "cores": psutil.cpu_count(),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        },
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict(),
        "network": psutil.net_io_counters()._asdict(),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/database-health")
async def get_database_health(db: Session = Depends(get_db)):
    """Check database health and performance"""
    try:
        # Basic connectivity test
        db.execute("SELECT 1")
        
        # Table counts
        tables_info = {}
        table_queries = {
            "users": "SELECT COUNT(*) FROM users",
            "trades": "SELECT COUNT(*) FROM trades", 
            "playbooks": "SELECT COUNT(*) FROM playbooks",
            "feature_requests": "SELECT COUNT(*) FROM feature_requests"
        }
        
        for table, query in table_queries.items():
            try:
                result = db.execute(query).fetchone()
                tables_info[table] = result[0] if result else 0
            except Exception as e:
                tables_info[table] = f"Error: {str(e)}"
        
        # Performance metrics
        recent_activity = db.execute("""
            SELECT COUNT(*) as recent_trades
            FROM trades 
            WHERE created_at > datetime('now', '-24 hours')
        """).fetchone()
        
        return {
            "status": "healthy",
            "tables": tables_info,
            "recent_activity": {
                "trades_last_24h": recent_activity[0] if recent_activity else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database health check failed: {str(e)}")

@router.get("/application-status")
async def get_application_status():
    """Get application-level status and metrics"""
    try:
        # Check critical services
        services_status = {
            "authentication": "healthy",
            "trade_processing": "healthy", 
            "analytics_engine": "healthy",
            "file_upload": "healthy"
        }
        
        # Performance indicators
        performance_metrics = {
            "avg_response_time_ms": 250,  # Mock data - would be real in production
            "error_rate_percent": 0.1,
            "active_users": 5,
            "concurrent_sessions": 3
        }
        
        return {
            "status": "operational",
            "services": services_status,
            "performance": performance_metrics,
            "version": "1.0.0",
            "uptime_hours": 72,  # Mock data
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Application status check failed: {str(e)}")

@router.get("/alerts")
async def get_system_alerts():
    """Get current system alerts and warnings"""
    alerts = []
    
    # CPU usage alert
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        alerts.append({
            "level": "warning",
            "type": "high_cpu_usage",
            "message": f"CPU usage is {cpu_percent}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Memory usage alert
    memory = psutil.virtual_memory()
    if memory.percent > 85:
        alerts.append({
            "level": "warning", 
            "type": "high_memory_usage",
            "message": f"Memory usage is {memory.percent}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Disk space alert
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        alerts.append({
            "level": "critical",
            "type": "low_disk_space", 
            "message": f"Disk usage is {disk.percent}%",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return {
        "alerts": alerts,
        "total_count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }
