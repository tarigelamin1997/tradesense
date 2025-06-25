from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from backend.models.trade_note import TradeNote
from backend.models.trade import Trade
from .schemas import JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse

class NotesService:
    def __init__(self, db: Session):
        self.db = db

    def create_journal_entry(
        self, 
        trade_id: str, 
        user_id: str, 
        entry_data: JournalEntryCreate
    ) -> JournalEntryResponse:
        """Create a new journal entry for a trade"""

        # Verify trade exists and belongs to user
        trade = self.db.query(Trade).filter(
            and_(Trade.id == trade_id, Trade.user_id == user_id)
        ).first()

        if not trade:
            raise ValueError("Trade not found or access denied")

        # Create journal entry
        journal_entry = TradeNote(
            user_id=user_id,
            trade_id=trade_id,
            title=entry_data.title,
            content=entry_data.content,
            mood=entry_data.mood,
            timestamp=datetime.utcnow()
        )

        self.db.add(journal_entry)
        self.db.commit()
        self.db.refresh(journal_entry)

        return JournalEntryResponse.from_orm(journal_entry)

    def get_trade_journal_entries(
        self, 
        trade_id: str, 
        user_id: str
    ) -> List[JournalEntryResponse]:
        """Get all journal entries for a specific trade"""

        entries = self.db.query(TradeNote).filter(
            and_(
                TradeNote.trade_id == trade_id,
                TradeNote.user_id == user_id
            )
        ).order_by(TradeNote.timestamp.desc()).all()

        return [JournalEntryResponse.from_orm(entry) for entry in entries]

    def update_journal_entry(
        self, 
        entry_id: str, 
        user_id: str, 
        update_data: JournalEntryUpdate
    ) -> JournalEntryResponse:
        """Update a journal entry"""

        entry = self.db.query(TradeNote).filter(
            and_(TradeNote.id == entry_id, TradeNote.user_id == user_id)
        ).first()

        if not entry:
            raise ValueError("Journal entry not found or access denied")

        # Update fields if provided
        if update_data.title is not None:
            entry.title = update_data.title
        if update_data.content is not None:
            entry.content = update_data.content
        if update_data.mood is not None:
            entry.mood = update_data.mood

        entry.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(entry)

        return JournalEntryResponse.from_orm(entry)

    def delete_journal_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a journal entry"""

        entry = self.db.query(TradeNote).filter(
            and_(TradeNote.id == entry_id, TradeNote.user_id == user_id)
        ).first()

        if not entry:
            raise ValueError("Journal entry not found or access denied")

        self.db.delete(entry)
        self.db.commit()
        return True

    def get_journal_entry(
        self, 
        entry_id: str, 
        user_id: str
    ) -> Optional[JournalEntryResponse]:
        """Get a specific journal entry"""

        entry = self.db.query(TradeNote).filter(
            and_(TradeNote.id == entry_id, TradeNote.user_id == user_id)
        ).first()

        if not entry:
            return None

        return JournalEntryResponse.from_orm(entry)

    def get_all_user_journal_entries(
        self, 
        user_id: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[JournalEntryResponse]:
        """Get all journal entries for a user across all trades"""

        entries = self.db.query(TradeNote).filter(
            TradeNote.user_id == user_id
        ).order_by(TradeNote.timestamp.desc()).offset(offset).limit(limit).all()

        return [JournalEntryResponse.from_orm(entry) for entry in entries]