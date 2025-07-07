
"""
Email Scheduler Router
Handles email notifications, reports, and scheduling
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, time
import logging

from app.services.email_service import EmailService
from app.services.auth_service import get_current_user
from app.models.email import EmailSchedule, EmailTemplate, EmailReport

router = APIRouter()
email_service = EmailService()
logger = logging.getLogger(__name__)

class ScheduleEmailRequest(BaseModel):
    email_type: str  # "daily_report", "weekly_summary", "performance_alert"
    schedule_time: time
    enabled: bool = True
    recipients: Optional[List[EmailStr]] = None

class SendReportRequest(BaseModel):
    report_type: str
    email: EmailStr
    include_charts: bool = True

@router.post("/schedule")
async def schedule_email(
    request: ScheduleEmailRequest,
    user=Depends(get_current_user)
):
    """Schedule recurring email reports"""
    try:
        schedule = await email_service.create_schedule(
            user_id=user.id,
            email_type=request.email_type,
            schedule_time=request.schedule_time,
            enabled=request.enabled,
            recipients=request.recipients or [user.email]
        )
        
        logger.info(f"Email scheduled for user {user.id}: {request.email_type}")
        return {
            "success": True,
            "message": "Email scheduled successfully",
            "schedule_id": schedule.id
        }
    except Exception as e:
        logger.error(f"Email scheduling failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule email")

@router.get("/schedules")
async def get_email_schedules(user=Depends(get_current_user)):
    """Get user's email schedules"""
    try:
        schedules = await email_service.get_user_schedules(user.id)
        return {
            "success": True,
            "schedules": schedules
        }
    except Exception as e:
        logger.error(f"Get schedules failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedules")

@router.put("/schedule/{schedule_id}")
async def update_email_schedule(
    schedule_id: int,
    request: ScheduleEmailRequest,
    user=Depends(get_current_user)
):
    """Update existing email schedule"""
    try:
        schedule = await email_service.update_schedule(
            schedule_id=schedule_id,
            user_id=user.id,
            **request.dict()
        )
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "message": "Schedule updated successfully"
        }
    except Exception as e:
        logger.error(f"Update schedule failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")

@router.delete("/schedule/{schedule_id}")
async def delete_email_schedule(
    schedule_id: int,
    user=Depends(get_current_user)
):
    """Delete email schedule"""
    try:
        success = await email_service.delete_schedule(schedule_id, user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "message": "Schedule deleted successfully"
        }
    except Exception as e:
        logger.error(f"Delete schedule failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")

@router.post("/send-report")
async def send_instant_report(
    request: SendReportRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    """Send instant performance report"""
    try:
        # Add email sending to background tasks
        background_tasks.add_task(
            email_service.send_performance_report,
            user_id=user.id,
            report_type=request.report_type,
            recipient_email=request.email,
            include_charts=request.include_charts
        )
        
        logger.info(f"Instant report queued for {request.email}")
        return {
            "success": True,
            "message": "Report queued for sending"
        }
    except Exception as e:
        logger.error(f"Send report failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue report")

@router.get("/templates")
async def get_email_templates():
    """Get available email templates"""
    try:
        templates = await email_service.get_templates()
        return {
            "success": True,
            "templates": templates
        }
    except Exception as e:
        logger.error(f"Get templates failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")

@router.post("/test-email")
async def send_test_email(
    email: EmailStr,
    user=Depends(get_current_user)
):
    """Send test email to verify email settings"""
    try:
        success = await email_service.send_test_email(email, user.username)
        
        if success:
            return {
                "success": True,
                "message": "Test email sent successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
    except Exception as e:
        logger.error(f"Test email failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test email")
