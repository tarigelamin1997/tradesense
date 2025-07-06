from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from backend.core.db.session import get_db
from backend.models.trade import Trade
from backend.models.user import User
from ..auth.service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/search")
async def search_trades(
    query: Optional[str] = Query(None, description="Full-text search in notes, strategy, and tags"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags (any match)"),
    instruments: Optional[List[str]] = Query(None, description="Filter by trading instruments/symbols"),
    strategies: Optional[List[str]] = Query(None, description="Filter by strategy tags"),
    win_only: Optional[bool] = Query(None, description="Show only winning trades"),
    loss_only: Optional[bool] = Query(None, description="Show only losing trades"),
    start_date: Optional[datetime] = Query(None, description="Filter trades after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter trades before this date"),
    min_pnl: Optional[float] = Query(None, description="Minimum PnL filter"),
    max_pnl: Optional[float] = Query(None, description="Maximum PnL filter"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    offset: int = Query(0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Advanced search and filtering for trades
    """
    try:
        # Start with base query for user's trades
        trade_query = db.query(Trade).filter(Trade.user_id == current_user.id)

        # Full-text search in notes, strategy_tag, and JSON tags
        if query and query.strip():
            search_term = f"%{query.strip().lower()}%"
            trade_query = trade_query.filter(
                or_(
                    Trade.notes.ilike(search_term),
                    Trade.strategy_tag.ilike(search_term),
                    text("LOWER(CAST(tags AS TEXT))").like(search_term)
                )
            )

        # Filter by tags (JSON array contains any of the specified tags)
        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(
                    text("JSON_EXTRACT(tags, '$') LIKE :tag").bindparam(tag=f'%"{tag}"%')
                )
            if tag_conditions:
                trade_query = trade_query.filter(or_(*tag_conditions))

        # Filter by instruments/symbols
        if instruments:
            trade_query = trade_query.filter(Trade.symbol.in_([s.upper() for s in instruments]))

        # Filter by strategies
        if strategies:
            trade_query = trade_query.filter(Trade.strategy_tag.in_(strategies))

        # Win/Loss filters
        if win_only is True:
            trade_query = trade_query.filter(Trade.pnl > 0)
        elif loss_only is True:
            trade_query = trade_query.filter(Trade.pnl < 0)

        # Date range filters
        if start_date:
            trade_query = trade_query.filter(Trade.entry_time >= start_date)
        if end_date:
            trade_query = trade_query.filter(Trade.entry_time <= end_date)

        # PnL range filters
        if min_pnl is not None:
            trade_query = trade_query.filter(Trade.pnl >= min_pnl)
        if max_pnl is not None:
            trade_query = trade_query.filter(Trade.pnl <= max_pnl)

        # Get total count before pagination
        total_count = trade_query.count()

        # Apply pagination and ordering
        trades = trade_query.order_by(Trade.entry_time.desc()).offset(offset).limit(limit).all()

        # Convert to dict format
        trade_results = []
        for trade in trades:
            trade_dict = {
                "id": trade.id,
                "symbol": trade.symbol,
                "direction": trade.direction,
                "quantity": trade.quantity,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
                "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
                "pnl": trade.pnl,
                "net_pnl": trade.net_pnl,
                "notes": trade.notes,
                "tags": trade.tags or [],
                "strategy_tag": trade.strategy_tag,
                "confidence_score": trade.confidence_score,
                "created_at": trade.created_at.isoformat() if trade.created_at else None,
                "updated_at": trade.updated_at.isoformat() if trade.updated_at else None
            }
            trade_results.append(trade_dict)

        # Get filter metadata for frontend
        all_tags = set()
        all_instruments = set()
        all_strategies = set()
        
        # Query for distinct values to populate filter options
        distinct_query = db.query(Trade).filter(Trade.user_id == current_user.id)
        
        for trade in distinct_query.all():
            if trade.symbol:
                all_instruments.add(trade.symbol)
            if trade.strategy_tag:
                all_strategies.add(trade.strategy_tag)
            if trade.tags:
                if isinstance(trade.tags, list):
                    all_tags.update(trade.tags)

        return {
            "status": "success",
            "data": {
                "trades": trade_results,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                },
                "filters": {
                    "available_tags": sorted(list(all_tags)),
                    "available_instruments": sorted(list(all_instruments)),
                    "available_strategies": sorted(list(all_strategies))
                },
                "applied_filters": {
                    "query": query,
                    "tags": tags or [],
                    "instruments": instruments or [],
                    "strategies": strategies or [],
                    "win_only": win_only,
                    "loss_only": loss_only,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "min_pnl": min_pnl,
                    "max_pnl": max_pnl
                }
            }
        }

    except Exception as e:
        logger.error(f"Error in trade search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search trades"
        )


@router.get("/filters/options")
async def get_filter_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all available filter options for the current user
    """
    try:
        trades = db.query(Trade).filter(Trade.user_id == current_user.id).all()
        
        tags = set()
        instruments = set()
        strategies = set()
        
        for trade in trades:
            if trade.symbol:
                instruments.add(trade.symbol)
            if trade.strategy_tag:
                strategies.add(trade.strategy_tag)
            if trade.tags and isinstance(trade.tags, list):
                tags.update(trade.tags)
        
        return {
            "status": "success",
            "data": {
                "tags": sorted(list(tags)),
                "instruments": sorted(list(instruments)),
                "strategies": sorted(list(strategies))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get filter options"
        )
