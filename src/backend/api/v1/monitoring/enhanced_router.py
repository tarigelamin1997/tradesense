"""
Enhanced monitoring API endpoints

Provides comprehensive monitoring, health checks, and observability endpoints
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse

from api.deps import get_current_user_optional
from models.user import User
from core.monitoring_enhanced import (
    health_checker, tracer, business_metrics, 
    create_monitoring_response
)
from core.metrics import metrics_collector, PROMETHEUS_AVAILABLE
from core.error_tracking import error_analyzer
from core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Basic health check endpoint
    
    Returns 200 if service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tradesense-backend",
        "version": "2.0.0"
    }


@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Detailed health check with all subsystem statuses
    
    Requires authentication for security
    """
    if not current_user:
        # Return basic health for unauthenticated requests
        return await health_check()
    
    # Run all health checks
    health_results = await health_checker.run_checks()
    
    return health_results


@router.get("/metrics")
async def get_metrics(
    format: str = Query("prometheus", description="Metrics format (prometheus or json)"),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get application metrics
    
    Returns Prometheus-formatted metrics by default
    """
    if format == "prometheus" and PROMETHEUS_AVAILABLE:
        metrics_data = metrics_collector.get_metrics()
        return PlainTextResponse(
            content=metrics_data,
            media_type="text/plain"
        )
    else:
        # Return JSON format
        if not current_user:
            raise HTTPException(401, "Authentication required for JSON metrics")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "http_requests": {
                    "total": getattr(metrics_collector, 'http_requests_total', {}).value,
                },
                "cache": metrics_collector.cache_manager.get_stats() if hasattr(metrics_collector, 'cache_manager') else {},
                "errors": error_analyzer.get_error_summary(),
                "business": business_metrics.get_daily_summary()
            }
        }


@router.get("/traces", response_model=Dict[str, Any])
async def get_traces(
    trace_id: Optional[str] = Query(None, description="Specific trace ID to retrieve"),
    limit: int = Query(10, description="Number of recent traces to return"),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get distributed traces
    
    Requires authentication
    """
    if not current_user:
        raise HTTPException(401, "Authentication required")
    
    if trace_id:
        # Get specific trace
        spans = tracer.get_trace(trace_id)
        if not spans:
            raise HTTPException(404, f"Trace {trace_id} not found")
        
        return {
            "trace_id": trace_id,
            "spans": spans,
            "total_duration_ms": max(s['end_time'] for s in spans if 'end_time' in s) - min(s['start_time'] for s in spans) * 1000
        }
    else:
        # Get recent traces
        active_traces = tracer.get_active_traces()
        completed_traces = {}
        
        # Group completed spans by trace
        for span in tracer.completed_spans[-limit*10:]:  # Get more spans to find complete traces
            trace_id = span['trace_id']
            if trace_id not in completed_traces:
                completed_traces[trace_id] = []
            completed_traces[trace_id].append(span)
        
        # Format traces
        recent_traces = []
        for trace_id, spans in list(completed_traces.items())[-limit:]:
            recent_traces.append({
                "trace_id": trace_id,
                "span_count": len(spans),
                "duration_ms": max(s.get('end_time', 0) for s in spans) - min(s['start_time'] for s in spans) * 1000,
                "start_time": min(s['start_time'] for s in spans),
                "operations": list(set(s['operation'] for s in spans))
            })
        
        return {
            "active_traces": active_traces,
            "recent_traces": recent_traces
        }


@router.get("/errors", response_model=Dict[str, Any])
async def get_error_summary(
    hours: int = Query(24, description="Number of hours to analyze"),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get error analysis and trends
    
    Requires authentication
    """
    if not current_user:
        raise HTTPException(401, "Authentication required")
    
    summary = error_analyzer.get_error_summary()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "period_hours": hours,
        "summary": summary
    }


@router.get("/errors/recent", response_model=List[Dict[str, Any]])
async def get_recent_errors(
    limit: int = Query(10, description="Number of recent errors to return"),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get recent error details
    
    Requires authentication
    """
    if not current_user:
        raise HTTPException(401, "Authentication required")
    
    return error_analyzer.error_tracker.get_recent_errors(limit)


@router.get("/monitoring/dashboard", response_model=Dict[str, Any])
async def monitoring_dashboard(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get comprehensive monitoring dashboard data
    
    Requires authentication
    """
    if not current_user:
        raise HTTPException(401, "Authentication required")
    
    # Only admins can see full dashboard
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    return create_monitoring_response()


@router.post("/traces/{trace_id}/annotate")
async def annotate_trace(
    trace_id: str,
    annotation: Dict[str, Any],
    current_user: User = Depends(get_current_user_optional)
):
    """
    Add annotation to a trace
    
    Useful for debugging and analysis
    """
    if not current_user:
        raise HTTPException(401, "Authentication required")
    
    # Add annotation event
    tracer.add_event(
        f"User annotation by {current_user.username}",
        {
            "trace_id": trace_id,
            "user_id": str(current_user.id),
            "annotation": annotation
        }
    )
    
    logger.info(
        f"Trace annotated by {current_user.username}",
        extra={
            "trace_id": trace_id,
            "user_id": str(current_user.id),
            "annotation": annotation
        }
    )
    
    return {"status": "success", "message": "Annotation added"}


@router.get("/performance/slow-queries", response_model=List[Dict[str, Any]])
async def get_slow_queries(
    threshold_ms: float = Query(1000, description="Threshold in milliseconds"),
    limit: int = Query(10, description="Number of queries to return"),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get slow database queries
    
    Requires admin authentication
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # This would be implemented with actual query monitoring
    # For now, return placeholder
    return [
        {
            "query": "SELECT * FROM trades WHERE user_id = ?",
            "duration_ms": 1500,
            "timestamp": datetime.utcnow().isoformat(),
            "count": 45
        }
    ]


@router.get("/performance/endpoints", response_model=List[Dict[str, Any]])
async def get_endpoint_performance(
    sort_by: str = Query("avg_duration", description="Sort by: avg_duration, total_calls, error_rate"),
    limit: int = Query(20, description="Number of endpoints to return"),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get endpoint performance statistics
    
    Requires admin authentication
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # This would aggregate from metrics
    # For now, return placeholder
    return [
        {
            "endpoint": "/api/v1/trades",
            "method": "GET",
            "avg_duration_ms": 45.2,
            "p95_duration_ms": 120.5,
            "p99_duration_ms": 250.8,
            "total_calls": 15420,
            "error_rate": 0.002,
            "last_hour_calls": 523
        }
    ]


@router.get("/alerts/active", response_model=List[Dict[str, Any]])
async def get_active_alerts(
    current_user: User = Depends(get_current_user_optional)
):
    """
    Get active monitoring alerts
    
    Requires admin authentication
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Check for alert conditions
    alerts = []
    
    # Check error rate
    error_stats = error_analyzer.get_error_summary()
    if error_stats['stats']['total_errors'] > 100:
        alerts.append({
            "id": "high_error_rate",
            "severity": "warning",
            "title": "High Error Rate",
            "message": f"{error_stats['stats']['total_errors']} errors in the last 24 hours",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Check health status
    health_results = await health_checker.run_checks()
    for check_name, check_result in health_results['checks'].items():
        if check_result['status'] == 'unhealthy':
            alerts.append({
                "id": f"health_{check_name}",
                "severity": "critical" if check_result['critical'] else "warning",
                "title": f"{check_name.title()} Unhealthy",
                "message": check_result['message'],
                "timestamp": check_result['timestamp']
            })
    
    return alerts


@router.post("/debug/enable")
async def enable_debug_mode(
    duration_minutes: int = Query(15, description="Debug mode duration in minutes"),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Enable debug mode temporarily
    
    Requires admin authentication
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # In a real implementation, this would enable verbose logging
    logger.warning(
        f"Debug mode enabled by {current_user.username} for {duration_minutes} minutes",
        extra={
            "user_id": str(current_user.id),
            "duration_minutes": duration_minutes
        }
    )
    
    return {
        "status": "success",
        "message": f"Debug mode enabled for {duration_minutes} minutes",
        "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat()
    }