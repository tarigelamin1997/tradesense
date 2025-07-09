
"""
Behavioral Analytics Service for TradeSense
Analyzes trading behavior, streaks, consistency, and emotional patterns
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class BehavioralAnalyticsService:
    """Service for analyzing trading behavior and patterns"""
    
    def __init__(self):
        self.emotional_tags = {
            'fomo', 'revenge', 'overconfident', 'rushed', 'anxious', 
            'greedy', 'fearful', 'impulsive', 'frustrated'
        }
    
    def analyze_behavioral_patterns(self, trades_data: List[Dict]) -> Dict[str, Any]:
        """
        Comprehensive behavioral analysis of trading data
        """
        if not trades_data:
            return self._empty_behavioral_metrics()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(trades_data)
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce').fillna(0)
        
        # Sort by entry time for streak analysis
        df = df.sort_values('entry_time').reset_index(drop=True)
        
        # Calculate all behavioral metrics
        streaks = self._calculate_streaks(df)
        consistency = self._analyze_consistency(df)
        emotional_patterns = self._analyze_emotional_patterns(df)
        trading_frequency = self._analyze_trading_frequency(df)
        
        # Determine overall consistency rating
        consistency_rating = self._calculate_consistency_rating(
            consistency, emotional_patterns, trading_frequency
        )
        
        return {
            "streaks": streaks,
            "consistency_rating": consistency_rating,
            "max_win_streak": streaks.get("max_win_streak", 0),
            "max_loss_streak": streaks.get("max_loss_streak", 0),
            "current_streak": streaks.get("current_streak", {"type": "none", "count": 0}),
            "average_trades_per_day": trading_frequency.get("avg_trades_per_day", 0),
            "days_with_no_trades": trading_frequency.get("days_with_no_trades", 0),
            "total_trading_days": trading_frequency.get("total_trading_days", 0),
            "emotional_indicators": emotional_patterns,
            "discipline_score": consistency.get("discipline_score", 0),
            "volume_consistency": consistency.get("volume_consistency", "unknown"),
            "timing_patterns": self._analyze_timing_patterns(df),
            "behavioral_flags": self._identify_behavioral_flags(df, emotional_patterns)
        }
    
    def _calculate_streaks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate win/loss streaks"""
        if df.empty:
            return {"max_win_streak": 0, "max_loss_streak": 0, "current_streak": {"type": "none", "count": 0}}
        
        # Create win/loss indicators
        df['is_winner'] = df['pnl'] > 0
        
        streaks = []
        current_streak_type = df['is_winner'].iloc[0]
        current_streak_count = 1
        
        for i in range(1, len(df)):
            if df['is_winner'].iloc[i] == current_streak_type:
                current_streak_count += 1
            else:
                streaks.append({
                    'type': 'win' if current_streak_type else 'loss',
                    'count': current_streak_count
                })
                current_streak_type = df['is_winner'].iloc[i]
                current_streak_count = 1
        
        # Add the final streak
        streaks.append({
            'type': 'win' if current_streak_type else 'loss',
            'count': current_streak_count
        })
        
        # Calculate max streaks
        win_streaks = [s['count'] for s in streaks if s['type'] == 'win']
        loss_streaks = [s['count'] for s in streaks if s['type'] == 'loss']
        
        max_win_streak = max(win_streaks) if win_streaks else 0
        max_loss_streak = max(loss_streaks) if loss_streaks else 0
        
        # Current streak
        current_streak = streaks[-1] if streaks else {"type": "none", "count": 0}
        
        return {
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
            "current_streak": current_streak,
            "all_streaks": streaks,
            "total_streak_periods": len(streaks)
        }
    
    def _analyze_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading consistency patterns"""
        if df.empty:
            return {"discipline_score": 0, "volume_consistency": "unknown"}
        
        # Volume consistency (quantity analysis)
        quantities = df['quantity'].dropna()
        if len(quantities) > 1:
            cv_quantity = quantities.std() / quantities.mean() if quantities.mean() > 0 else float('inf')
            volume_consistency = self._classify_volume_consistency(cv_quantity)
        else:
            volume_consistency = "insufficient_data"
        
        # Discipline score based on multiple factors
        discipline_factors = []
        
        # Factor 1: Position sizing consistency
        if len(quantities) > 1:
            discipline_factors.append(min(1.0, 1.0 / (cv_quantity + 0.1)))
        
        # Factor 2: P&L distribution (avoiding extreme outliers)
        pnl_values = df['pnl'].dropna()
        if len(pnl_values) > 2:
            pnl_cv = abs(pnl_values.std() / pnl_values.mean()) if pnl_values.mean() != 0 else float('inf')
            discipline_factors.append(min(1.0, 1.0 / (pnl_cv * 0.1 + 0.1)))
        
        # Factor 3: Trading frequency regularity
        daily_counts = df.groupby(df['entry_time'].dt.date).size()
        if len(daily_counts) > 1:
            freq_cv = daily_counts.std() / daily_counts.mean()
            discipline_factors.append(min(1.0, 1.0 / (freq_cv + 0.1)))
        
        discipline_score = sum(discipline_factors) / len(discipline_factors) if discipline_factors else 0
        
        return {
            "discipline_score": round(discipline_score * 100, 1),  # Convert to 0-100 scale
            "volume_consistency": volume_consistency,
            "position_size_cv": round(cv_quantity, 3) if 'cv_quantity' in locals() else None
        }
    
    def _analyze_emotional_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze emotional trading patterns from tags"""
        emotional_indicators = {
            'fomo_trades': 0,
            'revenge_trades': 0,
            'emotional_tag_count': 0,
            'most_common_emotional_tag': None,
            'emotional_impact_on_pnl': 0
        }
        
        if df.empty or 'tags' not in df.columns:
            return emotional_indicators
        
        emotional_trades = []
        all_emotional_tags = []
        
        for _, trade in df.iterrows():
            trade_tags = trade.get('tags', [])
            if isinstance(trade_tags, list):
                trade_emotional_tags = [tag.lower() for tag in trade_tags if tag.lower() in self.emotional_tags]
                
                if trade_emotional_tags:
                    emotional_trades.append({
                        'pnl': trade['pnl'],
                        'tags': trade_emotional_tags
                    })
                    all_emotional_tags.extend(trade_emotional_tags)
                    
                    # Count specific patterns
                    if 'fomo' in trade_emotional_tags:
                        emotional_indicators['fomo_trades'] += 1
                    if 'revenge' in trade_emotional_tags:
                        emotional_indicators['revenge_trades'] += 1
        
        emotional_indicators['emotional_tag_count'] = len(all_emotional_tags)
        
        # Most common emotional tag
        if all_emotional_tags:
            tag_counts = defaultdict(int)
            for tag in all_emotional_tags:
                tag_counts[tag] += 1
            emotional_indicators['most_common_emotional_tag'] = max(tag_counts, key=tag_counts.get)
        
        # Emotional impact on P&L
        if emotional_trades:
            emotional_pnl = sum(trade['pnl'] for trade in emotional_trades)
            total_pnl = df['pnl'].sum()
            emotional_indicators['emotional_impact_on_pnl'] = round(
                (emotional_pnl / total_pnl * 100) if total_pnl != 0 else 0, 2
            )
        
        return emotional_indicators
    
    def _analyze_trading_frequency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading frequency patterns"""
        if df.empty:
            return {
                'avg_trades_per_day': 0,
                'days_with_no_trades': 0,
                'total_trading_days': 0
            }
        
        # Group by date
        daily_trades = df.groupby(df['entry_time'].dt.date).size()
        
        # Calculate date range
        start_date = df['entry_time'].min().date()
        end_date = df['entry_time'].max().date()
        total_days = (end_date - start_date).days + 1
        
        trading_days = len(daily_trades)
        days_with_no_trades = total_days - trading_days
        avg_trades_per_day = len(df) / total_days if total_days > 0 else 0
        
        return {
            'avg_trades_per_day': round(avg_trades_per_day, 2),
            'days_with_no_trades': days_with_no_trades,
            'total_trading_days': trading_days,
            'total_calendar_days': total_days,
            'max_trades_in_day': daily_trades.max() if not daily_trades.empty else 0
        }
    
    def _analyze_timing_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze timing patterns in trading"""
        if df.empty:
            return {}
        
        df['hour'] = df['entry_time'].dt.hour
        df['day_of_week'] = df['entry_time'].dt.day_name()
        
        # Find most active trading hours
        hourly_counts = df['hour'].value_counts()
        daily_counts = df['day_of_week'].value_counts()
        
        return {
            'most_active_hour': int(hourly_counts.index[0]) if not hourly_counts.empty else None,
            'most_active_day': daily_counts.index[0] if not daily_counts.empty else None,
            'trading_session_concentration': round(hourly_counts.max() / len(df) * 100, 1) if len(df) > 0 else 0
        }
    
    def _calculate_consistency_rating(self, consistency: Dict, emotional_patterns: Dict, frequency: Dict) -> str:
        """Calculate overall consistency rating"""
        discipline_score = consistency.get('discipline_score', 0)
        emotional_impact = abs(emotional_patterns.get('emotional_impact_on_pnl', 0))
        days_no_trades = frequency.get('days_with_no_trades', 0)
        total_days = frequency.get('total_calendar_days', 1)
        
        # Calculate gaps ratio
        gap_ratio = days_no_trades / total_days if total_days > 0 else 1
        
        # Rating logic
        if discipline_score >= 80 and emotional_impact < 10 and gap_ratio < 0.3:
            return "Perfect"
        elif discipline_score >= 60 and emotional_impact < 20 and gap_ratio < 0.5:
            return "Healthy"
        elif discipline_score >= 40 and emotional_impact < 30 and gap_ratio < 0.7:
            return "Inconsistent"
        else:
            return "Erratic"
    
    def _identify_behavioral_flags(self, df: pd.DataFrame, emotional_patterns: Dict) -> List[str]:
        """Identify concerning behavioral patterns"""
        flags = []
        
        if emotional_patterns.get('fomo_trades', 0) > len(df) * 0.2:
            flags.append("High FOMO trading detected")
        
        if emotional_patterns.get('revenge_trades', 0) > 0:
            flags.append("Revenge trading pattern detected")
        
        if emotional_patterns.get('emotional_impact_on_pnl', 0) < -20:
            flags.append("Emotional trades significantly hurting performance")
        
        # Check for overtrading patterns
        daily_trades = df.groupby(df['entry_time'].dt.date).size()
        if not daily_trades.empty and daily_trades.max() > 20:
            flags.append("Potential overtrading detected")
        
        return flags
    
    def _classify_volume_consistency(self, cv: float) -> str:
        """Classify volume consistency based on coefficient of variation"""
        if cv < 0.2:
            return "Very Consistent"
        elif cv < 0.5:
            return "Consistent"
        elif cv < 1.0:
            return "Moderate"
        else:
            return "Highly Variable"
    
    def _empty_behavioral_metrics(self) -> Dict[str, Any]:
        """Return empty behavioral metrics for no data case"""
        return {
            "streaks": {"max_win_streak": 0, "max_loss_streak": 0, "current_streak": {"type": "none", "count": 0}},
            "consistency_rating": "Insufficient Data",
            "max_win_streak": 0,
            "max_loss_streak": 0,
            "current_streak": {"type": "none", "count": 0},
            "average_trades_per_day": 0,
            "days_with_no_trades": 0,
            "total_trading_days": 0,
            "emotional_indicators": {},
            "discipline_score": 0,
            "volume_consistency": "unknown",
            "timing_patterns": {},
            "behavioral_flags": []
        }
