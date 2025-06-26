
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np
import statistics

from backend.models.trade import Trade
from backend.models.playbook import Playbook
from backend.api.v1.strategy_lab.schemas import (
    SimulationFilters, SimulationRequest, SimulationResponse,
    PerformanceMetrics, ComparisonMetrics, TradeSimulationResult,
    PlaybookPerformanceComparison, WhatIfScenario
)

class StrategyLabService:
    def __init__(self, db: Session):
        self.db = db

    def simulate_strategy(self, user_id: UUID, request: SimulationRequest) -> SimulationResponse:
        """Main simulation engine that applies filters and calculates performance"""
        
        # Get all user trades for baseline
        all_trades = self._get_user_trades(user_id)
        baseline_metrics = self._calculate_performance_metrics(all_trades) if request.compare_to_baseline else None
        
        # Apply filters to get simulation trades
        filtered_trades = self._apply_filters(user_id, request.filters)
        simulation_metrics = self._calculate_performance_metrics(filtered_trades)
        
        # Calculate comparison if baseline requested
        comparison = None
        if baseline_metrics:
            comparison = self._calculate_comparison(simulation_metrics, baseline_metrics)
        
        # Convert trades to response format
        trade_results = self._format_trade_results(filtered_trades)
        
        # Generate insights and recommendations
        insights = self._generate_insights(simulation_metrics, baseline_metrics, request.filters)
        recommendations = self._generate_recommendations(simulation_metrics, comparison, request.filters)
        
        return SimulationResponse(
            scenario_name=request.name,
            filters_applied=request.filters,
            simulation_metrics=simulation_metrics,
            baseline_metrics=baseline_metrics,
            comparison=comparison,
            filtered_trades=trade_results,
            insights=insights,
            recommendations=recommendations
        )

    def compare_playbooks(self, user_id: UUID) -> List[PlaybookPerformanceComparison]:
        """Compare performance across all user playbooks"""
        playbooks = self.db.query(Playbook).filter(Playbook.user_id == user_id).all()
        comparisons = []
        
        for playbook in playbooks:
            trades = self.db.query(Trade).filter(
                and_(Trade.user_id == user_id, Trade.playbook_id == playbook.id)
            ).all()
            
            if trades:  # Only include playbooks with trades
                metrics = self._calculate_performance_metrics(trades)
                comparisons.append(PlaybookPerformanceComparison(
                    playbook_id=playbook.id,
                    playbook_name=playbook.name,
                    metrics=metrics,
                    trade_count=len(trades)
                ))
        
        # Sort by total PnL descending
        comparisons.sort(key=lambda x: x.metrics.total_pnl, reverse=True)
        return comparisons

    def generate_what_if_scenarios(self, user_id: UUID) -> List[WhatIfScenario]:
        """Generate common what-if scenarios for analysis"""
        all_trades = self._get_user_trades(user_id)
        baseline_metrics = self._calculate_performance_metrics(all_trades)
        
        scenarios = []
        
        # Scenario 1: Only high confidence trades (8+)
        high_conf_trades = [t for t in all_trades if t.confidence_score and t.confidence_score >= 8]
        if high_conf_trades:
            metrics = self._calculate_performance_metrics(high_conf_trades)
            improvement = ((metrics.total_pnl - baseline_metrics.total_pnl) / abs(baseline_metrics.total_pnl) * 100) if baseline_metrics.total_pnl != 0 else 0
            scenarios.append(WhatIfScenario(
                scenario_name="High Confidence Only",
                description="Trading only with confidence score 8 or higher",
                metrics=metrics,
                improvement_pct=improvement
            ))
        
        # Scenario 2: Avoid emotional trades
        emotional_tags = ['fomo', 'revenge', 'greedy', 'fearful', 'impulsive', 'frustrated']
        non_emotional_trades = [
            t for t in all_trades 
            if not t.tags or not any(tag.lower() in emotional_tags for tag in (t.tags or []))
        ]
        if non_emotional_trades and len(non_emotional_trades) != len(all_trades):
            metrics = self._calculate_performance_metrics(non_emotional_trades)
            improvement = ((metrics.total_pnl - baseline_metrics.total_pnl) / abs(baseline_metrics.total_pnl) * 100) if baseline_metrics.total_pnl != 0 else 0
            scenarios.append(WhatIfScenario(
                scenario_name="No Emotional Trading",
                description="Avoiding trades tagged with emotional indicators",
                metrics=metrics,
                improvement_pct=improvement
            ))
        
        # Scenario 3: Only profitable playbooks
        profitable_playbooks = self._get_profitable_playbooks(user_id)
        if profitable_playbooks:
            profitable_trades = [t for t in all_trades if t.playbook_id in profitable_playbooks]
            if profitable_trades:
                metrics = self._calculate_performance_metrics(profitable_trades)
                improvement = ((metrics.total_pnl - baseline_metrics.total_pnl) / abs(baseline_metrics.total_pnl) * 100) if baseline_metrics.total_pnl != 0 else 0
                scenarios.append(WhatIfScenario(
                    scenario_name="Profitable Playbooks Only",
                    description="Trading only with historically profitable playbooks",
                    metrics=metrics,
                    improvement_pct=improvement
                ))
        
        return scenarios

    def _get_user_trades(self, user_id: UUID) -> List[Trade]:
        """Get all trades for a user"""
        return self.db.query(Trade).filter(Trade.user_id == str(user_id)).all()

    def _apply_filters(self, user_id: UUID, filters: SimulationFilters) -> List[Trade]:
        """Apply simulation filters to user trades"""
        query = self.db.query(Trade).filter(Trade.user_id == str(user_id))
        
        # Playbook filters
        if filters.playbook_ids:
            query = query.filter(Trade.playbook_id.in_([str(pid) for pid in filters.playbook_ids]))
        if filters.exclude_playbook_ids:
            query = query.filter(~Trade.playbook_id.in_([str(pid) for pid in filters.exclude_playbook_ids]))
        
        # Confidence score filters
        if filters.confidence_score_min:
            query = query.filter(Trade.confidence_score >= filters.confidence_score_min)
        if filters.confidence_score_max:
            query = query.filter(Trade.confidence_score <= filters.confidence_score_max)
        
        # Time filters
        if filters.entry_time_start:
            query = query.filter(Trade.entry_time >= filters.entry_time_start)
        if filters.entry_time_end:
            query = query.filter(Trade.entry_time <= filters.entry_time_end)
        
        # Symbol filters
        if filters.symbols:
            query = query.filter(Trade.symbol.in_(filters.symbols))
        
        # Direction filters
        if filters.directions:
            query = query.filter(Trade.direction.in_(filters.directions))
        
        # P&L filters
        if filters.pnl_min is not None:
            query = query.filter(Trade.pnl >= filters.pnl_min)
        if filters.pnl_max is not None:
            query = query.filter(Trade.pnl <= filters.pnl_max)
        
        trades = query.all()
        
        # Apply additional filters that require Python logic
        if filters.tags_include or filters.tags_exclude or filters.min_hold_time_minutes or filters.max_hold_time_minutes:
            trades = self._apply_python_filters(trades, filters)
        
        return trades

    def _apply_python_filters(self, trades: List[Trade], filters: SimulationFilters) -> List[Trade]:
        """Apply filters that require Python logic"""
        filtered_trades = []
        
        for trade in trades:
            # Tag filters
            if filters.tags_include:
                if not trade.tags or not any(tag in (trade.tags or []) for tag in filters.tags_include):
                    continue
            
            if filters.tags_exclude:
                if trade.tags and any(tag in (trade.tags or []) for tag in filters.tags_exclude):
                    continue
            
            # Hold time filters
            if filters.min_hold_time_minutes or filters.max_hold_time_minutes:
                if trade.entry_time and trade.exit_time:
                    hold_time_minutes = (trade.exit_time - trade.entry_time).total_seconds() / 60
                    
                    if filters.min_hold_time_minutes and hold_time_minutes < filters.min_hold_time_minutes:
                        continue
                    if filters.max_hold_time_minutes and hold_time_minutes > filters.max_hold_time_minutes:
                        continue
            
            filtered_trades.append(trade)
        
        return filtered_trades

    def _calculate_performance_metrics(self, trades: List[Trade]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics for a set of trades"""
        if not trades:
            return PerformanceMetrics(
                total_trades=0, completed_trades=0, total_pnl=0.0, avg_pnl=0.0,
                win_rate=0.0, avg_win=0.0, avg_loss=0.0, profit_factor=None,
                sharpe_ratio=None, max_drawdown=0.0, consecutive_wins=0,
                consecutive_losses=0, avg_hold_time_minutes=None,
                best_trade=0.0, worst_trade=0.0
            )
        
        # Filter completed trades (with P&L)
        completed_trades = [t for t in trades if t.pnl is not None]
        total_trades = len(trades)
        completed_count = len(completed_trades)
        
        if completed_count == 0:
            return PerformanceMetrics(
                total_trades=total_trades, completed_trades=0, total_pnl=0.0, avg_pnl=0.0,
                win_rate=0.0, avg_win=0.0, avg_loss=0.0, profit_factor=None,
                sharpe_ratio=None, max_drawdown=0.0, consecutive_wins=0,
                consecutive_losses=0, avg_hold_time_minutes=None,
                best_trade=0.0, worst_trade=0.0
            )
        
        # Basic P&L metrics
        pnls = [t.pnl for t in completed_trades]
        total_pnl = sum(pnls)
        avg_pnl = total_pnl / completed_count
        
        # Win/Loss analysis
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        win_rate = (len(wins) / completed_count) * 100 if completed_count > 0 else 0
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Profit factor
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else None
        
        # Sharpe ratio (simplified)
        if len(pnls) > 1:
            pnl_std = statistics.stdev(pnls)
            sharpe_ratio = (avg_pnl / pnl_std) if pnl_std > 0 else None
        else:
            sharpe_ratio = None
        
        # Max drawdown calculation
        max_drawdown = self._calculate_max_drawdown(pnls)
        
        # Streak analysis
        consecutive_wins, consecutive_losses = self._calculate_streaks(pnls)
        
        # Hold time analysis
        hold_times = []
        for trade in completed_trades:
            if trade.entry_time and trade.exit_time:
                hold_time = (trade.exit_time - trade.entry_time).total_seconds() / 60
                hold_times.append(hold_time)
        
        avg_hold_time = sum(hold_times) / len(hold_times) if hold_times else None
        
        # Best and worst trades
        best_trade = max(pnls) if pnls else 0
        worst_trade = min(pnls) if pnls else 0
        
        return PerformanceMetrics(
            total_trades=total_trades,
            completed_trades=completed_count,
            total_pnl=total_pnl,
            avg_pnl=avg_pnl,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            avg_hold_time_minutes=avg_hold_time,
            best_trade=best_trade,
            worst_trade=worst_trade
        )

    def _calculate_comparison(self, simulation: PerformanceMetrics, baseline: PerformanceMetrics) -> ComparisonMetrics:
        """Calculate comparison metrics between simulation and baseline"""
        return ComparisonMetrics(
            pnl_difference=simulation.total_pnl - baseline.total_pnl,
            pnl_improvement_pct=((simulation.total_pnl - baseline.total_pnl) / abs(baseline.total_pnl) * 100) if baseline.total_pnl != 0 else 0,
            win_rate_difference=simulation.win_rate - baseline.win_rate,
            profit_factor_difference=(simulation.profit_factor - baseline.profit_factor) if simulation.profit_factor and baseline.profit_factor else None,
            avg_pnl_difference=simulation.avg_pnl - baseline.avg_pnl,
            trade_count_difference=simulation.completed_trades - baseline.completed_trades
        )

    def _format_trade_results(self, trades: List[Trade]) -> List[TradeSimulationResult]:
        """Format trades for response"""
        results = []
        for trade in trades[:100]:  # Limit to 100 trades for response size
            # Get playbook name if available
            playbook_name = None
            if trade.playbook_id:
                playbook = self.db.query(Playbook).filter(Playbook.id == trade.playbook_id).first()
                playbook_name = playbook.name if playbook else None
            
            results.append(TradeSimulationResult(
                trade_id=trade.id,
                symbol=trade.symbol,
                direction=trade.direction,
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                pnl=trade.pnl,
                confidence_score=trade.confidence_score,
                playbook_name=playbook_name,
                tags=trade.tags
            ))
        
        return results

    def _generate_insights(self, simulation: PerformanceMetrics, baseline: Optional[PerformanceMetrics], filters: SimulationFilters) -> List[str]:
        """Generate insights based on simulation results"""
        insights = []
        
        if simulation.completed_trades == 0:
            insights.append("No completed trades match the specified criteria.")
            return insights
        
        # Basic performance insights
        if simulation.win_rate > 60:
            insights.append(f"High win rate of {simulation.win_rate:.1f}% indicates strong selection criteria.")
        elif simulation.win_rate < 40:
            insights.append(f"Low win rate of {simulation.win_rate:.1f}% suggests these criteria may need refinement.")
        
        if simulation.profit_factor and simulation.profit_factor > 2:
            insights.append(f"Excellent profit factor of {simulation.profit_factor:.2f} shows strong risk/reward management.")
        elif simulation.profit_factor and simulation.profit_factor < 1:
            insights.append(f"Profit factor of {simulation.profit_factor:.2f} indicates losses exceed gains.")
        
        # Comparison insights
        if baseline:
            if simulation.total_pnl > baseline.total_pnl:
                improvement = ((simulation.total_pnl - baseline.total_pnl) / abs(baseline.total_pnl) * 100)
                insights.append(f"This strategy would have improved total P&L by {improvement:.1f}%.")
            else:
                decline = ((baseline.total_pnl - simulation.total_pnl) / abs(baseline.total_pnl) * 100)
                insights.append(f"This strategy would have reduced total P&L by {decline:.1f}%.")
        
        # Filter-specific insights
        if filters.confidence_score_min and filters.confidence_score_min >= 8:
            insights.append("High confidence filtering significantly reduces trade frequency but may improve quality.")
        
        if filters.playbook_ids and len(filters.playbook_ids) == 1:
            insights.append("Single playbook analysis allows for focused strategy evaluation.")
        
        return insights

    def _generate_recommendations(self, simulation: PerformanceMetrics, comparison: Optional[ComparisonMetrics], filters: SimulationFilters) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if simulation.completed_trades == 0:
            recommendations.append("Consider relaxing filter criteria to include more trades for analysis.")
            return recommendations
        
        # Performance-based recommendations
        if simulation.win_rate < 45:
            recommendations.append("Consider tightening entry criteria or improving setup selection.")
        
        if simulation.profit_factor and simulation.profit_factor < 1.5:
            recommendations.append("Focus on improving risk/reward ratio or reducing losing trade sizes.")
        
        if simulation.max_drawdown > abs(simulation.total_pnl) * 0.3:
            recommendations.append("Consider implementing stricter stop-loss or position sizing rules.")
        
        # Comparison-based recommendations
        if comparison and comparison.pnl_improvement_pct > 10:
            recommendations.append("These criteria show strong potential - consider implementing them consistently.")
        elif comparison and comparison.pnl_improvement_pct < -10:
            recommendations.append("These criteria appear to hurt performance - consider avoiding them.")
        
        # Strategy-specific recommendations
        if simulation.consecutive_losses > 5:
            recommendations.append("Consider implementing a maximum consecutive loss rule to prevent streaks.")
        
        if filters.confidence_score_min and simulation.total_pnl > 0:
            recommendations.append("High confidence filtering appears beneficial - maintain strict entry standards.")
        
        return recommendations

    def _calculate_max_drawdown(self, pnls: List[float]) -> float:
        """Calculate maximum drawdown from P&L series"""
        if not pnls:
            return 0.0
        
        equity_curve = [sum(pnls[:i+1]) for i in range(len(pnls))]
        max_drawdown = 0.0
        peak = equity_curve[0]
        
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown

    def _calculate_streaks(self, pnls: List[float]) -> tuple:
        """Calculate maximum consecutive wins and losses"""
        if not pnls:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for pnl in pnls:
            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses

    def _get_profitable_playbooks(self, user_id: UUID) -> List[str]:
        """Get list of playbook IDs that are historically profitable"""
        result = self.db.query(
            Trade.playbook_id,
            func.sum(Trade.pnl).label('total_pnl')
        ).filter(
            and_(Trade.user_id == str(user_id), Trade.playbook_id.isnot(None), Trade.pnl.isnot(None))
        ).group_by(Trade.playbook_id).all()
        
        return [row.playbook_id for row in result if row.total_pnl > 0]
