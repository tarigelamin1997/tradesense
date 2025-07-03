"""
Notes router - handles all trade note endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from backend.core.db.session import get_db
from backend.api.deps import get_current_active_user
from backend.api.v1.notes.service import NotesService
from backend.api.v1.notes.schemas import (
    TradeNoteCreate, 
    TradeNoteRead, 
    TradeNoteUpdate,
    TradeNoteListResponse,
    MoodStatsResponse
)
from backend.core.response import ResponseHandler, APIResponse
from backend.core.exceptions import TradeSenseException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notes", tags=["Trade Notes & Journaling"])


@router.post("/", response_model=TradeNoteRead, summary="Create Trade Note")
async def create_note(
    note_data: TradeNoteCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeNoteRead:
    """
    Create a new trade note or journal entry
    
    - **title**: Note title (required)
    - **content**: Note content/body (required)
    - **mood**: Optional emotional state
    - **trade_id**: Optional trade ID to link the note to
    
    Returns the created note information
    """
    try:
        return await notes_service(db).create_note(db, current_user["user_id"], note_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Create note endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=TradeNoteListResponse, summary="List Trade Notes")
async def list_notes(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
    trade_id: Optional[str] = Query(default=None, description="Filter by trade ID"),
    mood: Optional[str] = Query(default=None, description="Filter by mood"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeNoteListResponse:
    """
    List all notes for the current user with optional filtering
    
    Supports pagination and filtering by trade ID and mood
    """
    try:
        notes = await notes_service(db).list_notes_by_user(
            db=db, 
            user_id=current_user["user_id"],
            skip=skip, 
            limit=limit,
            trade_id=trade_id,
            mood_filter=mood
        )
        
        # Get total count for pagination
        from backend.models.trade_note import TradeNote
        query = db.query(TradeNote).filter(TradeNote.user_id == current_user["user_id"])
        if trade_id:
            query = query.filter(TradeNote.trade_id == trade_id)
        if mood:
            query = query.filter(TradeNote.mood == mood.lower())
        total = query.count()
        
        return TradeNoteListResponse(
            notes=notes,
            total=total,
            skip=skip,
            limit=limit
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"List notes endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trade/{trade_id}", response_model=List[TradeNoteRead], summary="Get Notes for Trade")
async def get_notes_for_trade(
    trade_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> List[TradeNoteRead]:
    """
    Get all notes associated with a specific trade
    
    Returns all notes linked to the specified trade ID
    """
    try:
        return await notes_service(db).list_notes_by_trade(
            db, current_user["user_id"], trade_id
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get trade notes endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/mood", response_model=MoodStatsResponse, summary="Get Mood Statistics")
async def get_mood_stats(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> MoodStatsResponse:
    """
    Get mood distribution statistics for the current user
    
    Returns mood analytics including distribution and most common mood
    """
    try:
        stats = await notes_service(db).get_mood_statistics(db, current_user["user_id"])
        return MoodStatsResponse(**stats)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Mood stats endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{note_id}", response_model=TradeNoteRead, summary="Get Note by ID")
async def get_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeNoteRead:
    """
    Get a specific note by ID
    
    Users can only access their own notes
    """
    try:
        return await notes_service(db).get_note_by_id(db, current_user["user_id"], note_id)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get note endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{note_id}", response_model=TradeNoteRead, summary="Update Trade Note")
async def update_note(
    note_id: str,
    note_update: TradeNoteUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeNoteRead:
    """
    Update a trade note
    
    Users can only update their own notes
    """
    try:
        return await notes_service(db).update_note(
            db, current_user["user_id"], note_id, note_update
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Update note endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{note_id}", response_model=APIResponse, summary="Delete Trade Note")
async def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Delete a trade note
    
    Users can only delete their own notes
    """
    try:
        result = await notes_service(db).delete_note(db, current_user["user_id"], note_id)
        return ResponseHandler.success(
            data=result,
            message="Note deleted successfully"
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Delete note endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

from backend.api.v1.notes.schemas import (
    JournalEntryCreate, 
    JournalEntryUpdate, 
    JournalEntryResponse,
    EmotionAnalytics,
    PsychologyInsights
)

def get_notes_service(db: Session = Depends(get_db)) -> NotesService:
    return NotesService(db)

@router.post("/trades/{trade_id}/journal", response_model=JournalEntryResponse)
async def create_journal_entry(
    trade_id: str,
    entry_data: JournalEntryCreate,
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Create a new journal entry for a trade"""
    try:
        return await notes_service.create_journal_entry(
            trade_id=trade_id,
            user_id=current_user["user_id"],
            entry_data=entry_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create journal entry")

@router.get("/trades/{trade_id}/journal", response_model=List[JournalEntryResponse])
async def get_trade_journal_entries(
    trade_id: str,
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Get all journal entries for a specific trade"""
    return await notes_service.get_trade_journal_entries(
        trade_id=trade_id,
        user_id=current_user["user_id"]
    )

@router.put("/journal/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: str,
    update_data: JournalEntryUpdate,
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Update a journal entry"""
    try:
        return await notes_service.update_journal_entry(
            entry_id=entry_id,
            user_id=current_user["user_id"],
            update_data=update_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update journal entry")

@router.delete("/journal/{entry_id}")
async def delete_journal_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Delete a journal entry"""
    try:
        await notes_service.delete_journal_entry(
            entry_id=entry_id,
            user_id=current_user["user_id"]
        )
        return {"message": "Journal entry deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete journal entry")

@router.get("/journal/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Get a specific journal entry"""
    entry = await notes_service.get_journal_entry(
        entry_id=entry_id,
        user_id=current_user["user_id"]
    )

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    return entry

@router.get("/journal", response_model=List[JournalEntryResponse])
async def get_all_journal_entries(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Get all journal entries for the current user"""
    return await notes_service.get_all_user_journal_entries(
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset
    )

@router.get("/analytics/emotions", response_model=EmotionAnalytics)
async def get_emotion_analytics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Get emotion analytics for the current user"""
    from datetime import datetime
    
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    return notes_service.get_emotion_analytics(
        user_id=current_user["user_id"],
        start_date=start_dt,
        end_date=end_dt
    )

@router.get("/analytics/psychology", response_model=PsychologyInsights)
async def get_psychology_insights(
    current_user: dict = Depends(get_current_active_user),
    notes_service: NotesService = Depends(get_notes_service)
):
    """Get psychology insights and recommendations for the current user"""
    return notes_service.get_psychology_insights(
        user_id=current_user["user_id"]
    )