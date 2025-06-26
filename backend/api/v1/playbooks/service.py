
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd

from backend.models.playbook import Playbook, PlaybookCreate, PlaybookUpdate, PlaybookAnalytics
from backend.models.trade import Trade

class PlaybookService:
    def __init__(self, db: Session):
        self.db = db

    def create_playbook(self, user_id: str, playbook_data: PlaybookCreate) -> Playbook:
        """Create a new playbook"""
        playbook = Playbook(
            user_id=user_id,
            **playbook_data.dict()
        )
        self.db.add(playbook)
        self.db.commit()
        self.db.refresh(playbook)
        return playbook

    def get_playbooks(
        self,
        user_id: str,
        status: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50
    ) -> List[Playbook]:
        """Get user's playbooks with filters and sorting"""
        query = self.db.query(Playbook).filter(Playbook.user_id == user_id)
        
        if status:
            query = query.filter(Playbook.status == status)
        
        # Apply sorting
        if sort_by == "name":
            sort_col = Playbook.name
        elif sort_by == "total_pnl":
            sort_col = func.cast(Playbook.total_pnl, float)
        elif sort_by == "win_rate":
            sort_col = func.cast(Playbook.win_rate, float)
        elif sort_by == "created_at":
            sort_col = Playbook.created_at
        else:
            sort_col = Playbook.name
        
        if sort_order == "desc":
            query = query.order_by(desc(sort_col))
        else:
            query = query.order_by(asc(sort_col))
        
        return query.limit(limit).all()

    def get_playbook(self, playbook_id: str, user_id: str) -> Optional[Playbook]:
        """Get a specific playbook"""
        return self.db.query(Playbook).filter(
            and_(Playbook.id == playbook_id, Playbook.user_id == user_id)
        ).first()

    def update_playbook(
        self, playbook_id: str, user_id: str, playbook_data: PlaybookUpdate
    ) -> Optional[Playbook]:
        """Update a playbook"""
        playbook = self.get_playbook(playbook_id, user_id)
        if not playbook:
            return None
        
        update_data = playbook_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(playbook, field, value)
        
        playbook.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(playbook)
        return playbook

    def delete_playbook(self, playbook_id: str, user_id: str) -> bool:
        """Delete a playbook (hard delete)"""
        playbook = self.get_playbook(playbook_id, user_id)
        if not playbook:
            return False
        
        # Unlink trades first
        self.db.query(Trade).filter(Trade.playbook_id == playbook_id).update(
            {"playbook_id": None}
        )
        
        self.db.delete(playbook)
        self.db.commit()
        return True

    def archive_playbook(self, playbook_id: str, user_id: str) -> bool:
        """Archive a playbook (soft delete)"""
        playbook = self.get_playbook(playbook_id, user_id)
        if not playbook:
            return False
        
        playbook.status = "archived"
        playbook.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def activate_playbook(self, playbook_id: str, user_id: str) -> bool:
        """Reactivate an archived playbook"""
        playbook = self.get_playbook(playbook_id, user_id)
        if not playbook:
            return False
        
        playbook.status = "active"
        playbook.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_playbook_trades(
        self, playbook_id: str, user_id: str, limit: int = 50
    ) -> Optional[List[Dict[str, Any]]]:
        """Get all trades for a specific playbook"""
        playbook = self.get_playbook(playbook_id, user_id)
        if not playbook:
            return None
        
        trades = self.db.query(Trade).filter(
            and_(Trade.playbook_id == playbook_id, Trade.user_id == user_id)
        ).order_by(desc(Trade.entry_time)).limit(limit).all()
        
        trade_data = []
        for trade in trades:
            trade_data.append({
                'id': trade.id,
                'symbol': trade.symbol,
                'direction': trade.direction,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'pnl': trade.pnl,
                'quantity': trade.quantity,
                'confidence_score': trade.confidence_score,
                'notes': trade.notes
            })
        
        return trade_data

    def calculate_sharpe_ratio(self, pnl_series: List[float]) -> float:
        """Calculate Sharpe ratio for a series of PnL values"""
        if len(pnl_series) < 2:
            return 0.0
        
        returns = np.array(pnl_series)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # Assuming risk-free rate of 0 for simplicity
        sharpe = mean_return / std_return
        return round(sharpe * np.sqrt(252), 2)  # Annualized

    def calculate_max_drawdown(self, pnl_series: List[float]) -> float:
        """Calculate maximum drawdown from PnL series"""
        if not pnl_series:
            return 0.0
        
        cumulative = np.cumsum(pnl_series)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        return round(np.max(drawdown), 2)

    def calculate_sortino_ratio(self, pnl_series: List[float]) -> float:
        """Calculate Sortino ratio (downside deviation version of Sharpe)"""
        if len(pnl_series) < 2:
            return 0.0
        
        returns = np.array(pnl_series)
        mean_return = np.mean(returns)
        
        # Calculate downside deviation (only negative returns)
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return float('inf') if mean_return > 0 else 0.0
        
        downside_deviation = np.std(negative_returns)
        if downside_deviation == 0:
            return 0.0
        
        sortino = mean_return / downside_deviation
        return round(sortino * np.sqrt(252), 2)  # Annualized

    def analyze_confidence_trend(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analyze how confidence scores correlate with performance"""
        if not trades:
            return {"trend": "insufficient_data", "correlation": 0.0}
        
        confidence_data = []
        pnl_data = []
        
        for trade in trades:
            if trade.get('confidence_score') and trade.get('pnl') is not None:
                confidence_data.append(trade['confidence_score'])
                pnl_data.append(trade['pnl'])
        
        if len(confidence_data) < 3:
            return {"trend": "insufficient_data", "correlation": 0.0}
        
        # Calculate correlation between confidence and PnL
        correlation = np.corrcoef(confidence_data, pnl_data)[0, 1]
        if np.isnan(correlation):
            correlation = 0.0
        
        # Determine trend
        if correlation > 0.3:
            trend = "positive_correlation"
        elif correlation < -0.3:
            trend = "negative_correlation"
        else:
            trend = "no_clear_correlation"
        
        return {
            "trend": trend,
            "correlation": round(correlation, 3),
            "avg_confidence": round(np.mean(confidence_data), 1),
            "confidence_range": [round(min(confidence_data), 1), round(max(confidence_data), 1)]
        }

    def analyze_time_performance(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analyze performance by day of week and hour"""
        if not trades:
            return {}
        
        day_performance = {}
        hour_performance = {}
        
        for trade in trades:
            if trade.get('entry_time') and trade.get('pnl') is not None:
                entry_time = trade['entry_time']
                pnl = trade['pnl']
                
                # Day of week analysis
                day_name = entry_time.strftime('%A')
                if day_name not in day_performance:
                    day_performance[day_name] = []
                day_performance[day_name].append(pnl)
                
                # Hour analysis
                hour = entry_time.hour
                if hour not in hour_performance:
                    hour_performance[hour] = []
                hour_performance[hour].append(pnl)
        
        # Calculate averages
        day_stats = {}
        for day, pnls in day_performance.items():
            day_stats[day] = {
                "avg_pnl": round(np.mean(pnls), 2),
                "trade_count": len(pnls),
                "win_rate": round(len([p for p in pnls if p > 0]) / len(pnls) * 100, 1)
            }
        
        hour_stats = {}
        for hour, pnls in hour_performance.items():
            hour_stats[str(hour)] = {
                "avg_pnl": round(np.mean(pnls), 2),
                "trade_count": len(pnls),
                "win_rate": round(len([p for p in pnls if p > 0]) / len(pnls) * 100, 1)
            }
        
        # Find best performing times
        best_day = max(day_stats.items(), key=lambda x: x[1]['avg_pnl'])[0] if day_stats else None
        best_hour = max(hour_stats.items(), key=lambda x: x[1]['avg_pnl'])[0] if hour_stats else None
        
        return {
            "day_performance": day_stats,
            "hour_performance": hour_stats,
            "best_day": best_day,
            "best_hour": int(best_hour) if best_hour else None
        }

    def calculate_risk_reward_ratio(self, trades: List[Dict]) -> float:
        """Calculate average risk/reward ratio"""
        winners = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
        losers = [abs(t['pnl']) for t in trades if t.get('pnl', 0) < 0]
        
        if not winners or not losers:
            return 0.0
        
        avg_win = np.mean(winners)
        avg_loss = np.mean(losers)
        
        return round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0

    def get_playbook_optimization_summary(self, user_id: str) -> List[Dict[str, Any]]:
        """
        PLAYBOOK OPTIMIZATION ENGINE
        Analyze all playbooks and return comprehensive performance metrics
        """
        # Get all active playbooks for user
        playbooks = self.db.query(Playbook).filter(
            and_(Playbook.user_id == user_id, Playbook.status == "active")
        ).all()
        
        optimization_results = []
        
        for playbook in playbooks:
            # Get all trades for this playbook
            trades_query = self.db.query(Trade).filter(
                and_(Trade.playbook_id == playbook.id, Trade.user_id == user_id)
            ).order_by(Trade.entry_time).all()
            
            if not trades_query:
                continue  # Skip playbooks with no trades
            
            # Convert to dict for analysis
            trades = []
            for trade in trades_query:
                trades.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'direction': trade.direction,
                    'entry_time': trade.entry_time,
                    'exit_time': trade.exit_time,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'pnl': trade.pnl or 0,
                    'quantity': trade.quantity,
                    'confidence_score': trade.confidence_score,
                    'notes': trade.notes
                })
            
            # Filter completed trades (with PnL)
            completed_trades = [t for t in trades if t['pnl'] is not None]
            
            if len(completed_trades) < 5:  # Need minimum trades for meaningful analysis
                continue
            
            # Calculate core metrics
            total_trades = len(completed_trades)
            pnl_values = [t['pnl'] for t in completed_trades]
            winning_trades = [t for t in completed_trades if t['pnl'] > 0]
            losing_trades = [t for t in completed_trades if t['pnl'] < 0]
            
            # Basic performance metrics
            win_rate = len(winning_trades) / total_trades * 100
            total_pnl = sum(pnl_values)
            avg_pnl = total_pnl / total_trades
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
            
            # Advanced metrics
            sharpe_ratio = self.calculate_sharpe_ratio(pnl_values)
            sortino_ratio = self.calculate_sortino_ratio(pnl_values)
            max_drawdown = self.calculate_max_drawdown(pnl_values)
            risk_reward_ratio = self.calculate_risk_reward_ratio(completed_trades)
            
            # Profit factor
            gross_profit = sum([t['pnl'] for t in winning_trades])
            gross_loss = abs(sum([t['pnl'] for t in losing_trades]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Confidence analysis
            confidence_analysis = self.analyze_confidence_trend(completed_trades)
            
            # Time-based performance
            time_analysis = self.analyze_time_performance(completed_trades)
            
            # Calculate streaks
            win_streak = 0
            loss_streak = 0
            current_win_streak = 0
            current_loss_streak = 0
            max_win_streak = 0
            max_loss_streak = 0
            
            for trade in completed_trades:
                if trade['pnl'] > 0:
                    current_win_streak += 1
                    current_loss_streak = 0
                    max_win_streak = max(max_win_streak, current_win_streak)
                else:
                    current_loss_streak += 1
                    current_win_streak = 0
                    max_loss_streak = max(max_loss_streak, current_loss_streak)
            
            # Generate recommendation
            recommendation = self.generate_playbook_recommendation(
                win_rate, avg_pnl, sharpe_ratio, max_drawdown, total_trades, profit_factor
            )
            
            # Performance score (0-100)
            performance_score = self.calculate_performance_score(
                win_rate, sharpe_ratio, profit_factor, max_drawdown, total_trades
            )
            
            optimization_result = {
                "playbook_id": str(playbook.id),
                "playbook_name": playbook.name,
                "total_trades": total_trades,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "max_drawdown": max_drawdown,
                "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else 999,
                "risk_reward_ratio": risk_reward_ratio,
                "max_win_streak": max_win_streak,
                "max_loss_streak": max_loss_streak,
                "confidence_analysis": confidence_analysis,
                "time_analysis": time_analysis,
                "recommendation": recommendation,
                "performance_score": performance_score,
                "created_at": playbook.created_at.isoformat(),
                "last_trade_date": max([t['entry_time'] for t in completed_trades]).isoformat()
            }
            
            optimization_results.append(optimization_result)
        
        # Sort by performance score (highest first)
        optimization_results.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return optimization_results

    def generate_playbook_recommendation(self, win_rate: float, avg_pnl: float, 
                                       sharpe_ratio: float, max_drawdown: float, 
                                       total_trades: int, profit_factor: float) -> Dict[str, str]:
        """Generate actionable recommendations for a playbook"""
        
        if total_trades < 10:
            return {
                "action": "gather_more_data",
                "message": "Need more trades (at least 10) for reliable analysis",
                "priority": "low"
            }
        
        # High-performing playbook
        if win_rate >= 60 and sharpe_ratio >= 1.5 and avg_pnl > 0 and profit_factor >= 1.5:
            return {
                "action": "focus_and_scale",
                "message": "Excellent performance! Focus more trades on this strategy and consider increasing position size",
                "priority": "high"
            }
        
        # Good playbook with room for improvement
        elif win_rate >= 50 and avg_pnl > 0 and sharpe_ratio >= 1.0:
            return {
                "action": "optimize_and_refine",
                "message": "Good performance. Consider refining entry/exit criteria or risk management",
                "priority": "medium"
            }
        
        # High drawdown warning
        elif max_drawdown > abs(avg_pnl * total_trades * 0.3):  # Drawdown > 30% of total profit
            return {
                "action": "improve_risk_management",
                "message": "High drawdown detected. Review position sizing and stop-loss levels",
                "priority": "high"
            }
        
        # Low win rate but profitable
        elif win_rate < 40 and avg_pnl > 0:
            return {
                "action": "improve_win_rate",
                "message": "Profitable but low win rate. Consider tighter entry criteria or earlier exits",
                "priority": "medium"
            }
        
        # Consistently losing
        elif avg_pnl < 0 or profit_factor < 1.0:
            return {
                "action": "consider_retiring",
                "message": "Consistently unprofitable. Consider retiring or major strategy overhaul",
                "priority": "high"
            }
        
        # Default
        else:
            return {
                "action": "monitor_closely",
                "message": "Mixed performance. Continue monitoring and look for improvement opportunities",
                "priority": "medium"
            }

    def calculate_performance_score(self, win_rate: float, sharpe_ratio: float, 
                                  profit_factor: float, max_drawdown: float, 
                                  total_trades: int) -> int:
        """Calculate a composite performance score (0-100)"""
        score = 0
        
        # Win rate component (0-25 points)
        score += min(25, win_rate * 0.4)
        
        # Sharpe ratio component (0-25 points)
        score += min(25, max(0, sharpe_ratio * 12.5))
        
        # Profit factor component (0-25 points)
        if profit_factor >= 999:  # Handle infinity
            score += 25
        else:
            score += min(25, max(0, (profit_factor - 1) * 12.5))
        
        # Drawdown penalty (0-25 points, but negative impact)
        if max_drawdown > 0:
            # Penalize high drawdowns more severely
            drawdown_penalty = min(25, max_drawdown / 100 * 25)
            score += max(0, 25 - drawdown_penalty)
        else:
            score += 25
        
        # Sample size bonus/penalty
        if total_trades >= 50:
            score += 5  # Bonus for large sample
        elif total_trades < 10:
            score *= 0.8  # Penalty for small sample
        
        return max(0, min(100, int(score)))

    def get_playbook_session_heatmap(self, user_id: str) -> Dict[str, Any]:
        """Generate heatmap data showing playbook performance by trading session"""
        playbooks = self.db.query(Playbook).filter(
            and_(Playbook.user_id == user_id, Playbook.status == "active")
        ).all()
        
        # Define trading sessions (in UTC hours)
        sessions = {
            "Sydney": (22, 7),      # 22:00 - 07:00 UTC
            "Tokyo": (0, 9),        # 00:00 - 09:00 UTC  
            "London": (8, 17),      # 08:00 - 17:00 UTC
            "New_York": (13, 22)    # 13:00 - 22:00 UTC
        }
        
        heatmap_data = []
        
        for playbook in playbooks:
            trades = self.db.query(Trade).filter(
                and_(Trade.playbook_id == playbook.id, Trade.pnl.isnot(None))
            ).all()
            
            if not trades:
                continue
            
            playbook_sessions = {}
            
            for session_name, (start_hour, end_hour) in sessions.items():
                session_trades = []
                
                for trade in trades:
                    hour = trade.entry_time.hour
                    
                    # Handle sessions that cross midnight
                    if start_hour > end_hour:  # Cross midnight
                        if hour >= start_hour or hour <= end_hour:
                            session_trades.append(trade.pnl)
                    else:  # Normal session
                        if start_hour <= hour <= end_hour:
                            session_trades.append(trade.pnl)
                
                if session_trades:
                    avg_pnl = sum(session_trades) / len(session_trades)
                    win_rate = len([p for p in session_trades if p > 0]) / len(session_trades) * 100
                    
                    playbook_sessions[session_name] = {
                        "avg_pnl": round(avg_pnl, 2),
                        "win_rate": round(win_rate, 1),
                        "trade_count": len(session_trades),
                        "total_pnl": round(sum(session_trades), 2)
                    }
                else:
                    playbook_sessions[session_name] = {
                        "avg_pnl": 0,
                        "win_rate": 0,
                        "trade_count": 0,
                        "total_pnl": 0
                    }
            
            heatmap_data.append({
                "playbook_id": str(playbook.id),
                "playbook_name": playbook.name,
                "sessions": playbook_sessions
            })
        
        return {
            "heatmap_data": heatmap_data,
            "sessions": list(sessions.keys()),
            "generated_at": datetime.utcnow().isoformat()
        }

    # Keep existing methods...
    def calculate_playbook_stats(self, playbook_id: str) -> Dict[str, Any]:
        """Calculate performance statistics for a playbook"""
        trades = self.db.query(Trade).filter(Trade.playbook_id == playbook_id).all()
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0,
                'best_win': 0.0,
                'worst_loss': 0.0,
                'avg_hold_time_minutes': 0.0,
                'consecutive_wins': 0,
                'consecutive_losses': 0
            }
        
        # Calculate basic stats
        completed_trades = [t for t in trades if t.pnl is not None]
        total_trades = len(completed_trades)
        
        if total_trades == 0:
            return {
                'total_trades': len(trades),
                'win_rate': 0.0,
                'avg_pnl': 0.0,
                'total_pnl': 0.0,
                'best_win': 0.0,
                'worst_loss': 0.0,
                'avg_hold_time_minutes': 0.0,
                'consecutive_wins': 0,
                'consecutive_losses': 0
            }
        
        pnls = [t.pnl for t in completed_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
        avg_pnl = sum(pnls) / total_trades
        total_pnl = sum(pnls)
        best_win = max(pnls) if pnls else 0.0
        worst_loss = min(pnls) if pnls else 0.0
        
        # Calculate hold time
        hold_times = []
        for trade in completed_trades:
            if trade.entry_time and trade.exit_time:
                delta = trade.exit_time - trade.entry_time
                hold_times.append(delta.total_seconds() / 60)  # in minutes
        
        avg_hold_time = sum(hold_times) / len(hold_times) if hold_times else 0.0
        
        # Calculate streaks
        consecutive_wins = 0
        consecutive_losses = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_win_streak += 1
                current_loss_streak = 0
                consecutive_wins = max(consecutive_wins, current_win_streak)
            else:
                current_loss_streak += 1
                current_win_streak = 0
                consecutive_losses = max(consecutive_losses, current_loss_streak)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'best_win': best_win,
            'worst_loss': worst_loss,
            'avg_hold_time_minutes': avg_hold_time,
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses
        }

    def get_recommendation(self, stats: Dict[str, Any]) -> str:
        """Generate recommendation based on playbook performance"""
        if stats['total_trades'] < 10:
            return "insufficient_data"
        
        win_rate = stats['win_rate']
        avg_pnl = stats['avg_pnl']
        total_pnl = stats['total_pnl']
        
        if win_rate >= 0.6 and avg_pnl > 0 and total_pnl > 0:
            return "focus_more"
        elif win_rate >= 0.45 and avg_pnl > 0:
            return "keep_current"
        elif win_rate < 0.4 or avg_pnl < 0:
            return "cut_play"
        else:
            return "reduce_size"

    def get_performance_trend(self, playbook_id: str) -> str:
        """Analyze performance trend for a playbook"""
        # Get last 20 trades
        recent_trades = self.db.query(Trade).filter(
            Trade.playbook_id == playbook_id
        ).order_by(desc(Trade.entry_time)).limit(20).all()
        
        if len(recent_trades) < 10:
            return "insufficient_data"
        
        # Split into first half and second half
        mid_point = len(recent_trades) // 2
        first_half = recent_trades[mid_point:]  # Older trades
        second_half = recent_trades[:mid_point]  # Newer trades
        
        first_avg = sum([t.pnl for t in first_half if t.pnl]) / len([t for t in first_half if t.pnl])
        second_avg = sum([t.pnl for t in second_half if t.pnl]) / len([t for t in second_half if t.pnl])
        
        if second_avg > first_avg * 1.1:
            return "improving"
        elif second_avg < first_avg * 0.9:
            return "declining"
        else:
            return "stable"

    def get_playbook_analytics(
        self, user_id: str, min_trades: int = 5, include_archived: bool = False
    ) -> List[PlaybookAnalytics]:
        """Get comprehensive analytics for all playbooks"""
        query = self.db.query(Playbook).filter(Playbook.user_id == user_id)
        
        if not include_archived:
            query = query.filter(Playbook.status == "active")
        
        playbooks = query.all()
        analytics = []
        
        for playbook in playbooks:
            stats = self.calculate_playbook_stats(playbook.id)
            
            if stats['total_trades'] >= min_trades:
                recommendation = self.get_recommendation(stats)
                trend = self.get_performance_trend(playbook.id)
                
                analytics.append(PlaybookAnalytics(
                    id=playbook.id,
                    name=playbook.name,
                    total_trades=stats['total_trades'],
                    win_rate=stats['win_rate'],
                    avg_pnl=stats['avg_pnl'],
                    total_pnl=stats['total_pnl'],
                    avg_hold_time_minutes=stats['avg_hold_time_minutes'],
                    best_win=stats['best_win'],
                    worst_loss=stats['worst_loss'],
                    consecutive_wins=stats['consecutive_wins'],
                    consecutive_losses=stats['consecutive_losses'],
                    recommendation=recommendation,
                    performance_trend=trend
                ))
        
        # Sort by total PnL descending
        analytics.sort(key=lambda x: x.total_pnl, reverse=True)
        return analytics

    def refresh_all_playbook_stats(self, user_id: str):
        """Refresh cached statistics for all user playbooks"""
        playbooks = self.db.query(Playbook).filter(Playbook.user_id == user_id).all()
        
        for playbook in playbooks:
            stats = self.calculate_playbook_stats(playbook.id)
            
            # Update cached stats
            playbook.total_trades = str(stats['total_trades'])
            playbook.win_rate = str(round(stats['win_rate'], 3))
            playbook.avg_pnl = str(round(stats['avg_pnl'], 2))
            playbook.total_pnl = str(round(stats['total_pnl'], 2))
            playbook.updated_at = datetime.utcnow()
        
        self.db.commit()
