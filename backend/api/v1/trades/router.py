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
                                           AnalyticsResponse, TradeIngestRequest,
                                           TradeIngestResponse)
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


@router.post("/ingest",
             response_model=TradeIngestResponse,
             summary="Ingest Trade via API")
async def ingest_trade(
    trade_data: TradeIngestRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TradeIngestResponse:
    """
    Ingest a trade via authenticated API

    - **entry_time**: Trade entry timestamp
    - **exit_time**: Optional trade exit timestamp
    - **symbol**: Trading symbol (e.g., NQ, ES, AAPL)
    - **position**: Trade direction (long/short)
    - **size**: Position size
    - **entry_price**: Entry price
    - **exit_price**: Optional exit price
    - **tags**: Optional trade tags
    - **strategy**: Optional strategy name
    - **notes**: Optional trade notes

    Enables automated trade ingestion from external tools, bots, and integrations
    """
    try:
        return await trades_service.ingest_trade(current_user["user_id"], trade_data)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Ingest endpoint error: {str(e)}")
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


@router.get("/analytics/behavioral")
async def get_behavioral_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed behavioral analytics and trading patterns"""
    try:
        from backend.services.behavioral_analytics import BehavioralAnalyticsService

        # Get user trades for behavioral analysis
        query = db.query(Trade).filter(Trade.user_id == current_user["user_id"])

        if start_date:
            query = query.filter(Trade.entry_time >= start_date)
        if end_date:
            query = query.filter(Trade.entry_time <= end_date)

        trades = query.all()

        # Convert to dict format for analysis
        trades_data = []
        for trade in trades:
            trade_dict = {
                'id': trade.id,
                'symbol': trade.symbol,
                'direction': trade.direction,
                'quantity': trade.quantity,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'pnl': trade.pnl or 0,
                'tags': trade.tags or [],
                'strategy_tag': trade.strategy_tag,
                'confidence_score': trade.confidence_score
            }
            trades_data.append(trade_dict)

        # Perform behavioral analysis
        behavioral_service = BehavioralAnalyticsService()
        behavioral_metrics = behavioral_service.analyze_behavioral_patterns(trades_data)

        return ResponseHandler.success(
            data=behavioral_metrics,
            message="Behavioral analytics retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Behavioral analytics error: {str(e)}")
        return ResponseHandler.error(
            message=f"Failed to retrieve behavioral analytics: {str(e)}",
            status_code=500
        )

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    strategy_tag: Optional[str] = Query(None, description="Filter by strategy"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    confidence_score_min: Optional[int] = Query(None, ge=1, le=10, description="Min confidence score"),
    confidence_score_max: Optional[int] = Query(None, ge=1, le=10, description="Max confidence score"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics with optional filters including behavioral metrics"""
    try:
        analytics_service = AnalyticsService()

        # Get comprehensive analytics including behavioral patterns
        analytics = await analytics_service.get_user_analytics(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date
        )

        # Apply additional filters if needed
        # TODO: Implement strategy_tag, tags, confidence_score filters in service

        # Log behavioral insights for debugging
        if isinstance(analytics, dict) and 'behavioral_metrics' in analytics:
            logger.info(f"Behavioral analysis completed for user {current_user['user_id']}")
            behavioral_data = analytics['behavioral_metrics']
            logger.info(f"Consistency rating: {behavioral_data.get('consistency_rating', 'unknown')}")
            logger.info(f"Max win streak: {behavioral_data.get('max_win_streak', 0)}")
            logger.info(f"Max loss streak: {behavioral_data.get('max_loss_streak', 0)}")

        return ResponseHandler.success(
            data=analytics,
            message="Dashboard analytics with behavioral insights retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Dashboard analytics error: {str(e)}")
        return ResponseHandler.error(
            message=f"Failed to retrieve analytics: {str(e)}",
            status_code=500
        )
"""
Trades API endpoints with comprehensive filtering and analytics
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.db.session import get_db
from backend.api.deps import get_current_active_user
from backend.api.v1.trades.schemas import (
    TradeCreateRequest, TradeUpdateRequest, TradeResponse, 
    TradeQueryParams, AnalyticsRequest, AnalyticsResponse
)
from backend.api.v1.trades.service import TradesService
from backend.core.exceptions import NotFoundError, ValidationError, BusinessLogicError
from backend.core.response import create_response

router = APIRouter(prefix="/trades", tags=["Trades"])
trades_service = TradesService()


@router.post("/", response_model=TradeResponse, status_code=201)
async def create_trade(
    trade_data: TradeCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Create a new trade with optional tags"""
    try:
        trade = await trades_service.create_trade(current_user["user_id"], trade_data)
        return trade
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def get_trades(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    strategy_tag: Optional[str] = Query(None, description="Filter by strategy"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    status: Optional[str] = Query(None, description="Filter by status (open/closed)"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get trades with filtering, sorting, and pagination"""
    try:
        query_params = TradeQueryParams(
            page=page,
            per_page=per_page,
            symbol=symbol,
            strategy_tag=strategy_tag,
            tags=tags,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        result = await trades_service.get_trades(current_user["user_id"], query_params)
        return result
        
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/strategy/{strategy_id}", response_model=List[Dict[str, Any]])
async def get_trades_by_strategy(
    strategy_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get all trades for a specific strategy"""
    try:
        trades = await trades_service.get_trades_by_strategy(current_user["user_id"], strategy_id)
        return create_response(
            data=trades,
            message=f"Retrieved {len(trades)} trades for strategy"
        )
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/strategy/{strategy_id}/performance", response_model=Dict[str, Any])
async def get_strategy_performance(
    strategy_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get performance metrics for a specific strategy"""
    try:
        performance = await trades_service.get_strategy_performance(current_user["user_id"], strategy_id)
        return create_response(
            data=performance,
            message="Strategy performance calculated successfully"
        )
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get a specific trade by ID"""
    try:
        trade = await trades_service.get_trade(current_user["user_id"], trade_id)
        return trade
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Trade not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade(
    trade_id: str,
    trade_data: TradeUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Update an existing trade"""
    try:
        trade = await trades_service.update_trade(current_user["user_id"], trade_id, trade_data)
        return trade
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Trade not found")
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{trade_id}", status_code=204)
async def delete_trade(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Delete a trade"""
    try:
        await trades_service.delete_trade(current_user["user_id"], trade_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Trade not found")
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analytics", response_model=AnalyticsResponse)
async def calculate_analytics(
    request: AnalyticsRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Calculate trading analytics with optional filtering"""
    try:
        analytics = await trades_service.calculate_analytics(current_user["user_id"], request)
        return analytics
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/dashboard", response_model=Dict[str, Any])
async def get_dashboard_analytics(
    start_date: Optional[str] = Query(None, description="Start date filter"),
    end_date: Optional[str] = Query(None, description="End date filter"),
    strategy_tag: Optional[str] = Query(None, description="Filter by strategy"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get comprehensive analytics for dashboard"""
    try:
        from backend.api.v1.trades.service import AnalyticsFilters
        from datetime import datetime
        
        filters = None
        if any([start_date, end_date, strategy_tag, tags]):
            filters = AnalyticsFilters(
                start_date=datetime.fromisoformat(start_date) if start_date else None,
                end_date=datetime.fromisoformat(end_date) if end_date else None,
                strategy_tag=strategy_tag,
                tags=tags
            )
        
        analytics = await trades_service.get_analytics(current_user["user_id"], filters)
        return create_response(
            data=analytics,
            message="Dashboard analytics calculated successfully"
        )
    except (ValidationError, BusinessLogicError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/tags/{tag}", response_model=Dict[str, Any])
async def get_tag_analytics(
    tag: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get analytics for a specific tag"""
    try:
        analytics = await trades_service.get_tag_analytics(current_user["user_id"], tag)
        return create_response(
            data=analytics,
            message=f"Analytics calculated for tag '{tag}'"
        )
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/tags/popular", response_model=List[Dict[str, Any]])
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=50, description="Number of tags to return"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get most frequently used tags with performance data"""
    try:
        popular_tags = await trades_service.get_popular_tags(current_user["user_id"], limit)
        return create_response(
            data=popular_tags,
            message=f"Retrieved {len(popular_tags)} popular tags"
        )
    except BusinessLogicError as e:
        raise HTTPException(status_code=400, detail=str(e))
