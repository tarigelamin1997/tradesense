
"""
Notes service layer - handles all trade note business logic
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc
import logging

from backend.models.trade_note import TradeNote
from backend.api.v1.notes.schemas import TradeNoteCreate, TradeNoteRead, TradeNoteUpdate
from backend.core.exceptions import ValidationError, BusinessLogicError, NotFoundError

logger = logging.getLogger(__name__)


class NotesService:
    """Notes service handling trade note operations"""
    
    async def create_note(self, db: Session, user_id: str, note_data: TradeNoteCreate) -> TradeNoteRead:
        """Create a new trade note"""
        try:
            # Validate trade_id exists if provided
            if note_data.trade_id:
                from backend.models.trade import Trade
                trade = db.query(Trade).filter(
                    Trade.id == note_data.trade_id,
                    Trade.user_id == user_id
                ).first()
                
                if not trade:
                    raise ValidationError("Trade not found or doesn't belong to user")
            
            # Create note record
            db_note = TradeNote(
                user_id=user_id,
                trade_id=note_data.trade_id,
                title=note_data.title,
                content=note_data.content,
                mood=note_data.mood.lower() if note_data.mood else None
            )
            
            db.add(db_note)
            db.commit()
            db.refresh(db_note)
            
            logger.info(f"Note created for user {user_id}: {note_data.title}")
            
            return TradeNoteRead.from_orm(db_note)
            
        except ValidationError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Note creation failed for user {user_id}: {str(e)}")
            raise BusinessLogicError(f"Note creation failed: {str(e)}")
    
    async def list_notes_by_user(self, db: Session, user_id: str, 
                                skip: int = 0, limit: int = 100,
                                trade_id: Optional[str] = None,
                                mood_filter: Optional[str] = None) -> List[TradeNoteRead]:
        """Get notes for a specific user with optional filtering"""
        try:
            query = db.query(TradeNote).filter(TradeNote.user_id == user_id)
            
            if trade_id:
                query = query.filter(TradeNote.trade_id == trade_id)
            
            if mood_filter:
                query = query.filter(TradeNote.mood == mood_filter.lower())
            
            notes = query.order_by(desc(TradeNote.timestamp)).offset(skip).limit(limit).all()
            
            return [TradeNoteRead.from_orm(note) for note in notes]
            
        except Exception as e:
            logger.error(f"Failed to get notes for user {user_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve notes")
    
    async def list_notes_by_trade(self, db: Session, user_id: str, trade_id: str) -> List[TradeNoteRead]:
        """Get all notes for a specific trade"""
        try:
            # Verify trade belongs to user
            from backend.models.trade import Trade
            trade = db.query(Trade).filter(
                Trade.id == trade_id,
                Trade.user_id == user_id
            ).first()
            
            if not trade:
                raise NotFoundError("Trade not found")
            
            notes = db.query(TradeNote).filter(
                TradeNote.trade_id == trade_id,
                TradeNote.user_id == user_id
            ).order_by(desc(TradeNote.timestamp)).all()
            
            return [TradeNoteRead.from_orm(note) for note in notes]
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get notes for trade {trade_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve trade notes")
    
    async def get_note_by_id(self, db: Session, user_id: str, note_id: str) -> TradeNoteRead:
        """Get a specific note by ID (user can only access their own notes)"""
        try:
            note = db.query(TradeNote).filter(
                TradeNote.id == note_id,
                TradeNote.user_id == user_id
            ).first()
            
            if not note:
                raise NotFoundError("Note not found")
            
            return TradeNoteRead.from_orm(note)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get note {note_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve note")
    
    async def update_note(self, db: Session, user_id: str, note_id: str, 
                         note_update: TradeNoteUpdate) -> TradeNoteRead:
        """Update a trade note"""
        try:
            note = db.query(TradeNote).filter(
                TradeNote.id == note_id,
                TradeNote.user_id == user_id
            ).first()
            
            if not note:
                raise NotFoundError("Note not found")
            
            # Update fields
            update_data = note_update.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "mood" and value:
                    value = value.lower()
                setattr(note, field, value)
            
            db.commit()
            db.refresh(note)
            
            logger.info(f"Note {note_id} updated by user {user_id}")
            
            return TradeNoteRead.from_orm(note)
            
        except NotFoundError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Note update failed for {note_id}: {str(e)}")
            raise BusinessLogicError(f"Note update failed: {str(e)}")
    
    async def delete_note(self, db: Session, user_id: str, note_id: str) -> Dict[str, Any]:
        """Delete a trade note"""
        try:
            note = db.query(TradeNote).filter(
                TradeNote.id == note_id,
                TradeNote.user_id == user_id
            ).first()
            
            if not note:
                raise NotFoundError("Note not found")
            
            db.delete(note)
            db.commit()
            
            logger.info(f"Note {note_id} deleted by user {user_id}")
            
            return {"message": "Note deleted successfully", "note_id": note_id}
            
        except NotFoundError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Note deletion failed for {note_id}: {str(e)}")
            raise BusinessLogicError(f"Note deletion failed: {str(e)}")
    
    async def get_mood_statistics(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get mood distribution statistics for a user"""
        try:
            # Get mood distribution
            mood_stats = db.query(
                TradeNote.mood,
                func.count(TradeNote.mood).label('count')
            ).filter(
                TradeNote.user_id == user_id,
                TradeNote.mood.isnot(None)
            ).group_by(TradeNote.mood).all()
            
            mood_distribution = {mood: count for mood, count in mood_stats}
            
            # Get most common mood
            most_common_mood = None
            if mood_distribution:
                most_common_mood = max(mood_distribution, key=mood_distribution.get)
            
            # Get total notes count
            total_notes = db.query(TradeNote).filter(TradeNote.user_id == user_id).count()
            
            return {
                "mood_distribution": mood_distribution,
                "most_common_mood": most_common_mood,
                "total_notes": total_notes
            }
            
        except Exception as e:
            logger.error(f"Failed to get mood statistics for user {user_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve mood statistics")
