from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from .service import DailyReflectionService
from .schemas import (
    DailyEmotionReflectionCreate, 
    DailyEmotionReflectionUpdate,
    DailyEmotionReflectionResponse
)

router = APIRouter(tags=["reflections"])

def get_reflection_service(db: Session = Depends(get_db)) -> DailyReflectionService:
    return DailyReflectionService(db)

@router.post("/", response_model=DailyEmotionReflectionResponse)
async def create_daily_reflection(
    reflection: DailyEmotionReflectionCreate,
    current_user: dict = Depends(get_current_user),
    service: DailyReflectionService = Depends(get_reflection_service)
):
    """Create or update daily emotion reflection"""
    try:
        return await service.create_or_update_reflection(
            user_id=current_user["user_id"],
            reflection_data=reflection
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save reflection: {str(e)}")

@router.get("/{reflection_date}", response_model=Optional[DailyEmotionReflectionResponse])
async def get_daily_reflection(
    reflection_date: date,
    current_user: dict = Depends(get_current_user),
    service: DailyReflectionService = Depends(get_reflection_service)
):
    """Get daily emotion reflection for specific date"""
    try:
        return await service.get_reflection_by_date(
            user_id=current_user["user_id"],
            reflection_date=reflection_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reflection: {str(e)}")

@router.put("/{reflection_date}", response_model=DailyEmotionReflectionResponse)
async def update_daily_reflection(
    reflection_date: date,
    reflection_update: DailyEmotionReflectionUpdate,
    current_user: dict = Depends(get_current_user),
    service: DailyReflectionService = Depends(get_reflection_service)
):
    """Update daily emotion reflection"""
    try:
        return await service.update_reflection(
            user_id=current_user["user_id"],
            reflection_date=reflection_date,
            update_data=reflection_update
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update reflection: {str(e)}")

@router.delete("/{reflection_date}")
async def delete_daily_reflection(
    reflection_date: date,
    current_user: dict = Depends(get_current_user),
    service: DailyReflectionService = Depends(get_reflection_service)
):
    """Delete daily emotion reflection"""
    try:
        await service.delete_reflection(
            user_id=current_user["user_id"],
            reflection_date=reflection_date
        )
        return {"message": "Reflection deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete reflection: {str(e)}")

@router.get("/")
async def get_reflections_overview(
    current_user: dict = Depends(get_current_user),
    reflection_service: DailyReflectionService = Depends(get_reflection_service)
):
    """Get overview of daily reflections"""
    try:
        recent_reflections = reflection_service.get_recent_reflections(current_user.id, limit=5)
        stats = reflection_service.get_reflection_stats(current_user.id)
        
        return {
            "status": "available",
            "recent_reflections": recent_reflections,
            "stats": stats,
            "features": [
                "Daily mood tracking",
                "Performance reflection",
                "Goal setting and tracking",
                "Emotional pattern analysis"
            ]
        }
    except Exception as e:
        return {
            "status": "available",
            "message": "Reflections service ready",
            "features": [
                "Daily mood tracking", 
                "Performance reflection",
                "Goal setting and tracking"
            ]
        }
