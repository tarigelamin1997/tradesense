"""
Trades router - handles all trade-related endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from backend.api.v1.trades.schemas import (TradeCreateRequest,
                                           TradeUpdateRequest, TradeResponse,
                                           TradeQueryParams, AnalyticsRequest,
                                           AnalyticsResponse)
from backend.api.v1.trades.service import TradesService
from backend.core.security import get_current_active_user
from backend.core.response import ResponseHandler, APIResponse
from backend.core.exceptions import TradeSenseException
from backend.core.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trades", tags=["Trades"])
trades_service = TradesService()


@router.post("/", response_model=TradeResponse, summary="Create Trade")
async def create_trade(
    trade_data: TradeCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeResponse:
    """
    Create a new trade record
    
    - **symbol**: Trading symbol (e.g., ES, NQ, AAPL)
    - **direction**: Trade direction (long/short)
    - **quantity**: Number of shares/contracts
    - **entry_price**: Entry price
    - **entry_time**: Entry timestamp
    - **strategy_tag**: Optional strategy identifier
    - **confidence_score**: Optional confidence rating (1-10)
    - **notes**: Optional trade notes
    """
    try:
        return await trades_service.create_trade(current_user["user_id"],
                                                 trade_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Create trade endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=APIResponse, summary="Get Trades")
async def get_trades(
        symbol: Optional[str] = Query(None, description="Filter by symbol"),
        strategy_tag: Optional[str] = Query(None,
                                            description="Filter by strategy"),
        start_date: Optional[datetime] = Query(
            None, description="Start date filter"),
        end_date: Optional[datetime] = Query(None,
                                             description="End date filter"),
        status: Optional[str] = Query(None, description="Filter by status"),
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
        current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Get trades with filtering and pagination
    
    Returns paginated list of user's trades with optional filters
    """
    try:
        query_params = TradeQueryParams(symbol=symbol,
                                        strategy_tag=strategy_tag,
                                        start_date=start_date,
                                        end_date=end_date,
                                        status=status,
                                        page=page,
                                        per_page=per_page)

        result = await trades_service.get_trades(current_user["user_id"],
                                                 query_params)

        return ResponseHandler.paginated(
            items=[trade.dict() for trade in result["trades"]],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            message="Trades retrieved successfully")
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get trades endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{trade_id}", response_model=TradeResponse, summary="Get Trade")
async def get_trade(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeResponse:
    """
    Get a specific trade by ID
    """
    try:
        return await trades_service.get_trade(current_user["user_id"],
                                              trade_id)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Get trade endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{trade_id}",
            response_model=TradeResponse,
            summary="Update Trade")
async def update_trade(
    trade_id: str,
    update_data: TradeUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeResponse:
    """
    Update an existing trade
    
    - **exit_price**: Exit price (closes the trade)
    - **exit_time**: Exit timestamp
    - **notes**: Updated trade notes
    - **tags**: Trade tags
    """
    try:
        return await trades_service.update_trade(current_user["user_id"],
                                                 trade_id, update_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Update trade endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{trade_id}",
               response_model=APIResponse,
               summary="Delete Trade")
async def delete_trade(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Delete a trade
    """
    try:
        result = await trades_service.delete_trade(current_user["user_id"],
                                                   trade_id)
        return ResponseHandler.success(data=result,
                                       message="Trade deleted successfully")
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Delete trade endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analytics",
             response_model=AnalyticsResponse,
             summary="Calculate Analytics")
async def calculate_analytics(
    request: AnalyticsRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> AnalyticsResponse:
    """
    Calculate trading analytics from trade data
    
    - **data**: Array of trade data for analysis
    - **analysis_type**: Type of analysis to perform
    
    Returns comprehensive trading metrics and performance statistics
    """
    try:
        return await trades_service.calculate_analytics(
            current_user["user_id"], request)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Analytics endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/dashboard",
            response_model=APIResponse,
            summary="Get Dashboard Analytics")
async def get_dashboard_analytics(start_date: Optional[datetime] = Query(
    None, description="Start date filter"),
                                  end_date: Optional[datetime] = Query(
                                      None, description="End date filter"),
                                  current_user: Dict[str, Any] = Depends(
                                      get_current_active_user)) -> APIResponse:
    """
    Get comprehensive dashboard analytics for user
    
    Returns all analytics data needed for the dashboard
    """
    try:
        result = await trades_service.get_user_analytics(
            current_user["user_id"], start_date, end_date)

        return ResponseHandler.success(
            data=result, message="Dashboard analytics retrieved successfully")
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Dashboard analytics endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
