
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

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
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from backend.models.playbook import Playbook, PlaybookStatus
from backend.models.trade import Trade
from backend.api.v1.playbooks.schemas import (
    PlaybookCreate, PlaybookUpdate, PlaybookResponse, 
    PlaybookPerformance, PlaybookAnalytics
)

class PlaybookService:
    def __init__(self, db: Session):
        self.db = db

    def create_playbook(self, user_id: UUID, playbook_data: PlaybookCreate) -> PlaybookResponse:
        """Create a new playbook."""
        playbook = Playbook(
            user_id=user_id,
            **playbook_data.model_dump()
        )
        self.db.add(playbook)
        self.db.commit()
        self.db.refresh(playbook)
        return PlaybookResponse.model_validate(playbook)

    def get_playbooks(self, user_id: UUID, include_archived: bool = False) -> List[PlaybookResponse]:
        """Get all playbooks for a user."""
        query = self.db.query(Playbook).filter(Playbook.user_id == user_id)
        
        if not include_archived:
            query = query.filter(Playbook.status == PlaybookStatus.ACTIVE)
        
        playbooks = query.order_by(Playbook.created_at.desc()).all()
        return [PlaybookResponse.model_validate(p) for p in playbooks]

    def get_playbook(self, user_id: UUID, playbook_id: UUID) -> Optional[PlaybookResponse]:
        """Get a specific playbook."""
        playbook = self.db.query(Playbook).filter(
            and_(Playbook.id == playbook_id, Playbook.user_id == user_id)
        ).first()
        
        if playbook:
            return PlaybookResponse.model_validate(playbook)
        return None

    def update_playbook(self, user_id: UUID, playbook_id: UUID, playbook_data: PlaybookUpdate) -> Optional[PlaybookResponse]:
        """Update a playbook."""
        playbook = self.db.query(Playbook).filter(
            and_(Playbook.id == playbook_id, Playbook.user_id == user_id)
        ).first()
        
        if not playbook:
            return None

        update_data = playbook_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(playbook, field, value)
        
        self.db.commit()
        self.db.refresh(playbook)
        return PlaybookResponse.model_validate(playbook)

    def delete_playbook(self, user_id: UUID, playbook_id: UUID) -> bool:
        """Delete a playbook (soft delete by archiving)."""
        playbook = self.db.query(Playbook).filter(
            and_(Playbook.id == playbook_id, Playbook.user_id == user_id)
        ).first()
        
        if not playbook:
            return False

        playbook.status = PlaybookStatus.ARCHIVED
        self.db.commit()
        return True

    def get_playbook_analytics(self, user_id: UUID, days: Optional[int] = None) -> PlaybookAnalytics:
        """Get performance analytics for all playbooks."""
        base_query = self.db.query(
            Playbook.id.label('playbook_id'),
            Playbook.name.label('playbook_name'),
            func.count(Trade.id).label('trade_count'),
            func.sum(Trade.pnl).label('total_pnl'),
            func.avg(Trade.pnl).label('avg_pnl'),
            func.sum(func.case((Trade.pnl > 0, 1), else_=0)).label('wins'),
            func.avg(func.case((Trade.pnl > 0, Trade.pnl), else_=None)).label('avg_win'),
            func.avg(func.case((Trade.pnl < 0, Trade.pnl), else_=None)).label('avg_loss'),
            func.avg(
                func.extract('epoch', Trade.exit_time - Trade.entry_time) / 60
            ).label('avg_hold_time_minutes')
        ).join(
            Trade, Playbook.id == Trade.playbook_id
        ).filter(
            Playbook.user_id == user_id,
            Trade.pnl.isnot(None)
        )

        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            base_query = base_query.filter(Trade.entry_time >= cutoff_date)

        results = base_query.group_by(Playbook.id, Playbook.name).all()

        playbook_performances = []
        total_trades = 0
        total_pnl = 0.0

        for result in results:
            win_rate = (result.wins / result.trade_count * 100) if result.trade_count > 0 else 0
            
            profit_factor = None
            if result.avg_loss and result.avg_loss < 0:
                total_wins = result.wins * (result.avg_win or 0)
                total_losses = abs((result.trade_count - result.wins) * result.avg_loss)
                if total_losses > 0:
                    profit_factor = total_wins / total_losses

            performance = PlaybookPerformance(
                playbook_id=result.playbook_id,
                playbook_name=result.playbook_name,
                trade_count=result.trade_count,
                total_pnl=result.total_pnl or 0,
                avg_pnl=result.avg_pnl or 0,
                win_rate=win_rate,
                avg_win=result.avg_win or 0,
                avg_loss=result.avg_loss or 0,
                avg_hold_time_minutes=result.avg_hold_time_minutes,
                profit_factor=profit_factor
            )
            playbook_performances.append(performance)
            total_trades += result.trade_count
            total_pnl += result.total_pnl or 0

        summary = {
            "total_playbooks": len(playbook_performances),
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "best_performing": max(playbook_performances, key=lambda x: x.total_pnl).playbook_name if playbook_performances else None,
            "most_active": max(playbook_performances, key=lambda x: x.trade_count).playbook_name if playbook_performances else None
        }

        return PlaybookAnalytics(
            playbooks=playbook_performances,
            summary=summary
        )
