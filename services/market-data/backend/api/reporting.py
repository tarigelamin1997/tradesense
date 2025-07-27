from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from pydantic import BaseModel, Field
import logging
from enum import Enum
import uuid
import io

from core.db.session import get_db
from api.deps import get_current_user
from core.exceptions import (
    TradeSenseException, NotFoundError, ValidationError,
    DatabaseError, ExternalServiceError
)
from core.responses import create_success_response, create_error_response
from models.user import User
from services.reporting_service import ReportingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/reporting", tags=["reporting"])


# Enums
class ReportType(str, Enum):
    PERFORMANCE = "performance"
    TRADE_LOG = "trade_log"
    WIN_LOSS = "win_loss"
    STRATEGY_ANALYSIS = "strategy_analysis"
    RISK_ANALYSIS = "risk_analysis"
    TAX_REPORT = "tax_report"
    MONTHLY_SUMMARY = "monthly_summary"
    ANNUAL_SUMMARY = "annual_summary"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class WidgetType(str, Enum):
    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    HEATMAP = "heatmap"
    TIMELINE = "timeline"


# Request/Response Models
class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    start_date: date
    end_date: date
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    groupings: Optional[List[str]] = Field(default_factory=list)
    metrics: Optional[List[str]] = Field(default_factory=list)
    format: ReportFormat = ReportFormat.JSON
    include_charts: bool = True
    include_summary: bool = True


class ReportTypeInfo(BaseModel):
    type: ReportType
    name: str
    description: str
    available_metrics: List[str]
    available_groupings: List[str]
    default_format: ReportFormat
    supports_scheduling: bool


class ScheduleReportRequest(BaseModel):
    report_type: ReportType
    recurrence: RecurrenceType
    delivery_time: str  # HH:MM format
    delivery_emails: List[str]
    report_config: ReportGenerateRequest
    timezone: str = "UTC"
    active: bool = True


class ScheduledReportResponse(BaseModel):
    id: str
    user_id: int
    report_type: ReportType
    recurrence: RecurrenceType
    delivery_time: str
    delivery_emails: List[str]
    report_config: Dict[str, Any]
    timezone: str
    active: bool
    created_at: datetime
    last_run: Optional[datetime]
    next_run: datetime


class ReportHistoryItem(BaseModel):
    id: str
    report_type: ReportType
    generated_at: datetime
    start_date: date
    end_date: date
    format: ReportFormat
    file_size: Optional[int]
    download_url: Optional[str]
    expires_at: Optional[datetime]
    status: str


class DashboardRequest(BaseModel):
    name: str
    description: Optional[str]
    layout: Dict[str, Any]
    is_public: bool = False
    tags: Optional[List[str]] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    id: str
    user_id: int
    name: str
    description: Optional[str]
    layout: Dict[str, Any]
    is_public: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    widgets: List[Dict[str, Any]]


class WidgetRequest(BaseModel):
    type: WidgetType
    title: str
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y, width, height
    refresh_interval: Optional[int] = None  # seconds


class WidgetResponse(BaseModel):
    id: str
    dashboard_id: str
    type: WidgetType
    title: str
    config: Dict[str, Any]
    position: Dict[str, int]
    refresh_interval: Optional[int]
    created_at: datetime
    updated_at: datetime


# Dependency
def get_reporting_service(db: Session = Depends(get_db)) -> ReportingService:
    return ReportingService(db)


# Endpoints
@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Generate a report based on specified parameters"""
    try:
        # For file formats, generate in background and return download link
        if request.format in [ReportFormat.PDF, ReportFormat.EXCEL]:
            report_id = str(uuid.uuid4())
            background_tasks.add_task(
                service.generate_report_file,
                user_id=current_user.id,
                report_id=report_id,
                request=request
            )
            return create_success_response(
                data={
                    "report_id": report_id,
                    "status": "generating",
                    "message": "Report generation started. Check /history for download link."
                }
            )
        
        # For JSON/CSV, return data directly
        report_data = await service.generate_report(
            user_id=current_user.id,
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date,
            filters=request.filters,
            groupings=request.groupings,
            metrics=request.metrics,
            format=request.format,
            include_charts=request.include_charts,
            include_summary=request.include_summary
        )
        
        if request.format == ReportFormat.CSV:
            # Return as downloadable CSV
            csv_data = service.convert_to_csv(report_data)
            return StreamingResponse(
                io.StringIO(csv_data),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        
        return create_success_response(data=report_data)
        
    except ValidationError as e:
        logger.error(f"Validation error generating report: {str(e)}")
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return create_error_response(error="Failed to generate report", status_code=500)


@router.get("/types", response_model=List[ReportTypeInfo])
async def get_available_reports(
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Get list of available report types with descriptions"""
    try:
        report_types = await service.get_available_report_types(current_user.id)
        return report_types
    except Exception as e:
        logger.error(f"Error fetching report types: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch report types")


@router.post("/schedule")
async def schedule_report(
    request: ScheduleReportRequest,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Schedule a recurring report with email delivery"""
    try:
        scheduled_report = await service.schedule_report(
            user_id=current_user.id,
            report_type=request.report_type,
            recurrence=request.recurrence,
            delivery_time=request.delivery_time,
            delivery_emails=request.delivery_emails,
            report_config=request.report_config.dict(),
            timezone=request.timezone,
            active=request.active
        )
        return create_success_response(
            data=scheduled_report,
            message="Report scheduled successfully"
        )
    except ValidationError as e:
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error scheduling report: {str(e)}")
        return create_error_response(error="Failed to schedule report", status_code=500)


@router.get("/scheduled", response_model=List[ScheduledReportResponse])
async def get_scheduled_reports(
    active_only: bool = Query(True, description="Filter only active schedules"),
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """List user's scheduled reports"""
    try:
        scheduled_reports = await service.get_scheduled_reports(
            user_id=current_user.id,
            active_only=active_only
        )
        return scheduled_reports
    except Exception as e:
        logger.error(f"Error fetching scheduled reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch scheduled reports")


@router.put("/scheduled/{schedule_id}")
async def update_scheduled_report(
    schedule_id: str,
    request: ScheduleReportRequest,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Update or pause scheduled reports"""
    try:
        updated_report = await service.update_scheduled_report(
            schedule_id=schedule_id,
            user_id=current_user.id,
            update_data=request.dict()
        )
        return create_success_response(
            data=updated_report,
            message="Scheduled report updated successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except ValidationError as e:
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error updating scheduled report: {str(e)}")
        return create_error_response(error="Failed to update scheduled report", status_code=500)


@router.delete("/scheduled/{schedule_id}")
async def delete_scheduled_report(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Remove scheduled report"""
    try:
        await service.delete_scheduled_report(
            schedule_id=schedule_id,
            user_id=current_user.id
        )
        return create_success_response(
            message="Scheduled report deleted successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error deleting scheduled report: {str(e)}")
        return create_error_response(error="Failed to delete scheduled report", status_code=500)


@router.get("/history")
async def get_report_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    report_type: Optional[ReportType] = None,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """List previously generated reports with download links"""
    try:
        history = await service.get_report_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            report_type=report_type
        )
        return create_success_response(
            data={
                "items": history["items"],
                "total": history["total"],
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        logger.error(f"Error fetching report history: {str(e)}")
        return create_error_response(error="Failed to fetch report history", status_code=500)


@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Download a previously generated report file"""
    try:
        file_info = await service.get_report_file(
            report_id=report_id,
            user_id=current_user.id
        )
        
        if not file_info:
            raise NotFoundError("Report file not found or expired")
        
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["filename"],
            media_type=file_info["media_type"]
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return create_error_response(error="Failed to download report", status_code=500)


# Dashboard endpoints
@router.post("/dashboards")
async def create_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Create custom dashboard"""
    try:
        dashboard = await service.create_dashboard(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            layout=request.layout,
            is_public=request.is_public,
            tags=request.tags
        )
        return create_success_response(
            data=dashboard,
            message="Dashboard created successfully"
        )
    except ValidationError as e:
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error creating dashboard: {str(e)}")
        return create_error_response(error="Failed to create dashboard", status_code=500)


@router.get("/dashboards")
async def list_dashboards(
    include_public: bool = Query(True, description="Include public dashboards"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """List user's dashboards"""
    try:
        dashboards = await service.list_dashboards(
            user_id=current_user.id,
            include_public=include_public,
            limit=limit,
            offset=offset
        )
        return create_success_response(
            data={
                "items": dashboards["items"],
                "total": dashboards["total"],
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        logger.error(f"Error listing dashboards: {str(e)}")
        return create_error_response(error="Failed to list dashboards", status_code=500)


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Get dashboard details"""
    try:
        dashboard = await service.get_dashboard(
            dashboard_id=dashboard_id,
            user_id=current_user.id
        )
        return create_success_response(data=dashboard)
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        return create_error_response(error="Failed to fetch dashboard", status_code=500)


@router.put("/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str,
    request: DashboardRequest,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Update dashboard"""
    try:
        dashboard = await service.update_dashboard(
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            update_data=request.dict()
        )
        return create_success_response(
            data=dashboard,
            message="Dashboard updated successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except ValidationError as e:
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")
        return create_error_response(error="Failed to update dashboard", status_code=500)


@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Delete dashboard"""
    try:
        await service.delete_dashboard(
            dashboard_id=dashboard_id,
            user_id=current_user.id
        )
        return create_success_response(
            message="Dashboard deleted successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error deleting dashboard: {str(e)}")
        return create_error_response(error="Failed to delete dashboard", status_code=500)


@router.post("/dashboards/{dashboard_id}/widgets")
async def add_widget_to_dashboard(
    dashboard_id: str,
    request: WidgetRequest,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Add widget to dashboard"""
    try:
        widget = await service.add_widget(
            dashboard_id=dashboard_id,
            user_id=current_user.id,
            widget_type=request.type,
            title=request.title,
            config=request.config,
            position=request.position,
            refresh_interval=request.refresh_interval
        )
        return create_success_response(
            data=widget,
            message="Widget added successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except ValidationError as e:
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error adding widget: {str(e)}")
        return create_error_response(error="Failed to add widget", status_code=500)


@router.put("/dashboards/{dashboard_id}/widgets/{widget_id}")
async def update_widget(
    dashboard_id: str,
    widget_id: str,
    request: WidgetRequest,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Update widget"""
    try:
        widget = await service.update_widget(
            dashboard_id=dashboard_id,
            widget_id=widget_id,
            user_id=current_user.id,
            update_data=request.dict()
        )
        return create_success_response(
            data=widget,
            message="Widget updated successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except ValidationError as e:
        return create_error_response(error=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error updating widget: {str(e)}")
        return create_error_response(error="Failed to update widget", status_code=500)


@router.delete("/dashboards/{dashboard_id}/widgets/{widget_id}")
async def remove_widget(
    dashboard_id: str,
    widget_id: str,
    current_user: User = Depends(get_current_user),
    service: ReportingService = Depends(get_reporting_service)
):
    """Remove widget from dashboard"""
    try:
        await service.remove_widget(
            dashboard_id=dashboard_id,
            widget_id=widget_id,
            user_id=current_user.id
        )
        return create_success_response(
            message="Widget removed successfully"
        )
    except NotFoundError as e:
        return create_error_response(error=str(e), status_code=404)
    except Exception as e:
        logger.error(f"Error removing widget: {str(e)}")
        return create_error_response(error="Failed to remove widget", status_code=500)