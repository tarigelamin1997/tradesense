
"""
Exports Router
Handles PDF exports, data exports, and report generation
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import date
import logging

from app.services.export_service import ExportService
from app.services.auth_service import get_current_user

router = APIRouter()
export_service = ExportService()
logger = logging.getLogger(__name__)

@router.get("/pdf/performance-report")
async def export_performance_pdf(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_charts: bool = True,
    user=Depends(get_current_user)
):
    """Export performance report as PDF"""
    try:
        pdf_content = await export_service.generate_performance_pdf(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            include_charts=include_charts
        )
        
        logger.info(f"PDF report generated for user {user.id}")
        return StreamingResponse(
            pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=performance_report.pdf"}
        )
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

@router.get("/csv/trades")
async def export_trades_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    symbol: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Export trades data as CSV"""
    try:
        csv_content = await export_service.generate_trades_csv(
            user_id=user.id,
            start_date=start_date,
            end_date=end_date,
            symbol=symbol
        )
        
        logger.info(f"CSV export generated for user {user.id}")
        return StreamingResponse(
            csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=trades_export.csv"}
        )
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate CSV export")

@router.get("/json/analytics")
async def export_analytics_json(
    user=Depends(get_current_user)
):
    """Export complete analytics data as JSON"""
    try:
        analytics_data = await export_service.generate_analytics_json(user.id)
        
        return {
            "success": True,
            "data": analytics_data,
            "export_timestamp": analytics_data.get("timestamp")
        }
    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to export analytics data")
