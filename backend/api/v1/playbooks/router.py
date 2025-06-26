
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.core.db.session import get_db
from backend.api.deps import get_current_user
from backend.models.user import User
from backend.models.playbook import (
    PlaybookCreate, PlaybookUpdate, PlaybookResponse, PlaybookAnalytics
)
from .service import PlaybookService

router = APIRouter()

@router.post("/", response_model=PlaybookResponse)
async def create_playbook(
    playbook_data: PlaybookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trading playbook"""
    service = PlaybookService(db)
    return service.create_playbook(user_id=current_user.id, playbook_data=playbook_data)

@router.get("/", response_model=List[PlaybookResponse])
async def get_playbooks(
    status: Optional[str] = Query(None, description="Filter by status (active/archived)"),
    sort_by: str = Query("name", description="Sort by: name, total_pnl, win_rate, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    limit: int = Query(50, le=200, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's playbooks with optional filters"""
    service = PlaybookService(db)
    return service.get_playbooks(
        user_id=current_user.id,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit
    )

@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific playbook"""
    service = PlaybookService(db)
    playbook = service.get_playbook(playbook_id=playbook_id, user_id=current_user.id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook

@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: str,
    playbook_update: PlaybookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a playbook"""
    service = PlaybookService(db)
    playbook = service.update_playbook(
        playbook_id=playbook_id,
        user_id=current_user.id,
        playbook_data=playbook_update
    )
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook

@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a playbook"""
    service = PlaybookService(db)
    success = service.delete_playbook(playbook_id=playbook_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return {"message": "Playbook deleted successfully"}

@router.get("/analytics/summary", response_model=List[PlaybookAnalytics])
async def get_playbook_analytics(
    min_trades: int = Query(5, ge=1, description="Minimum trades required for analytics"),
    include_archived: bool = Query(False, description="Include archived playbooks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analytics for all playbooks"""
    service = PlaybookService(db)
    return service.get_playbook_analytics(
        user_id=current_user.id,
        min_trades=min_trades,
        include_archived=include_archived
    )

@router.get("/{playbook_id}/trades")
async def get_playbook_trades(
    playbook_id: str,
    limit: int = Query(50, le=200, description="Limit results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all trades associated with a specific playbook"""
    service = PlaybookService(db)
    trades = service.get_playbook_trades(
        playbook_id=playbook_id,
        user_id=current_user.id,
        limit=limit
    )
    if trades is None:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return {"playbook_id": playbook_id, "trades": trades}

@router.post("/{playbook_id}/archive")
async def archive_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive a playbook (soft delete)"""
    service = PlaybookService(db)
    success = service.archive_playbook(playbook_id=playbook_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return {"message": "Playbook archived successfully"}

@router.post("/{playbook_id}/activate")
async def activate_playbook(
    playbook_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reactivate an archived playbook"""
    service = PlaybookService(db)
    success = service.activate_playbook(playbook_id=playbook_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return {"message": "Playbook reactivated successfully"}

@router.post("/refresh-stats")
async def refresh_playbook_stats(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh performance statistics for all user playbooks"""
    service = PlaybookService(db)
    background_tasks.add_task(service.refresh_all_playbook_stats, current_user.id)
    return {"message": "Playbook statistics refresh started"}
