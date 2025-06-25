
"""
Trades service layer - handles all trade-related business logic
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np
import uuid
import logging

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
