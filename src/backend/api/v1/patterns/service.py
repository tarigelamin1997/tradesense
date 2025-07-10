
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from models.pattern_cluster import PatternCluster
from models.trade import Trade
from models.pattern_cluster import PatternClusterUpdate
from services.pattern_detection import PatternDetectionEngine

class PatternService:
    def __init__(self, db: Session):
        self.db = db
        self.detection_engine = PatternDetectionEngine(db)

    def get_user_trade_count(self, user_id: str) -> int:
        """Get total number of trades for a user"""
        return self.db.query(Trade).filter(Trade.user_id == user_id).count()

    def run_pattern_analysis(self, user_id: str, min_trades: int = 20) -> List[PatternCluster]:
        """Run pattern detection analysis for a user"""
        
        # Delete existing clusters for fresh analysis
        self.db.query(PatternCluster).filter(PatternCluster.user_id == user_id).delete()
        self.db.commit()
        
        # Run pattern detection
        clusters = self.detection_engine.analyze_patterns(user_id, min_trades)
        
        return clusters

    def get_analysis_status(self, user_id: str) -> Dict[str, Any]:
        """Get status of pattern analysis"""
        cluster_count = self.db.query(PatternCluster).filter(
            PatternCluster.user_id == user_id
        ).count()
        
        latest_analysis = self.db.query(PatternCluster).filter(
            PatternCluster.user_id == user_id
        ).order_by(desc(PatternCluster.analysis_date)).first()
        
        if latest_analysis:
            return {
                "status": "completed",
                "cluster_count": cluster_count,
                "last_analysis": latest_analysis.analysis_date,
                "message": f"Found {cluster_count} distinct trading patterns"
            }
        else:
            return {
                "status": "not_started",
                "cluster_count": 0,
                "last_analysis": None,
                "message": "No pattern analysis has been run yet"
            }

    def get_pattern_clusters(
        self,
        user_id: str,
        cluster_type: Optional[str] = None,
        min_avg_return: Optional[float] = None,
        max_avg_return: Optional[float] = None,
        saved_only: bool = False,
        limit: int = 50
    ) -> List[PatternCluster]:
        """Get pattern clusters with filters"""
        query = self.db.query(PatternCluster).filter(PatternCluster.user_id == user_id)
        
        if cluster_type:
            query = query.filter(PatternCluster.cluster_type == cluster_type)
        
        if min_avg_return is not None:
            query = query.filter(PatternCluster.avg_return >= min_avg_return)
        
        if max_avg_return is not None:
            query = query.filter(PatternCluster.avg_return <= max_avg_return)
        
        if saved_only:
            query = query.filter(PatternCluster.is_saved_to_playbook == "true")
        
        return query.order_by(desc(PatternCluster.total_pnl)).limit(limit).all()

    def get_pattern_cluster(self, cluster_id: str, user_id: str) -> Optional[PatternCluster]:
        """Get a specific pattern cluster"""
        return self.db.query(PatternCluster).filter(
            and_(PatternCluster.id == cluster_id, PatternCluster.user_id == user_id)
        ).first()

    def update_pattern_cluster(
        self, cluster_id: str, user_id: str, cluster_data: PatternClusterUpdate
    ) -> Optional[PatternCluster]:
        """Update a pattern cluster"""
        cluster = self.get_pattern_cluster(cluster_id, user_id)
        if not cluster:
            return None
        
        update_data = cluster_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cluster, field, value)
        
        self.db.commit()
        self.db.refresh(cluster)
        return cluster

    def delete_pattern_cluster(self, cluster_id: str, user_id: str) -> bool:
        """Delete a pattern cluster"""
        cluster = self.get_pattern_cluster(cluster_id, user_id)
        if not cluster:
            return False
        
        self.db.delete(cluster)
        self.db.commit()
        return True

    def get_cluster_trades(self, cluster_id: str, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all trades in a specific cluster"""
        cluster = self.get_pattern_cluster(cluster_id, user_id)
        if not cluster:
            return None
        
        trade_ids = cluster.trade_ids or []
        if not trade_ids:
            return []
        
        trades = self.db.query(Trade).filter(
            and_(Trade.id.in_(trade_ids), Trade.user_id == user_id)
        ).all()
        
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
                'strategy_tag': trade.strategy_tag,
                'confidence_score': trade.confidence_score,
                'notes': trade.notes
            })
        
        return trade_data

    def get_pattern_insights(self, user_id: str) -> Dict[str, Any]:
        """Get high-level insights from pattern analysis"""
        clusters = self.db.query(PatternCluster).filter(
            PatternCluster.user_id == user_id
        ).all()
        
        if not clusters:
            return {
                "total_patterns": 0,
                "best_pattern": None,
                "worst_pattern": None,
                "insights": ["No patterns detected yet. Run pattern analysis first."]
            }
        
        # Best and worst patterns
        best_pattern = max(clusters, key=lambda c: c.total_pnl or 0)
        worst_pattern = min(clusters, key=lambda c: c.total_pnl or 0)
        
        # Generate insights
        insights = []
        profitable_patterns = [c for c in clusters if (c.avg_return or 0) > 0]
        losing_patterns = [c for c in clusters if (c.avg_return or 0) < 0]
        
        insights.append(f"Detected {len(clusters)} distinct trading patterns")
        
        if profitable_patterns:
            insights.append(f"{len(profitable_patterns)} patterns are profitable")
            best_win_rate = max(profitable_patterns, key=lambda c: c.win_rate or 0)
            insights.append(f"Best pattern has {(best_win_rate.win_rate or 0) * 100:.1f}% win rate")
        
        if losing_patterns:
            insights.append(f"{len(losing_patterns)} patterns are losing money")
            insights.append("Consider avoiding or modifying losing patterns")
        
        # Time-based insights
        time_patterns = {}
        for cluster in clusters:
            time_window = cluster.dominant_time_window
            if time_window:
                if time_window not in time_patterns:
                    time_patterns[time_window] = []
                time_patterns[time_window].append(cluster.avg_return or 0)
        
        if time_patterns:
            best_time = max(time_patterns.items(), key=lambda x: sum(x[1]) / len(x[1]))
            insights.append(f"Best performing time window: {best_time[0]}")
        
        return {
            "total_patterns": len(clusters),
            "profitable_patterns": len(profitable_patterns),
            "losing_patterns": len(losing_patterns),
            "best_pattern": {
                "name": best_pattern.name,
                "total_pnl": best_pattern.total_pnl,
                "win_rate": best_pattern.win_rate
            } if best_pattern else None,
            "worst_pattern": {
                "name": worst_pattern.name,
                "total_pnl": worst_pattern.total_pnl,
                "win_rate": worst_pattern.win_rate
            } if worst_pattern else None,
            "insights": insights,
            "time_patterns": time_patterns
        }

    def save_to_playbook(self, cluster_id: str, user_id: str) -> bool:
        """Save a pattern cluster to user's playbook"""
        cluster = self.get_pattern_cluster(cluster_id, user_id)
        if not cluster:
            return False
        
        cluster.is_saved_to_playbook = "true"
        self.db.commit()
        return True
