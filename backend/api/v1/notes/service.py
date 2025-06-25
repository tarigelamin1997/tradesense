from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import json

from backend.models.trade_note import TradeNote
from backend.models.trade import Trade
from .schemas import JournalEntryCreate, JournalEntryUpdate, JournalEntryResponse, EmotionAnalytics, PsychologyInsights

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

    def get_emotion_analytics(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EmotionAnalytics:
        """Generate emotion analytics for a user"""

        query = self.db.query(TradeNote).filter(TradeNote.user_id == user_id)

        if start_date:
            query = query.filter(TradeNote.timestamp >= start_date)
        if end_date:
            query = query.filter(TradeNote.timestamp <= end_date)

        entries = query.all()

        # Analyze emotion distribution
        emotion_dist = {}
        confidence_scores = []
        trigger_counts = {}

        for entry in entries:
            if entry.emotion:
                emotion_dist[entry.emotion] = emotion_dist.get(entry.emotion, 0) + 1

            if entry.confidence_score:
                confidence_scores.append(entry.confidence_score)

            if entry.mental_triggers:
                try:
                    triggers = json.loads(entry.mental_triggers)
                    for trigger in triggers:
                        trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
                except json.JSONDecodeError:
                    pass

        # Calculate statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
        most_common_triggers = sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_common_triggers = [trigger for trigger, count in most_common_triggers]

        return EmotionAnalytics(
            emotion_distribution=emotion_dist,
            avg_confidence_score=avg_confidence,
            most_common_triggers=most_common_triggers,
            confidence_vs_performance={},  # TODO: Correlate with trade data
            emotional_trend={}  # TODO: Add time-based trend analysis
        )

    def get_psychology_insights(self, user_id: str) -> PsychologyInsights:
        """Generate psychology insights and recommendations"""

        entries = self.db.query(TradeNote).filter(
            TradeNote.user_id == user_id
        ).all()

        emotional_entries = [e for e in entries if e.emotion or e.confidence_score or e.mental_triggers]

        # Find dominant emotion
        emotion_counts = {}
        trigger_warning_count = 0
        confidence_scores = []

        concerning_triggers = ["FOMO", "Revenge", "Desperation", "Fear", "Greed"]

        for entry in emotional_entries:
            if entry.emotion:
                emotion_counts[entry.emotion] = emotion_counts.get(entry.emotion, 0) + 1

            if entry.confidence_score:
                confidence_scores.append(entry.confidence_score)

            if entry.mental_triggers:
                try:
                    triggers = json.loads(entry.mental_triggers)
                    if any(trigger in concerning_triggers for trigger in triggers):
                        trigger_warning_count += 1
                except json.JSONDecodeError:
                    pass

        dominant_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None

        # Calculate confidence consistency (lower std dev = more consistent)
        confidence_consistency = 0.0
        if len(confidence_scores) > 1:
            import statistics
            std_dev = statistics.stdev(confidence_scores)
            confidence_consistency = max(0, 10 - std_dev)  # Scale to 0-10

        # Generate recommendations
        recommendations = []
        if trigger_warning_count > len(emotional_entries) * 0.3:
            recommendations.append("Consider implementing cooling-off periods before entering trades")
        if confidence_consistency < 5:
            recommendations.append("Work on developing consistent confidence assessment criteria")
        if dominant_emotion in ["Anxious", "Fearful"]:
            recommendations.append("Consider mindfulness or stress reduction techniques")

        return PsychologyInsights(
            total_emotional_entries=len(emotional_entries),
            dominant_emotion=dominant_emotion,
            trigger_warning_count=trigger_warning_count,
            confidence_consistency=confidence_consistency,
            recommendations=recommendations
        )