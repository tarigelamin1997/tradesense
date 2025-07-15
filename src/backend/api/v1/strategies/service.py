
"""
Strategy service layer - handles all strategy business logic
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc
import logging

from models.strategy import Strategy
from api.v1.strategies.schemas import StrategyCreate, StrategyRead, StrategyUpdate
from core.exceptions import ValidationError, BusinessLogicError, NotFoundError

logger = logging.getLogger(__name__)


class StrategyService:
    """Strategy service handling strategy operations"""
    
    async def create_strategy(self, db: Session, user_id: str, strategy_data: StrategyCreate) -> StrategyRead:
        """Create a new strategy"""
        try:
            # Check if strategy name already exists for user
            existing = db.query(Strategy).filter(
                Strategy.user_id == user_id,
                Strategy.name == strategy_data.name
            ).first()
            
            if existing:
                raise ValidationError(f"Strategy '{strategy_data.name}' already exists")
            
            # Create strategy record
            db_strategy = Strategy(
                user_id=user_id,
                name=strategy_data.name,
                description=strategy_data.description
            )
            
            db.add(db_strategy)
            db.commit()
            db.refresh(db_strategy)
            
            logger.info(f"Strategy created for user {user_id}: {strategy_data.name}")
            
            return StrategyRead.from_orm(db_strategy)
            
        except ValidationError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Strategy creation failed for user {user_id}: {str(e)}")
            raise BusinessLogicError(f"Strategy creation failed: {str(e)}")
    
    async def list_strategies(self, db: Session, user_id: str) -> List[StrategyRead]:
        """Get all strategies for a user"""
        try:
            strategies = db.query(Strategy).filter(
                Strategy.user_id == user_id
            ).order_by(desc(Strategy.created_at)).all()
            
            return [StrategyRead.from_orm(strategy) for strategy in strategies]
            
        except Exception as e:
            logger.error(f"Failed to get strategies for user {user_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve strategies")
    
    async def get_strategy_by_id(self, db: Session, user_id: str, strategy_id: str) -> StrategyRead:
        """Get a specific strategy by ID"""
        try:
            strategy = db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise NotFoundError("Strategy not found")
            
            return StrategyRead.from_orm(strategy)
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get strategy {strategy_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve strategy")
    
    async def update_strategy(self, db: Session, user_id: str, strategy_id: str, 
                             strategy_update: StrategyUpdate) -> StrategyRead:
        """Update a strategy"""
        try:
            strategy = db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise NotFoundError("Strategy not found")
            
            # Check if new name conflicts with existing strategy
            if strategy_update.name and strategy_update.name != strategy.name:
                existing = db.query(Strategy).filter(
                    Strategy.user_id == user_id,
                    Strategy.name == strategy_update.name,
                    Strategy.id != strategy_id
                ).first()
                
                if existing:
                    raise ValidationError(f"Strategy '{strategy_update.name}' already exists")
            
            # Update fields
            update_data = strategy_update.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(strategy, field, value)
            
            db.commit()
            db.refresh(strategy)
            
            logger.info(f"Strategy {strategy_id} updated by user {user_id}")
            
            return StrategyRead.from_orm(strategy)
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Strategy update failed for {strategy_id}: {str(e)}")
            raise BusinessLogicError(f"Strategy update failed: {str(e)}")
    
    async def delete_strategy(self, db: Session, user_id: str, strategy_id: str) -> Dict[str, Any]:
        """Delete a strategy"""
        try:
            strategy = db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise NotFoundError("Strategy not found")
            
            strategy_name = strategy.name
            
            # Check if strategy is in use by trades
            from models.trade import Trade
            trades_using_strategy = db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.strategy_tag == strategy_name
            ).count()
            
            if trades_using_strategy > 0:
                raise ValidationError(f"Cannot delete strategy '{strategy_name}' - it is used by {trades_using_strategy} trades")
            
            db.delete(strategy)
            db.commit()
            
            logger.info(f"Strategy {strategy_id} deleted by user {user_id}")
            
            return {"message": "Strategy deleted successfully", "strategy_id": strategy_id}
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Strategy deletion failed for {strategy_id}: {str(e)}")
            raise BusinessLogicError(f"Strategy deletion failed: {str(e)}")
    
    async def get_strategy_analytics(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get performance analytics by strategy"""
        try:
            from models.trade import Trade
            from sqlalchemy import case
            
            # Get strategy performance stats
            strategy_stats = db.query(
                Trade.strategy_tag.label('strategy_name'),
                func.count(Trade.id).label('total_trades'),
                func.avg(case((Trade.pnl > 0, 1), else_=0) * 100).label('win_rate'),
                func.sum(Trade.pnl).label('total_pnl'),
                func.avg(Trade.pnl).label('avg_pnl'),
                func.max(Trade.pnl).label('best_trade'),
                func.min(Trade.pnl).label('worst_trade')
            ).filter(
                Trade.user_id == user_id,
                Trade.strategy_tag.isnot(None),
                Trade.pnl.isnot(None)
            ).group_by(Trade.strategy_tag).all()
            
            analytics = []
            for stat in strategy_stats:
                # Calculate profit factor
                winning_trades = db.query(func.sum(Trade.pnl)).filter(
                    Trade.user_id == user_id,
                    Trade.strategy_tag == stat.strategy_name,
                    Trade.pnl > 0
                ).scalar() or 0
                
                losing_trades = db.query(func.sum(func.abs(Trade.pnl))).filter(
                    Trade.user_id == user_id,
                    Trade.strategy_tag == stat.strategy_name,
                    Trade.pnl < 0
                ).scalar() or 1
                
                profit_factor = winning_trades / losing_trades if losing_trades > 0 else 999
                
                analytics.append({
                    "strategy_name": stat.strategy_name,
                    "total_trades": stat.total_trades,
                    "win_rate": round(stat.win_rate or 0, 2),
                    "total_pnl": round(stat.total_pnl or 0, 2),
                    "avg_pnl": round(stat.avg_pnl or 0, 2),
                    "profit_factor": round(profit_factor, 2),
                    "best_trade": round(stat.best_trade or 0, 2),
                    "worst_trade": round(stat.worst_trade or 0, 2)
                })
            
            return sorted(analytics, key=lambda x: x['total_pnl'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get strategy analytics for user {user_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve strategy analytics")
    
    async def get_tag_analytics(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Get performance analytics by tag"""
        try:
            from models.trade import Trade
            from sqlalchemy import case, text
            
            # This requires a more complex query to unnest JSON tags
            # For simplicity, we'll use a Python approach
            trades = db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.tags.isnot(None),
                Trade.pnl.isnot(None)
            ).all()
            
            tag_stats = {}
            
            for trade in trades:
                if trade.tags:
                    for tag in trade.tags:
                        if tag not in tag_stats:
                            tag_stats[tag] = {
                                'trades': [],
                                'total_trades': 0,
                                'wins': 0,
                                'total_pnl': 0
                            }
                        
                        tag_stats[tag]['trades'].append(trade.pnl)
                        tag_stats[tag]['total_trades'] += 1
                        if trade.pnl > 0:
                            tag_stats[tag]['wins'] += 1
                        tag_stats[tag]['total_pnl'] += trade.pnl
            
            analytics = []
            for tag, stats in tag_stats.items():
                win_rate = (stats['wins'] / stats['total_trades'] * 100) if stats['total_trades'] > 0 else 0
                avg_pnl = stats['total_pnl'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
                
                analytics.append({
                    "tag": tag,
                    "total_trades": stats['total_trades'],
                    "win_rate": round(win_rate, 2),
                    "total_pnl": round(stats['total_pnl'], 2),
                    "avg_pnl": round(avg_pnl, 2)
                })
            
            return sorted(analytics, key=lambda x: x['total_pnl'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get tag analytics for user {user_id}: {str(e)}")
            raise BusinessLogicError("Failed to retrieve tag analytics")
