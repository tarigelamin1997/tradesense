
"""
Confidence Calibration Engine - Analyzes correlation between confidence and performance
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import statistics
import numpy as np

from backend.models.trade import Trade
from backend.core.exceptions import NotFoundError


class ConfidenceCalibrationService:
    """Service for analyzing confidence vs performance correlation"""

    def __init__(self, db: Session):
        self.db = db

    def get_confidence_calibration(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze confidence calibration for a user
        Returns breakdown by confidence bins and insights
        """
        # Get all closed trades with confidence scores
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.confidence_score.isnot(None),
            Trade.pnl.isnot(None)
        ).all()

        if not trades:
            raise NotFoundError("No trades with confidence scores found")

        # Group trades by confidence bins
        confidence_bins = self._group_by_confidence_bins(trades)
        
        # Calculate calibration metrics
        calibration_data = self._calculate_calibration_metrics(confidence_bins)
        
        # Generate insights
        insights = self._generate_confidence_insights(calibration_data, trades)
        
        # Calculate overall confidence statistics
        overall_stats = self._calculate_overall_confidence_stats(trades)

        return {
            "calibration_data": calibration_data,
            "insights": insights,
            "overall_stats": overall_stats,
            "total_trades_analyzed": len(trades)
        }

    def _group_by_confidence_bins(self, trades: List[Trade]) -> Dict[str, List[Trade]]:
        """Group trades into confidence bins (0-10%, 11-20%, etc.)"""
        bins = {}
        
        for trade in trades:
            confidence = trade.confidence_score
            if confidence is None:
                continue
                
            # Determine bin (0-10, 11-20, ..., 91-100)
            bin_start = (confidence - 1) // 10 * 10 + 1
            bin_end = min(bin_start + 9, 100)
            
            # Handle edge case for confidence = 100
            if confidence == 100:
                bin_start = 91
                bin_end = 100
            elif confidence <= 10:
                bin_start = 1
                bin_end = 10
                
            bin_key = f"{bin_start}-{bin_end}%"
            
            if bin_key not in bins:
                bins[bin_key] = []
            bins[bin_key].append(trade)
        
        return bins

    def _calculate_calibration_metrics(self, confidence_bins: Dict[str, List[Trade]]) -> List[Dict[str, Any]]:
        """Calculate metrics for each confidence bin"""
        calibration_data = []
        
        for bin_range, trades in confidence_bins.items():
            if not trades:
                continue
                
            # Basic metrics
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl > 0])
            win_rate = (winning_trades / total_trades) * 100
            
            # PnL metrics
            pnl_values = [t.pnl for t in trades]
            avg_pnl = statistics.mean(pnl_values)
            median_pnl = statistics.median(pnl_values)
            
            # Risk metrics
            winning_pnl = [pnl for pnl in pnl_values if pnl > 0]
            losing_pnl = [pnl for pnl in pnl_values if pnl < 0]
            
            avg_win = statistics.mean(winning_pnl) if winning_pnl else 0
            avg_loss = statistics.mean(losing_pnl) if losing_pnl else 0
            
            # Profit factor
            gross_profit = sum(winning_pnl)
            gross_loss = abs(sum(losing_pnl))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Get confidence midpoint for calibration curve
            bin_parts = bin_range.replace('%', '').split('-')
            confidence_midpoint = (int(bin_parts[0]) + int(bin_parts[1])) / 2
            
            calibration_data.append({
                "confidence_range": bin_range,
                "confidence_midpoint": confidence_midpoint,
                "total_trades": total_trades,
                "win_rate": round(win_rate, 1),
                "avg_pnl": round(avg_pnl, 2),
                "median_pnl": round(median_pnl, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "total_pnl": round(sum(pnl_values), 2),
                "std_dev": round(statistics.stdev(pnl_values), 2) if len(pnl_values) > 1 else 0
            })
        
        # Sort by confidence midpoint
        return sorted(calibration_data, key=lambda x: x["confidence_midpoint"])

    def _generate_confidence_insights(self, calibration_data: List[Dict], all_trades: List[Trade]) -> List[str]:
        """Generate actionable insights about confidence calibration"""
        insights = []
        
        if len(calibration_data) < 2:
            insights.append("Need more confidence diversity to generate insights")
            return insights
        
        # Find best and worst performing confidence ranges
        best_range = max(calibration_data, key=lambda x: x["avg_pnl"])
        worst_range = min(calibration_data, key=lambda x: x["avg_pnl"])
        
        # Find ranges with sufficient sample size
        significant_ranges = [r for r in calibration_data if r["total_trades"] >= 5]
        
        if significant_ranges:
            # Calibration insights
            highest_win_rate = max(significant_ranges, key=lambda x: x["win_rate"])
            
            insights.append(
                f"Your {best_range['confidence_range']} confidence trades perform best "
                f"(Avg PnL: ${best_range['avg_pnl']}, Win Rate: {best_range['win_rate']}%)"
            )
            
            if worst_range["avg_pnl"] < 0:
                insights.append(
                    f"Your {worst_range['confidence_range']} confidence trades underperform "
                    f"(Avg PnL: ${worst_range['avg_pnl']}). Consider reassessing criteria."
                )
            
            # Check for overconfidence
            high_confidence_ranges = [r for r in significant_ranges if r["confidence_midpoint"] >= 80]
            if high_confidence_ranges:
                avg_high_confidence_pnl = statistics.mean([r["avg_pnl"] for r in high_confidence_ranges])
                medium_confidence_ranges = [r for r in significant_ranges if 50 <= r["confidence_midpoint"] < 80]
                
                if medium_confidence_ranges:
                    avg_medium_confidence_pnl = statistics.mean([r["avg_pnl"] for r in medium_confidence_ranges])
                    
                    if avg_high_confidence_pnl < avg_medium_confidence_pnl:
                        insights.append(
                            "⚠️ Potential overconfidence detected: High confidence trades "
                            f"(${avg_high_confidence_pnl:.2f}) underperform medium confidence "
                            f"(${avg_medium_confidence_pnl:.2f})"
                        )
            
            # Check calibration accuracy
            perfect_calibration_errors = []
            for range_data in significant_ranges:
                expected_win_rate = range_data["confidence_midpoint"]
                actual_win_rate = range_data["win_rate"]
                error = abs(expected_win_rate - actual_win_rate)
                perfect_calibration_errors.append(error)
            
            avg_calibration_error = statistics.mean(perfect_calibration_errors)
            if avg_calibration_error > 20:
                insights.append(
                    f"⚠️ Poor confidence calibration detected (avg error: {avg_calibration_error:.1f}%). "
                    "Your confidence doesn't match actual win rates."
                )
            elif avg_calibration_error < 10:
                insights.append("✅ Good confidence calibration! Your confidence aligns well with outcomes.")
        
        # Volume insights
        total_trades = sum(r["total_trades"] for r in calibration_data)
        high_confidence_trades = sum(r["total_trades"] for r in calibration_data if r["confidence_midpoint"] >= 70)
        
        if high_confidence_trades / total_trades > 0.6:
            insights.append("📊 You trade with high confidence 60%+ of the time. Ensure quality over quantity.")
        
        return insights

    def _calculate_overall_confidence_stats(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate overall confidence statistics"""
        confidence_scores = [t.confidence_score for t in trades if t.confidence_score is not None]
        pnl_values = [t.pnl for t in trades if t.pnl is not None]
        
        if not confidence_scores or not pnl_values:
            return {}
        
        # Confidence distribution
        confidence_distribution = {}
        for score in confidence_scores:
            confidence_distribution[str(score)] = confidence_distribution.get(str(score), 0) + 1
        
        # Correlation between confidence and PnL
        confidence_pnl_pairs = [(t.confidence_score, t.pnl) for t in trades 
                               if t.confidence_score is not None and t.pnl is not None]
        
        if len(confidence_pnl_pairs) > 2:
            confidence_values = [pair[0] for pair in confidence_pnl_pairs]
            pnl_values = [pair[1] for pair in confidence_pnl_pairs]
            correlation = np.corrcoef(confidence_values, pnl_values)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
        else:
            correlation = 0.0
        
        return {
            "avg_confidence": round(statistics.mean(confidence_scores), 1),
            "median_confidence": round(statistics.median(confidence_scores), 1),
            "confidence_std": round(statistics.stdev(confidence_scores), 1) if len(confidence_scores) > 1 else 0,
            "confidence_distribution": confidence_distribution,
            "confidence_pnl_correlation": round(correlation, 3),
            "correlation_interpretation": self._interpret_correlation(correlation)
        }

    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret the correlation coefficient"""
        if correlation > 0.5:
            return "Strong positive correlation - Higher confidence leads to better results"
        elif correlation > 0.3:
            return "Moderate positive correlation - Confidence somewhat predicts performance"
        elif correlation > -0.3:
            return "Weak/no correlation - Confidence doesn't predict performance"
        elif correlation > -0.5:
            return "Moderate negative correlation - Higher confidence leads to worse results"
        else:
            return "Strong negative correlation - Overconfidence is hurting performance"

    def get_confidence_by_playbook(self, user_id: str) -> Dict[str, Any]:
        """Analyze confidence calibration by playbook"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.confidence_score.isnot(None),
            Trade.pnl.isnot(None),
            Trade.playbook_id.isnot(None)
        ).all()
        
        if not trades:
            return {"message": "No trades with both confidence and playbook data found"}
        
        # Group by playbook
        playbook_data = {}
        for trade in trades:
            playbook_id = trade.playbook_id
            if playbook_id not in playbook_data:
                playbook_data[playbook_id] = []
            playbook_data[playbook_id].append(trade)
        
        # Analyze each playbook
        playbook_analysis = {}
        for playbook_id, playbook_trades in playbook_data.items():
            confidence_bins = self._group_by_confidence_bins(playbook_trades)
            calibration_data = self._calculate_calibration_metrics(confidence_bins)
            
            playbook_analysis[playbook_id] = {
                "total_trades": len(playbook_trades),
                "avg_confidence": round(statistics.mean([t.confidence_score for t in playbook_trades]), 1),
                "avg_pnl": round(statistics.mean([t.pnl for t in playbook_trades]), 2),
                "calibration_data": calibration_data
            }
        
        return playbook_analysis
