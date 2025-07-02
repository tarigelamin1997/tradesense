
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from backend.models.trade_note import TradeNote
from .schemas import JournalEntryCreate, JournalEntryUpdate

class JournalService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_entries(
        self, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 50,
        trade_id: Optional[UUID] = None
    ) -> List[TradeNote]:
        """Get journal entries for a user"""
        query = self.db.query(TradeNote).filter(TradeNote.user_id == user_id)
        
        if trade_id:
            query = query.filter(TradeNote.trade_id == trade_id)
        
        return query.order_by(TradeNote.timestamp.desc()).offset(skip).limit(limit).all()

    def create_entry(self, user_id: UUID, entry_data: JournalEntryCreate) -> TradeNote:
        """Create a new journal entry"""
        entry = TradeNote(
            user_id=user_id,
            trade_id=entry_data.trade_id,
            title=entry_data.title,
            content=entry_data.content,
            tags=entry_data.tags,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update_entry(
        self, 
        entry_id: UUID, 
        user_id: UUID, 
        entry_data: JournalEntryUpdate
    ) -> Optional[TradeNote]:
        """Update a journal entry"""
        entry = self.db.query(TradeNote).filter(
            and_(TradeNote.id == entry_id, TradeNote.user_id == user_id)
        ).first()
        
        if not entry:
            return None

        update_data = entry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        
        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete_entry(self, entry_id: UUID, user_id: UUID) -> bool:
        """Delete a journal entry"""
        entry = self.db.query(TradeNote).filter(
            and_(TradeNote.id == entry_id, TradeNote.user_id == user_id)
        ).first()
        
        if not entry:
            return False

        self.db.delete(entry)
        self.db.commit()
        return True

    def search_entries(self, user_id: UUID, search_query: str) -> List[TradeNote]:
        """Search journal entries by content"""
        return self.db.query(TradeNote).filter(
            and_(
                TradeNote.user_id == user_id,
                or_(
                    TradeNote.title.contains(search_query),
                    TradeNote.content.contains(search_query)
                )
            )
        ).order_by(TradeNote.timestamp.desc()).all()
