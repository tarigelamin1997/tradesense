
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.core.db.session import get_db
from backend.core.security import get_current_user
from backend.models.milestone import MilestoneResponse, UserProgress
from backend.services.milestone_engine import MilestoneEngine

router = APIRouter(prefix="/api/v1/milestones", tags=["milestones"])

def get_milestone_engine(db: Session = Depends(get_db)) -> MilestoneEngine:
    return MilestoneEngine(db)

@router.get("/", response_model=List[MilestoneResponse])
async def get_user_milestones(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user),
    milestone_engine: MilestoneEngine = Depends(get_milestone_engine)
):
    """Get user's milestones with optional filtering"""
    try:
        milestones = milestone_engine.db.query(milestone_engine.db.model_class).filter(
            milestone_engine.db.model_class.user_id == current_user["user_id"]
        )
        
        if category:
            milestones = milestones.filter(milestone_engine.db.model_class.category == category)
        
        milestones = milestones.order_by(
            milestone_engine.db.model_class.achieved_at.desc()
        ).limit(limit).all()
        
        return milestones
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch milestones")

@router.get("/progress", response_model=UserProgress)
async def get_user_progress(
    current_user: dict = Depends(get_current_user),
    milestone_engine: MilestoneEngine = Depends(get_milestone_engine)
):
    """Get comprehensive user progress and gamification data"""
    try:
        return milestone_engine.get_user_progress(current_user["user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch user progress")

@router.post("/check/{trigger_type}")
async def trigger_milestone_check(
    trigger_type: str,
    context: dict = {},
    current_user: dict = Depends(get_current_user),
    milestone_engine: MilestoneEngine = Depends(get_milestone_engine)
):
    """Manually trigger milestone checking (for testing or specific events)"""
    try:
        awarded_milestones = milestone_engine.check_and_award_milestones(
            user_id=current_user["user_id"],
            trigger_type=trigger_type,
            context=context
        )
        
        return {
            "message": f"Milestone check completed",
            "awarded_count": len(awarded_milestones),
            "new_milestones": [
                {
                    "title": m.title,
                    "description": m.description,
                    "xp_points": m.xp_points,
                    "badge_icon": m.badge_icon,
                    "rarity": m.rarity
                }
                for m in awarded_milestones
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to check milestones")

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    milestone_engine: MilestoneEngine = Depends(get_milestone_engine)
):
    """Get leaderboard based on XP and milestones (for future team features)"""
    try:
        # For now, just return user's own progress as placeholder
        user_progress = milestone_engine.get_user_progress(current_user["user_id"])
        
        return {
            "leaderboard": [
                {
                    "user_id": current_user["user_id"],
                    "username": current_user.get("username", "You"),
                    "total_xp": user_progress.total_xp,
                    "level": user_progress.level,
                    "total_milestones": user_progress.total_milestones,
                    "rank": 1
                }
            ],
            "user_rank": 1,
            "total_users": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")
