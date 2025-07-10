
"""
Streak & Consistency Analysis Service for TradeSense

Analyzes trading streaks and consistency patterns to help traders
understand their performance rhythm and make better risk decisions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class StreakAnalyzer:
    """Main streak analysis engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_streaks(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive streak analysis for a trader
        
        Args:
            trades: List of trade dictionaries with required fields
            
        Returns:
            Dictionary with streak metrics and consistency score
        """
        if not trades:
            return self._empty_analysis()
        
        # Group trades by session/day
        sessions = self._group_trades_by_session(trades)
        
        # Calculate session-based streaks
        streak_data = self._calculate_session_streaks(sessions)
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(sessions, trades)
        
        # Get current streak information
        current_streak_info = self._get_current_streak_details(sessions)
        
        return {
            **streak_data,
            "consistency_score": consistency_score,
            "session_breakdown": self._get_session_breakdown(sessions),
            "current_streak_details": current_streak_info,
            "streak_patterns": self._analyze_streak_patterns(sessions),
            "performance_insights": self._generate_insights(streak_data, consistency_score)
        }
    
    def _group_trades_by_session(self, trades: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group trades by trading session/day"""
        sessions = defaultdict(list)
        
        for trade in trades:
            # Use exit_time or entry_time for session grouping
            trade_time = trade.get('exit_time') or trade.get('entry_time')
            if not trade_time:
                continue
                
            # Parse datetime if it's a string
            if isinstance(trade_time, str):
                try:
                    trade_time = datetime.fromisoformat(trade_time.replace('Z', '+00:00'))
                except ValueError:
                    continue
            
            # Group by date
            session_date = trade_time.date().isoformat()
            sessions[session_date].append(trade)
        
        return dict(sessions)
    
    def _calculate_session_streaks(self, sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate win/loss streaks based on session performance"""
        if not sessions:
            return {
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "current_streak": 0,
                "current_streak_type": "none",
                "win_sessions": 0,
                "loss_sessions": 0,
                "neutral_sessions": 0
            }
        
        # Calculate session outcomes
        session_outcomes = []
        sorted_sessions = sorted(sessions.items(), key=lambda x: x[0])  # Sort by date
        
        win_sessions = 0
        loss_sessions = 0
        neutral_sessions = 0
        
        for date, session_trades in sorted_sessions:
            session_pnl = sum(trade.get('pnl', 0) for trade in session_trades)
            
            if session_pnl > 0:
                session_outcomes.append('win')
                win_sessions += 1
            elif session_pnl < 0:
                session_outcomes.append('loss')
                loss_sessions += 1
            else:
                session_outcomes.append('neutral')
                neutral_sessions += 1
        
        # Calculate streaks
        streaks = self._find_streaks(session_outcomes)
        
        return {
            "max_win_streak": streaks["max_win_streak"],
            "max_loss_streak": streaks["max_loss_streak"],
            "current_streak": streaks["current_streak"],
            "current_streak_type": streaks["current_streak_type"],
            "win_sessions": win_sessions,
            "loss_sessions": loss_sessions,
            "neutral_sessions": neutral_sessions,
            "total_sessions": len(session_outcomes)
        }
    
    def _find_streaks(self, outcomes: List[str]) -> Dict[str, Any]:
        """Find streak patterns in session outcomes"""
        if not outcomes:
            return {
                "max_win_streak": 0,
                "max_loss_streak": 0,
                "current_streak": 0,
                "current_streak_type": "none"
            }
        
        max_win_streak = 0
        max_loss_streak = 0
        current_streak = 0
        current_streak_type = "none"
        
        temp_win_streak = 0
        temp_loss_streak = 0
        
        for outcome in outcomes:
            if outcome == 'win':
                temp_win_streak += 1
                temp_loss_streak = 0
                max_win_streak = max(max_win_streak, temp_win_streak)
                current_streak = temp_win_streak
                current_streak_type = "win"
            elif outcome == 'loss':
                temp_loss_streak += 1
                temp_win_streak = 0
                max_loss_streak = max(max_loss_streak, temp_loss_streak)
                current_streak = temp_loss_streak
                current_streak_type = "loss"
            else:  # neutral
                temp_win_streak = 0
                temp_loss_streak = 0
                current_streak = 0
                current_streak_type = "neutral"
        
        return {
            "max_win_streak": max_win_streak,
            "max_loss_streak": max_loss_streak,
            "current_streak": current_streak,
            "current_streak_type": current_streak_type
        }
    
    def _calculate_consistency_score(self, sessions: Dict[str, List[Dict[str, Any]]], trades: List[Dict[str, Any]]) -> float:
        """
        Calculate consistency score (0-100)
        Higher score = more consistent performance
        """
        if not sessions:
            return 0.0
        
        session_pnls = []
        win_count = 0
        total_sessions = len(sessions)
        
        for session_trades in sessions.values():
            session_pnl = sum(trade.get('pnl', 0) for trade in session_trades)
            session_pnls.append(session_pnl)
            if session_pnl > 0:
                win_count += 1
        
        # Base win rate component (0-50 points)
        win_rate = (win_count / total_sessions) if total_sessions > 0 else 0
        base_score = win_rate * 50
        
        # Volatility penalty (0-30 points deduction)
        if len(session_pnls) > 1:
            pnl_std = statistics.stdev(session_pnls)
            pnl_mean = statistics.mean([abs(pnl) for pnl in session_pnls])
            
            if pnl_mean > 0:
                coefficient_of_variation = pnl_std / pnl_mean
                volatility_penalty = min(30, coefficient_of_variation * 20)
            else:
                volatility_penalty = 30
        else:
            volatility_penalty = 0
        
        # Neutral sessions penalty (0-20 points deduction)
        neutral_count = sum(1 for pnl in session_pnls if pnl == 0)
        neutral_penalty = (neutral_count / total_sessions) * 20
        
        # Calculate final score
        consistency_score = base_score - volatility_penalty - neutral_penalty + 50  # Add 50 for second half
        
        return max(0, min(100, consistency_score))
    
    def _get_current_streak_details(self, sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Get detailed information about current streak"""
        if not sessions:
            return {"status": "No trading sessions", "recommendation": "Start trading to build streak data"}
        
        sorted_sessions = sorted(sessions.items(), key=lambda x: x[0], reverse=True)
        latest_session = sorted_sessions[0]
        latest_pnl = sum(trade.get('pnl', 0) for trade in latest_session[1])
        
        # Determine current streak status and recommendation
        if latest_pnl > 0:
            status = f"🔥 Currently on a winning streak"
            recommendation = "Consider maintaining position sizes or slight increase if confidence is high"
        elif latest_pnl < 0:
            status = f"⛔️ Currently on a losing streak"
            recommendation = "Consider reducing position sizes and reviewing strategy"
        else:
            status = f"➖ Last session was neutral"
            recommendation = "Monitor next few trades carefully for direction"
        
        return {
            "status": status,
            "recommendation": recommendation,
            "latest_session_pnl": latest_pnl,
            "latest_session_date": latest_session[0]
        }
    
    def _get_session_breakdown(self, sessions: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Get detailed breakdown of each session"""
        breakdown = []
        
        for date, session_trades in sorted(sessions.items()):
            session_pnl = sum(trade.get('pnl', 0) for trade in session_trades)
            trade_count = len(session_trades)
            
            outcome = "win" if session_pnl > 0 else ("loss" if session_pnl < 0 else "neutral")
            
            breakdown.append({
                "date": date,
                "pnl": session_pnl,
                "trade_count": trade_count,
                "outcome": outcome,
                "avg_trade_pnl": session_pnl / trade_count if trade_count > 0 else 0
            })
        
        return breakdown
    
    def _analyze_streak_patterns(self, sessions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze patterns in streaks"""
        if not sessions:
            return {}
        
        session_outcomes = []
        sorted_sessions = sorted(sessions.items(), key=lambda x: x[0])
        
        for date, session_trades in sorted_sessions:
            session_pnl = sum(trade.get('pnl', 0) for trade in session_trades)
            session_outcomes.append('win' if session_pnl > 0 else ('loss' if session_pnl < 0 else 'neutral'))
        
        # Find all streaks
        streaks = []
        current_type = None
        current_length = 0
        
        for outcome in session_outcomes:
            if outcome == current_type:
                current_length += 1
            else:
                if current_type is not None:
                    streaks.append({"type": current_type, "length": current_length})
                current_type = outcome
                current_length = 1
        
        # Add the final streak
        if current_type is not None:
            streaks.append({"type": current_type, "length": current_length})
        
        # Analyze streak patterns
        win_streaks = [s["length"] for s in streaks if s["type"] == "win"]
        loss_streaks = [s["length"] for s in streaks if s["type"] == "loss"]
        
        return {
            "avg_win_streak_length": statistics.mean(win_streaks) if win_streaks else 0,
            "avg_loss_streak_length": statistics.mean(loss_streaks) if loss_streaks else 0,
            "total_streaks": len(streaks),
            "longest_overall_streak": max(s["length"] for s in streaks) if streaks else 0
        }
    
    def _generate_insights(self, streak_data: Dict[str, Any], consistency_score: float) -> List[str]:
        """Generate actionable insights based on streak analysis"""
        insights = []
        
        # Consistency insights
        if consistency_score >= 90:
            insights.append("🎯 Rock-solid performer: Your consistency is exceptional")
        elif consistency_score >= 60:
            insights.append("✅ Generally consistent: Good overall performance with room for improvement")
        elif consistency_score >= 30:
            insights.append("⚠️ Volatile performance: Focus on risk management and strategy refinement")
        else:
            insights.append("🚨 Highly erratic: Consider reducing position sizes and reviewing your edge")
        
        # Streak insights
        max_loss_streak = streak_data.get("max_loss_streak", 0)
        if max_loss_streak >= 5:
            insights.append(f"📉 Watch out: Your max loss streak is {max_loss_streak} sessions - implement circuit breakers")
        
        current_streak_type = streak_data.get("current_streak_type", "none")
        current_streak = streak_data.get("current_streak", 0)
        
        if current_streak_type == "win" and current_streak >= 3:
            insights.append(f"🔥 Hot streak detected: {current_streak} winning sessions - consider slight size increase")
        elif current_streak_type == "loss" and current_streak >= 3:
            insights.append(f"❄️ Cold streak: {current_streak} losing sessions - reduce size and reassess")
        
        return insights
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            "max_win_streak": 0,
            "max_loss_streak": 0,
            "current_streak": 0,
            "current_streak_type": "none",
            "win_sessions": 0,
            "loss_sessions": 0,
            "neutral_sessions": 0,
            "total_sessions": 0,
            "consistency_score": 0,
            "session_breakdown": [],
            "current_streak_details": {
                "status": "No data available",
                "recommendation": "Upload trades to start analysis"
            },
            "streak_patterns": {},
            "performance_insights": ["No trading data available for analysis"]
        }


# Global analyzer instance
streak_analyzer = StreakAnalyzer()
