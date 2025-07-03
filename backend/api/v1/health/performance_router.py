"""
Performance Monitoring Router

Provides endpoints for monitoring system performance, query statistics, and optimization metrics.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime

from backend.core.query_optimizer import get_performance_metrics, query_optimizer
from backend.core.async_manager import task_manager
from backend.api.deps import get_current_user
from backend.core.responses import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/metrics")
async def get_performance_metrics_endpoint(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive performance metrics
    
    Returns:
        Performance metrics including query statistics, cache performance, and system health
    """
    try:
        # Get query performance metrics
        query_metrics = get_performance_metrics()
        
        # Get task manager metrics
        task_metrics = {
            "total_tasks": len(task_manager.tasks),
            "running_tasks": len([t for t in task_manager.tasks.values() if t.status.value == "running"]),
            "completed_tasks": len([t for t in task_manager.tasks.values() if t.status.value == "completed"]),
            "failed_tasks": len([t for t in task_manager.tasks.values() if t.status.value == "failed"]),
            "cache_size": len(task_manager.task_results)
        }
        
        # Get cache performance
        cache_metrics = {
            "cache_size": len(query_optimizer.query_cache),
            "cache_hit_rate": query_metrics.get("cache_hit_rate", 0),
            "total_cached_queries": len(query_optimizer.query_cache),
            "cache_ttl_entries": len(query_optimizer.cache_ttl)
        }
        
        # System health indicators
        health_indicators = {
            "database_queries_per_second": query_metrics.get("total_queries", 0) / max(query_metrics.get("average_query_time", 1), 1),
            "average_response_time": query_metrics.get("average_query_time", 0),
            "slow_query_count": len([q for q in query_metrics.get("slowest_queries", []) if q[1] > 1.0]),
            "system_status": "healthy" if query_metrics.get("average_query_time", 0) < 0.5 else "degraded"
        }
        
        return success_response(
            data={
                "query_performance": query_metrics,
                "task_metrics": task_metrics,
                "cache_performance": cache_metrics,
                "health_indicators": health_indicators,
                "timestamp": datetime.utcnow().isoformat()
            },
            message="Performance metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {str(e)}")
        return error_response(
            message="Failed to retrieve performance metrics",
            error=str(e)
        )

@router.get("/slow-queries")
async def get_slow_queries(
    current_user = Depends(get_current_user),
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get list of slowest queries
    
    Args:
        limit: Maximum number of slow queries to return
        
    Returns:
        List of slowest queries with performance details
    """
    try:
        metrics = get_performance_metrics()
        slow_queries = metrics.get("slowest_queries", [])[:limit]
        
        detailed_queries = []
        for query_name, avg_time in slow_queries:
            stats = metrics.get("detailed_stats", {}).get(query_name, {})
            detailed_queries.append({
                "query_name": query_name,
                "average_time": avg_time,
                "total_executions": stats.get("count", 0),
                "min_time": stats.get("min_time", 0),
                "max_time": stats.get("max_time", 0),
                "last_execution": stats.get("last_time", 0)
            })
        
        return success_response(
            data={
                "slow_queries": detailed_queries,
                "total_slow_queries": len(slow_queries)
            },
            message="Slow queries retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving slow queries: {str(e)}")
        return error_response(
            message="Failed to retrieve slow queries",
            error=str(e)
        )

@router.post("/cache/clear")
async def clear_cache(
    current_user = Depends(get_current_user),
    pattern: str = None
) -> Dict[str, Any]:
    """
    Clear query cache
    
    Args:
        pattern: Optional pattern to match cache keys for selective clearing
        
    Returns:
        Cache clearing results
    """
    try:
        cache_size_before = len(query_optimizer.query_cache)
        query_optimizer.clear_cache(pattern)
        cache_size_after = len(query_optimizer.query_cache)
        
        return success_response(
            data={
                "cache_cleared": cache_size_before - cache_size_after,
                "remaining_cache_size": cache_size_after,
                "pattern_used": pattern or "all"
            },
            message="Cache cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return error_response(
            message="Failed to clear cache",
            error=str(e)
        )

@router.get("/tasks")
async def get_task_status(
    current_user = Depends(get_current_user),
    status: str = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get background task status
    
    Args:
        status: Filter by task status (pending, running, completed, failed, cancelled)
        limit: Maximum number of tasks to return
        
    Returns:
        List of tasks with their status and details
    """
    try:
        from backend.core.async_manager import TaskStatus
        
        # Convert string status to enum if provided
        task_status = None
        if status:
            try:
                task_status = TaskStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        tasks = task_manager.list_tasks(status=task_status, limit=limit)
        
        # Convert tasks to serializable format
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.task_id,
                "function_name": task.function_name,
                "status": task.status.value,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "progress": task.progress,
                "error": task.error
            })
        
        return success_response(
            data={
                "tasks": task_list,
                "total_tasks": len(task_list),
                "status_filter": status
            },
            message="Task status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving task status: {str(e)}")
        return error_response(
            message="Failed to retrieve task status",
            error=str(e)
        )

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Cancel a background task
    
    Args:
        task_id: ID of the task to cancel
        
    Returns:
        Cancellation result
    """
    try:
        success = task_manager.cancel_task(task_id)
        
        if success:
            return success_response(
                data={"task_id": task_id, "cancelled": True},
                message="Task cancelled successfully"
            )
        else:
            return error_response(
                message="Failed to cancel task - task may not exist or already be completed",
                error="Task cancellation failed"
            )
        
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return error_response(
            message="Failed to cancel task",
            error=str(e)
        )

@router.get("/optimization/recommendations")
async def get_optimization_recommendations(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance optimization recommendations
    
    Returns:
        List of optimization recommendations based on current metrics
    """
    try:
        metrics = get_performance_metrics()
        recommendations = []
        
        # Analyze query performance
        avg_query_time = metrics.get("average_query_time", 0)
        if avg_query_time > 0.5:
            recommendations.append({
                "type": "query_optimization",
                "priority": "high",
                "description": f"Average query time ({avg_query_time:.3f}s) is above optimal threshold (0.5s)",
                "suggestion": "Consider adding database indexes or optimizing query patterns"
            })
        
        # Analyze cache performance
        cache_hit_rate = metrics.get("cache_hit_rate", 0)
        if cache_hit_rate < 0.3:
            recommendations.append({
                "type": "caching",
                "priority": "medium",
                "description": f"Cache hit rate ({cache_hit_rate:.1%}) is below optimal threshold (30%)",
                "suggestion": "Consider increasing cache TTL or adding more cacheable queries"
            })
        
        # Analyze slow queries
        slow_queries = metrics.get("slowest_queries", [])
        if slow_queries:
            slowest_query = slow_queries[0]
            if slowest_query[1] > 2.0:
                recommendations.append({
                    "type": "critical_query",
                    "priority": "critical",
                    "description": f"Query '{slowest_query[0]}' is very slow ({slowest_query[1]:.3f}s)",
                    "suggestion": "Immediate optimization required - consider query restructuring or indexing"
                })
        
        # Analyze task performance
        task_metrics = {
            "total_tasks": len(task_manager.tasks),
            "failed_tasks": len([t for t in task_manager.tasks.values() if t.status.value == "failed"])
        }
        
        if task_metrics["failed_tasks"] > 0:
            failure_rate = task_metrics["failed_tasks"] / max(task_metrics["total_tasks"], 1)
            if failure_rate > 0.1:
                recommendations.append({
                    "type": "task_failures",
                    "priority": "high",
                    "description": f"Task failure rate ({failure_rate:.1%}) is above acceptable threshold (10%)",
                    "suggestion": "Investigate and fix recurring task failures"
                })
        
        return success_response(
            data={
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "critical_count": len([r for r in recommendations if r["priority"] == "critical"]),
                "high_count": len([r for r in recommendations if r["priority"] == "high"]),
                "medium_count": len([r for r in recommendations if r["priority"] == "medium"])
            },
            message="Optimization recommendations generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error generating optimization recommendations: {str(e)}")
        return error_response(
            message="Failed to generate optimization recommendations",
            error=str(e)
        ) 