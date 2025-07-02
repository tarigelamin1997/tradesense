
from typing import Dict, List, Optional
from backend.services.cross_account_analytics import CrossAccountAnalyticsService
from datetime import datetime, timedelta

class LeaderboardService:
    """Service for global leaderboard and cross-account analytics"""

    def __init__(self):
        self.analytics_service = CrossAccountAnalyticsService()

    def get_global_leaderboard(self, limit: int = 50, metric: str = "overall", timeframe: str = "all_time") -> Dict:
        """Get global leaderboard data"""
        try:
            # Mock leaderboard data - replace with actual database aggregation
            leaderboard_data = {
                "timeframe": timeframe,
                "metric": metric,
                "total_participants": 1000,
                "last_updated": datetime.now().isoformat(),
                "rankings": []
            }
            
            # Generate mock rankings
            for i in range(min(limit, 50)):
                rank_data = {
                    "rank": i + 1,
                    "user_id": f"anonymous_{i+1}",
                    "display_name": f"Trader #{i+1}",
                    "consistency_score": 95 - (i * 0.5),
                    "win_rate": 75 - (i * 0.3),
                    "profit_factor": 2.5 - (i * 0.02),
                    "total_trades": 500 - (i * 5),
                    "risk_adjusted_return": 1.5 - (i * 0.01),
                    "account_count": 3,
                    "joined_date": "2024-01-01"
                }
                leaderboard_data["rankings"].append(rank_data)
            
            return leaderboard_data
            
        except Exception as e:
            raise Exception(f"Failed to get leaderboard: {str(e)}")

    def get_user_ranking(self, user_id: str) -> Dict:
        """Get user's global ranking and detailed stats"""
        try:
            # Get cross-account analytics
            stats = self.analytics_service.get_global_leaderboard_stats(user_id)
            
            return {
                "user_id": user_id,
                "global_ranking": stats["global_ranking"],
                "performance_summary": stats["user_stats"],
                "improvement_suggestions": stats["improvement_suggestions"],
                "leaderboard_status": self._get_leaderboard_status(user_id),
                "peer_comparison": self._get_peer_comparison(user_id, stats)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get user ranking: {str(e)}")

    def get_cross_account_analytics(self, user_id: str) -> Dict:
        """Get comprehensive cross-account analytics"""
        try:
            aggregate_stats = self.analytics_service.get_user_aggregate_stats(user_id)
            account_comparison = self.analytics_service.get_account_comparison(user_id)
            
            return {
                "aggregate_performance": aggregate_stats,
                "account_comparison": account_comparison,
                "insights": self._generate_cross_account_insights(aggregate_stats, account_comparison),
                "recommendations": self._generate_account_recommendations(account_comparison)
            }
            
        except Exception as e:
            raise Exception(f"Failed to get cross-account analytics: {str(e)}")

    def get_account_comparison(self, user_id: str) -> List[Dict]:
        """Get detailed account performance comparison"""
        try:
            return self.analytics_service.get_account_comparison(user_id)
        except Exception as e:
            raise Exception(f"Failed to get account comparison: {str(e)}")

    def opt_into_leaderboard(self, user_id: str) -> bool:
        """Opt user into global leaderboard"""
        try:
            # Update user preferences in database
            self._update_leaderboard_preference(user_id, True)
            return True
        except Exception as e:
            raise Exception(f"Failed to opt into leaderboard: {str(e)}")

    def opt_out_of_leaderboard(self, user_id: str) -> bool:
        """Opt user out of global leaderboard"""
        try:
            # Update user preferences in database
            self._update_leaderboard_preference(user_id, False)
            return True
        except Exception as e:
            raise Exception(f"Failed to opt out of leaderboard: {str(e)}")

    def _get_leaderboard_status(self, user_id: str) -> Dict:
        """Get user's leaderboard participation status"""
        # Mock implementation - replace with actual database query
        return {
            "opted_in": True,
            "display_name": "Anonymous Trader",
            "joined_leaderboard": "2024-01-01",
            "privacy_level": "anonymous"  # anonymous, username, full_profile
        }

    def _get_peer_comparison(self, user_id: str, user_stats: Dict) -> Dict:
        """Compare user to similar peers"""
        user_ranking = user_stats["global_ranking"]
        
        return {
            "similar_traders": {
                "trade_count_range": f"{user_stats['user_stats']['total_trades'] - 50}-{user_stats['user_stats']['total_trades'] + 50}",
                "avg_consistency": 65.0,
                "avg_win_rate": 55.0,
                "avg_profit_factor": 1.3
            },
            "outperforming_areas": self._identify_strengths(user_ranking),
            "improvement_areas": self._identify_weaknesses(user_ranking)
        }

    def _identify_strengths(self, ranking: Dict) -> List[str]:
        """Identify areas where user outperforms peers"""
        strengths = []
        
        if ranking["consistency_percentile"] > 75:
            strengths.append("Consistency - Top 25% of traders")
        if ranking["win_rate_percentile"] > 75:
            strengths.append("Win Rate - Excellent trade selection")
        if ranking["profit_factor_percentile"] > 75:
            strengths.append("Risk Management - Strong profit factor")
        if ranking["risk_adjusted_return_percentile"] > 75:
            strengths.append("Risk-Adjusted Returns - Efficient capital use")
        
        return strengths

    def _identify_weaknesses(self, ranking: Dict) -> List[str]:
        """Identify areas where user underperforms"""
        weaknesses = []
        
        if ranking["consistency_percentile"] < 25:
            weaknesses.append("Consistency - High performance variation")
        if ranking["win_rate_percentile"] < 25:
            weaknesses.append("Win Rate - Need better trade selection")
        if ranking["profit_factor_percentile"] < 25:
            weaknesses.append("Risk Management - Improve risk/reward ratio")
        if ranking["risk_adjusted_return_percentile"] < 25:
            weaknesses.append("Risk-Adjusted Returns - Optimize capital efficiency")
        
        return weaknesses

    def _generate_cross_account_insights(self, aggregate_stats: Dict, account_comparison: List[Dict]) -> List[str]:
        """Generate insights from cross-account analysis"""
        insights = []
        
        if len(account_comparison) > 1:
            # Find best and worst performing accounts
            best_account = max(account_comparison, key=lambda x: x["stats"]["consistency_score"])
            worst_account = min(account_comparison, key=lambda x: x["stats"]["consistency_score"])
            
            insights.append(f"Your {best_account['account_name']} account ({best_account['account_type']}) is your top performer")
            
            if worst_account["stats"]["consistency_score"] < 50:
                insights.append(f"Consider reviewing your strategy on {worst_account['account_name']} - it's underperforming")
            
            # Check for account type patterns
            sim_accounts = [acc for acc in account_comparison if acc["account_type"] == "sim"]
            live_accounts = [acc for acc in account_comparison if acc["account_type"] in ["live", "funded"]]
            
            if sim_accounts and live_accounts:
                sim_avg = sum(acc["stats"]["consistency_score"] for acc in sim_accounts) / len(sim_accounts)
                live_avg = sum(acc["stats"]["consistency_score"] for acc in live_accounts) / len(live_accounts)
                
                if sim_avg > live_avg + 10:
                    insights.append("Your simulation performance is significantly better than live trading - consider psychology factors")
                elif live_avg > sim_avg + 10:
                    insights.append("You're performing better in live trading than simulation - good emotional control")
        
        return insights

    def _generate_account_recommendations(self, account_comparison: List[Dict]) -> List[str]:
        """Generate recommendations based on account performance"""
        recommendations = []
        
        if not account_comparison:
            recommendations.append("Add multiple trading accounts to compare performance across different strategies or brokers")
            return recommendations
        
        # Find underperforming accounts
        avg_score = sum(acc["stats"]["consistency_score"] for acc in account_comparison) / len(account_comparison)
        underperforming = [acc for acc in account_comparison if acc["stats"]["consistency_score"] < avg_score - 15]
        
        for account in underperforming:
            recommendations.append(f"Focus on improving {account['account_name']} - it's dragging down your overall performance")
        
        # Check for account diversification
        account_types = set(acc["account_type"] for acc in account_comparison)
        if "sim" not in account_types:
            recommendations.append("Consider adding a simulation account to test new strategies risk-free")
        
        if len(account_comparison) == 1:
            recommendations.append("Consider adding another account to compare performance and reduce platform risk")
        
        return recommendations

    def _update_leaderboard_preference(self, user_id: str, opted_in: bool) -> bool:
        """Update user's leaderboard participation preference"""
        # Mock implementation - replace with actual database update
        return True
