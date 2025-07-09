
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter
import json

from backend.models.mental_map import MentalMapEntry, SessionReplay
from backend.models.trade import Trade
from backend.models.mental_map import (
    MentalMapEntryCreate, MentalMapEntryUpdate,
    SessionReplayCreate, SessionReplayUpdate
)

class MentalMapService:
    def __init__(self, db: Session):
        self.db = db

    def create_mental_entry(self, user_id: str, entry_data: MentalMapEntryCreate) -> MentalMapEntry:
        """Create a new mental map entry"""
        entry = MentalMapEntry(
            user_id=user_id,
            trade_id=entry_data.trade_id,
            session_id=entry_data.session_id,
            timestamp=entry_data.timestamp,
            note=entry_data.note,
            mood=entry_data.mood,
            confidence_score=entry_data.confidence_score,
            checklist_flags=entry_data.checklist_flags,
            screenshot_url=entry_data.screenshot_url,
            chart_context=entry_data.chart_context
        )
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        # Update session summary if entry is part of a session
        if entry.session_id:
            self._update_session_summary(entry.session_id)
        
        return entry

    def get_mental_entries(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        trade_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        mood: Optional[str] = None,
        limit: int = 100
    ) -> List[MentalMapEntry]:
        """Get mental map entries with filters"""
        query = self.db.query(MentalMapEntry).filter(MentalMapEntry.user_id == user_id)
        
        if session_id:
            query = query.filter(MentalMapEntry.session_id == session_id)
        
        if trade_id:
            query = query.filter(MentalMapEntry.trade_id == trade_id)
        
        if start_date:
            query = query.filter(MentalMapEntry.timestamp >= start_date)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(MentalMapEntry.timestamp <= end_datetime)
        
        if mood:
            query = query.filter(MentalMapEntry.mood == mood)
        
        return query.order_by(desc(MentalMapEntry.timestamp)).limit(limit).all()

    def get_mental_entry(self, entry_id: str, user_id: str) -> Optional[MentalMapEntry]:
        """Get a specific mental map entry"""
        return self.db.query(MentalMapEntry).filter(
            and_(MentalMapEntry.id == entry_id, MentalMapEntry.user_id == user_id)
        ).first()

    def update_mental_entry(
        self, entry_id: str, user_id: str, entry_data: MentalMapEntryUpdate
    ) -> Optional[MentalMapEntry]:
        """Update a mental map entry"""
        entry = self.get_mental_entry(entry_id, user_id)
        if not entry:
            return None
        
        update_data = entry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        
        self.db.commit()
        self.db.refresh(entry)
        
        # Update session summary if needed
        if entry.session_id:
            self._update_session_summary(entry.session_id)
        
        return entry

    def delete_mental_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a mental map entry"""
        entry = self.get_mental_entry(entry_id, user_id)
        if not entry:
            return False
        
        session_id = entry.session_id
        self.db.delete(entry)
        self.db.commit()
        
        # Update session summary if needed
        if session_id:
            self._update_session_summary(session_id)
        
        return True

    def create_session(self, user_id: str, session_data: SessionReplayCreate) -> SessionReplay:
        """Create a new session replay"""
        session = SessionReplay(
            user_id=user_id,
            start_time=session_data.start_time,
            end_time=session_data.end_time,
            session_name=session_data.session_name,
            market_conditions=session_data.market_conditions,
            session_notes=session_data.session_notes
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_sessions(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50
    ) -> List[SessionReplay]:
        """Get session replays with filters"""
        query = self.db.query(SessionReplay).filter(SessionReplay.user_id == user_id)
        
        if start_date:
            query = query.filter(SessionReplay.start_time >= start_date)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(SessionReplay.start_time <= end_datetime)
        
        return query.order_by(desc(SessionReplay.start_time)).limit(limit).all()

    def get_session(self, session_id: str, user_id: str) -> Optional[SessionReplay]:
        """Get a specific session replay"""
        return self.db.query(SessionReplay).filter(
            and_(SessionReplay.id == session_id, SessionReplay.user_id == user_id)
        ).first()

    def update_session(
        self, session_id: str, user_id: str, session_data: SessionReplayUpdate
    ) -> Optional[SessionReplay]:
        """Update a session replay"""
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        
        update_data = session_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_timeline(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete timeline for a session including trades and mental entries"""
        session = self.get_session(session_id, user_id)
        if not session:
            return None
        
        # Get mental entries for this session
        mental_entries = self.db.query(MentalMapEntry).filter(
            MentalMapEntry.session_id == session_id
        ).order_by(MentalMapEntry.timestamp).all()
        
        # Get trades within session timeframe
        trade_query = self.db.query(Trade).filter(Trade.user_id == user_id)
        
        if session.start_time:
            trade_query = trade_query.filter(Trade.entry_time >= session.start_time)
        
        if session.end_time:
            trade_query = trade_query.filter(Trade.entry_time <= session.end_time)
        
        trades = trade_query.order_by(Trade.entry_time).all()
        
        # Combine timeline
        timeline_events = []
        
        # Add mental entries
        for entry in mental_entries:
            timeline_events.append({
                "type": "mental_entry",
                "timestamp": entry.timestamp,
                "data": {
                    "id": entry.id,
                    "note": entry.note,
                    "mood": entry.mood,
                    "confidence_score": entry.confidence_score,
                    "checklist_flags": entry.checklist_flags,
                    "screenshot_url": entry.screenshot_url,
                    "chart_context": entry.chart_context
                }
            })
        
        # Add trades
        for trade in trades:
            timeline_events.append({
                "type": "trade",
                "timestamp": trade.entry_time,
                "data": {
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "direction": trade.direction,
                    "quantity": trade.quantity,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "pnl": trade.pnl,
                    "strategy_tag": trade.strategy_tag
                }
            })
        
        # Sort by timestamp
        timeline_events.sort(key=lambda x: x["timestamp"])
        
        return {
            "session": {
                "id": session.id,
                "session_name": session.session_name,
                "start_time": session.start_time,
                "end_time": session.end_time,
                "market_conditions": session.market_conditions,
                "session_notes": session.session_notes,
                "total_trades": session.total_trades,
                "dominant_mood": session.dominant_mood
            },
            "timeline": timeline_events
        }

    def get_mood_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze mood patterns over time"""
        start_date = datetime.now() - timedelta(days=days)
        
        entries = self.db.query(MentalMapEntry).filter(
            and_(
                MentalMapEntry.user_id == user_id,
                MentalMapEntry.timestamp >= start_date
            )
        ).all()
        
        if not entries:
            return {"mood_distribution": {}, "mood_trend": [], "insights": []}
        
        # Mood distribution
        mood_counts = Counter([entry.mood for entry in entries])
        mood_distribution = dict(mood_counts)
        
        # Daily mood trends
        daily_moods = defaultdict(list)
        for entry in entries:
            day = entry.timestamp.date()
            daily_moods[day].append(entry.mood)
        
        mood_trend = []
        for day in sorted(daily_moods.keys()):
            day_moods = daily_moods[day]
            dominant_mood = Counter(day_moods).most_common(1)[0][0]
            mood_trend.append({
                "date": day,
                "dominant_mood": dominant_mood,
                "mood_count": len(day_moods)
            })
        
        # Generate insights
        insights = []
        total_entries = len(entries)
        
        # Most common mood
        if mood_distribution:
            most_common_mood = max(mood_distribution, key=mood_distribution.get)
            percentage = (mood_distribution[most_common_mood] / total_entries) * 100
            insights.append(f"Your most common mood is '{most_common_mood}' ({percentage:.1f}% of entries)")
        
        # Negative mood warning
        negative_moods = ['anxious', 'revenge', 'fearful', 'frustrated']
        negative_count = sum(mood_distribution.get(mood, 0) for mood in negative_moods)
        if negative_count > total_entries * 0.3:  # More than 30% negative
            insights.append("High frequency of negative emotions detected - consider implementing stress management techniques")
        
        return {
            "mood_distribution": mood_distribution,
            "mood_trend": mood_trend,
            "insights": insights
        }

    def get_rule_break_analysis(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze rule break patterns"""
        start_date = datetime.now() - timedelta(days=days)
        
        entries = self.db.query(MentalMapEntry).filter(
            and_(
                MentalMapEntry.user_id == user_id,
                MentalMapEntry.timestamp >= start_date,
                MentalMapEntry.checklist_flags.isnot(None)
            )
        ).all()
        
        if not entries:
            return {"rule_break_distribution": {}, "rule_break_trend": [], "insights": []}
        
        # Flatten all rule breaks
        all_rule_breaks = []
        for entry in entries:
            if entry.checklist_flags:
                all_rule_breaks.extend(entry.checklist_flags)
        
        if not all_rule_breaks:
            return {"rule_break_distribution": {}, "rule_break_trend": [], "insights": []}
        
        # Rule break distribution
        rule_break_counts = Counter(all_rule_breaks)
        rule_break_distribution = dict(rule_break_counts)
        
        # Daily rule break trends
        daily_breaks = defaultdict(list)
        for entry in entries:
            if entry.checklist_flags:
                day = entry.timestamp.date()
                daily_breaks[day].extend(entry.checklist_flags)
        
        rule_break_trend = []
        for day in sorted(daily_breaks.keys()):
            day_breaks = daily_breaks[day]
            rule_break_trend.append({
                "date": day,
                "rule_breaks": len(day_breaks),
                "unique_breaks": len(set(day_breaks))
            })
        
        # Generate insights
        insights = []
        total_breaks = len(all_rule_breaks)
        
        if rule_break_distribution:
            most_common_break = max(rule_break_distribution, key=rule_break_distribution.get)
            percentage = (rule_break_distribution[most_common_break] / total_breaks) * 100
            insights.append(f"Most frequent rule break: '{most_common_break}' ({percentage:.1f}% of violations)")
        
        # High rule break frequency warning
        entries_with_breaks = len([e for e in entries if e.checklist_flags])
        if entries_with_breaks > len(entries) * 0.5:  # More than 50% of entries have rule breaks
            insights.append("High frequency of rule violations detected - consider reviewing your trading plan")
        
        return {
            "rule_break_distribution": rule_break_distribution,
            "rule_break_trend": rule_break_trend,
            "insights": insights
        }

    def _update_session_summary(self, session_id: str):
        """Update session summary with computed metrics"""
        session = self.db.query(SessionReplay).filter(SessionReplay.id == session_id).first()
        if not session:
            return
        
        # Get mental entries for this session
        mental_entries = self.db.query(MentalMapEntry).filter(
            MentalMapEntry.session_id == session_id
        ).all()
        
        # Get trades within session timeframe
        trade_count = 0
        if session.start_time:
            trade_query = self.db.query(Trade).filter(
                and_(
                    Trade.user_id == session.user_id,
                    Trade.entry_time >= session.start_time
                )
            )
            
            if session.end_time:
                trade_query = trade_query.filter(Trade.entry_time <= session.end_time)
            
            trade_count = trade_query.count()
        
        # Calculate dominant mood
        dominant_mood = None
        if mental_entries:
            mood_counts = Counter([entry.mood for entry in mental_entries])
            dominant_mood = mood_counts.most_common(1)[0][0]
        
        # Calculate rule breaks
        rule_breaks = []
        for entry in mental_entries:
            if entry.checklist_flags:
                rule_breaks.extend(entry.checklist_flags)
        
        unique_rule_breaks = list(set(rule_breaks))
        
        # Update session
        session.total_trades = str(trade_count)
        session.dominant_mood = dominant_mood
        session.rule_breaks = unique_rule_breaks
        
        self.db.commit()
