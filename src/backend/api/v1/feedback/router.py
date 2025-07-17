from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import hashlib

from api.deps import get_current_user, get_db
from api.v1.users.schemas import User
from .schemas import (
    FeedbackSubmit,
    FeedbackResponse,
    FeedbackItem,
    FeedbackAnalytics,
    FeedbackPattern,
    FeedbackUpdate
)
from .service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Submit new feedback with automatic pattern detection"""
    service = FeedbackService(db)
    
    # Create feedback entry
    feedback_id = await service.create_feedback(
        user_id=current_user.id if current_user else None,
        user_email=feedback.email,
        feedback_data=feedback
    )
    
    # Check for duplicates and patterns
    pattern_id = await service.detect_pattern(feedback)
    
    # Send notification if critical
    if feedback.severity == "critical":
        await service.send_critical_alert(feedback_id, feedback)
    
    return FeedbackResponse(
        trackingId=feedback_id,
        message="Thank you for your feedback! We'll look into this issue."
    )

@router.get("/analytics", response_model=FeedbackAnalytics)
async def get_feedback_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback analytics (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    return await service.get_analytics()

@router.get("/patterns/{pattern_id}")
async def get_pattern_details(
    pattern_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed pattern information (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    pattern = await service.get_pattern_details(pattern_id)
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    return pattern

@router.get("/list", response_model=List[FeedbackItem])
async def list_feedback(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all feedback with filters (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    return await service.list_feedback(
        status=status,
        type=type,
        severity=severity,
        date_from=date_from,
        date_to=date_to
    )

@router.patch("/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    update: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update feedback status (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    feedback = await service.update_status(
        feedback_id=feedback_id,
        status=update.status,
        resolution_notes=update.resolution_notes,
        assigned_to=current_user.username
    )
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Notify user if resolved
    if update.status == "resolved":
        await service.send_resolution_notification(feedback_id)
    
    return feedback

@router.patch("/{feedback_id}/assign")
async def assign_feedback(
    feedback_id: str,
    assignee: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign feedback to team member (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    feedback = await service.assign_feedback(feedback_id, assignee)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    return feedback

@router.post("/{feedback_id}/duplicate")
async def mark_as_duplicate(
    feedback_id: str,
    original_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark feedback as duplicate (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    await service.mark_duplicate(feedback_id, original_id)
    
    return {"message": "Marked as duplicate"}

@router.get("/my-feedback", response_model=List[FeedbackItem])
async def get_user_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's feedback history"""
    service = FeedbackService(db)
    return await service.get_user_feedback(current_user.id)

@router.get("/dashboard")
async def get_feedback_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time feedback dashboard data (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    
    # Get various metrics for dashboard
    return {
        "recent_feedback": await service.get_recent_feedback(limit=10),
        "critical_issues": await service.get_critical_issues(),
        "trending_patterns": await service.get_trending_patterns(),
        "resolution_stats": await service.get_resolution_stats(),
        "impact_analysis": await service.get_impact_analysis(),
        "feedback_heatmap": await service.get_feedback_heatmap()
    }

@router.post("/patterns/train")
async def train_pattern_detection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrain pattern detection ML model (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = FeedbackService(db)
    results = await service.train_pattern_detection()
    
    return {
        "message": "Pattern detection model updated",
        "patterns_discovered": results["new_patterns"],
        "accuracy": results["accuracy"]
    }