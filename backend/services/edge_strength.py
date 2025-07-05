"""
Edge Strength Analytics Service
Analyzes strategy performance and calculates edge strength scores
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from collections import defaultdict

from backend.models.trade import Trade
from backend.analytics.performance import calculate_win_rate, calculate_profit_factor
from backend.analytics.equity import calculate_max_drawdown


class EdgeStrengthService:
    """Service for calculating strategy edge strength metrics"""
    
    def __init__(self):
        self.minimum_trades_threshold = 10  # Minimum trades for reliable stats
        
    def calculate_edge_strength(self, trades: List[Trade]) -> Dict[str, Any]:
        """
        Calculate edge strength metrics for all strategies
        
        Args:
            trades: List of trade objects
            
        Returns:
            Dictionary with strategy performance metrics
        """
        if not trades:
            return {"strategies": {}, "summary": self._empty_summary()}
        
        # Group trades by strategy
        strategy_groups = self._group_trades_by_strategy(trades)
        
        strategy_metrics = {}
        all_strategies_summary = {
            "total_strategies": len(strategy_groups),
            "profitable_strategies": 0,
            "strong_edge_strategies": 0,
            "weak_edge_strategies": 0,
            "best_strategy": None,
            "worst_strategy": None,
            "total_trades_analyzed": len(trades)
        }
        
        best_edge_score = 0
        worst_edge_score = 100
        
        for strategy, strategy_trades in strategy_groups.items():
            if len(strategy_trades) < self.minimum_trades_threshold:
                continue
                
            metrics = self._calculate_strategy_metrics(strategy_trades)
            strategy_metrics[strategy] = metrics
            
            # Update summary stats
            if metrics["total_pnl"] > 0:
                all_strategies_summary["profitable_strategies"] += 1
            
            if metrics["edge_strength"] >= 70:
                all_strategies_summary["strong_edge_strategies"] += 1
            elif metrics["edge_strength"] <= 40:
                all_strategies_summary["weak_edge_strategies"] += 1
            
            # Track best/worst strategies
            if metrics["edge_strength"] > best_edge_score:
                best_edge_score = metrics["edge_strength"]
                all_strategies_summary["best_strategy"] = strategy
                
            if metrics["edge_strength"] < worst_edge_score:
                worst_edge_score = metrics["edge_strength"]
                all_strategies_summary["worst_strategy"] = strategy
        
        return {
            "strategies": strategy_metrics,
            "summary": all_strategies_summary,
            "generated_at": datetime.now().isoformat()
        }
    
    def _group_trades_by_strategy(self, trades: List[Trade]) -> Dict[str, List[Trade]]:
        """Group trades by strategy tag"""
        strategy_groups = defaultdict(list)
        
        for trade in trades:
            strategy = trade.strategy_tag or "No Strategy"
            strategy_groups[strategy].append(trade)
        
        return dict(strategy_groups)
    
    def _calculate_strategy_metrics(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a single strategy"""
        
        # Convert to list of PnL values for calculations
        pnl_values = [trade.pnl or 0 for trade in trades]
        pnl_series = pd.Series(pnl_values)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
        losing_trades = len([pnl for pnl in pnl_values if pnl < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(pnl_values)
        avg_win = np.mean([pnl for pnl in pnl_values if pnl > 0]) if winning_trades > 0 else 0
        avg_loss = np.mean([pnl for pnl in pnl_values if pnl < 0]) if losing_trades > 0 else 0
        
        # Risk/Reward ratio
        avg_risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Profit factor
        gross_profit = sum([pnl for pnl in pnl_values if pnl > 0])
        gross_loss = abs(sum([pnl for pnl in pnl_values if pnl < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
        
        # Drawdown calculation
        cumulative_pnl = pnl_series.cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown_series = running_max - cumulative_pnl
        max_drawdown = drawdown_series.max()
        max_drawdown_pct = (max_drawdown / running_max.max() * 100) if running_max.max() > 0 else 0
        
        # Edge Strength Score calculation
        edge_strength = self._calculate_edge_strength_score(
            win_rate, profit_factor, max_drawdown_pct, total_trades
        )
        
        # Consistency metrics
        consistency_score = self._calculate_consistency_score(pnl_values)
        
        # Trade frequency analysis
        trade_frequency = self._calculate_trade_frequency(trades)
        
        return {
            "strategy_name": trades[0].strategy_tag or "No Strategy",
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_pnl_per_trade": round(total_pnl / total_trades, 2) if total_trades > 0 else 0,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "avg_risk_reward": round(avg_risk_reward, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != 999 else 999,
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "edge_strength": round(edge_strength, 1),
            "consistency_score": round(consistency_score, 2),
            "trade_frequency": trade_frequency,
            "largest_win": round(max(pnl_values), 2) if pnl_values else 0,
            "largest_loss": round(min(pnl_values), 2) if pnl_values else 0,
            "sharpe_ratio": self._calculate_sharpe_ratio(pnl_series),
            "kelly_criterion": self._calculate_kelly_criterion(win_rate, avg_risk_reward)
        }
    
    def _calculate_edge_strength_score(
        self, 
        win_rate: float, 
        profit_factor: float, 
        max_drawdown_pct: float, 
        sample_size: int
    ) -> float:
        """
        Calculate custom Edge Strength Score
        
        Formula combines:
        - Win rate (40% weight)
        - Profit factor (30% weight) 
        - Drawdown penalty (20% weight)
        - Sample size confidence (10% weight)
        """
        # Normalize win rate (0-100 scale)
        win_rate_score = min(win_rate, 100)
        
        # Normalize profit factor (cap at 5.0 for scoring)
        profit_factor_score = min(profit_factor * 20, 100)  # 2.0 PF = 40 points
        
        # Drawdown penalty (higher drawdown = lower score)
        drawdown_penalty = max(0, 100 - (max_drawdown_pct * 2))  # 50% DD = 0 points
        
        # Sample size confidence (more trades = higher confidence)
        sample_confidence = min(sample_size / 50 * 100, 100)  # 50+ trades = full confidence
        
        # Weighted composite score
        edge_strength = (
            win_rate_score * 0.4 +
            profit_factor_score * 0.3 +
            drawdown_penalty * 0.2 +
            sample_confidence * 0.1
        )
        
        return max(0, min(100, edge_strength))  # Clamp between 0-100
    
    def _calculate_consistency_score(self, pnl_values: List[float]) -> float:
        """Calculate how consistent the strategy returns are"""
        if len(pnl_values) < 2:
            return 0
        
        pnl_series = pd.Series(pnl_values)
        
        # Calculate coefficient of variation (lower = more consistent)
        if pnl_series.mean() != 0:
            cv = abs(pnl_series.std() / pnl_series.mean())
            consistency_score = max(0, 100 - (cv * 20))  # Convert to 0-100 scale
        else:
            consistency_score = 0
        
        return consistency_score
    
    def _calculate_trade_frequency(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate trade frequency metrics"""
        if not trades:
            return {"trades_per_month": 0, "avg_days_between_trades": 0}
        
        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda t: t.entry_time)
        
        # Calculate date range
        start_date = sorted_trades[0].entry_time
        end_date = sorted_trades[-1].entry_time
        total_days = (end_date - start_date).days or 1
        
        trades_per_month = len(trades) / (total_days / 30.44)  # Average days per month
        avg_days_between_trades = total_days / len(trades) if len(trades) > 1 else 0
        
        return {
            "trades_per_month": round(trades_per_month, 2),
            "avg_days_between_trades": round(avg_days_between_trades, 2)
        }
    
    def _calculate_sharpe_ratio(self, pnl_series: pd.Series) -> float:
        """Calculate annualized Sharpe ratio"""
        if len(pnl_series) < 2 or pnl_series.std() == 0:
            return 0
        
        # Assume daily returns, annualize
        daily_mean = pnl_series.mean()
        daily_std = pnl_series.std()
        
        # Annualized Sharpe (assuming 252 trading days)
        sharpe = (daily_mean / daily_std) * np.sqrt(252) if daily_std != 0 else 0
        return round(sharpe, 2)
    
    def _calculate_kelly_criterion(self, win_rate: float, avg_risk_reward: float) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        if avg_risk_reward == 0:
            return 0
        
        win_prob = win_rate / 100
        lose_prob = 1 - win_prob
        
        # Kelly % = (bp - q) / b
        # where b = avg_risk_reward, p = win_prob, q = lose_prob
        kelly_pct = (avg_risk_reward * win_prob - lose_prob) / avg_risk_reward
        
        return round(max(0, kelly_pct * 100), 2)  # Convert to percentage
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary when no data available"""
        return {
            "total_strategies": 0,
            "profitable_strategies": 0,
            "strong_edge_strategies": 0,
            "weak_edge_strategies": 0,
            "best_strategy": None,
            "worst_strategy": None,
            "total_trades_analyzed": 0
        }
    
    def get_strategy_comparison(self, trades: List[Trade]) -> Dict[str, Any]:
        """Generate strategy comparison analysis"""
        edge_analysis = self.calculate_edge_strength(trades)
        strategies = edge_analysis.get("strategies", {})
        
        if not strategies:
            return {"comparison": [], "insights": []}
        
        # Sort strategies by edge strength
        sorted_strategies = sorted(
            strategies.items(), 
            key=lambda x: x[1]["edge_strength"], 
            reverse=True
        )
        
        comparison = []
        insights = []
        
        for strategy_name, metrics in sorted_strategies:
            comparison.append({
                "strategy": strategy_name,
                "edge_strength": metrics["edge_strength"],
                "win_rate": metrics["win_rate"],
                "profit_factor": metrics["profit_factor"],
                "total_pnl": metrics["total_pnl"],
                "sample_size": metrics["total_trades"],
                "recommendation": self._get_strategy_recommendation(metrics)
            })
        
        # Generate insights
        if len(sorted_strategies) > 1:
            best_strategy = sorted_strategies[0]
            worst_strategy = sorted_strategies[-1]
            
            insights.append(f"🎯 Your strongest edge is '{best_strategy[0]}' with {best_strategy[1]['edge_strength']:.1f}% edge strength")
            insights.append(f"⚠️ Consider reviewing '{worst_strategy[0]}' - only {worst_strategy[1]['edge_strength']:.1f}% edge strength")
            
            # Performance gap insight
            performance_gap = best_strategy[1]["total_pnl"] - worst_strategy[1]["total_pnl"]
            if performance_gap > 1000:
                insights.append(f"💰 Performance gap: ${performance_gap:,.0f} between best and worst strategy")
        
        return {
            "comparison": comparison,
            "insights": insights,
            "total_strategies_analyzed": len(sorted_strategies)
        }
    
    def _get_strategy_recommendation(self, metrics: Dict[str, Any]) -> str:
        """Generate recommendation based on strategy metrics"""
        edge_strength = metrics["edge_strength"]
        sample_size = metrics["total_trades"]
        
        if sample_size < self.minimum_trades_threshold:
            return "Need more data"
        elif edge_strength >= 70:
            return "Scale up"
        elif edge_strength >= 50:
            return "Monitor closely"
        elif edge_strength >= 30:
            return "Needs improvement"
        else:
            return "Consider stopping"
