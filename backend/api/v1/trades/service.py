"""
Trades service layer - handles all trade-related business logic
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import uuid
import logging

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from backend.models.trade import Trade
from backend.models.tag import Tag
from backend.api.v1.trades.schemas import (
    TradeCreateRequest, 
    TradeUpdateRequest, 
    TradeResponse, 
    TradeQueryParams,
    AnalyticsRequest,
    AnalyticsResponse
)
from backend.core.exceptions import NotFoundError, ValidationError, BusinessLogicError
from backend.services.analytics_service import AnalyticsService

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
    """Service for managing trades and analytics"""

    def __init__(self):
        self.analytics_service = AnalyticsService()
        # In production, this would be a database connection
        self._trades_storage = {}

    async def create_trade(self, user_id: str, trade_data: TradeCreateRequest) -> TradeResponse:
        """Create a new trade"""
        try:
            trade_id = str(uuid.uuid4())

            # Calculate initial PnL if exit price is provided
            pnl = None
            net_pnl = None
            status = "open"

            # Create trade record
            trade = {
                "id": trade_id,
                "user_id": user_id,
                "symbol": trade_data.symbol,
                "direction": trade_data.direction,
                "quantity": trade_data.quantity,
                "entry_price": trade_data.entry_price,
                "exit_price": None,
                "entry_time": trade_data.entry_time,
                "exit_time": None,
                "pnl": pnl,
                "commission": 0.0,
                "net_pnl": net_pnl,
                "strategy_tag": trade_data.strategy_tag,
                "confidence_score": trade_data.confidence_score,
                "notes": trade_data.notes,
                "status": status,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            # Store trade (in production, save to database)
            self._trades_storage[trade_id] = trade

            logger.info(f"Trade {trade_id} created for user {user_id}")

            return TradeResponse(**trade)

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
                "losing_trades": trade_count - winning
            }

        return performance

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
```

```python
"""Service layer to handle trade-related business logic with tag support."""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from backend.models.trade import Trade
from backend.models.tag import Tag
from backend.api.v1.trades.schemas import TradeCreateRequest, TradeUpdateRequest, TradeQueryParams
from backend.core.exceptions import NotFoundError, ValidationError

class TradeService:
    """Service for managing trades"""

    @staticmethod
    async def get_trade_by_id(db: Session, trade_id: str, user_id: str) -> Trade:
        """Get a specific trade by ID"""

        trade = db.query(Trade).filter(
            and_(Trade.id == trade_id, Trade.user_id == user_id)
        ).options(joinedload(Trade.tag_objects)).first()

        if not trade:
            raise NotFoundError("Trade not found")

        return trade

    @staticmethod
    async def create_trade(db: Session, trade_data: TradeCreateRequest, user_id: str) -> Trade:
        """Create a new trade"""

        # Calculate P&L if exit price is provided
        pnl = None
        net_pnl = None
        if trade_data.exit_price:
            if trade_data.direction == "long":
                pnl = (trade_data.exit_price - trade_data.entry_price) * trade_data.quantity
            else:  # short
                pnl = (trade_data.entry_price - trade_data.exit_price) * trade_data.quantity

            net_pnl = pnl - (trade_data.commission or 0)

        # Create trade instance
        trade = Trade(
            user_id=user_id,
            symbol=trade_data.symbol.upper(),
            direction=trade_data.direction,
            quantity=trade_data.quantity,
            entry_price=trade_data.entry_price,
            exit_price=trade_data.exit_price,
            entry_time=trade_data.entry_time,
            exit_time=trade_data.exit_time,
            strategy_tag=trade_data.strategy_tag,
            confidence_score=trade_data.confidence_score,
            notes=trade_data.notes,
            tags=trade_data.tags,
            pnl=pnl,
            net_pnl=net_pnl
        )

        db.add(trade)
        db.flush()  # Get the trade ID without committing

        # Assign tags if provided
        if trade_data.tag_ids:
            await TradeService._assign_tags_to_trade(db, trade, trade_data.tag_ids, user_id)

        db.commit()
        db.refresh(trade)
        return trade

    @staticmethod
    async def update_trade(db: Session, trade_id: str, trade_data: TradeUpdateRequest, user_id: str) -> Trade:
        """Update an existing trade"""

        trade = await TradeService.get_trade_by_id(db, trade_id, user_id)

        # Handle tag updates separately
        tag_ids = trade_data.dict().pop('tag_ids', None)

        # Update fields
        for field, value in trade_data.dict(exclude_unset=True).items():
            if field != 'tag_ids':  # Skip tag_ids as it's handled separately
                setattr(trade, field, value)

        # Update tags if provided
        if tag_ids is not None:
            await TradeService._assign_tags_to_trade(db, trade, tag_ids, user_id)

        # Recalculate P&L if exit price was updated
        if trade_data.exit_price is not None and trade.entry_price:
            if trade.direction == "long":
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
            else:  # short
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.quantity

            trade.net_pnl = trade.pnl - (trade.commission or 0)

        db.commit()
        db.refresh(trade)
        return trade

    @staticmethod
    async def get_trades(db: Session, user_id: str, params: TradeQueryParams) -> Dict[str, Any]:
        """Get trades with filtering, sorting, and pagination"""

        query = db.query(Trade).filter(Trade.user_id == user_id).options(
            joinedload(Trade.tag_objects)  # Eager load tag relationships
        )

        # Apply filters
        if params.symbol:
            query = query.filter(Trade.symbol == params.symbol.upper())

        if params.strategy_tag:
            query = query.filter(Trade.strategy_tag == params.strategy_tag)

        if params.tags:
            # Filter by legacy tags stored in JSON field
            for tag in params.tags:
                query = query.filter(Trade.tags.contains([tag]))

        if params.tag_ids:
            # Filter by new tag system
            query = query.join(Trade.tag_objects).filter(Tag.id.in_(params.tag_ids))

        if params.confidence_score_min:
            query = query.filter(Trade.confidence_score >= params.confidence_score_min)

        if params.confidence_score_max:
            query = query.filter(Trade.confidence_score <= params.confidence_score_max)

        if params.status:
            if params.status == "open":
                query = query.filter(Trade.exit_time.is_(None))
            else:  # closed
                query = query.filter(Trade.exit_time.isnot(None))

        if params.start_date:
            query = query.filter(Trade.entry_time >= params.start_date)

        if params.end_date:
            query = query.filter(Trade.entry_time <= params.end_date)

        # Apply sorting
        sort_column = getattr(Trade, params.sort_by, Trade.entry_time)
        if params.sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        offset = (params.page - 1) * params.per_page
        trades = query.offset(offset).limit(params.per_page).all()

        return {
            "trades": trades,
            "total_count": total_count,
            "page": params.page,
            "per_page": params.per_page,
            "has_more": total_count > params.page * params.per_page
        }

    @staticmethod
    async def delete_trade(db: Session, trade_id: str, user_id: str) -> bool:
        """Delete a trade"""

        trade = await TradeService.get_trade_by_id(db, trade_id, user_id)

        db.delete(trade)
        db.commit()
        return True

    @staticmethod
    async def _assign_tags_to_trade(db: Session, trade: Trade, tag_ids: List[str], user_id: str) -> None:
        """Helper method to assign tags to a trade"""

        if not tag_ids:
            # Clear all tags if empty list is provided
            trade.tag_objects.clear()
            return

        # Get valid tags for this user
        tags = db.query(Tag).filter(
            and_(Tag.id.in_(tag_ids), Tag.user_id == user_id)
        ).all()

        if len(tags) != len(tag_ids):
            raise ValidationError("Some tags were not found or don't belong to this user")

        # Clear existing tags and assign new ones
        trade.tag_objects.clear()
        trade.tag_objects.extend(tags)
```

This code implements tag management for trades, including model updates, CRUD operations, and API enhancements.
```replit_final_file
"""Service layer to handle trade-related business logic with tag support."""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from backend.models.trade import Trade
from backend.models.tag import Tag
from backend.api.v1.trades.schemas import TradeCreateRequest, TradeUpdateRequest, TradeQueryParams
from backend.core.exceptions import NotFoundError, ValidationError

class TradeService:
    """Service for managing trades"""

    @staticmethod
    async def get_trade_by_id(db: Session, trade_id: str, user_id: str) -> Trade:
        """Get a specific trade by ID"""

        trade = db.query(Trade).filter(
            and_(Trade.id == trade_id, Trade.user_id == user_id)
        ).options(joinedload(Trade.tag_objects)).first()

        if not trade:
            raise NotFoundError("Trade not found")

        return trade

    @staticmethod
    async def create_trade(db: Session, trade_data: TradeCreateRequest, user_id: str) -> Trade:
        """Create a new trade"""

        # Calculate P&L if exit price is provided
        pnl = None
        net_pnl = None
        if trade_data.exit_price:
            if trade_data.direction == "long":
                pnl = (trade_data.exit_price - trade_data.entry_price) * trade_data.quantity
            else:  # short
                pnl = (trade_data.entry_price - trade_data.exit_price) * trade_data.quantity

            net_pnl = pnl - (trade_data.commission or 0)

        # Create trade instance
        trade = Trade(
            user_id=user_id,
            symbol=trade_data.symbol.upper(),
            direction=trade_data.direction,
            quantity=trade_data.quantity,
            entry_price=trade_data.entry_price,
            exit_price=trade_data.exit_price,
            entry_time=trade_data.entry_time,
            exit_time=trade_data.exit_time,
            strategy_tag=trade_data.strategy_tag,
            confidence_score=trade_data.confidence_score,
            notes=trade_data.notes,
            tags=trade_data.tags,
            pnl=pnl,
            net_pnl=net_pnl
        )

        db.add(trade)
        db.flush()  # Get the trade ID without committing

        # Assign tags if provided
        if trade_data.tag_ids:
            await TradeService._assign_tags_to_trade(db, trade, trade_data.tag_ids, user_id)

        db.commit()
        db.refresh(trade)
        return trade

    @staticmethod
    async def update_trade(db: Session, trade_id: str, trade_data: TradeUpdateRequest, user_id: str) -> Trade:
        """Update an existing trade"""

        trade = await TradeService.get_trade_by_id(db, trade_id, user_id)

        # Handle tag updates separately
        tag_ids = trade_data.dict().pop('tag_ids', None)

        # Update fields
        for field, value in trade_data.dict(exclude_unset=True).items():
            if field != 'tag_ids':  # Skip tag_ids as it's handled separately
                setattr(trade, field, value)

        # Update tags if provided
        if tag_ids is not None:
            await TradeService._assign_tags_to_trade(db, trade, tag_ids, user_id)

        # Recalculate P&L if exit price was updated
        if trade_data.exit_price is not None and trade.entry_price:
            if trade.direction == "long":
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
            else:  # short
                trade.pnl = (trade.entry_price - trade.exit_price) * trade.quantity

            trade.net_pnl = trade.pnl - (trade.commission or 0)

        db.commit()
        db.refresh(trade)