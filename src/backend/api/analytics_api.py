"""
Analytics API endpoints for TradeSense.
Provides analytics data and insights.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from core.auth import get_current_user, require_admin
from models.user import User
from src.backend.analytics import (
    user_analytics,
    product_analytics,
    EventType,
    track_feature_usage
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class TrackEventRequest(BaseModel):
    event_type: str
    properties: Optional[Dict[str, Any]] = None
    page_url: Optional[str] = None
    referrer_url: Optional[str] = None


class DateRangeQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.post("/track")
async def track_event(
    event: TrackEventRequest,
    current_user: User = Depends(get_current_user)
):
    """Track a user analytics event."""
    try:
        # Validate event type
        try:
            event_type = EventType(event.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event.event_type}"
            )
        
        # Track the event
        event_id = await user_analytics.track_event(
            user_id=str(current_user.id),
            event_type=event_type,
            properties=event.properties,
            page_url=event.page_url,
            referrer_url=event.referrer_url
        )
        
        return {"event_id": event_id, "status": "tracked"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/journey")
async def get_user_journey(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's journey/activity timeline."""
    try:
        journey = await user_analytics.get_user_journey(
            user_id=str(current_user.id),
            start_date=start_date,
            end_date=end_date
        )
        
        # Track analytics view
        await track_feature_usage(
            str(current_user.id),
            "user_journey_viewed"
        )
        
        return {
            "user_id": str(current_user.id),
            "journey": journey,
            "event_count": len(journey)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/stats")
async def get_user_stats(
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics."""
    # Users can view their own stats, admins can view any user's stats
    if user_id and user_id != str(current_user.id):
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
    
    target_user_id = user_id or str(current_user.id)
    
    try:
        stats = await user_analytics.get_user_stats(target_user_id)
        
        return {
            "user_id": target_user_id,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/metrics")
async def get_product_metrics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_admin)
):
    """Get comprehensive product metrics (admin only)."""
    try:
        metrics = await product_analytics.get_product_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cohort/analysis")
async def get_cohort_analysis(
    cohort_type: str = Query("signup_month", description="Type of cohort"),
    metric: str = Query("retention", description="Metric to analyze"),
    current_user: User = Depends(require_admin)
):
    """Get cohort analysis (admin only)."""
    try:
        analysis = await user_analytics.get_cohort_analysis(
            cohort_type=cohort_type,
            metric=metric
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/funnel/analysis")
async def get_funnel_analysis(
    funnel_steps: List[str] = Body(..., description="List of event types in order"),
    start_date: Optional[datetime] = Body(None),
    end_date: Optional[datetime] = Body(None),
    current_user: User = Depends(require_admin)
):
    """Analyze conversion funnel (admin only)."""
    try:
        # Validate event types
        for step in funnel_steps:
            try:
                EventType(step)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {step}"
                )
        
        analysis = await user_analytics.get_funnel_analysis(
            funnel_steps=funnel_steps,
            start_date=start_date,
            end_date=end_date
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/segments")
async def get_user_segments(
    current_user: User = Depends(require_admin)
):
    """Get user segments based on behavior (admin only)."""
    try:
        segments = await user_analytics.get_user_segments()
        
        # Get counts for each segment
        segment_stats = {}
        for segment_name, user_ids in segments.items():
            segment_stats[segment_name] = {
                "count": len(user_ids),
                "percentage": round((len(user_ids) / max(sum(len(s) for s in segments.values()), 1)) * 100, 2)
            }
        
        return {
            "segments": segment_stats,
            "total_segmented_users": sum(len(s) for s in segments.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/flow")
async def get_user_flow(
    start_page: str = Query(..., description="Starting page URL"),
    end_page: Optional[str] = Query(None, description="Optional ending page URL"),
    max_steps: int = Query(5, ge=1, le=10),
    current_user: User = Depends(require_admin)
):
    """Analyze user flow through the application (admin only)."""
    try:
        flow_analysis = await product_analytics.get_user_flow_analysis(
            start_page=start_page,
            end_page=end_page,
            max_steps=max_steps
        )
        
        return flow_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversions")
async def get_conversion_metrics(
    conversions: List[List[str]] = Body(
        ...,
        description="List of [start_event, end_event] pairs",
        example=[
            ["sign_up", "subscription_started"],
            ["trade_created", "subscription_upgraded"]
        ]
    ),
    current_user: User = Depends(require_admin)
):
    """Calculate conversion metrics between events (admin only)."""
    try:
        # Validate event types
        for start_event, end_event in conversions:
            try:
                EventType(start_event)
                EventType(end_event)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {str(e)}"
                )
        
        metrics = await product_analytics.get_conversion_metrics(
            conversion_events=[(s, e) for s, e in conversions]
        )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior/insights")
async def get_behavior_insights(
    current_user: User = Depends(require_admin)
):
    """Get user behavior insights (admin only)."""
    try:
        insights = await product_analytics.get_user_behavior_insights()
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime/activity")
async def get_realtime_activity(
    current_user: User = Depends(require_admin)
):
    """Get real-time activity data (admin only)."""
    try:
        from core.cache import redis_client
        
        # Get recent events
        recent_events_raw = await redis_client.lrange(
            "analytics:events:recent",
            0,
            49
        )
        
        recent_events = []
        for event_json in recent_events_raw:
            try:
                event = json.loads(event_json)
                recent_events.append(event)
            except:
                pass
        
        # Get active users
        active_users = await redis_client.zcount(
            "analytics:active_users",
            datetime.utcnow().timestamp() - 300,  # Last 5 minutes
            datetime.utcnow().timestamp()
        )
        
        # Get today's event counters
        today_key = f"analytics:counters:{datetime.utcnow().strftime('%Y%m%d')}"
        counters = await redis_client.hgetall(today_key)
        
        return {
            "recent_events": recent_events[:20],  # Limit to 20 most recent
            "active_users_5min": active_users,
            "today_events": {
                k.decode(): int(v.decode())
                for k, v in counters.items()
            } if counters else {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feature/adoption")
async def track_feature_adoption(
    feature_name: str = Body(...),
    adopted: bool = Body(True),
    properties: Optional[Dict[str, Any]] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """Track feature adoption."""
    try:
        await user_analytics.track_feature_adoption(
            feature_name=feature_name,
            user_id=str(current_user.id),
            adopted=adopted
        )
        
        # Track additional properties if provided
        if properties:
            await track_feature_usage(
                str(current_user.id),
                feature_name,
                properties
            )
        
        return {
            "feature": feature_name,
            "adopted": adopted,
            "status": "tracked"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/events")
async def export_events(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    event_types: Optional[List[str]] = Query(None),
    format: str = Query("csv", enum=["csv", "json"]),
    current_user: User = Depends(require_admin)
):
    """Export analytics events (admin only)."""
    try:
        from io import StringIO
        import csv
        from fastapi.responses import StreamingResponse
        
        # Query events
        from core.db.session import get_db
        from sqlalchemy import text
        
        async with get_db() as db:
            query = """
                SELECT 
                    event_id, user_id, session_id, event_type,
                    timestamp, properties, page_url, referrer_url
                FROM user_events
                WHERE timestamp BETWEEN :start_date AND :end_date
            """
            
            params = {
                "start_date": start_date,
                "end_date": end_date
            }
            
            if event_types:
                query += " AND event_type = ANY(:event_types)"
                params["event_types"] = event_types
            
            query += " ORDER BY timestamp DESC"
            
            result = await db.execute(text(query), params)
            
            if format == "csv":
                # Create CSV
                output = StringIO()
                writer = csv.writer(output)
                
                # Write headers
                writer.writerow([
                    "event_id", "user_id", "session_id", "event_type",
                    "timestamp", "properties", "page_url", "referrer_url"
                ])
                
                # Write data
                for row in result:
                    writer.writerow([
                        row.event_id,
                        row.user_id,
                        row.session_id,
                        row.event_type,
                        row.timestamp.isoformat(),
                        row.properties,
                        row.page_url,
                        row.referrer_url
                    ])
                
                output.seek(0)
                
                return StreamingResponse(
                    iter([output.getvalue()]),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename=analytics_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
                    }
                )
            
            else:  # JSON format
                events = []
                for row in result:
                    events.append({
                        "event_id": row.event_id,
                        "user_id": row.user_id,
                        "session_id": row.session_id,
                        "event_type": row.event_type,
                        "timestamp": row.timestamp.isoformat(),
                        "properties": json.loads(row.properties) if row.properties else {},
                        "page_url": row.page_url,
                        "referrer_url": row.referrer_url
                    })
                
                return {
                    "events": events,
                    "count": len(events),
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    }
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))