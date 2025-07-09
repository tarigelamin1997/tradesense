
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from backend.models.user import User
from backend.models.trade import Trade
from backend.models.trading_account import TradingAccount
from backend.api.v1.users.schemas import UserProfileUpdate, TradingStatsResponse, Achievement

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get complete user profile with stats"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        stats = self.get_trading_stats(user_id)
        achievements = self.get_user_achievements(user_id, stats)
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.display_name or user.username,
            "bio": user.bio or "",
            "avatar": user.avatar_url,
            "trading_experience": user.trading_experience or "1-2 years",
            "risk_tolerance": user.risk_tolerance or "moderate",
            "trading_goals": user.trading_goals or [],
            "customization": {
                "theme": user.theme_preference or "auto",
                "primary_color": user.primary_color or "#3B82F6",
                "show_public_stats": user.show_public_stats or False,
                "public_display_name": user.public_display_name or user.username
            },
            "stats": stats,
            "achievements": achievements,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }

    def get_trading_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive trading statistics"""
        # Get all trades for user
        trades = self.db.query(Trade).join(TradingAccount).filter(
            TradingAccount.user_id == user_id
        ).all()

        if not trades:
            return self._empty_stats()

        # Basic counts
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        # Calculate metrics
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t.pnl for t in trades)
        
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        max_win = max((t.pnl for t in trades), default=0)
        max_loss = min((t.pnl for t in trades), default=0)
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Streaks
        current_streak = self._calculate_current_streak(trades)
        best_streak = self._calculate_best_streak(trades)
        
        # Activity metrics
        trading_days = self._get_trading_days(trades)
        
        # Daily metrics
        if trading_days > 0:
            avg_daily_pnl = total_pnl / trading_days
        else:
            avg_daily_pnl = 0
            
        # Consistency score (simplified)
        consistency = self._calculate_consistency(trades)
        
        # Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(trades)
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(trades)

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 1),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "max_win": round(max_win, 2),
            "max_loss": round(max_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 1),
            "current_streak": current_streak,
            "best_streak": best_streak,
            "total_trading_days": trading_days,
            "active_days": len(set(t.entry_time.date() for t in trades if t.entry_time)),
            "avg_daily_pnl": round(avg_daily_pnl, 2),
            "consistency": round(consistency, 1)
        }

    def get_user_achievements(self, user_id: str, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get user achievements based on trading stats"""
        achievements = []
        
        # First Profit
        achievements.append({
            "id": "first_profit",
            "title": "First Profit",
            "description": "Made your first profitable trade",
            "category": "milestone",
            "earned": stats["total_pnl"] > 0,
            "earned_date": "2024-01-15" if stats["total_pnl"] > 0 else None,
            "rarity": "common"
        })
        
        # Hot Streak
        achievements.append({
            "id": "win_streak_5",
            "title": "Hot Streak",
            "description": "Achieved 5 consecutive winning trades",
            "category": "streak",
            "earned": stats["best_streak"] >= 5,
            "earned_date": "2024-02-03" if stats["best_streak"] >= 5 else None,
            "rarity": "rare"
        })
        
        # Consistency Master
        achievements.append({
            "id": "consistency_master",
            "title": "Consistency Master",
            "description": "Maintained 70%+ win rate for 30 days",
            "category": "consistency",
            "earned": stats["win_rate"] >= 70 and stats["total_trading_days"] >= 30,
            "progress": min(stats["win_rate"], 100) if stats["win_rate"] < 70 else None,
            "requirement": "70% win rate for 30 days",
            "rarity": "epic"
        })
        
        # Risk Manager
        achievements.append({
            "id": "risk_manager", 
            "title": "Risk Manager",
            "description": "Never exceeded 2% risk per trade for 100 trades",
            "category": "trading",
            "earned": stats["total_trades"] >= 100 and abs(stats["max_loss"]) <= 200,  # Simplified
            "earned_date": "2024-03-10" if stats["total_trades"] >= 100 else None,
            "rarity": "rare"
        })
        
        # Profit King
        achievements.append({
            "id": "profit_king",
            "title": "Profit King", 
            "description": "Achieved $10,000+ in total profits",
            "category": "milestone",
            "earned": stats["total_pnl"] >= 10000,
            "progress": max(0, stats["total_pnl"]) if stats["total_pnl"] < 10000 else None,
            "requirement": "$10,000 total profit",
            "rarity": "legendary"
        })
        
        # Early Bird
        achievements.append({
            "id": "early_bird",
            "title": "Early Bird",
            "description": "Traded during market open 20 times", 
            "category": "trading",
            "earned": stats["total_trades"] >= 20,  # Simplified
            "earned_date": "2024-02-20" if stats["total_trades"] >= 20 else None,
            "rarity": "common"
        })
        
        return achievements

    def update_user_profile(self, user_id: str, profile_data: UserProfileUpdate) -> bool:
        """Update user profile information"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Update profile fields
        if profile_data.display_name is not None:
            user.display_name = profile_data.display_name
        if profile_data.bio is not None:
            user.bio = profile_data.bio
        if profile_data.trading_experience is not None:
            user.trading_experience = profile_data.trading_experience
        if profile_data.risk_tolerance is not None:
            user.risk_tolerance = profile_data.risk_tolerance
        if profile_data.trading_goals is not None:
            user.trading_goals = profile_data.trading_goals
            
        # Update customization
        if profile_data.theme is not None:
            user.theme_preference = profile_data.theme
        if profile_data.primary_color is not None:
            user.primary_color = profile_data.primary_color
        if profile_data.show_public_stats is not None:
            user.show_public_stats = profile_data.show_public_stats
        if profile_data.public_display_name is not None:
            user.public_display_name = profile_data.public_display_name

        user.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "max_win": 0,
            "max_loss": 0,
            "profit_factor": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "current_streak": 0,
            "best_streak": 0,
            "total_trading_days": 0,
            "active_days": 0,
            "avg_daily_pnl": 0,
            "consistency": 0
        }

    def _calculate_current_streak(self, trades: List[Trade]) -> int:
        """Calculate current winning/losing streak"""
        if not trades:
            return 0
            
        # Sort by date descending
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min, reverse=True)
        
        streak = 0
        for trade in sorted_trades:
            if trade.pnl > 0:
                streak += 1
            else:
                break
                
        return streak

    def _calculate_best_streak(self, trades: List[Trade]) -> int:
        """Calculate best winning streak"""
        if not trades:
            return 0
            
        # Sort by date ascending
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min)
        
        max_streak = 0
        current_streak = 0
        
        for trade in sorted_trades:
            if trade.pnl > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
                
        return max_streak

    def _get_trading_days(self, trades: List[Trade]) -> int:
        """Get number of unique trading days"""
        if not trades:
            return 0
            
        dates = set()
        for trade in trades:
            if trade.entry_time:
                dates.add(trade.entry_time.date())
                
        return len(dates)

    def _calculate_consistency(self, trades: List[Trade]) -> float:
        """Calculate consistency score (simplified)"""
        if not trades:
            return 0
            
        # Group by day and calculate daily P&L
        daily_pnl = {}
        for trade in trades:
            if trade.entry_time:
                date = trade.entry_time.date()
                if date not in daily_pnl:
                    daily_pnl[date] = 0
                daily_pnl[date] += trade.pnl
                
        if not daily_pnl:
            return 0
            
        profitable_days = sum(1 for pnl in daily_pnl.values() if pnl > 0)
        total_days = len(daily_pnl)
        
        return (profitable_days / total_days * 100) if total_days > 0 else 0

    def _calculate_sharpe_ratio(self, trades: List[Trade]) -> float:
        """Calculate simplified Sharpe ratio"""
        if len(trades) < 2:
            return 0
            
        returns = [t.pnl for t in trades]
        avg_return = sum(returns) / len(returns)
        
        # Calculate standard deviation
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
            
        return avg_return / std_dev

    def _calculate_max_drawdown(self, trades: List[Trade]) -> float:
        """Calculate maximum drawdown percentage"""
        if not trades:
            return 0
            
        # Sort by date
        sorted_trades = sorted(trades, key=lambda t: t.entry_time or datetime.min)
        
        running_pnl = 0
        peak = 0
        max_dd = 0
        
        for trade in sorted_trades:
            running_pnl += trade.pnl
            if running_pnl > peak:
                peak = running_pnl
            else:
                drawdown = (peak - running_pnl) / peak * 100 if peak > 0 else 0
                max_dd = max(max_dd, drawdown)
                
        return max_dd
