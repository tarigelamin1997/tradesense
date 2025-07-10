
"""
Execution Quality Engine - Analyzes trading execution efficiency
"""
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import statistics
import numpy as np
from datetime import datetime, timedelta

from models.trade import Trade
from core.exceptions import NotFoundError


class ExecutionQualityService:
    """Service for analyzing execution quality metrics"""
    
    def __init__(self):
        self.entry_timing_weights = {
            "immediate": 1.0,    # Price moved in favor immediately
            "delayed": 0.7,      # Price moved in favor after delay
            "chased": 0.3        # Price moved against before favor
        }
        
    def analyze_execution_quality(self, user_id: str, db: Session) -> Dict[str, Any]:
        """
        Analyze execution quality for all user trades
        
        Args:
            user_id: User identifier
            db: Database session
            
        Returns:
            Dictionary with execution quality metrics
        """
        trades = db.query(Trade).filter(Trade.user_id == user_id).all()
        
        if not trades:
            return self._empty_execution_metrics()
        
        execution_data = []
        
        for trade in trades:
            if self._is_valid_trade_for_execution_analysis(trade):
                metrics = self._calculate_trade_execution_metrics(trade)
                execution_data.append({
                    "trade_id": trade.id,
                    "symbol": trade.symbol,
                    "entry_time": trade.entry_time,
                    "exit_time": trade.exit_time,
                    "pnl": trade.pnl,
                    **metrics
                })
        
        if not execution_data:
            return self._empty_execution_metrics()
        
        # Calculate aggregate metrics
        summary = self._calculate_execution_summary(execution_data)
        
        return {
            "trade_execution_data": execution_data,
            "execution_summary": summary,
            "insights": self._generate_execution_insights(execution_data),
            "recommendations": self._generate_execution_recommendations(execution_data)
        }
    
    def _calculate_trade_execution_metrics(self, trade: Trade) -> Dict[str, Any]:
        """Calculate execution metrics for a single trade"""
        
        # Entry timing score (0-100)
        entry_score = self._calculate_entry_timing_score(trade)
        
        # Exit quality score (0-100)
        exit_score = self._calculate_exit_quality_score(trade)
        
        # Slippage calculation
        slippage = self._calculate_slippage(trade)
        
        # Regret index (0-1, higher = more regret)
        regret_index = self._calculate_regret_index(trade)
        
        # Composite execution score
        execution_score = self._calculate_composite_execution_score(
            entry_score, exit_score, slippage, regret_index
        )
        
        return {
            "entry_timing_score": round(entry_score, 1),
            "exit_quality_score": round(exit_score, 1),
            "slippage_cost": round(slippage, 4),
            "regret_index": round(regret_index, 3),
            "execution_score": round(execution_score, 1),
            "execution_grade": self._get_execution_grade(execution_score),
            "primary_weakness": self._identify_primary_weakness(
                entry_score, exit_score, slippage, regret_index
            )
        }
    
    def _calculate_entry_timing_score(self, trade: Trade) -> float:
        """
        Calculate entry timing score based on price movement after entry
        Uses MFE/MAE if available, otherwise estimates from price path
        """
        if not trade.entry_price or not trade.exit_price:
            return 50.0  # Neutral score
        
        # If we have MFE data, use it for more accurate scoring
        if trade.max_favorable_excursion and trade.max_adverse_excursion:
            return self._score_entry_with_mfe_mae(trade)
        
        # Fallback: estimate from final outcome
        return self._estimate_entry_score_from_outcome(trade)
    
    def _score_entry_with_mfe_mae(self, trade: Trade) -> float:
        """Score entry timing using MFE/MAE data"""
        entry_price = trade.entry_price
        mfe = trade.max_favorable_excursion
        mae = trade.max_adverse_excursion
        
        # Calculate how quickly trade moved in favor
        # Good entry: MFE >> MAE early in trade
        # Bad entry: Large MAE before MFE
        
        mfe_ratio = abs(mfe) / entry_price if entry_price > 0 else 0
        mae_ratio = abs(mae) / entry_price if entry_price > 0 else 0
        
        if mfe_ratio > mae_ratio * 2:
            # Strong immediate move in favor
            return 85 + min(15, mfe_ratio * 1000)
        elif mfe_ratio > mae_ratio:
            # Moderate favorable move
            return 65 + min(20, mfe_ratio * 500)
        elif mae_ratio > mfe_ratio * 1.5:
            # Poor entry, price moved against first
            return max(20, 50 - mae_ratio * 500)
        else:
            # Neutral entry
            return 50
    
    def _estimate_entry_score_from_outcome(self, trade: Trade) -> float:
        """Estimate entry quality from final outcome"""
        if not trade.pnl or not trade.entry_price:
            return 50.0
        
        # Calculate return percentage
        return_pct = (trade.pnl / (trade.quantity * trade.entry_price)) * 100
        
        # Estimate entry quality based on final return
        # This is a rough approximation
        if return_pct > 2:
            return min(90, 70 + return_pct * 5)
        elif return_pct > 0:
            return 55 + return_pct * 10
        elif return_pct > -1:
            return 45 + return_pct * 10
        else:
            return max(10, 45 + return_pct * 5)
    
    def _calculate_exit_quality_score(self, trade: Trade) -> float:
        """
        Calculate exit quality score based on how close exit was to MFE
        """
        if not trade.max_favorable_excursion or not trade.entry_price or not trade.exit_price:
            return 50.0  # Neutral if no MFE data
        
        direction_multiplier = 1 if trade.direction.lower() == 'long' else -1
        
        # Calculate actual return and maximum possible return
        actual_return = (trade.exit_price - trade.entry_price) * direction_multiplier
        max_possible_return = trade.max_favorable_excursion * direction_multiplier
        
        if max_possible_return <= 0:
            return 50.0  # No favorable excursion
        
        # Calculate how much of the potential was captured
        capture_ratio = actual_return / max_possible_return
        
        if capture_ratio >= 0.9:
            return 95  # Excellent exit near peak
        elif capture_ratio >= 0.7:
            return 80 + (capture_ratio - 0.7) * 75  # Good exit
        elif capture_ratio >= 0.5:
            return 60 + (capture_ratio - 0.5) * 100  # Average exit
        elif capture_ratio >= 0.2:
            return 35 + (capture_ratio - 0.2) * 83  # Poor exit
        else:
            return max(10, 35 * capture_ratio / 0.2)  # Very poor exit
    
    def _calculate_slippage(self, trade: Trade) -> float:
        """
        Calculate slippage cost as percentage of trade value
        Note: This requires order execution data which may not be available
        """
        # Without actual fill vs order price data, we estimate slippage
        # based on trade characteristics
        
        if not trade.entry_price or not trade.quantity:
            return 0.0
        
        # Rough estimate based on trade size and assumed market conditions
        # In real implementation, this would use actual fill prices
        position_value = trade.entry_price * trade.quantity
        
        # Estimate slippage as small percentage (typical retail slippage)
        estimated_slippage = 0.001  # 0.1% typical slippage
        
        # Adjust for trade size (larger trades = more slippage)
        if position_value > 100000:
            estimated_slippage *= 1.5
        elif position_value > 50000:
            estimated_slippage *= 1.2
        
        return estimated_slippage
    
    def _calculate_regret_index(self, trade: Trade) -> float:
        """
        Calculate regret index - how much price moved favorably after exit
        Higher values indicate more "regret" (early exit)
        """
        # Without post-exit price data, we estimate based on available metrics
        # In real implementation, this would track price for period after exit
        
        if not trade.max_favorable_excursion or not trade.pnl or not trade.entry_price:
            return 0.0
        
        # Estimate regret based on how much MFE was left on table
        actual_pnl_pct = (trade.pnl / (trade.quantity * trade.entry_price)) * 100
        mfe_pct = (abs(trade.max_favorable_excursion) / trade.entry_price) * 100
        
        if mfe_pct > actual_pnl_pct:
            regret_ratio = (mfe_pct - actual_pnl_pct) / mfe_pct
            return min(1.0, regret_ratio)
        
        return 0.0
    
    def _calculate_composite_execution_score(self, entry_score: float, exit_score: float, 
                                           slippage: float, regret_index: float) -> float:
        """Calculate weighted composite execution score"""
        
        # Weights for different components
        weights = {
            "entry": 0.3,
            "exit": 0.4,
            "slippage": 0.15,
            "regret": 0.15
        }
        
        # Convert slippage to score (lower slippage = higher score)
        slippage_score = max(0, 100 - (slippage * 10000))  # Convert % to score
        
        # Convert regret to score (lower regret = higher score)
        regret_score = max(0, 100 - (regret_index * 100))
        
        composite_score = (
            entry_score * weights["entry"] +
            exit_score * weights["exit"] +
            slippage_score * weights["slippage"] +
            regret_score * weights["regret"]
        )
        
        return max(0, min(100, composite_score))
    
    def _get_execution_grade(self, score: float) -> str:
        """Convert execution score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        elif score >= 40:
            return "D"
        else:
            return "F"
    
    def _identify_primary_weakness(self, entry_score: float, exit_score: float, 
                                 slippage: float, regret_index: float) -> str:
        """Identify the primary area for improvement"""
        
        scores = {
            "entry_timing": entry_score,
            "exit_quality": exit_score,
            "slippage_control": max(0, 100 - (slippage * 10000)),
            "regret_management": max(0, 100 - (regret_index * 100))
        }
        
        lowest_score = min(scores.values())
        primary_weakness = [k for k, v in scores.items() if v == lowest_score][0]
        
        weakness_messages = {
            "entry_timing": "Entry Timing - Consider waiting for better setups",
            "exit_quality": "Exit Strategy - Work on profit-taking discipline", 
            "slippage_control": "Order Execution - Use limit orders when possible",
            "regret_management": "Exit Timing - Avoid premature exits"
        }
        
        return weakness_messages.get(primary_weakness, "Overall execution needs improvement")
    
    def _calculate_execution_summary(self, execution_data: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics across all trades"""
        
        if not execution_data:
            return {}
        
        # Extract metrics
        entry_scores = [trade["entry_timing_score"] for trade in execution_data]
        exit_scores = [trade["exit_quality_score"] for trade in execution_data]
        execution_scores = [trade["execution_score"] for trade in execution_data]
        regret_indices = [trade["regret_index"] for trade in execution_data]
        
        # Grade distribution
        grades = [trade["execution_grade"] for trade in execution_data]
        grade_counts = {}
        for grade in grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        return {
            "total_trades_analyzed": len(execution_data),
            "average_execution_score": round(statistics.mean(execution_scores), 1),
            "average_entry_score": round(statistics.mean(entry_scores), 1),
            "average_exit_score": round(statistics.mean(exit_scores), 1),
            "average_regret_index": round(statistics.mean(regret_indices), 3),
            "execution_consistency": round(100 - statistics.stdev(execution_scores), 1),
            "grade_distribution": grade_counts,
            "top_quartile_threshold": round(np.percentile(execution_scores, 75), 1),
            "bottom_quartile_threshold": round(np.percentile(execution_scores, 25), 1)
        }
    
    def _generate_execution_insights(self, execution_data: List[Dict]) -> List[str]:
        """Generate actionable insights from execution analysis"""
        
        insights = []
        
        if not execution_data:
            return insights
        
        # Analyze patterns
        entry_scores = [trade["entry_timing_score"] for trade in execution_data]
        exit_scores = [trade["exit_quality_score"] for trade in execution_data]
        execution_scores = [trade["execution_score"] for trade in execution_data]
        
        avg_entry = statistics.mean(entry_scores)
        avg_exit = statistics.mean(exit_scores)
        avg_execution = statistics.mean(execution_scores)
        
        # Entry timing insights
        if avg_entry < 40:
            insights.append("🎯 CRITICAL: Poor entry timing detected. Consider waiting for better confirmation signals.")
        elif avg_entry < 60:
            insights.append("⚠️ Entry timing needs improvement. Focus on patience and setup quality.")
        elif avg_entry > 80:
            insights.append("✅ Excellent entry timing! Your setup recognition is strong.")
        
        # Exit quality insights
        if avg_exit < 40:
            insights.append("🚨 EXIT ISSUE: Consistently poor exit timing. Review profit-taking strategy.")
        elif avg_exit < 60:
            insights.append("📊 Exit strategy needs work. Consider using trailing stops or profit targets.")
        elif avg_exit > 80:
            insights.append("🎯 Strong exit discipline! You're capturing most available profits.")
        
        # Overall execution insights
        if avg_execution > 80:
            insights.append("🏆 EXCELLENT: Your execution quality is in the top tier!")
        elif avg_execution < 50:
            insights.append("⚡ OPPORTUNITY: Significant execution improvements could boost performance.")
        
        # Consistency insights
        score_std = statistics.stdev(execution_scores)
        if score_std > 25:
            insights.append("📈 Inconsistent execution detected. Focus on developing systematic processes.")
        
        return insights
    
    def _generate_execution_recommendations(self, execution_data: List[Dict]) -> List[str]:
        """Generate specific recommendations for execution improvement"""
        
        recommendations = []
        
        if not execution_data:
            return recommendations
        
        # Analyze weaknesses
        entry_scores = [trade["entry_timing_score"] for trade in execution_data]
        exit_scores = [trade["exit_quality_score"] for trade in execution_data]
        regret_indices = [trade["regret_index"] for trade in execution_data]
        
        avg_entry = statistics.mean(entry_scores)
        avg_exit = statistics.mean(exit_scores)
        avg_regret = statistics.mean(regret_indices)
        
        # Entry recommendations
        if avg_entry < 60:
            recommendations.append("📍 ENTRY: Implement entry checklist to avoid chasing momentum")
            recommendations.append("⏰ TIMING: Use limit orders instead of market orders for better fills")
        
        # Exit recommendations
        if avg_exit < 60:
            recommendations.append("🎯 EXIT: Set profit targets at trade entry to avoid emotional exits")
            recommendations.append("📊 STOPS: Use trailing stops to capture more upside while protecting gains")
        
        # Regret management
        if avg_regret > 0.3:
            recommendations.append("⏳ PATIENCE: Consider holding winners longer - you're exiting too early")
            recommendations.append("📈 TARGETS: Increase initial profit targets to capture more of trend moves")
        
        # Process recommendations
        recommendations.append("📝 JOURNAL: Track entry/exit reasons to identify recurring mistakes")
        recommendations.append("🔄 REVIEW: Weekly execution review to reinforce best practices")
        
        return recommendations
    
    def _is_valid_trade_for_execution_analysis(self, trade: Trade) -> bool:
        """Check if trade has sufficient data for execution analysis"""
        return (
            trade.entry_price is not None and
            trade.exit_price is not None and
            trade.entry_time is not None and
            trade.exit_time is not None and
            trade.quantity is not None and
            trade.pnl is not None
        )
    
    def _empty_execution_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "trade_execution_data": [],
            "execution_summary": {
                "total_trades_analyzed": 0,
                "average_execution_score": 0,
                "message": "No trades available for execution analysis"
            },
            "insights": ["No execution data available for analysis"],
            "recommendations": ["Add trades with complete entry/exit data to begin execution analysis"]
        }


def get_execution_quality_analysis(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Get execution quality analysis for user
    
    Args:
        user_id: User identifier
        db: Database session
        
    Returns:
        Execution quality analysis results
    """
    service = ExecutionQualityService()
    return service.analyze_execution_quality(user_id, db)
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics
from uuid import UUID

from models.trade import Trade
from models.playbook import Playbook

class ExecutionQualityService:
    """Service for analyzing trade execution quality"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_execution_quality_analysis(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive execution quality analysis for user"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.exit_price.isnot(None),
            Trade.exit_time.isnot(None)
        ).all()
        
        if not trades:
            raise ValueError("No completed trades found for execution analysis")
        
        # Calculate execution metrics for each trade
        execution_results = []
        for trade in trades:
            metrics = self._calculate_trade_execution_metrics(trade)
            execution_results.append({
                "trade_id": trade.id,
                "symbol": trade.symbol,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "pnl": trade.pnl,
                "direction": trade.direction,
                "playbook_id": trade.playbook_id,
                **metrics
            })
        
        # Generate aggregate insights
        overall_stats = self._calculate_overall_execution_stats(execution_results)
        playbook_analysis = self._analyze_execution_by_playbook(execution_results)
        insights = self._generate_execution_insights(execution_results, overall_stats)
        
        return {
            "total_trades_analyzed": len(execution_results),
            "overall_stats": overall_stats,
            "trade_execution_data": execution_results,
            "playbook_analysis": playbook_analysis,
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_trade_execution_metrics(self, trade: Trade) -> Dict[str, Any]:
        """Calculate execution quality metrics for a single trade"""
        
        # Entry Timing Score (0-100)
        entry_score = self._calculate_entry_timing_score(trade)
        
        # Exit Quality Score (0-100) 
        exit_score = self._calculate_exit_quality_score(trade)
        
        # Slippage Analysis
        slippage = self._calculate_slippage(trade)
        
        # Regret Index (how much the trade moved after exit)
        regret_index = self._calculate_regret_index(trade)
        
        # Holding Efficiency 
        holding_efficiency = self._calculate_holding_efficiency(trade)
        
        # Composite Execution Score
        execution_score = self._calculate_composite_execution_score(
            entry_score, exit_score, slippage, regret_index, holding_efficiency
        )
        
        return {
            "entry_score": entry_score,
            "exit_score": exit_score,
            "slippage": slippage,
            "regret_index": regret_index,
            "holding_efficiency": holding_efficiency,
            "execution_score": execution_score,
            "execution_grade": self._get_execution_grade(execution_score)
        }
    
    def _calculate_entry_timing_score(self, trade: Trade) -> int:
        """Calculate how well the trader timed their entry (0-100)"""
        base_score = 70
        
        # Use MFE to assess if they entered near the optimal point
        if trade.max_favorable_excursion and trade.pnl:
            mfe_ratio = abs(trade.max_favorable_excursion) / abs(trade.pnl) if trade.pnl != 0 else 1
            
            # If MFE is much larger than final PnL, they entered well but exited poorly
            if mfe_ratio > 2:
                base_score += 15  # Good entry timing
            elif mfe_ratio < 0.5:
                base_score -= 20  # Poor entry timing (chased the move)
        
        # Consider direction vs outcome
        if trade.pnl and trade.pnl > 0:
            base_score += 10  # Successful trade suggests good entry
        elif trade.pnl and trade.pnl < 0:
            base_score -= 5   # Loss suggests timing issues
        
        return max(0, min(100, base_score))
    
    def _calculate_exit_quality_score(self, trade: Trade) -> int:
        """Calculate how well the trader timed their exit (0-100)"""
        base_score = 65
        
        if trade.max_favorable_excursion and trade.pnl:
            # Compare final PnL to MFE to see if they captured the move
            if trade.pnl > 0 and trade.max_favorable_excursion > 0:
                capture_ratio = trade.pnl / trade.max_favorable_excursion
                
                if capture_ratio > 0.8:
                    base_score += 25  # Excellent exit - captured most of the move
                elif capture_ratio > 0.5:
                    base_score += 15  # Good exit
                elif capture_ratio > 0.2:
                    base_score += 5   # Mediocre exit
                else:
                    base_score -= 15  # Poor exit - left money on table
            
            # Check if they cut losses appropriately
            if trade.pnl < 0 and trade.max_adverse_excursion:
                loss_ratio = abs(trade.pnl) / abs(trade.max_adverse_excursion) if trade.max_adverse_excursion != 0 else 1
                if loss_ratio < 1.2:
                    base_score += 10  # Cut losses near the worst point
        
        return max(0, min(100, base_score))
    
    def _calculate_slippage(self, trade: Trade) -> float:
        """Calculate estimated slippage (simplified)"""
        # In a real implementation, this would compare expected vs actual fill prices
        # For now, return a placeholder based on trade size and volatility
        if trade.quantity and trade.entry_price:
            estimated_slippage = (trade.quantity * 0.01) / trade.entry_price
            return round(estimated_slippage, 4)
        return 0.0
    
    def _calculate_regret_index(self, trade: Trade) -> float:
        """Calculate how much the trade moved after exit (0-1 scale)"""
        # Simplified regret calculation
        # In practice, you'd need post-exit price data
        if trade.max_favorable_excursion and trade.pnl and trade.pnl > 0:
            # If MFE >> PnL, there was likely more upside after exit
            potential_missed = max(0, trade.max_favorable_excursion - trade.pnl)
            regret = potential_missed / trade.max_favorable_excursion if trade.max_favorable_excursion != 0 else 0
            return round(min(1.0, regret), 3)
        return 0.0
    
    def _calculate_holding_efficiency(self, trade: Trade) -> int:
        """Calculate if holding period was appropriate (0-100)"""
        if not trade.entry_time or not trade.exit_time:
            return 50
        
        holding_time = trade.exit_time - trade.entry_time
        holding_hours = holding_time.total_seconds() / 3600
        
        base_score = 70
        
        # Adjust based on P&L and holding time
        if trade.pnl and trade.pnl > 0:
            # Profitable trades
            if holding_hours < 0.5:
                base_score += 5   # Quick profits are good
            elif holding_hours > 24:
                base_score -= 5   # Very long holds may indicate indecision
        elif trade.pnl and trade.pnl < 0:
            # Losing trades
            if holding_hours < 1:
                base_score += 15  # Cut losses quickly
            elif holding_hours > 8:
                base_score -= 20  # Held losers too long
        
        return max(0, min(100, base_score))
    
    def _calculate_composite_execution_score(self, entry_score: int, exit_score: int, 
                                           slippage: float, regret_index: float, 
                                           holding_efficiency: int) -> int:
        """Calculate weighted composite execution score"""
        # Weighted average of components
        composite = (
            entry_score * 0.25 +
            exit_score * 0.35 +
            holding_efficiency * 0.25 +
            (100 - regret_index * 100) * 0.15  # Lower regret = higher score
        )
        
        # Adjust for slippage
        slippage_penalty = min(10, slippage * 1000)  # Cap penalty at 10 points
        composite -= slippage_penalty
        
        return max(0, min(100, int(composite)))
    
    def _get_execution_grade(self, score: int) -> str:
        """Convert execution score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "F"
    
    def _calculate_overall_execution_stats(self, execution_results: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate execution statistics"""
        if not execution_results:
            return {}
        
        execution_scores = [r["execution_score"] for r in execution_results]
        entry_scores = [r["entry_score"] for r in execution_results]
        exit_scores = [r["exit_score"] for r in execution_results]
        
        return {
            "avg_execution_score": round(statistics.mean(execution_scores), 1),
            "execution_score_std": round(statistics.stdev(execution_scores) if len(execution_scores) > 1 else 0, 1),
            "avg_entry_score": round(statistics.mean(entry_scores), 1),
            "avg_exit_score": round(statistics.mean(exit_scores), 1),
            "excellent_executions": len([s for s in execution_scores if s >= 85]),
            "poor_executions": len([s for s in execution_scores if s < 60]),
            "grade_distribution": self._calculate_grade_distribution(execution_scores)
        }
    
    def _calculate_grade_distribution(self, scores: List[int]) -> Dict[str, int]:
        """Calculate distribution of execution grades"""
        distribution = {"A+": 0, "A": 0, "A-": 0, "B+": 0, "B": 0, "B-": 0, "C+": 0, "C": 0, "C-": 0, "F": 0}
        
        for score in scores:
            grade = self._get_execution_grade(score)
            distribution[grade] += 1
        
        return distribution
    
    def _analyze_execution_by_playbook(self, execution_results: List[Dict]) -> Dict[str, Any]:
        """Analyze execution quality grouped by playbook"""
        playbook_stats = {}
        
        for result in execution_results:
            playbook_id = result.get("playbook_id")
            if not playbook_id:
                continue
            
            if playbook_id not in playbook_stats:
                playbook_stats[playbook_id] = {
                    "trades": [],
                    "total_trades": 0,
                    "avg_execution_score": 0,
                    "avg_pnl": 0,
                    "win_rate": 0
                }
            
            playbook_stats[playbook_id]["trades"].append(result)
            playbook_stats[playbook_id]["total_trades"] += 1
        
        # Calculate stats for each playbook
        for playbook_id, stats in playbook_stats.items():
            trades = stats["trades"]
            execution_scores = [t["execution_score"] for t in trades]
            pnls = [t["pnl"] for t in trades if t["pnl"] is not None]
            
            stats["avg_execution_score"] = round(statistics.mean(execution_scores), 1)
            stats["avg_pnl"] = round(statistics.mean(pnls), 2) if pnls else 0
            stats["win_rate"] = round(len([p for p in pnls if p > 0]) / len(pnls) * 100, 1) if pnls else 0
            
            # Remove trades list from final output
            del stats["trades"]
        
        return playbook_stats
    
    def _generate_execution_insights(self, execution_results: List[Dict], 
                                   overall_stats: Dict[str, Any]) -> List[str]:
        """Generate actionable insights about execution quality"""
        insights = []
        
        if overall_stats.get("avg_execution_score", 0) < 65:
            insights.append("⚠️ Your average execution score is below 65. Focus on improving entry and exit timing.")
        
        if overall_stats.get("poor_executions", 0) > len(execution_results) * 0.3:
            insights.append("🎯 Over 30% of your trades have poor execution scores. Consider reducing trade frequency and focusing on quality setups.")
        
        # Analyze entry vs exit performance
        avg_entry = overall_stats.get("avg_entry_score", 0)
        avg_exit = overall_stats.get("avg_exit_score", 0)
        
        if avg_entry > avg_exit + 10:
            insights.append("💡 Your entries are stronger than your exits. Work on exit discipline and profit-taking strategies.")
        elif avg_exit > avg_entry + 10:
            insights.append("💡 Your exits are stronger than your entries. Focus on better entry timing and setup selection.")
        
        # Find best performing combination
        high_execution_trades = [r for r in execution_results if r["execution_score"] >= 80]
        if high_execution_trades:
            win_rate = len([t for t in high_execution_trades if t["pnl"] and t["pnl"] > 0]) / len(high_execution_trades)
            if win_rate > 0.7:
                insights.append(f"✅ When your execution score is 80+, your win rate is {win_rate:.1%}. Maintain high execution standards.")
        
        return insights
