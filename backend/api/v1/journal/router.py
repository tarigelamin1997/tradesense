
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.models.trade_note import TradeNote
from .schemas import JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse
from .service import JournalService

router = APIRouter(prefix="/journal", tags=["journal"])

@router.get("/entries", response_model=List[JournalEntryResponse])
async def get_journal_entries(
    skip: int = 0,
    limit: int = 50,
    trade_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get journal entries for the current user"""
    service = JournalService(db)
    return service.get_user_entries(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        trade_id=trade_id
    )

@router.post("/entries", response_model=JournalEntryResponse)
async def create_journal_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new journal entry"""
    service = JournalService(db)
    return service.create_entry(
        user_id=current_user.id,
        entry_data=entry
    )

@router.put("/entries/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: UUID,
    entry: JournalEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a journal entry"""
    service = JournalService(db)
    updated_entry = service.update_entry(
        entry_id=entry_id,
        user_id=current_user.id,
        entry_data=entry
    )
    if not updated_entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return updated_entry

@router.delete("/entries/{entry_id}")
async def delete_journal_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a journal entry"""
    service = JournalService(db)
    success = service.delete_entry(entry_id=entry_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"message": "Journal entry deleted successfully"}

@router.get("/search")
async def search_journal_entries(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search journal entries by content"""
    service = JournalService(db)
    return service.search_entries(user_id=current_user.id, search_query=query)
