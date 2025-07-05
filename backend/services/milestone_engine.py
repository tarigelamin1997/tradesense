"""
Milestone Engine Service for TradeSense
Tracks user progress, achievements, and gamification elements
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from sqlalchemy.orm import Session
from models.milestone import Milestone, MilestoneCreate, UserProgress
from backend.models.trade import Trade

logger = logging.getLogger(__name__)

class MilestoneEngine:
    """Service for tracking milestones and gamification"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # Milestone definitions
        self.milestone_definitions = {
            "journaling": {
                "first_trade_logged": {
                    "title": "First Steps",
                    "description": "Logged your first trade! Every journey begins with a single step.",
                    "xp": 50,
                    "icon": "📝",
                    "rarity": "common"
                },
                "journal_streak_7": {
                    "title": "Week Warrior",
                    "description": "Completed 7 consecutive days of trade journaling",
                    "xp": 200,
                    "icon": "🔥",
                    "rarity": "rare"
                },
                "journal_streak_30": {
                    "title": "Month Master",
                    "description": "Maintained a 30-day journaling streak",
                    "xp": 1000,
                    "icon": "👑",
                    "rarity": "epic"
                },
                "trades_logged_50": {
                    "title": "Data Collector",
                    "description": "Logged 50 trades with detailed notes",
                    "xp": 300,
                    "icon": "📊",
                    "rarity": "rare"
                },
                "trades_logged_100": {
                    "title": "Analysis Expert",
                    "description": "Reached 100 logged trades",
                    "xp": 500,
                    "icon": "🎯",
                    "rarity": "epic"
                }
            },
            "performance": {
                "win_streak_5": {
                    "title": "Hot Streak",
                    "description": "Achieved 5 winning trades in a row",
                    "xp": 150,
                    "icon": "🚀",
                    "rarity": "rare"
                },
                "win_streak_10": {
                    "title": "On Fire",
                    "description": "Dominated with 10 consecutive wins",
                    "xp": 500,
                    "icon": "🔥",
                    "rarity": "epic"
                },
                "positive_month": {
                    "title": "Monthly Winner",
                    "description": "Finished the month with positive P&L",
                    "xp": 200,
                    "icon": "📈",
                    "rarity": "rare"
                },
                "recovery_hero": {
                    "title": "Recovery Hero",
                    "description": "Bounced back from 5+ loss streak with a win",
                    "xp": 300,
                    "icon": "💪",
                    "rarity": "epic"
                }
            },
            "discipline": {
                "no_revenge_trades": {
                    "title": "Disciplined Mind",
                    "description": "20 trades without revenge trading patterns",
                    "xp": 400,
                    "icon": "🧘",
                    "rarity": "epic"
                },
                "stop_loss_champion": {
                    "title": "Risk Manager",
                    "description": "Used stop losses on 20 consecutive trades",
                    "xp": 250,
                    "icon": "🛡️",
                    "rarity": "rare"
                },
                "daily_limit_respect": {
                    "title": "Boundary Keeper",
                    "description": "Respected daily loss limits for 10 sessions",
                    "xp": 300,
                    "icon": "⚖️",
                    "rarity": "rare"
                },
                "size_consistency": {
                    "title": "Position Master",
                    "description": "Maintained consistent position sizing for 25 trades",
                    "xp": 200,
                    "icon": "📏",
                    "rarity": "rare"
                }
            },
            "analytics": {
                "first_report": {
                    "title": "Data Explorer",
                    "description": "Generated your first analytics report",
                    "xp": 100,
                    "icon": "🔍",
                    "rarity": "common"
                },
                "streak_analyzer": {
                    "title": "Pattern Hunter",
                    "description": "Used streak analysis to identify trading patterns",
                    "xp": 150,
                    "icon": "🎯",
                    "rarity": "rare"
                },
                "edge_strength_master": {
                    "title": "Edge Detective",
                    "description": "Analyzed edge strength across 5 different strategies",
                    "xp": 300,
                    "icon": "🔬",
                    "rarity": "epic"
                },
                "consistency_expert": {
                    "title": "Consistency Expert",
                    "description": "Achieved 'Healthy' consistency rating for 30 days",
                    "xp": 500,
                    "icon": "💎",
                    "rarity": "legendary"
                }
            }
        }
        
        # XP levels
        self.level_thresholds = [
            0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5200,
            6600, 8200, 10000, 12000, 14500, 17500, 21000, 25000, 30000, 36000
        ]
    
    def check_and_award_milestones(self, user_id: str, trigger_type: str, context: Dict[str, Any]) -> List[Milestone]:
        """Check for milestone achievements and award them"""
        awarded_milestones = []
        
        # Get user's existing milestones to avoid duplicates
        existing_milestones = self.db.query(Milestone).filter(
            Milestone.user_id == user_id
        ).all()
        existing_types = {m.type for m in existing_milestones}
        
        # Check different milestone categories based on trigger
        if trigger_type == "trade_logged":
            awarded_milestones.extend(self._check_journaling_milestones(user_id, existing_types, context))
        elif trigger_type == "trade_completed":
            awarded_milestones.extend(self._check_performance_milestones(user_id, existing_types, context))
        elif trigger_type == "analytics_used":
            awarded_milestones.extend(self._check_analytics_milestones(user_id, existing_types, context))
        elif trigger_type == "discipline_check":
            awarded_milestones.extend(self._check_discipline_milestones(user_id, existing_types, context))
        
        # Save awarded milestones
        for milestone in awarded_milestones:
            self.db.add(milestone)
        
        if awarded_milestones:
            self.db.commit()
            logger.info(f"Awarded {len(awarded_milestones)} milestones to user {user_id}")
        
        return awarded_milestones
    
    def _check_journaling_milestones(self, user_id: str, existing_types: set, context: Dict) -> List[Milestone]:
        """Check journaling-related milestones"""
        milestones = []
        
        # Get trade count
        trade_count = self.db.query(Trade).filter(Trade.user_id == user_id).count()
        
        # First trade logged
        if "first_trade_logged" not in existing_types and trade_count == 1:
            milestones.append(self._create_milestone(user_id, "first_trade_logged", "journaling", trade_count))
        
        # Trade count milestones
        if "trades_logged_50" not in existing_types and trade_count >= 50:
            milestones.append(self._create_milestone(user_id, "trades_logged_50", "journaling", trade_count))
        
        if "trades_logged_100" not in existing_types and trade_count >= 100:
            milestones.append(self._create_milestone(user_id, "trades_logged_100", "journaling", trade_count))
        
        # Check journaling streak
        streak_days = self._calculate_journaling_streak(user_id)
        if "journal_streak_7" not in existing_types and streak_days >= 7:
            milestones.append(self._create_milestone(user_id, "journal_streak_7", "journaling", streak_days))
        
        if "journal_streak_30" not in existing_types and streak_days >= 30:
            milestones.append(self._create_milestone(user_id, "journal_streak_30", "journaling", streak_days))
        
        return milestones
    
    def _check_performance_milestones(self, user_id: str, existing_types: set, context: Dict) -> List[Milestone]:
        """Check performance-related milestones"""
        milestones = []
        
        # Get recent trades for streak analysis
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.pnl.isnot(None)
        ).order_by(Trade.entry_time.desc()).limit(50).all()
        
        if not trades:
            return milestones
        
        # Calculate current win streak
        current_win_streak = 0
        for trade in trades:
            if trade.pnl > 0:
                current_win_streak += 1
            else:
                break
        
        # Win streak milestones
        if "win_streak_5" not in existing_types and current_win_streak >= 5:
            milestones.append(self._create_milestone(user_id, "win_streak_5", "performance", current_win_streak))
        
        if "win_streak_10" not in existing_types and current_win_streak >= 10:
            milestones.append(self._create_milestone(user_id, "win_streak_10", "performance", current_win_streak))
        
        # Recovery from loss streak
        if current_win_streak >= 1:  # Just won a trade
            loss_streak_before = 0
            for trade in trades[1:]:  # Skip the winning trade
                if trade.pnl <= 0:
                    loss_streak_before += 1
                else:
                    break
            
            if "recovery_hero" not in existing_types and loss_streak_before >= 5:
                milestones.append(self._create_milestone(user_id, "recovery_hero", "performance", loss_streak_before))
        
        # Monthly performance check
        if "positive_month" not in existing_types:
            monthly_pnl = self._calculate_current_month_pnl(user_id)
            if monthly_pnl > 0:
                milestones.append(self._create_milestone(user_id, "positive_month", "performance", monthly_pnl))
        
        return milestones
    
    def _check_analytics_milestones(self, user_id: str, existing_types: set, context: Dict) -> List[Milestone]:
        """Check analytics usage milestones"""
        milestones = []
        
        # First analytics report
        if "first_report" not in existing_types:
            milestones.append(self._create_milestone(user_id, "first_report", "analytics", 1))
        
        # Specific analytics features used
        analytics_type = context.get("analytics_type", "")
        
        if "streak_analyzer" not in existing_types and analytics_type == "streak":
            milestones.append(self._create_milestone(user_id, "streak_analyzer", "analytics", 1))
        
        if "edge_strength_master" not in existing_types and analytics_type == "edge_strength":
            strategy_count = len(context.get("strategies_analyzed", []))
            if strategy_count >= 5:
                milestones.append(self._create_milestone(user_id, "edge_strength_master", "analytics", strategy_count))
        
        return milestones
    
    def _check_discipline_milestones(self, user_id: str, existing_types: set, context: Dict) -> List[Milestone]:
        """Check discipline-related milestones"""
        milestones = []
        
        # Analyze recent trades for discipline patterns
        recent_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id
        ).order_by(Trade.entry_time.desc()).limit(25).all()
        
        if len(recent_trades) < 20:
            return milestones
        
        # Check for revenge trading patterns (based on tags)
        revenge_trades = 0
        for trade in recent_trades[:20]:
            if trade.tags and 'revenge' in [tag.lower() for tag in trade.tags]:
                revenge_trades += 1
        
        if "no_revenge_trades" not in existing_types and revenge_trades == 0:
            milestones.append(self._create_milestone(user_id, "no_revenge_trades", "discipline", 20))
        
        # Position size consistency
        if len(recent_trades) >= 25:
            quantities = [trade.quantity for trade in recent_trades[:25]]
            avg_qty = sum(quantities) / len(quantities)
            consistency = all(abs(qty - avg_qty) / avg_qty < 0.2 for qty in quantities)  # Within 20%
            
            if "size_consistency" not in existing_types and consistency:
                milestones.append(self._create_milestone(user_id, "size_consistency", "discipline", 25))
        
        return milestones
    
    def _create_milestone(self, user_id: str, milestone_type: str, category: str, value: float) -> Milestone:
        """Create a milestone instance"""
        definition = self.milestone_definitions[category][milestone_type]
        
        return Milestone(
            user_id=user_id,
            type=milestone_type,
            category=category,
            title=definition["title"],
            description=definition["description"],
            value=value,
            xp_points=definition["xp"],
            badge_icon=definition["icon"],
            rarity=definition["rarity"],
            metadata={"awarded_for": value}
        )
    
    def _calculate_journaling_streak(self, user_id: str) -> int:
        """Calculate current journaling streak in days"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id
        ).order_by(Trade.entry_time.desc()).all()
        
        if not trades:
            return 0
        
        # Group trades by date
        trade_dates = set()
        for trade in trades:
            trade_dates.add(trade.entry_time.date())
        
        # Calculate consecutive days from today backwards
        current_date = datetime.now().date()
        streak = 0
        
        while current_date in trade_dates:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak
    
    def _calculate_current_month_pnl(self, user_id: str) -> float:
        """Calculate P&L for current month"""
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.entry_time >= month_start,
            Trade.pnl.isnot(None)
        ).all()
        
        return sum(trade.pnl for trade in trades)
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get comprehensive user progress and gamification data"""
        # Get all milestones
        milestones = self.db.query(Milestone).filter(
            Milestone.user_id == user_id
        ).order_by(Milestone.achieved_at.desc()).all()
        
        # Calculate totals
        total_xp = sum(m.xp_points for m in milestones)
        total_milestones = len(milestones)
        
        # Calculate level
        level = self._calculate_level(total_xp)
        level_progress, xp_to_next = self._calculate_level_progress(total_xp, level)
        
        # Recent milestones (last 5)
        recent_milestones = milestones[:5]
        
        # Category progress
        category_progress = self._calculate_category_progress(milestones)
        
        # Active streaks
        active_streaks = self._calculate_active_streaks(user_id)
        
        return UserProgress(
            total_xp=total_xp,
            total_milestones=total_milestones,
            level=level,
            level_progress=level_progress,
            xp_to_next_level=xp_to_next,
            recent_milestones=recent_milestones,
            category_progress=category_progress,
            active_streaks=active_streaks
        )
    
    def _calculate_level(self, total_xp: float) -> int:
        """Calculate user level based on XP"""
        for i, threshold in enumerate(self.level_thresholds):
            if total_xp < threshold:
                return max(0, i - 1)
        return len(self.level_thresholds) - 1
    
    def _calculate_level_progress(self, total_xp: float, level: int) -> tuple:
        """Calculate progress to next level"""
        if level >= len(self.level_thresholds) - 1:
            return 100.0, 0.0
        
        current_threshold = self.level_thresholds[level] if level >= 0 else 0
        next_threshold = self.level_thresholds[level + 1]
        
        xp_in_level = total_xp - current_threshold
        xp_needed = next_threshold - current_threshold
        
        progress = (xp_in_level / xp_needed) * 100 if xp_needed > 0 else 100
        xp_to_next = next_threshold - total_xp
        
        return min(progress, 100), max(xp_to_next, 0)
    
    def _calculate_category_progress(self, milestones: List[Milestone]) -> Dict[str, Dict[str, Any]]:
        """Calculate progress by category"""
        categories = defaultdict(lambda: {"count": 0, "xp": 0, "recent": None})
        
        for milestone in milestones:
            cat = categories[milestone.category]
            cat["count"] += 1
            cat["xp"] += milestone.xp_points
            if cat["recent"] is None or milestone.achieved_at > cat["recent"]:
                cat["recent"] = milestone.achieved_at
        
        return dict(categories)
    
    def _calculate_active_streaks(self, user_id: str) -> Dict[str, int]:
        """Calculate current active streaks"""
        return {
            "journaling_days": self._calculate_journaling_streak(user_id),
            "win_streak": self._calculate_current_win_streak(user_id),
            "discipline_streak": self._calculate_discipline_streak(user_id)
        }
    
    def _calculate_current_win_streak(self, user_id: str) -> int:
        """Calculate current win streak"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.pnl.isnot(None)
        ).order_by(Trade.entry_time.desc()).limit(20).all()
        
        streak = 0
        for trade in trades:
            if trade.pnl > 0:
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_discipline_streak(self, user_id: str) -> int:
        """Calculate days without emotional trading"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id
        ).order_by(Trade.entry_time.desc()).limit(50).all()
        
        emotional_tags = {'fomo', 'revenge', 'impulsive', 'greedy', 'fearful'}
        
        streak = 0
        trade_dates = set()
        
        for trade in trades:
            trade_date = trade.entry_time.date()
            if trade_date in trade_dates:
                continue
            trade_dates.add(trade_date)
            
            # Check if trade has emotional tags
            has_emotional_tags = False
            if trade.tags:
                trade_tags = {tag.lower() for tag in trade.tags}
                has_emotional_tags = bool(trade_tags & emotional_tags)
            
            if not has_emotional_tags:
                streak += 1
            else:
                break
        
        return streak
