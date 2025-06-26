
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
import pandas as pd
import numpy as np
from collections import defaultdict

from backend.models.trade import Trade
from backend.models.trade_note import TradeNote
from backend.models.daily_emotion_reflection import DailyEmotionReflection
from .schemas import (
    AnalyticsSummaryResponse, AnalyticsFilters, StrategyStats, 
    EmotionImpact, TriggerAnalysis, ConfidenceAnalysis, EmotionalLeak,
    TimelineResponse, DailyTimelineData
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        
    async def get_analytics_summary(self, user_id: str, filters: AnalyticsFilters) -> AnalyticsSummaryResponse:
        """Generate comprehensive analytics summary"""
        
        # Get base trade query with filters
        trade_query = self.db.query(Trade).filter(Trade.user_id == user_id)
        
        if filters.start_date:
            trade_query = trade_query.filter(Trade.entry_time >= filters.start_date)
        if filters.end_date:
            trade_query = trade_query.filter(Trade.entry_time <= filters.end_date)
        if filters.strategy_filter:
            trade_query = trade_query.filter(Trade.strategy_tag == filters.strategy_filter)
            
        trades = trade_query.all()
        
        if not trades:
            return self._empty_summary()
        
        # Get trade notes for emotional analysis
        note_query = self.db.query(TradeNote).filter(TradeNote.user_id == user_id)
        if filters.start_date:
            note_query = note_query.filter(TradeNote.created_at >= filters.start_date)
        if filters.end_date:
            note_query = note_query.filter(TradeNote.created_at <= filters.end_date)
        notes = note_query.all()
        
        # Convert to DataFrames for analysis
        trades_df = pd.DataFrame([{
            'id': t.id,
            'symbol': t.symbol,
            'strategy_tag': t.strategy_tag,
            'pnl': t.pnl or 0,
            'confidence_score': t.confidence_score,
            'entry_time': t.entry_time,
            'tags': t.tags or []
        } for t in trades])
        
        notes_df = pd.DataFrame([{
            'trade_id': n.trade_id,
            'emotion': n.emotion,
            'confidence_score': n.confidence_score,
            'mental_triggers': n.mental_triggers
        } for n in notes])
        
        # Merge trades with notes
        combined_df = trades_df.merge(notes_df, left_on='id', right_on='trade_id', how='left')
        
        # Calculate all analytics components
        strategy_stats = self._calculate_strategy_stats(trades_df)
        emotion_impact = self._calculate_emotion_impact(combined_df)
        trigger_analysis = self._calculate_trigger_analysis(combined_df)
        confidence_analysis = self._calculate_confidence_analysis(combined_df)
        emotional_leaks = self._identify_emotional_leaks(combined_df)
        behavioral_patterns = self._calculate_behavioral_patterns(combined_df)
        
        # Core metrics
        total_trades = len(trades)
        total_pnl = trades_df['pnl'].sum()
        overall_win_rate = len(trades_df[trades_df['pnl'] > 0]) / total_trades * 100
        
        return AnalyticsSummaryResponse(
            total_trades=total_trades,
            total_pnl=round(total_pnl, 2),
            overall_win_rate=round(overall_win_rate, 2),
            strategy_stats=strategy_stats,
            best_strategy=strategy_stats[0].name if strategy_stats else None,
            worst_strategy=strategy_stats[-1].name if strategy_stats else None,
            emotion_impact=emotion_impact,
            trigger_analysis=trigger_analysis,
            confidence_analysis=confidence_analysis,
            emotional_leaks=emotional_leaks,
            **behavioral_patterns,
            generated_at=datetime.now(),
            period_analyzed=f"{filters.start_date or 'All time'} to {filters.end_date or 'Present'}"
        )
    
    def _calculate_strategy_stats(self, df: pd.DataFrame) -> List[StrategyStats]:
        """Calculate performance statistics by strategy"""
        if df.empty or df['strategy_tag'].isna().all():
            return []
            
        strategy_groups = df.groupby('strategy_tag')
        stats = []
        
        for strategy, group in strategy_groups:
            if pd.isna(strategy):
                continue
                
            wins = group[group['pnl'] > 0]
            losses = group[group['pnl'] < 0]
            
            win_rate = len(wins) / len(group) * 100 if len(group) > 0 else 0
            avg_return = group['pnl'].mean()
            total_pnl = group['pnl'].sum()
            
            gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
            gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
            
            stats.append(StrategyStats(
                name=strategy,
                total_trades=len(group),
                win_rate=round(win_rate, 2),
                avg_return=round(avg_return, 2),
                total_pnl=round(total_pnl, 2),
                profit_factor=round(profit_factor, 2),
                best_trade=round(group['pnl'].max(), 2),
                worst_trade=round(group['pnl'].min(), 2)
            ))
        
        return sorted(stats, key=lambda x: x.total_pnl, reverse=True)
    
    def _calculate_emotion_impact(self, df: pd.DataFrame) -> List[EmotionImpact]:
        """Calculate impact of emotions on trading performance"""
        if df.empty or df['emotion'].isna().all():
            return []
        
        emotion_groups = df.dropna(subset=['emotion']).groupby('emotion')
        impacts = []
        
        for emotion, group in emotion_groups:
            wins = group[group['pnl'] > 0]
            win_rate = len(wins) / len(group) * 100 if len(group) > 0 else 0
            net_pnl = group['pnl'].sum()
            avg_pnl = group['pnl'].mean()
            
            # Impact score: negative emotions should have negative impact
            negative_emotions = ['anxious', 'fearful', 'frustrated', 'greedy', 'impulsive']
            base_impact = avg_pnl * len(group)  # Total impact
            impact_score = -abs(base_impact) if emotion.lower() in negative_emotions else base_impact
            
            impacts.append(EmotionImpact(
                emotion=emotion,
                trade_count=len(group),
                win_rate=round(win_rate, 2),
                net_pnl=round(net_pnl, 2),
                avg_pnl=round(avg_pnl, 2),
                impact_score=round(impact_score, 2)
            ))
        
        return sorted(impacts, key=lambda x: x.impact_score)
    
    def _calculate_trigger_analysis(self, df: pd.DataFrame) -> List[TriggerAnalysis]:
        """Analyze mental triggers and their impact"""
        if df.empty:
            return []
        
        trigger_stats = defaultdict(lambda: {'trades': [], 'pnl': []})
        
        for _, row in df.iterrows():
            if pd.notna(row['mental_triggers']):
                try:
                    import json
                    triggers = json.loads(row['mental_triggers']) if isinstance(row['mental_triggers'], str) else row['mental_triggers']
                    if isinstance(triggers, list):
                        for trigger in triggers:
                            trigger_stats[trigger]['trades'].append(row)
                            trigger_stats[trigger]['pnl'].append(row['pnl'])
                except:
                    continue
        
        analysis = []
        for trigger, data in trigger_stats.items():
            if not data['pnl']:
                continue
                
            pnl_series = pd.Series(data['pnl'])
            wins = len(pnl_series[pnl_series > 0])
            win_rate = wins / len(pnl_series) * 100 if len(pnl_series) > 0 else 0
            
            analysis.append(TriggerAnalysis(
                trigger=trigger,
                usage_count=len(data['pnl']),
                win_rate=round(win_rate, 2),
                net_result=round(pnl_series.sum(), 2),
                avg_impact=round(pnl_series.mean(), 2),
                frequency_rank=len(data['pnl'])
            ))
        
        return sorted(analysis, key=lambda x: x.usage_count, reverse=True)
    
    def _calculate_confidence_analysis(self, df: pd.DataFrame) -> List[ConfidenceAnalysis]:
        """Analyze confidence score vs performance correlation"""
        confidence_col = df['confidence_score_x'].fillna(df['confidence_score_y'])
        df_with_confidence = df[confidence_col.notna()].copy()
        df_with_confidence['confidence'] = confidence_col[confidence_col.notna()]
        
        if df_with_confidence.empty:
            return []
        
        confidence_groups = df_with_confidence.groupby('confidence')
        analysis = []
        
        for confidence, group in confidence_groups:
            wins = group[group['pnl'] > 0]
            win_rate = len(wins) / len(group) * 100 if len(group) > 0 else 0
            
            analysis.append(ConfidenceAnalysis(
                confidence_level=int(confidence),
                trade_count=len(group),
                win_rate=round(win_rate, 2),
                avg_pnl=round(group['pnl'].mean(), 2),
                avg_return=round(group['pnl'].mean(), 2)
            ))
        
        return sorted(analysis, key=lambda x: x.confidence_level)
    
    def _identify_emotional_leaks(self, df: pd.DataFrame) -> List[EmotionalLeak]:
        """Identify costly emotional patterns"""
        leaks = []
        
        # FOMO leak
        fomo_trades = df[df['tags'].apply(lambda x: 'fomo' in [tag.lower() for tag in (x or [])])]
        if not fomo_trades.empty:
            fomo_cost = fomo_trades[fomo_trades['pnl'] < 0]['pnl'].sum()
            if fomo_cost < -100:  # Significant cost threshold
                leaks.append(EmotionalLeak(
                    category="trigger",
                    name="FOMO",
                    cost=abs(fomo_cost),
                    frequency=len(fomo_trades),
                    description=f"FOMO-driven trades cost ${abs(fomo_cost):.0f} across {len(fomo_trades)} trades",
                    severity="high" if abs(fomo_cost) > 1000 else "medium"
                ))
        
        # Revenge trading leak
        revenge_trades = df[df['tags'].apply(lambda x: 'revenge' in [tag.lower() for tag in (x or [])])]
        if not revenge_trades.empty:
            revenge_cost = revenge_trades[revenge_trades['pnl'] < 0]['pnl'].sum()
            if revenge_cost < -50:
                leaks.append(EmotionalLeak(
                    category="pattern",
                    name="Revenge Trading",
                    cost=abs(revenge_cost),
                    frequency=len(revenge_trades),
                    description=f"Revenge trading pattern cost ${abs(revenge_cost):.0f}",
                    severity="critical" if abs(revenge_cost) > 500 else "high"
                ))
        
        # Overconfidence leak
        overconfident_trades = df[df['emotion'] == 'overconfident']
        if not overconfident_trades.empty:
            overconf_cost = overconfident_trades[overconfident_trades['pnl'] < 0]['pnl'].sum()
            if overconf_cost < -100:
                leaks.append(EmotionalLeak(
                    category="emotion",
                    name="Overconfidence",
                    cost=abs(overconf_cost),
                    frequency=len(overconfident_trades),
                    description=f"Overconfident trades resulted in ${abs(overconf_cost):.0f} in losses",
                    severity="medium"
                ))
        
        return sorted(leaks, key=lambda x: x.cost, reverse=True)
    
    def _calculate_behavioral_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate behavioral pattern metrics"""
        
        # Confidence vs performance correlation
        confidence_col = df['confidence_score_x'].fillna(df['confidence_score_y'])
        conf_corr = 0.0
        if not confidence_col.isna().all():
            conf_corr = confidence_col.corr(df['pnl'])
        
        # Emotional costs
        fomo_cost = df[df['tags'].apply(lambda x: 'fomo' in [tag.lower() for tag in (x or [])] if x else False)]['pnl'].sum()
        revenge_cost = df[df['tags'].apply(lambda x: 'revenge' in [tag.lower() for tag in (x or [])] if x else False)]['pnl'].sum()
        hesitation_cost = df[df['emotion'] == 'hesitant']['pnl'].sum() if 'hesitant' in df['emotion'].values else 0
        
        return {
            'top_emotional_cost': abs(min(fomo_cost, revenge_cost, hesitation_cost)),
            'most_profitable_emotion': df.groupby('emotion')['pnl'].sum().idxmax() if not df['emotion'].isna().all() else None,
            'most_costly_emotion': df.groupby('emotion')['pnl'].sum().idxmin() if not df['emotion'].isna().all() else None,
            'overconfidence_bias': abs(df[df['emotion'] == 'overconfident']['pnl'].sum()) if 'overconfident' in df['emotion'].values else 0,
            'hesitation_cost': abs(hesitation_cost),
            'fomo_impact': fomo_cost,
            'revenge_trading_cost': abs(revenge_cost),
            'confidence_vs_performance_correlation': round(conf_corr, 3) if not pd.isna(conf_corr) else 0,
            'emotional_consistency_score': self._calculate_emotional_consistency(df)
        }
    
    def _calculate_emotional_consistency(self, df: pd.DataFrame) -> float:
        """Calculate how consistent emotional states are with performance"""
        if df.empty or df['emotion'].isna().all():
            return 0.0
        
        # Simple consistency metric: how often positive emotions = positive results
        positive_emotions = ['confident', 'calm', 'focused', 'disciplined']
        negative_emotions = ['anxious', 'fearful', 'frustrated', 'greedy', 'impulsive']
        
        consistent_trades = 0
        total_emotional_trades = 0
        
        for _, row in df.iterrows():
            if pd.notna(row['emotion']):
                total_emotional_trades += 1
                emotion = row['emotion'].lower()
                pnl = row['pnl']
                
                if (emotion in positive_emotions and pnl > 0) or (emotion in negative_emotions and pnl < 0):
                    consistent_trades += 1
        
        return round(consistent_trades / total_emotional_trades * 100, 2) if total_emotional_trades > 0 else 0
    
    def _empty_summary(self) -> AnalyticsSummaryResponse:
        """Return empty summary when no data available"""
        return AnalyticsSummaryResponse(
            total_trades=0,
            total_pnl=0.0,
            overall_win_rate=0.0,
            strategy_stats=[],
            best_strategy=None,
            worst_strategy=None,
            emotion_impact=[],
            trigger_analysis=[],
            confidence_analysis=[],
            emotional_leaks=[],
            top_emotional_cost=0.0,
            most_profitable_emotion=None,
            most_costly_emotion=None,
            overconfidence_bias=0.0,
            hesitation_cost=0.0,
            fomo_impact=0.0,
            revenge_trading_cost=0.0,
            confidence_vs_performance_correlation=0.0,
            emotional_consistency_score=0.0,
            generated_at=datetime.now(),
            period_analyzed="No data available"
        )
    
    async def get_emotion_impact_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get detailed emotion impact analysis"""
        # Implementation for dedicated emotion endpoint
        pass
    
    async def get_strategy_performance_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get detailed strategy performance analysis"""
        # Implementation for dedicated strategy endpoint
        pass
    
    async def get_confidence_performance_correlation(self, user_id: str) -> Dict[str, Any]:
        """Get confidence vs performance correlation analysis"""
        # Implementation for dedicated confidence endpoint
        pass
    
    async def get_timeline_analysis(
        self, 
        user_id: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TimelineResponse:
        """Generate timeline heatmap data with emotional patterns"""
        
        # Default to last 90 days if no dates specified
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        # Get trades in date range
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            func.date(Trade.entry_time) >= start_date,
            func.date(Trade.entry_time) <= end_date
        ).all()
        
        # Get trade notes for emotional data
        notes = self.db.query(TradeNote).filter(
            TradeNote.user_id == user_id,
            func.date(TradeNote.created_at) >= start_date,
            func.date(TradeNote.created_at) <= end_date
        ).all()
        
        # Get daily reflections
        reflections = self.db.query(DailyEmotionReflection).filter(
            DailyEmotionReflection.user_id == user_id,
            DailyEmotionReflection.reflection_date >= start_date,
            DailyEmotionReflection.reflection_date <= end_date
        ).all()
        
        # Group data by date
        daily_data = self._build_daily_timeline_data(trades, notes, reflections, start_date, end_date)
        
        # Calculate summary statistics
        timeline_stats = self._calculate_timeline_stats(daily_data)
        
        return TimelineResponse(
            timeline_data=daily_data,
            date_range={"start_date": start_date, "end_date": end_date},
            total_days=(end_date - start_date).days + 1,
            trading_days=len([d for d in daily_data.values() if d.trade_count > 0]),
            **timeline_stats
        )
    
    def _build_daily_timeline_data(
        self, 
        trades: List[Trade], 
        notes: List[TradeNote], 
        reflections: List[DailyEmotionReflection],
        start_date: date,
        end_date: date
    ) -> Dict[str, DailyTimelineData]:
        """Build daily timeline data structure"""
        
        # Create date range
        current_date = start_date
        daily_data = {}
        
        while current_date <= end_date:
            daily_data[current_date.isoformat()] = DailyTimelineData(
                date=current_date,
                pnl=0.0,
                trade_count=0,
                dominant_emotion=None,
                emotion_emoji=None,
                trades=[],
                mood_score=None,
                reflection_summary=None
            )
            current_date += timedelta(days=1)
        
        # Populate with trade data
        for trade in trades:
            trade_date = trade.entry_time.date()
            date_key = trade_date.isoformat()
            
            if date_key in daily_data:
                daily_data[date_key].pnl += trade.pnl or 0
                daily_data[date_key].trade_count += 1
                daily_data[date_key].trades.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'pnl': trade.pnl,
                    'strategy': trade.strategy_tag,
                    'entry_time': trade.entry_time.isoformat()
                })
        
        # Add emotional data from notes
        emotion_by_date = defaultdict(list)
        for note in notes:
            note_date = note.created_at.date()
            if note.emotion:
                emotion_by_date[note_date].append(note.emotion)
        
        # Determine dominant emotion for each day
        for date_str, day_data in daily_data.items():
            trade_date = datetime.fromisoformat(date_str).date()
            if trade_date in emotion_by_date:
                emotions = emotion_by_date[trade_date]
                if emotions:
                    # Use most common emotion, or first if tie
                    emotion_counts = defaultdict(int)
                    for emotion in emotions:
                        emotion_counts[emotion] += 1
                    day_data.dominant_emotion = max(emotion_counts, key=emotion_counts.get)
                    day_data.emotion_emoji = self._get_emotion_emoji(day_data.dominant_emotion)
        
        # Add reflection data
        for reflection in reflections:
            date_key = reflection.reflection_date.isoformat()
            if date_key in daily_data:
                daily_data[date_key].mood_score = reflection.mood_score
                daily_data[date_key].reflection_summary = reflection.summary
                if reflection.dominant_emotion and not daily_data[date_key].dominant_emotion:
                    daily_data[date_key].dominant_emotion = reflection.dominant_emotion
                    daily_data[date_key].emotion_emoji = self._get_emotion_emoji(reflection.dominant_emotion)
        
        return daily_data
    
    def _get_emotion_emoji(self, emotion: str) -> str:
        """Map emotion to emoji for visual display"""
        emotion_map = {
            'confident': '😎',
            'anxious': '😰',
            'frustrated': '😤',
            'calm': '😌',
            'excited': '🤩',
            'fearful': '😨',
            'greedy': '🤑',
            'disciplined': '🧘',
            'impulsive': '🤪',
            'focused': '🎯',
            'overwhelmed': '😵',
            'optimistic': '😊',
            'pessimistic': '😔',
            'neutral': '😐'
        }
        return emotion_map.get(emotion.lower(), '🤔')
    
    def _calculate_timeline_stats(self, daily_data: Dict[str, DailyTimelineData]) -> Dict[str, Any]:
        """Calculate timeline summary statistics"""
        
        trading_days = [d for d in daily_data.values() if d.trade_count > 0]
        
        if not trading_days:
            return {
                'best_day': None,
                'worst_day': None,
                'emotional_patterns': {}
            }
        
        # Find best and worst days
        best_day = max(trading_days, key=lambda x: x.pnl)
        worst_day = min(trading_days, key=lambda x: x.pnl)
        
        # Emotional patterns
        emotions = [d.dominant_emotion for d in trading_days if d.dominant_emotion]
        emotion_counts = defaultdict(int)
        emotion_pnl = defaultdict(float)
        
        for day in trading_days:
            if day.dominant_emotion:
                emotion_counts[day.dominant_emotion] += 1
                emotion_pnl[day.dominant_emotion] += day.pnl
        
        most_common_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None
        
        # Day of week patterns
        weekday_pnl = defaultdict(list)
        for day in trading_days:
            weekday = day.date.strftime('%A')
            weekday_pnl[weekday].append(day.pnl)
        
        weekday_avg = {
            day: sum(pnls) / len(pnls) 
            for day, pnls in weekday_pnl.items()
        }
        
        best_weekday = max(weekday_avg, key=weekday_avg.get) if weekday_avg else None
        worst_weekday = min(weekday_avg, key=weekday_avg.get) if weekday_avg else None
        
        return {
            'best_day': best_day,
            'worst_day': worst_day,
            'emotional_patterns': {
                'most_common_emotion': most_common_emotion,
                'emotion_frequency': dict(emotion_counts),
                'emotion_profitability': {k: round(v, 2) for k, v in emotion_pnl.items()},
                'best_weekday': best_weekday,
                'worst_weekday': worst_weekday,
                'weekday_performance': {k: round(v, 2) for k, v in weekday_avg.items()}
            }
        }
