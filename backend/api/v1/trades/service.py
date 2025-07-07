"""
Trades service layer - handles all trade-related business logic with optimizations
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import uuid
import logging
from functools import lru_cache

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.trade import Trade
from backend.models.tag import Tag
from backend.api.v1.trades.schemas import (
    TradeCreateRequest, 
    TradeUpdateRequest, 
    TradeResponse, 
    TradeQueryParams,
    AnalyticsRequest,
    AnalyticsResponse,
    TradeIngestRequest,
    TradeIngestResponse
)
from backend.core.exceptions import NotFoundError, ValidationError, BusinessLogicError
from backend.services.analytics_service import AnalyticsService
from backend.models.trade_note import TradeNote
from backend.models.strategy import Strategy
from backend.services.critique_engine import CritiqueEngine
from .schemas import TradeCreateRequest, TradeUpdateRequest, TradeResponse
from backend.services.milestone_engine import MilestoneEngine
from backend.core.cache import cache_manager, query_cache

logger = logging.getLogger(__name__)

class AnalyticsFilters:
    """Data class to hold analytics filters"""
    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        strategy_tag: Optional[str] = None,
        tags: Optional[List[str]] = None,
        confidence_score_min: Optional[int] = None,
        confidence_score_max: Optional[int] = None,
        min_pnl: Optional[float] = None,
        max_pnl: Optional[float] = None
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.strategy_tag = strategy_tag
        self.tags = tags
        self.confidence_score_min = confidence_score_min
        self.confidence_score_max = confidence_score_max
        self.min_pnl = min_pnl
        self.max_pnl = max_pnl


class TradesService:
    """Service for managing trades and analytics with optimizations"""

    def __init__(self, db: Session):
        self.analytics_service = AnalyticsService()
        self.db = db
        self.critique_engine = CritiqueEngine()
        self._trades_storage = {}

        # Import analytics modules
        from backend.analytics.performance import calculate_risk_reward_metrics
        from backend.analytics.equity import generate_equity_curve
        from backend.analytics.streaks import calculate_win_loss_streaks
        from backend.analytics.filters import apply_trade_filters

        self.calculate_performance = calculate_risk_reward_metrics
        self.calculate_equity = generate_equity_curve
        self.calculate_streaks = calculate_win_loss_streaks
        self.apply_filters = apply_trade_filters

    @query_cache.cache_query(ttl=300)
    async def get_user_trades_optimized(self, user_id: str, limit: int = 100, offset: int = 0, include_journal: bool = False):
        """Optimized method to get user trades with efficient querying"""
        try:
            # Build optimized query with eager loading
            query = self.db.query(Trade).filter(Trade.user_id == user_id)
            
            if include_journal:
                query = query.options(
                    selectinload(Trade.notes),
                    selectinload(Trade.tags),
                    selectinload(Trade.review)
                )
            
            # Add ordering and pagination
            query = query.order_by(desc(Trade.entry_time)).offset(offset).limit(limit)
            
            # Execute query
            trades = query.all()
            
            # Convert to response format
            result = []
            for trade in trades:
                trade_data = {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'direction': trade.direction,
                    'quantity': trade.quantity,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'entry_time': trade.entry_time,
                    'exit_time': trade.exit_time,
                    'pnl': trade.pnl,
                    'net_pnl': trade.net_pnl,
                    'strategy_tag': trade.strategy_tag,
                    'confidence_score': trade.confidence_score,
                    'status': 'closed' if trade.exit_price else 'open',
                    'created_at': trade.created_at,
                    'updated_at': trade.updated_at
                }
                
                if include_journal and trade.notes:
                    trade_data['notes'] = [
                        {
                            'id': note.id,
                            'content': note.content,
                            'created_at': note.created_at
                        } for note in trade.notes
                    ]
                
                result.append(trade_data)
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_trades_optimized: {e}")
            raise BusinessLogicError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_user_trades_optimized: {e}")
            raise BusinessLogicError(f"Failed to retrieve trades: {str(e)}")

    @query_cache.cache_query(ttl=180)
    async def get_trade_analytics_optimized(self, user_id: str, filters: Optional[AnalyticsFilters] = None) -> Dict[str, Any]:
        """Optimized analytics calculation with caching"""
        try:
            # Build base query
            query = self.db.query(Trade).filter(Trade.user_id == user_id)
            
            # Apply filters
            if filters:
                if filters.start_date:
                    query = query.filter(Trade.entry_time >= filters.start_date)
                if filters.end_date:
                    query = query.filter(Trade.entry_time <= filters.end_date)
                if filters.strategy_tag:
                    query = query.filter(Trade.strategy_tag == filters.strategy_tag)
                if filters.confidence_score_min is not None:
                    query = query.filter(Trade.confidence_score >= filters.confidence_score_min)
                if filters.confidence_score_max is not None:
                    query = query.filter(Trade.confidence_score <= filters.confidence_score_max)
            
            # Execute query with specific columns for performance
            trades_data = query.with_entities(
                Trade.pnl,
                Trade.net_pnl,
                Trade.confidence_score,
                Trade.strategy_tag,
                Trade.entry_time,
                Trade.exit_time
            ).all()
            
            if not trades_data:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_pnl': 0,
                    'max_win': 0,
                    'max_loss': 0,
                    'sharpe_ratio': 0,
                    'strategy_breakdown': {},
                    'monthly_performance': {}
                }
            
            # Convert to pandas for efficient calculations
            df = pd.DataFrame([
                {
                    'pnl': t.pnl or 0,
                    'net_pnl': t.net_pnl or 0,
                    'confidence_score': t.confidence_score,
                    'strategy_tag': t.strategy_tag,
                    'entry_time': t.entry_time,
                    'exit_time': t.exit_time
                } for t in trades_data
            ])
            
            # Calculate analytics efficiently
            total_trades = len(df)
            winning_trades = len(df[df['net_pnl'] > 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            total_pnl = df['net_pnl'].sum()
            avg_pnl = df['net_pnl'].mean()
            max_win = df['net_pnl'].max()
            max_loss = df['net_pnl'].min()
            
            # Calculate Sharpe ratio (simplified)
            returns = df['net_pnl'].dropna()
            sharpe_ratio = (returns.mean() / returns.std()) if len(returns) > 1 and returns.std() > 0 else 0
            
            # Strategy breakdown
            strategy_breakdown = df.groupby('strategy_tag').agg({
                'net_pnl': ['count', 'sum', 'mean'],
                'pnl': 'sum'
            }).round(2).to_dict()
            
            # Monthly performance
            df['month'] = df['entry_time'].dt.to_period('M')
            monthly_performance = df.groupby('month')['net_pnl'].sum().to_dict()
            
            return {
                'total_trades': total_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2),
                'max_win': round(max_win, 2),
                'max_loss': round(max_loss, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'strategy_breakdown': strategy_breakdown,
                'monthly_performance': {str(k): round(v, 2) for k, v in monthly_performance.items()}
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_trade_analytics_optimized: {e}")
            raise BusinessLogicError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_trade_analytics_optimized: {e}")
            raise BusinessLogicError(f"Failed to calculate analytics: {str(e)}")

    async def create_trade(self, user_id: str, trade_data: TradeCreateRequest) -> TradeResponse:
        """Create a new trade with cache invalidation"""
        try:
            trade_id = str(uuid.uuid4())

            # Calculate initial PnL if exit price is provided
            pnl = None
            net_pnl = None

            # Create trade record in database
            trade = Trade(
                id=trade_id,
                user_id=user_id,
                symbol=trade_data.symbol,
                direction=trade_data.direction,
                quantity=trade_data.quantity,
                entry_price=trade_data.entry_price,
                exit_price=None,
                entry_time=trade_data.entry_time,
                exit_time=None,
                pnl=pnl,
                commission=0.0,
                net_pnl=net_pnl,
                strategy_tag=trade_data.strategy_tag,
                strategy_id=trade_data.strategy_id,
                confidence_score=trade_data.confidence_score,
                notes=trade_data.notes
            )

            # Save to database
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)

            # Invalidate user cache
            query_cache.invalidate_user_cache(user_id)

            logger.info(f"Trade {trade_id} created for user {user_id}")

            return TradeResponse(
                id=trade.id,
                user_id=trade.user_id,
                symbol=trade.symbol,
                direction=trade.direction,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                entry_time=trade.entry_time,
                exit_time=trade.exit_time,
                pnl=trade.pnl,
                commission=trade.commission,
                net_pnl=trade.net_pnl,
                strategy_tag=trade.strategy_tag,
                strategy_id=trade.strategy_id,
                confidence_score=trade.confidence_score,
                notes=trade.notes,
                status="open" if trade.exit_price is None else "closed",
                created_at=trade.created_at,
                updated_at=trade.updated_at
            )

        except Exception as e:
            logger.error(f"Failed to create trade: {str(e)}")
            raise BusinessLogicError(f"Failed to create trade: {str(e)}")

    async def update_trade(self, user_id: str, trade_id: str, update_data: TradeUpdateRequest) -> TradeResponse:
        """Update an existing trade"""
        try:
            # Get trade (in production, query database)
            trade = self._trades_storage.get(trade_id)
            if not trade:
                raise NotFoundError("Trade not found")

            # Verify ownership
            if trade["user_id"] != user_id:
                raise ValidationError("Access denied to this trade")

            # Update fields
            if update_data.exit_price is not None:
                trade["exit_price"] = update_data.exit_price
                trade["status"] = "closed"

                # Calculate PnL
                if trade["direction"] == "long":
                    pnl = (update_data.exit_price - trade["entry_price"]) * trade["quantity"]
                else:  # short
                    pnl = (trade["entry_price"] - update_data.exit_price) * trade["quantity"]

                trade["pnl"] = pnl
                trade["net_pnl"] = pnl - trade.get("commission", 0.0)

            if update_data.exit_time is not None:
                trade["exit_time"] = update_data.exit_time

            if update_data.notes is not None:
                trade["notes"] = update_data.notes

            if update_data.tags is not None:
                trade["tags"] = update_data.tags

            trade["updated_at"] = datetime.utcnow()

            logger.info(f"Trade {trade_id} updated for user {user_id}")

            return TradeResponse(**trade)

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to update trade {trade_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to update trade: {str(e)}")

    async def get_trade(self, user_id: str, trade_id: str) -> TradeResponse:
        """Get a specific trade"""
        try:
            trade = self._trades_storage.get(trade_id)
            if not trade:
                raise NotFoundError("Trade not found")

            if trade["user_id"] != user_id:
                raise ValidationError("Access denied to this trade")

            return TradeResponse(**trade)

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to get trade {trade_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve trade: {str(e)}")

    async def get_trades(self, user_id: str, query_params: TradeQueryParams) -> Dict[str, Any]:
        """Get trades with filtering and pagination"""
        try:
            # Filter trades for user (in production, use database query)
            user_trades = [
                trade for trade in self._trades_storage.values() 
                if trade["user_id"] == user_id
            ]

            # Apply filters
            if query_params.symbol:
                user_trades = [t for t in user_trades if t["symbol"] == query_params.symbol]

            if query_params.strategy_tag:
                user_trades = [t for t in user_trades if t.get("strategy_tag") == query_params.strategy_tag]

            if query_params.status:
                user_trades = [t for t in user_trades if t["status"] == query_params.status]

            if query_params.start_date:
                user_trades = [t for t in user_trades if t["entry_time"] >= query_params.start_date]

            if query_params.end_date:
                user_trades = [t for t in user_trades if t["entry_time"] <= query_params.end_date]

            # Sort by entry time (newest first)
            user_trades.sort(key=lambda x: x["entry_time"], reverse=True)

            # Pagination
            total = len(user_trades)
            start_idx = (query_params.page - 1) * query_params.per_page
            end_idx = start_idx + query_params.per_page
            paginated_trades = user_trades[start_idx:end_idx]

            trades_response = [TradeResponse(**trade) for trade in paginated_trades]

            return {
                "trades": trades_response,
                "total": total,
                "page": query_params.page,
                "per_page": query_params.per_page,
                "pages": (total + query_params.per_page - 1) // query_params.per_page
            }

        except Exception as e:
            logger.error(f"Failed to get trades for user {user_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve trades: {str(e)}")

    async def get_trades_by_strategy(self, user_id: str, strategy_id: str) -> List[Dict[str, Any]]:
        """Get all trades for a specific strategy"""
        user_trades = [
            trade for trade in self._trades_storage.values() 
            if trade["user_id"] == user_id and trade.get("strategy_id") == strategy_id
        ]
        return user_trades

    async def get_strategy_performance(self, user_id: str, strategy_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific strategy"""
        trades = await self.get_trades_by_strategy(user_id, strategy_id)

        if not trades:
            return {"total_trades": 0, "total_pnl": 0, "win_rate": 0}

        total_pnl = sum(trade.get("pnl", 0) or 0 for trade in trades)
        winning_trades = sum(1 for trade in trades if (trade.get("pnl", 0) or 0) > 0)
        win_rate = (winning_trades / len(trades)) * 100 if trades else 0

        return {
            "total_trades": len(trades),
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "winning_trades": winning_trades,
            "losing_trades": len(trades) - winning_trades
        }

    async def delete_trade(self, user_id: str, trade_id: str) -> Dict[str, str]:
        """Delete a trade"""
        try:
            trade = self._trades_storage.get(trade_id)
            if not trade:
                raise NotFoundError("Trade not found")

            if trade["user_id"] != user_id:
                raise ValidationError("Access denied to this trade")

            del self._trades_storage[trade_id]

            logger.info(f"Trade {trade_id} deleted for user {user_id}")

            return {"message": "Trade deleted successfully"}

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Failed to delete trade {trade_id}: {str(e)}")
            raise BusinessLogicError(f"Failed to delete trade: {str(e)}")

    async def ingest_trade(self, user_id: str, trade_data: TradeIngestRequest) -> TradeIngestResponse:
        """Ingest a trade via API"""
        try:
            trade_id = str(uuid.uuid4())

            # Calculate PnL if exit price is provided
            pnl = None
            net_pnl = None
            status = "open"

            if trade_data.exit_price:
                if trade_data.position == "long":
                    pnl = (trade_data.exit_price - trade_data.entry_price) * trade_data.size
                else:  # short
                    pnl = (trade_data.entry_price - trade_data.exit_price) * trade_data.size

                net_pnl = pnl
                status = "closed"

            # Create trade record
            trade = {
                "id": trade_id,
                "user_id": user_id,
                "symbol": trade_data.symbol.upper(),
                "direction": trade_data.position,
                "quantity": trade_data.size,
                "entry_price": trade_data.entry_price,
                "exit_price": trade_data.exit_price,
                "entry_time": trade_data.entry_time,
                "exit_time": trade_data.exit_time,
                "pnl": pnl,
                "commission": 0.0,
                "net_pnl": net_pnl,
                "strategy_tag": trade_data.strategy,
                "confidence_score": None,
                "notes": trade_data.notes,
                "tags": trade_data.tags,
                "status": status,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Store trade (in production, save to database)
            self._trades_storage[trade_id] = trade

            logger.info(f"Trade {trade_id} ingested via API for user {user_id}")

            return TradeIngestResponse(
                status="ok",
                trade_id=trade_id,
                message="Trade ingested successfully"
            )

        except Exception as e:
            import traceback
            logger.error(f"Failed to ingest trade via API for user {user_id} with data {trade_data.dict() if hasattr(trade_data, 'dict') else trade_data}: {str(e)}\n{traceback.format_exc()}")
            raise BusinessLogicError(f"Failed to ingest trade: {str(e)}")

    async def calculate_analytics(self, user_id: str, request: AnalyticsRequest) -> AnalyticsResponse:
        """Calculate trading analytics"""
        try:
            if not request.data:
                raise ValidationError("No data provided for analysis")

            # Convert to DataFrame for analysis
            df = pd.DataFrame(request.data)

            # Validate required columns
            required_columns = ['pnl']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValidationError(f"Missing required columns: {missing_columns}")

            # Use analytics service
            analytics_result = await self.analytics_service._calculate_comprehensive_analytics(df)

            logger.info(f"Analytics calculated for user {user_id}: {len(df)} trades analyzed")

            return AnalyticsResponse(**analytics_result)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Analytics calculation failed for user {user_id}: {str(e)}")
            raise BusinessLogicError(f"Analytics calculation failed: {str(e)}")

    async def get_user_analytics(self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive analytics for user's trades"""
        try:
            return await self.analytics_service.get_user_analytics(user_id, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            raise BusinessLogicError(f"Failed to retrieve analytics: {str(e)}")

    async def get_analytics(self, user_id: str, filters: Optional[AnalyticsFilters] = None) -> AnalyticsResponse:
        """Get analytics for user with optional filtering"""
        try:
            # Get user trades
            user_trades = [
                trade for trade in self._trades_storage.values() 
                if trade["user_id"] == user_id
            ]

            # Apply filters if provided
            if filters:
                user_trades = self._apply_analytics_filters(user_trades, filters)

            if not user_trades:
                return AnalyticsResponse(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_pnl=0.0,
                    avg_pnl_per_trade=0.0,
                    best_trade=0.0,
                    worst_trade=0.0,
                    profit_factor=0.0,
                    filters_applied=filters
                )

            # Calculate comprehensive analytics
            return self._calculate_comprehensive_analytics(user_trades, filters)

        except Exception as e:
            logger.error(f"Error calculating analytics: {str(e)}")
            raise BusinessLogicError(
                message="Failed to calculate analytics",
                details={"error": str(e)}
            )

    def _apply_analytics_filters(self, trades: List[Dict], filters: AnalyticsFilters) -> List[Dict]:
        """Apply analytics filters to trade list"""
        filtered = trades

        if filters.start_date:
            filtered = [t for t in filtered if t.get("entry_time") and t["entry_time"] >= filters.start_date]

        if filters.end_date:
            filtered = [t for t in filtered if t.get("entry_time") and t["entry_time"] <= filters.end_date]

        if filters.strategy_tag:
            filtered = [t for t in filtered if t.get("strategy_tag") == filters.strategy_tag]

        if filters.tags:
            def has_matching_tag(trade):
                trade_tags = trade.get("tags", [])
                if isinstance(trade_tags, str):
                    trade_tags = [tag.strip() for tag in trade_tags.split(",")]
                return any(tag in trade_tags for tag in filters.tags)

            filtered = [t for t in filtered if has_matching_tag(t)]

        if filters.confidence_score_min is not None:
            filtered = [t for t in filtered if t.get("confidence_score", 0) >= filters.confidence_score_min]

        if filters.confidence_score_max is not None:
            filtered = [t for t in filtered if t.get("confidence_score", 10) <= filters.confidence_score_max]

        if filters.min_pnl is not None:
            filtered = [t for t in filtered if t.get("pnl", 0) >= filters.min_pnl]

        if filters.max_pnl is not None:
            filtered = [t for t in filtered if t.get("pnl", 0) <= filters.max_pnl]

        return filtered

    def _calculate_comprehensive_analytics(self, trades: List[Dict], filters: Optional[AnalyticsFilters]) -> AnalyticsResponse:
        """Calculate comprehensive analytics for filtered trades"""
        total_trades = len(trades)
        pnl_values = [trade.get("pnl", 0) for trade in trades]
        winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
        losing_trades = len([pnl for pnl in pnl_values if pnl < 0])

        # Basic metrics
        total_pnl = sum(pnl_values)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        best_trade = max(pnl_values) if pnl_values else 0
        worst_trade = min(pnl_values) if pnl_values else 0

        # Profit factor
        gross_profit = sum([pnl for pnl in pnl_values if pnl > 0])
        gross_loss = abs(sum([pnl for pnl in pnl_values if pnl < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Confidence metrics
        confidence_scores = [t.get("confidence_score") for t in trades if t.get("confidence_score") is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

        confidence_distribution = {}
        for score in confidence_scores:
            confidence_distribution[str(score)] = confidence_distribution.get(str(score), 0) + 1

        # Strategy performance
        strategy_performance = self._calculate_strategy_performance(trades)

        # Tag performance
        tag_performance = self._calculate_tag_performance(trades)

        # Time-based analytics
        monthly_pnl = self._calculate_monthly_pnl(trades)
        daily_pnl = self._calculate_daily_pnl(trades)
        trades_by_day = self._calculate_trades_by_day_of_week(trades)

        return AnalyticsResponse(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_pnl_per_trade=avg_pnl,
            best_trade=best_trade,
            worst_trade=worst_trade,
            profit_factor=profit_factor,
            avg_confidence_score=avg_confidence,
            confidence_distribution=confidence_distribution,
            strategy_performance=strategy_performance,
            tag_performance=tag_performance,
            monthly_pnl=monthly_pnl,
            daily_pnl=daily_pnl,
            trades_by_day_of_week=trades_by_day,
            filters_applied=filters
        )

    def _calculate_strategy_performance(self, trades: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Calculate performance by strategy"""
        strategy_stats = {}

        for trade in trades:
            strategy = trade.get("strategy_tag", "No Strategy")
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"trades": [], "pnl": 0}

            strategy_stats[strategy]["trades"].append(trade)
            strategy_stats[strategy]["pnl"] += trade.get("pnl", 0)

        performance = {}
        for strategy, stats in strategy_stats.items():
            trade_count = len(stats["trades"])
            pnl_values = [t.get("pnl", 0) for t in stats["trades"]]
            winning = len([p for p in pnl_values if p > 0])

            performance[strategy] = {
                "total_trades": trade_count,
                "total_pnl": stats["pnl"],
                "avg_pnl": stats["pnl"] / trade_count if trade_count > 0 else 0,
                "win_rate": (winning / trade_count) * 100 if trade_count > 0 else 0,
                "winning_trades": winning,
                "losing_trades": trade_count - winning
            }

        return performance

    def _calculate_tag_performance(self, trades: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Calculate performance by tag"""
        tag_stats = {}

        for trade in trades:
            tags = trade.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {"trades": [], "pnl": 0}

                tag_stats[tag]["trades"].append(trade)
                tag_stats[tag]["pnl"] += trade.get("pnl", 0)

        performance = {}
        for tag, stats in tag_stats.items():
            trade_count = len(stats["trades"])
            pnl_values = [t.get("pnl", 0) for t in stats["trades"]]
            winning = len([p for p in pnl_values if p > 0])

            performance[tag] = {
                "total_trades": trade_count,
                "total_pnl": stats["pnl"],
                "avg_pnl": stats["pnl"] / trade_count if trade_count > 0 else 0,
                "win_rate": (winning / trade_count) * 100 if trade_count > 0 else 0,
                "winning_trades": winning,
                "losing_trades": trade_count - winning,
                "best_trade": max(pnl_values) if pnl_values else 0,
                "worst_trade": min(pnl_values) if pnl_values else 0
            }

        return performance

    async def get_tag_analytics(self, user_id: str, tag: str) -> Dict[str, Any]:
        """Get analytics for a specific tag"""
        try:
            # Get all trades for user
            user_trades = [
                trade for trade in self._trades_storage.values() 
                if trade["user_id"] == user_id
            ]

            # Filter trades that have the specified tag
            tag_trades = []
            for trade in user_trades:
                tags = trade.get("tags", [])
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]

                if tag.lower() in [t.lower() for t in tags]:
                    tag_trades.append(trade)

            if not tag_trades:
                return {
                    "tag": tag,
                    "total_trades": 0,
                    "total_pnl": 0,
                    "win_rate": 0,
                    "avg_pnl": 0
                }

            # Calculate analytics for tag
            total_trades = len(tag_trades) 
            pnl_values = [trade.get("pnl", 0) for trade in tag_trades]
            total_pnl = sum(pnl_values)
            winning_trades = len([pnl for pnl in pnl_values if pnl > 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            return {
                "tag": tag,
                "total_trades": total_trades,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / total_trades if total_trades > 0 else 0,
                "win_rate": win_rate,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "best_trade": max(pnl_values) if pnl_values else 0,
                "worst_trade": min(pnl_values) if pnl_values else 0
            }

        except Exception as e:
            logger.error(f"Failed to get tag analytics: {str(e)}")
            raise BusinessLogicError(f"Failed to calculate tag analytics: {str(e)}")

    async def get_popular_tags(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently used tags"""
        try:
            user_trades = [
                trade for trade in self._trades_storage.values() 
                if trade["user_id"] == user_id
            ]

            tag_counts = {}
            tag_pnl = {}

            for trade in user_trades:
                tags = trade.get("tags", [])
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

                trade_pnl = trade.get("pnl", 0)

                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    tag_pnl[tag] = tag_pnl.get(tag, 0) + trade_pnl

            # Sort by usage count
            popular_tags = sorted(
                tag_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit]

            return [
                {
                    "name": tag,
                    "usage_count": count,
                    "total_pnl": tag_pnl.get(tag, 0),
                    "avg_pnl": tag_pnl.get(tag, 0) / count if count > 0 else 0
                }
                for tag, count in popular_tags
            ]

        except Exception as e:
            logger.error(f"Failed to get popular tags: {str(e)}")
            raise BusinessLogicError(f"Failed to get popular tags: {str(e)}")

    def _calculate_monthly_pnl(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate PnL by month"""
        monthly_pnl = {}

        for trade in trades:
            entry_time = trade.get("entry_time")
            if entry_time:
                month_key = entry_time.strftime("%Y-%m")
                monthly_pnl[month_key] = monthly_pnl.get(month_key, 0) + trade.get("pnl", 0)

        return monthly_pnl

    def _calculate_daily_pnl(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate PnL by day (last 30 days)"""
        daily_pnl = {}

        for trade in trades:
            entry_time = trade.get("entry_time")
            if entry_time:
                day_key = entry_time.strftime("%Y-%m-%d")
                daily_pnl[day_key] = daily_pnl.get(day_key, 0) + trade.get("pnl", 0)

        return daily_pnl

    def _calculate_trades_by_day_of_week(self, trades: List[Dict]) -> Dict[str, int]:
        """Calculate trade count by day of week"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_counts = {day: 0 for day in days}

        for trade in trades:
            entry_time = trade.get("entry_time")
            if entry_time:
                day_name = days[entry_time.weekday()]
                day_counts[day_name] += 1

        return day_counts

    async def get_user_trades(self, user_id: str, limit: int = 100, offset: int = 0, include_journal: bool = False):
        """Return a list of trades for the user, with pagination."""
        # In production, this would query the database
        user_trades = [
            trade for trade in self._trades_storage.values()
            if trade["user_id"] == user_id
        ]
        # Sort by entry_time descending
        user_trades.sort(key=lambda x: x["entry_time"], reverse=True)
        paginated = user_trades[offset:offset+limit]
        # For now, ignore include_journal
        return paginated

    async def get_trade_with_journal(self, trade_id: str, user_id: str):
        """Fetch a trade by ID for a user, including journal entries if available."""
        trade = self.db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user_id).first()
        if not trade:
            return None
        # Fetch related journal entries (if any)
        journal_entries = self.db.query(TradeNote).filter(TradeNote.trade_id == trade_id).all()
        trade_dict = {
            "id": trade.id,
            "user_id": trade.user_id,
            "symbol": trade.symbol,
            "direction": trade.direction,
            "quantity": trade.quantity,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "entry_time": trade.entry_time,
            "exit_time": trade.exit_time,
            "pnl": trade.pnl,
            "commission": trade.commission,
            "net_pnl": trade.net_pnl,
            "strategy_tag": trade.strategy_tag,
            "strategy_id": trade.strategy_id,
            "confidence_score": trade.confidence_score,
            "notes": trade.notes,
            "status": "open" if trade.exit_price is None else "closed",
            "created_at": trade.created_at,
            "updated_at": trade.updated_at,
            "journal_entries": [
                {
                    "id": j.id,
                    "trade_id": j.trade_id,
                    "content": j.content,
                    "created_at": j.created_at,
                    "updated_at": j.updated_at
                } for j in journal_entries
            ]
        }
        return trade_dict