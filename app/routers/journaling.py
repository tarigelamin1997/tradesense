
"""
Journaling Router
Handles trade journaling, notes, and reflection features
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import logging

from app.services.journaling_service import JournalingService
from app.services.auth_service import get_current_user
from app.models.journal import JournalEntry, TradeNote, Reflection

router = APIRouter()
journal_service = JournalingService()
logger = logging.getLogger(__name__)

class CreateJournalEntryRequest(BaseModel):
    title: str
    content: str
    trade_id: Optional[int] = None
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    confidence: Optional[int] = None

class CreateReflectionRequest(BaseModel):
    period: str  # "daily", "weekly", "monthly"
    content: str
    key_learnings: List[str]
    goals_for_next_period: List[str]

@router.post("/entries")
async def create_journal_entry(
    request: CreateJournalEntryRequest,
    user=Depends(get_current_user)
):
    """Create a new journal entry"""
    try:
        entry = await journal_service.create_entry(
            user_id=user.id,
            **request.dict()
        )
        
        logger.info(f"Journal entry created for user {user.id}")
        return {
            "success": True,
            "message": "Journal entry created",
            "entry_id": entry.id
        }
    except Exception as e:
        logger.error(f"Create journal entry failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create journal entry")

@router.get("/entries")
async def get_journal_entries(
    limit: int = 20,
    offset: int = 0,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tag: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Get paginated journal entries"""
    try:
        entries = await journal_service.get_entries(
            user_id=user.id,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
            tag=tag
        )
        
        return {
            "success": True,
            "entries": entries,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(entries) == limit
            }
        }
    except Exception as e:
        logger.error(f"Get journal entries failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch entries")

@router.get("/entries/{entry_id}")
async def get_journal_entry(
    entry_id: int,
    user=Depends(get_current_user)
):
    """Get specific journal entry"""
    try:
        entry = await journal_service.get_entry(entry_id, user.id)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return {
            "success": True,
            "entry": entry
        }
    except Exception as e:
        logger.error(f"Get journal entry failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch entry")

@router.put("/entries/{entry_id}")
async def update_journal_entry(
    entry_id: int,
    request: CreateJournalEntryRequest,
    user=Depends(get_current_user)
):
    """Update journal entry"""
    try:
        entry = await journal_service.update_entry(
            entry_id=entry_id,
            user_id=user.id,
            **request.dict()
        )
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return {
            "success": True,
            "message": "Entry updated successfully"
        }
    except Exception as e:
        logger.error(f"Update journal entry failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update entry")

@router.delete("/entries/{entry_id}")
async def delete_journal_entry(
    entry_id: int,
    user=Depends(get_current_user)
):
    """Delete journal entry"""
    try:
        success = await journal_service.delete_entry(entry_id, user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return {
            "success": True,
            "message": "Entry deleted successfully"
        }
    except Exception as e:
        logger.error(f"Delete journal entry failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete entry")

@router.post("/reflections")
async def create_reflection(
    request: CreateReflectionRequest,
    user=Depends(get_current_user)
):
    """Create periodic reflection"""
    try:
        reflection = await journal_service.create_reflection(
            user_id=user.id,
            **request.dict()
        )
        
        logger.info(f"Reflection created for user {user.id}: {request.period}")
        return {
            "success": True,
            "message": "Reflection created",
            "reflection_id": reflection.id
        }
    except Exception as e:
        logger.error(f"Create reflection failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create reflection")

@router.get("/reflections")
async def get_reflections(
    period: Optional[str] = None,
    limit: int = 10,
    user=Depends(get_current_user)
):
    """Get user reflections"""
    try:
        reflections = await journal_service.get_reflections(
            user_id=user.id,
            period=period,
            limit=limit
        )
        
        return {
            "success": True,
            "reflections": reflections
        }
    except Exception as e:
        logger.error(f"Get reflections failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch reflections")

@router.get("/insights")
async def get_journal_insights(user=Depends(get_current_user)):
    """Get AI-powered journaling insights"""
    try:
        insights = await journal_service.analyze_journal_patterns(user.id)
        
        return {
            "success": True,
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Get insights failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")
