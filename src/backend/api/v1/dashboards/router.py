"""
Dashboard API Router

Handles all dashboard-related endpoints including:
- Dashboard CRUD operations
- Widget management
- Data fetching
- Template management
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json

from core.auth import get_current_user
from core.db.session import get_db
from core.redis import get_redis
from models.user import User
from reporting.dashboard_service import (
    DashboardService,
    Dashboard,
    DashboardFilter,
    DashboardTemplate,
    WidgetConfig,
    WidgetDataRequest,
    WidgetType,
    DataSource
)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


# Dashboard Management Endpoints
@router.post("/", response_model=Dashboard)
async def create_dashboard(
    name: str,
    template: DashboardTemplate = DashboardTemplate.CUSTOM,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dashboard"""
    service = DashboardService(db)
    dashboard = service.create_dashboard(
        user_id=current_user.id,
        name=name,
        template=template,
        description=description
    )
    return dashboard


@router.get("/", response_model=Dict[str, Any])
async def list_dashboards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    template: Optional[DashboardTemplate] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    is_public: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's dashboards with filtering"""
    service = DashboardService(db)
    
    filter_criteria = DashboardFilter(
        user_id=current_user.id,
        template=template,
        tags=tags,
        is_public=is_public,
        search_term=search
    )
    
    dashboards, total = service.list_dashboards(filter_criteria, page, page_size)
    
    return {
        "dashboards": [d.model_dump() for d in dashboards],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_dashboard_templates():
    """Get available dashboard templates"""
    templates = []
    for template in DashboardTemplate:
        templates.append({
            "id": template.value,
            "name": template.value.replace("_", " ").title(),
            "description": f"Pre-configured dashboard for {template.value.replace('_', ' ')}"
        })
    return templates


@router.get("/{dashboard_id}", response_model=Dashboard)
async def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific dashboard"""
    service = DashboardService(db)
    dashboard = service._get_dashboard(dashboard_id, current_user.id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    return dashboard


@router.put("/{dashboard_id}", response_model=Dashboard)
async def update_dashboard(
    dashboard_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update dashboard configuration"""
    service = DashboardService(db)
    
    try:
        dashboard = service.update_dashboard(dashboard_id, current_user.id, updates)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dashboard"""
    service = DashboardService(db)
    
    if not service.delete_dashboard(dashboard_id, current_user.id):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    return {"message": "Dashboard deleted successfully"}


@router.post("/{dashboard_id}/clone", response_model=Dashboard)
async def clone_dashboard(
    dashboard_id: str,
    new_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clone an existing dashboard"""
    service = DashboardService(db)
    
    try:
        dashboard = service.clone_dashboard(dashboard_id, current_user.id, new_name)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{dashboard_id}/share", response_model=Dashboard)
async def share_dashboard(
    dashboard_id: str,
    user_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share dashboard with other users"""
    service = DashboardService(db)
    
    try:
        dashboard = service.share_dashboard(dashboard_id, current_user.id, user_ids)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Widget Management Endpoints
@router.post("/{dashboard_id}/widgets", response_model=Dashboard)
async def add_widget(
    dashboard_id: str,
    widget_config: WidgetConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a widget to dashboard"""
    service = DashboardService(db)
    
    try:
        dashboard = service.add_widget(dashboard_id, current_user.id, widget_config)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=Dashboard)
async def update_widget(
    dashboard_id: str,
    widget_id: str,
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update widget configuration"""
    service = DashboardService(db)
    
    try:
        dashboard = service.update_widget(
            dashboard_id, widget_id, current_user.id, updates
        )
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{dashboard_id}/widgets/{widget_id}", response_model=Dashboard)
async def remove_widget(
    dashboard_id: str,
    widget_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove widget from dashboard"""
    service = DashboardService(db)
    
    try:
        dashboard = service.remove_widget(dashboard_id, widget_id, current_user.id)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{dashboard_id}/widgets/reorder", response_model=Dashboard)
async def reorder_widgets(
    dashboard_id: str,
    positions: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder widgets in dashboard"""
    service = DashboardService(db)
    
    try:
        dashboard = service.reorder_widgets(
            dashboard_id, current_user.id, positions
        )
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Widget Types and Data Sources
@router.get("/widgets/types", response_model=List[Dict[str, Any]])
async def get_widget_types():
    """Get available widget types"""
    widget_types = []
    for widget_type in WidgetType:
        widget_types.append({
            "id": widget_type.value,
            "name": widget_type.value.replace("_", " ").title(),
            "category": _get_widget_category(widget_type),
            "description": _get_widget_description(widget_type)
        })
    return widget_types


@router.get("/widgets/data-sources", response_model=List[Dict[str, Any]])
async def get_data_sources():
    """Get available data sources"""
    sources = []
    for source in DataSource:
        sources.append({
            "id": source.value,
            "name": source.value.replace("_", " ").title(),
            "description": _get_data_source_description(source)
        })
    return sources


# Data Fetching Endpoints
@router.post("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_data(
    dashboard_id: str,
    widget_id: str,
    time_range: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data for a specific widget"""
    service = DashboardService(db)
    
    request = WidgetDataRequest(
        widget_id=widget_id,
        dashboard_id=dashboard_id,
        user_id=current_user.id,
        time_range=time_range,
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    try:
        data = await service.get_widget_data(request)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: str,
    time_range: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get data for all widgets in dashboard"""
    service = DashboardService(db)
    
    try:
        data = await service.get_dashboard_data(
            dashboard_id, current_user.id, time_range
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{dashboard_id}/data/stream")
async def stream_dashboard_data(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream real-time dashboard data updates"""
    service = DashboardService(db)
    
    async def event_generator():
        while True:
            try:
                # Get dashboard data
                data = await service.get_dashboard_data(
                    dashboard_id, current_user.id
                )
                
                # Send as Server-Sent Event
                yield f"data: {json.dumps(data)}\n\n"
                
                # Wait before next update
                await asyncio.sleep(5)  # 5 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/{dashboard_id}/export")
async def export_dashboard_data(
    dashboard_id: str,
    format: str = Query("json", regex="^(json|csv|excel)$"),
    include_config: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Export dashboard data"""
    service = DashboardService(db)
    
    try:
        # Get dashboard data
        data = await service.get_dashboard_data(dashboard_id, current_user.id)
        
        if format == "json":
            return data
        else:
            # For CSV/Excel, we'd need additional processing
            raise HTTPException(
                status_code=501, 
                detail=f"Export format '{format}' not implemented yet"
            )
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Helper functions
def _get_widget_category(widget_type: WidgetType) -> str:
    """Get category for widget type"""
    chart_types = [
        WidgetType.LINE_CHART, WidgetType.BAR_CHART, 
        WidgetType.PIE_CHART, WidgetType.CANDLESTICK, 
        WidgetType.HEATMAP
    ]
    metric_types = [WidgetType.METRIC_CARD, WidgetType.GAUGE]
    
    if widget_type in chart_types:
        return "Charts"
    elif widget_type in metric_types:
        return "Metrics"
    elif widget_type == WidgetType.TABLE:
        return "Tables"
    else:
        return "Special"


def _get_widget_description(widget_type: WidgetType) -> str:
    """Get description for widget type"""
    descriptions = {
        WidgetType.LINE_CHART: "Display trends over time",
        WidgetType.BAR_CHART: "Compare values across categories",
        WidgetType.PIE_CHART: "Show composition or proportions",
        WidgetType.CANDLESTICK: "Display price movements",
        WidgetType.HEATMAP: "Visualize data density or correlations",
        WidgetType.METRIC_CARD: "Show single key metrics with trends",
        WidgetType.GAUGE: "Display progress or performance metrics",
        WidgetType.TABLE: "Display tabular data with sorting and filtering",
        WidgetType.TEXT_MARKDOWN: "Add custom text or documentation",
        WidgetType.LIVE_MARKET: "Show real-time market data",
        WidgetType.PNL_CALENDAR: "Visualize daily P&L in calendar format",
        WidgetType.WIN_RATE_GAUGE: "Display win rate performance",
        WidgetType.DRAWDOWN_CHART: "Track maximum drawdown over time",
        WidgetType.TRADE_DISTRIBUTION_MAP: "Visualize trade distribution by symbol"
    }
    return descriptions.get(widget_type, "Custom widget type")


def _get_data_source_description(source: DataSource) -> str:
    """Get description for data source"""
    descriptions = {
        DataSource.TRADES: "Historical trade data and performance metrics",
        DataSource.PORTFOLIO: "Current portfolio positions and values",
        DataSource.MARKET_DATA: "Real-time and historical market prices",
        DataSource.CUSTOM_CALCULATION: "Custom calculations and derived metrics",
        DataSource.EXTERNAL_API: "Data from external APIs and services"
    }
    return descriptions.get(source, "Custom data source")