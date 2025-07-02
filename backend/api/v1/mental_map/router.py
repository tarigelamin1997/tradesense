
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.models.mental_map import (
    MentalMapEntryCreate, MentalMapEntryUpdate, MentalMapEntryResponse,
    SessionReplayCreate, SessionReplayUpdate, SessionReplayResponse
)
from .service import MentalMapService

router = APIRouter()

@router.post("/entries", response_model=MentalMapEntryResponse)
async def create_mental_entry(
    entry: MentalMapEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new mental map entry"""
    service = MentalMapService(db)
    return service.create_mental_entry(user_id=current_user.id, entry_data=entry)

@router.get("/entries", response_model=List[MentalMapEntryResponse])
async def get_mental_entries(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    trade_id: Optional[str] = Query(None, description="Filter by trade ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    limit: int = Query(100, le=500, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get mental map entries with optional filters"""
    service = MentalMapService(db)
    return service.get_mental_entries(
        user_id=current_user.id,
        session_id=session_id,
        trade_id=trade_id,
        start_date=start_date,
        end_date=end_date,
        mood=mood,
        limit=limit
    )

@router.get("/entries/{entry_id}", response_model=MentalMapEntryResponse)
async def get_mental_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific mental map entry"""
    service = MentalMapService(db)
    entry = service.get_mental_entry(entry_id=entry_id, user_id=current_user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="Mental map entry not found")
    return entry

@router.put("/entries/{entry_id}", response_model=MentalMapEntryResponse)
async def update_mental_entry(
    entry_id: str,
    entry_update: MentalMapEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a mental map entry"""
    service = MentalMapService(db)
    entry = service.update_mental_entry(
        entry_id=entry_id,
        user_id=current_user.id,
        entry_data=entry_update
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Mental map entry not found")
    return entry

@router.delete("/entries/{entry_id}")
async def delete_mental_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a mental map entry"""
    service = MentalMapService(db)
    success = service.delete_mental_entry(entry_id=entry_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Mental map entry not found")
    return {"message": "Mental map entry deleted successfully"}

# Session Replay endpoints
@router.post("/sessions", response_model=SessionReplayResponse)
async def create_session(
    session: SessionReplayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new session replay"""
    service = MentalMapService(db)
    return service.create_session(user_id=current_user.id, session_data=session)

@router.get("/sessions", response_model=List[SessionReplayResponse])
async def get_sessions(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    limit: int = Query(50, le=200, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get session replays with optional filters"""
    service = MentalMapService(db)
    return service.get_sessions(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

@router.get("/sessions/{session_id}", response_model=SessionReplayResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific session replay"""
    service = MentalMapService(db)
    session = service.get_session(session_id=session_id, user_id=current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session replay not found")
    return session

@router.put("/sessions/{session_id}", response_model=SessionReplayResponse)
async def update_session(
    session_id: str,
    session_update: SessionReplayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a session replay"""
    service = MentalMapService(db)
    session = service.update_session(
        session_id=session_id,
        user_id=current_user.id,
        session_data=session_update
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session replay not found")
    return session

@router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete timeline for a session including trades and mental entries"""
    service = MentalMapService(db)
    timeline = service.get_session_timeline(session_id=session_id, user_id=current_user.id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Session timeline not found")
    return timeline

@router.get("/analytics/mood-patterns")
async def get_mood_patterns(
    days: int = Query(30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get mood pattern analytics"""
    service = MentalMapService(db)
    return service.get_mood_patterns(user_id=current_user.id, days=days)

@router.get("/analytics/rule-breaks")
async def get_rule_break_analysis(
    days: int = Query(30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get rule break pattern analysis"""
    service = MentalMapService(db)
    return service.get_rule_break_analysis(user_id=current_user.id, days=days)
