
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics

class CrossAccountAnalyticsService:
    """Service for cross-account analytics and aggregation"""

    def get_user_aggregate_stats(self, user_id: str) -> Dict:
        """Get aggregated stats across all user accounts"""
        try:
            # Get all accounts for user
            accounts = self._get_user_accounts(user_id)
            
            # Aggregate stats across accounts
            aggregate_stats = {
                "total_accounts": len(accounts),
                "total_trades": 0,
                "total_pnl": 0.0,
                "total_volume": 0.0,
                "overall_win_rate": 0.0,
                "overall_profit_factor": 0.0,
                "consistency_score": 0.0,
                "risk_adjusted_return": 0.0,
                "account_breakdown": []
            }
            
            all_trades = []
            account_stats = []
            
            for account in accounts:
                account_trades = self._get_account_trades(account["id"])
                account_stat = self._calculate_account_stats(account, account_trades)
                account_stats.append(account_stat)
                all_trades.extend(account_trades)
                
                # Add to aggregate
                aggregate_stats["total_trades"] += account_stat["trade_count"]
                aggregate_stats["total_pnl"] += account_stat["total_pnl"]
                aggregate_stats["total_volume"] += account_stat["total_volume"]
            
            # Calculate overall metrics
            if all_trades:
                winning_trades = [t for t in all_trades if t.get("pnl", 0) > 0]
                aggregate_stats["overall_win_rate"] = len(winning_trades) / len(all_trades) * 100
                
                # Calculate profit factor
                gross_profits = sum(t["pnl"] for t in winning_trades)
                gross_losses = abs(sum(t["pnl"] for t in all_trades if t.get("pnl", 0) < 0))
                aggregate_stats["overall_profit_factor"] = gross_profits / gross_losses if gross_losses > 0 else 0
                
                # Calculate consistency score
                aggregate_stats["consistency_score"] = self._calculate_consistency_score(all_trades)
                
                # Calculate risk-adjusted return
                aggregate_stats["risk_adjusted_return"] = self._calculate_risk_adjusted_return(all_trades)
            
            aggregate_stats["account_breakdown"] = account_stats
            return aggregate_stats
            
        except Exception as e:
            raise Exception(f"Failed to calculate aggregate stats: {str(e)}")

    def get_account_comparison(self, user_id: str) -> List[Dict]:
        """Compare performance across user's accounts"""
        try:
            accounts = self._get_user_accounts(user_id)
            comparison_data = []
            
            for account in accounts:
                trades = self._get_account_trades(account["id"])
                stats = self._calculate_account_stats(account, trades)
                
                comparison_data.append({
                    "account_id": account["id"],
                    "account_name": account["name"],
                    "account_type": account.get("account_type", "unknown"),
                    "broker": account.get("broker", "unknown"),
                    "stats": stats,
                    "performance_grade": self._calculate_performance_grade(stats)
                })
            
            # Sort by performance score
            comparison_data.sort(key=lambda x: x["stats"]["consistency_score"], reverse=True)
            return comparison_data
            
        except Exception as e:
            raise Exception(f"Failed to generate account comparison: {str(e)}")

    def get_global_leaderboard_stats(self, user_id: str) -> Dict:
        """Calculate user's position in global leaderboard"""
        try:
            # Get user's normalized performance metrics
            user_stats = self.get_user_aggregate_stats(user_id)
            
            # Get global percentiles (mock data for now)
            global_stats = self._get_global_percentiles()
            
            # Calculate user's ranking
            ranking = {
                "consistency_percentile": self._calculate_percentile(
                    user_stats["consistency_score"], 
                    global_stats["consistency_scores"]
                ),
                "win_rate_percentile": self._calculate_percentile(
                    user_stats["overall_win_rate"], 
                    global_stats["win_rates"]
                ),
                "profit_factor_percentile": self._calculate_percentile(
                    user_stats["overall_profit_factor"], 
                    global_stats["profit_factors"]
                ),
                "risk_adjusted_return_percentile": self._calculate_percentile(
                    user_stats["risk_adjusted_return"], 
                    global_stats["risk_adjusted_returns"]
                ),
                "overall_rank": 0,  # To be calculated based on composite score
                "total_users": global_stats["total_users"]
            }
            
            # Calculate composite rank
            ranking["overall_rank"] = self._calculate_composite_rank(ranking)
            
            return {
                "user_stats": user_stats,
                "global_ranking": ranking,
                "improvement_suggestions": self._generate_improvement_suggestions(user_stats, ranking)
            }
            
        except Exception as e:
            raise Exception(f"Failed to calculate leaderboard stats: {str(e)}")

    def _calculate_account_stats(self, account: Dict, trades: List[Dict]) -> Dict:
        """Calculate statistics for a single account"""
        if not trades:
            return {
                "trade_count": 0,
                "total_pnl": 0.0,
                "total_volume": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "consistency_score": 0.0,
                "avg_trade_size": 0.0,
                "max_drawdown": 0.0
            }
        
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        total_volume = sum(abs(t.get("quantity", 0) * t.get("entry_price", 0)) for t in trades)
        
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        gross_profits = sum(t["pnl"] for t in winning_trades)
        gross_losses = abs(sum(t["pnl"] for t in losing_trades))
        profit_factor = gross_profits / gross_losses if gross_losses > 0 else 0
        
        return {
            "trade_count": len(trades),
            "total_pnl": total_pnl,
            "total_volume": total_volume,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "consistency_score": self._calculate_consistency_score(trades),
            "avg_trade_size": total_volume / len(trades) if trades else 0,
            "max_drawdown": self._calculate_max_drawdown(trades)
        }

    def _calculate_consistency_score(self, trades: List[Dict]) -> float:
        """Calculate consistency score based on trade results"""
        if len(trades) < 10:
            return 0.0
        
        pnl_values = [t.get("pnl", 0) for t in trades]
        
        # Calculate rolling metrics
        rolling_wins = []
        window_size = min(20, len(trades) // 2)
        
        for i in range(len(trades) - window_size + 1):
            window_trades = trades[i:i + window_size]
            wins = sum(1 for t in window_trades if t.get("pnl", 0) > 0)
            rolling_wins.append(wins / window_size)
        
        # Consistency is inverse of standard deviation of rolling win rates
        if len(rolling_wins) > 1:
            consistency = 1 - (statistics.stdev(rolling_wins) / statistics.mean(rolling_wins))
            return max(0, min(1, consistency)) * 100
        
        return 0.0

    def _calculate_risk_adjusted_return(self, trades: List[Dict]) -> float:
        """Calculate risk-adjusted return (Sharpe-like ratio)"""
        if len(trades) < 10:
            return 0.0
        
        pnl_values = [t.get("pnl", 0) for t in trades]
        avg_return = statistics.mean(pnl_values)
        
        if len(pnl_values) > 1:
            return_volatility = statistics.stdev(pnl_values)
            if return_volatility > 0:
                return avg_return / return_volatility
        
        return 0.0

    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        if not trades:
            return 0.0
        
        # Sort trades by entry time
        sorted_trades = sorted(trades, key=lambda x: x.get("entry_time", datetime.now()))
        
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted_trades:
            cumulative_pnl += trade.get("pnl", 0)
            peak = max(peak, cumulative_pnl)
            drawdown = peak - cumulative_pnl
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown

    def _calculate_performance_grade(self, stats: Dict) -> str:
        """Calculate letter grade for account performance"""
        score = 0
        
        # Win rate component (0-25 points)
        if stats["win_rate"] >= 60:
            score += 25
        elif stats["win_rate"] >= 50:
            score += 20
        elif stats["win_rate"] >= 40:
            score += 15
        elif stats["win_rate"] >= 30:
            score += 10
        
        # Profit factor component (0-25 points)
        if stats["profit_factor"] >= 2.0:
            score += 25
        elif stats["profit_factor"] >= 1.5:
            score += 20
        elif stats["profit_factor"] >= 1.2:
            score += 15
        elif stats["profit_factor"] >= 1.0:
            score += 10
        
        # Consistency component (0-25 points)
        score += min(25, stats["consistency_score"] / 4)
        
        # Trade count component (0-25 points)
        if stats["trade_count"] >= 100:
            score += 25
        elif stats["trade_count"] >= 50:
            score += 20
        elif stats["trade_count"] >= 20:
            score += 15
        elif stats["trade_count"] >= 10:
            score += 10
        
        # Convert to letter grade
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
            return "D"

    def _calculate_percentile(self, value: float, population: List[float]) -> float:
        """Calculate percentile rank of value in population"""
        if not population:
            return 50.0
        
        below = sum(1 for x in population if x < value)
        return (below / len(population)) * 100

    def _calculate_composite_rank(self, ranking: Dict) -> int:
        """Calculate composite rank from multiple percentiles"""
        percentiles = [
            ranking["consistency_percentile"],
            ranking["win_rate_percentile"],
            ranking["profit_factor_percentile"],
            ranking["risk_adjusted_return_percentile"]
        ]
        
        avg_percentile = sum(percentiles) / len(percentiles)
        total_users = ranking["total_users"]
        
        # Convert percentile to rank
        rank = int((100 - avg_percentile) / 100 * total_users) + 1
        return max(1, min(rank, total_users))

    def _generate_improvement_suggestions(self, user_stats: Dict, ranking: Dict) -> List[str]:
        """Generate improvement suggestions based on performance"""
        suggestions = []
        
        if ranking["consistency_percentile"] < 50:
            suggestions.append("Focus on consistency - your performance varies significantly between trades")
        
        if ranking["win_rate_percentile"] < 50:
            suggestions.append("Work on trade selection - your win rate could be improved")
        
        if ranking["profit_factor_percentile"] < 50:
            suggestions.append("Optimize your risk/reward ratio - let winners run longer")
        
        if user_stats["total_trades"] < 50:
            suggestions.append("Increase your trading frequency to build more statistical significance")
        
        return suggestions

    def _get_user_accounts(self, user_id: str) -> List[Dict]:
        """Get user accounts from database"""
        # Mock implementation - replace with actual database query
        return []

    def _get_account_trades(self, account_id: str) -> List[Dict]:
        """Get trades for an account"""
        # Mock implementation - replace with actual database query
        return []

    def _get_global_percentiles(self) -> Dict:
        """Get global performance percentiles"""
        # Mock implementation - replace with actual database aggregation
        return {
            "total_users": 1000,
            "consistency_scores": [50.0, 60.0, 70.0, 80.0, 90.0],
            "win_rates": [30.0, 40.0, 50.0, 60.0, 70.0],
            "profit_factors": [0.8, 1.0, 1.2, 1.5, 2.0],
            "risk_adjusted_returns": [0.1, 0.3, 0.5, 0.8, 1.2]
        }
