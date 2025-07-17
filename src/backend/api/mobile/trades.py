"""
Mobile-optimized trades endpoints.
Provides lightweight, paginated trade data with offline support.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from core.db.session import get_db
from models.user import User
from api.mobile.base import (
    MobileResponse, MobilePaginatedResponse, MobilePaginationParams,
    get_pagination_params, create_paginated_response, RequireAuth,
    format_currency, format_percentage, create_etag, check_etag
)
from sqlalchemy import text


router = APIRouter(prefix="/api/mobile/v1/trades")


class MobileTradeSummary(BaseModel):
    """Lightweight trade summary for mobile."""
    id: str
    symbol: str
    type: str  # long/short
    status: str  # open/closed
    entry_price: float
    current_price: Optional[float]
    exit_price: Optional[float]
    shares: float
    pnl: Optional[float]
    pnl_percent: Optional[float]
    entry_time: datetime
    exit_time: Optional[datetime]
    
    # Formatted values for display
    pnl_formatted: Optional[Dict[str, Any]]
    pnl_percent_formatted: Optional[Dict[str, Any]]
    entry_price_formatted: Dict[str, Any]
    value_formatted: Dict[str, Any]


class TradeDetailsMobile(BaseModel):
    """Detailed trade information for mobile."""
    summary: MobileTradeSummary
    metrics: Dict[str, Any]
    notes: Optional[str]
    tags: List[str]
    strategy: Optional[str]
    chart_data: Optional[Dict[str, Any]]
    related_trades: List[MobileTradeSummary]


class QuickTradeRequest(BaseModel):
    """Quick trade entry for mobile."""
    symbol: str
    type: str = Field(..., regex="^(long|short)$")
    shares: float
    entry_price: float
    entry_time: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class TradeUpdateRequest(BaseModel):
    """Update trade request."""
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/summary", response_model=MobileResponse[Dict[str, Any]])
async def get_trades_summary(
    timeframe: str = Query("7d", regex="^(1d|7d|30d|90d|1y|all)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, Any]]:
    """Get trading summary for mobile dashboard."""
    # Calculate date range
    now = datetime.utcnow()
    if timeframe == "1d":
        since = now - timedelta(days=1)
    elif timeframe == "7d":
        since = now - timedelta(days=7)
    elif timeframe == "30d":
        since = now - timedelta(days=30)
    elif timeframe == "90d":
        since = now - timedelta(days=90)
    elif timeframe == "1y":
        since = now - timedelta(days=365)
    else:
        since = None
    
    # Get summary stats
    query = """
        SELECT 
            COUNT(*) as total_trades,
            COUNT(CASE WHEN status = 'open' THEN 1 END) as open_trades,
            COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_trades,
            SUM(CASE WHEN status = 'closed' THEN pnl ELSE 0 END) as total_pnl,
            COUNT(CASE WHEN status = 'closed' AND pnl > 0 THEN 1 END) as winning_trades,
            COUNT(CASE WHEN status = 'closed' AND pnl < 0 THEN 1 END) as losing_trades,
            AVG(CASE WHEN status = 'closed' AND pnl > 0 THEN pnl ELSE NULL END) as avg_win,
            AVG(CASE WHEN status = 'closed' AND pnl < 0 THEN pnl ELSE NULL END) as avg_loss,
            MAX(CASE WHEN status = 'closed' THEN pnl ELSE NULL END) as best_trade,
            MIN(CASE WHEN status = 'closed' THEN pnl ELSE NULL END) as worst_trade
        FROM trades
        WHERE user_id = :user_id
    """
    
    params = {"user_id": current_user.id}
    
    if since:
        query += " AND entry_time >= :since"
        params["since"] = since
    
    result = await db.execute(text(query), params)
    stats = result.first()
    
    # Calculate derived metrics
    total_closed = stats.closed_trades or 0
    win_rate = (stats.winning_trades / total_closed * 100) if total_closed > 0 else 0
    profit_factor = abs(stats.avg_win / stats.avg_loss) if stats.avg_loss and stats.avg_loss != 0 else 0
    
    # Get recent trades
    recent_query = """
        SELECT 
            id, symbol, type, status, entry_price, exit_price,
            shares, pnl, entry_time, exit_time
        FROM trades
        WHERE user_id = :user_id
        ORDER BY COALESCE(exit_time, entry_time) DESC
        LIMIT 5
    """
    
    recent_result = await db.execute(text(recent_query), {"user_id": current_user.id})
    recent_trades = []
    
    for trade in recent_result:
        pnl_percent = None
        if trade.pnl and trade.entry_price:
            pnl_percent = (trade.pnl / (trade.entry_price * trade.shares)) * 100
        
        recent_trades.append({
            "id": str(trade.id),
            "symbol": trade.symbol,
            "type": trade.type,
            "status": trade.status,
            "pnl": format_currency(trade.pnl) if trade.pnl else None,
            "pnl_percent": format_percentage(pnl_percent) if pnl_percent else None,
            "time": trade.exit_time or trade.entry_time
        })
    
    return MobileResponse(
        data={
            "timeframe": timeframe,
            "stats": {
                "total_trades": stats.total_trades or 0,
                "open_trades": stats.open_trades or 0,
                "closed_trades": stats.closed_trades or 0,
                "total_pnl": format_currency(stats.total_pnl or 0),
                "win_rate": format_percentage(win_rate),
                "profit_factor": round(profit_factor, 2),
                "winning_trades": stats.winning_trades or 0,
                "losing_trades": stats.losing_trades or 0,
                "avg_win": format_currency(stats.avg_win or 0),
                "avg_loss": format_currency(stats.avg_loss or 0),
                "best_trade": format_currency(stats.best_trade or 0),
                "worst_trade": format_currency(stats.worst_trade or 0)
            },
            "recent_trades": recent_trades,
            "last_updated": datetime.utcnow()
        }
    )


@router.get("/list")
async def list_trades(
    request: Request,
    status: Optional[str] = Query(None, regex="^(open|closed|all)$"),
    symbol: Optional[str] = None,
    sort: str = Query("recent", regex="^(recent|pnl|symbol)$"),
    pagination: MobilePaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get paginated list of trades."""
    # Build query
    query = """
        SELECT 
            t.*,
            CASE 
                WHEN t.status = 'open' THEN 
                    (SELECT price FROM market_data WHERE symbol = t.symbol ORDER BY timestamp DESC LIMIT 1)
                ELSE NULL
            END as current_price
        FROM trades t
        WHERE t.user_id = :user_id
    """
    
    count_query = "SELECT COUNT(*) FROM trades WHERE user_id = :user_id"
    params = {"user_id": current_user.id}
    
    # Apply filters
    if status and status != "all":
        query += " AND t.status = :status"
        count_query += " AND status = :status"
        params["status"] = status
    
    if symbol:
        query += " AND t.symbol = :symbol"
        count_query += " AND symbol = :symbol"
        params["symbol"] = symbol.upper()
    
    # Apply sorting
    if sort == "recent":
        query += " ORDER BY COALESCE(t.exit_time, t.entry_time) DESC"
    elif sort == "pnl":
        query += " ORDER BY t.pnl DESC NULLS LAST"
    elif sort == "symbol":
        query += " ORDER BY t.symbol, t.entry_time DESC"
    
    # Apply pagination
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = pagination.limit
    params["offset"] = pagination.offset
    
    # Execute queries
    result = await db.execute(text(query), params)
    count_result = await db.execute(text(count_query), params)
    total = count_result.scalar()
    
    # Format trades
    trades = []
    for row in result:
        # Calculate current P&L for open trades
        pnl = row.pnl
        pnl_percent = None
        
        if row.status == "open" and row.current_price:
            if row.type == "long":
                pnl = (row.current_price - row.entry_price) * row.shares
            else:  # short
                pnl = (row.entry_price - row.current_price) * row.shares
        
        if pnl is not None and row.entry_price:
            pnl_percent = (pnl / (row.entry_price * row.shares)) * 100
        
        trades.append(MobileTradeSummary(
            id=str(row.id),
            symbol=row.symbol,
            type=row.type,
            status=row.status,
            entry_price=row.entry_price,
            current_price=row.current_price,
            exit_price=row.exit_price,
            shares=row.shares,
            pnl=pnl,
            pnl_percent=pnl_percent,
            entry_time=row.entry_time,
            exit_time=row.exit_time,
            pnl_formatted=format_currency(pnl) if pnl else None,
            pnl_percent_formatted=format_percentage(pnl_percent) if pnl_percent else None,
            entry_price_formatted=format_currency(row.entry_price),
            value_formatted=format_currency(row.entry_price * row.shares)
        ))
    
    # Generate ETag for caching
    etag = create_etag(trades)
    if check_etag(request, etag):
        return {"cached": True}
    
    return create_paginated_response(
        items=[t.dict() for t in trades],
        total=total,
        pagination=pagination,
        etag=etag
    )


@router.get("/{trade_id}", response_model=MobileResponse[TradeDetailsMobile])
async def get_trade_details(
    trade_id: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[TradeDetailsMobile]:
    """Get detailed trade information."""
    # Get trade with current price
    result = await db.execute(
        text("""
            SELECT 
                t.*,
                CASE 
                    WHEN t.status = 'open' THEN 
                        (SELECT price FROM market_data WHERE symbol = t.symbol ORDER BY timestamp DESC LIMIT 1)
                    ELSE NULL
                END as current_price
            FROM trades t
            WHERE t.id = :trade_id AND t.user_id = :user_id
        """),
        {
            "trade_id": trade_id,
            "user_id": current_user.id
        }
    )
    
    trade = result.first()
    if not trade:
        from fastapi import HTTPException
        raise HTTPException(404, "Trade not found")
    
    # Calculate metrics
    pnl = trade.pnl
    pnl_percent = None
    
    if trade.status == "open" and trade.current_price:
        if trade.type == "long":
            pnl = (trade.current_price - trade.entry_price) * trade.shares
        else:
            pnl = (trade.entry_price - trade.current_price) * trade.shares
    
    if pnl is not None and trade.entry_price:
        pnl_percent = (pnl / (trade.entry_price * trade.shares)) * 100
    
    # Get trade metrics
    hold_time = None
    if trade.exit_time:
        hold_time = (trade.exit_time - trade.entry_time).total_seconds() / 3600  # hours
    elif trade.status == "open":
        hold_time = (datetime.utcnow() - trade.entry_time).total_seconds() / 3600
    
    metrics = {
        "hold_time_hours": round(hold_time, 1) if hold_time else None,
        "risk_reward_ratio": trade.risk_reward_ratio,
        "position_size_percent": None,  # Would calculate based on account value
        "max_drawdown": None  # Would calculate from price history
    }
    
    # Get related trades (same symbol)
    related_result = await db.execute(
        text("""
            SELECT 
                id, symbol, type, status, entry_price, exit_price,
                shares, pnl, entry_time, exit_time
            FROM trades
            WHERE user_id = :user_id
            AND symbol = :symbol
            AND id != :trade_id
            ORDER BY entry_time DESC
            LIMIT 5
        """),
        {
            "user_id": current_user.id,
            "symbol": trade.symbol,
            "trade_id": trade_id
        }
    )
    
    related_trades = []
    for rel in related_result:
        rel_pnl_percent = None
        if rel.pnl and rel.entry_price:
            rel_pnl_percent = (rel.pnl / (rel.entry_price * rel.shares)) * 100
        
        related_trades.append(MobileTradeSummary(
            id=str(rel.id),
            symbol=rel.symbol,
            type=rel.type,
            status=rel.status,
            entry_price=rel.entry_price,
            current_price=None,
            exit_price=rel.exit_price,
            shares=rel.shares,
            pnl=rel.pnl,
            pnl_percent=rel_pnl_percent,
            entry_time=rel.entry_time,
            exit_time=rel.exit_time,
            pnl_formatted=format_currency(rel.pnl) if rel.pnl else None,
            pnl_percent_formatted=format_percentage(rel_pnl_percent) if rel_pnl_percent else None,
            entry_price_formatted=format_currency(rel.entry_price),
            value_formatted=format_currency(rel.entry_price * rel.shares)
        ))
    
    # Create summary
    summary = MobileTradeSummary(
        id=str(trade.id),
        symbol=trade.symbol,
        type=trade.type,
        status=trade.status,
        entry_price=trade.entry_price,
        current_price=trade.current_price,
        exit_price=trade.exit_price,
        shares=trade.shares,
        pnl=pnl,
        pnl_percent=pnl_percent,
        entry_time=trade.entry_time,
        exit_time=trade.exit_time,
        pnl_formatted=format_currency(pnl) if pnl else None,
        pnl_percent_formatted=format_percentage(pnl_percent) if pnl_percent else None,
        entry_price_formatted=format_currency(trade.entry_price),
        value_formatted=format_currency(trade.entry_price * trade.shares)
    )
    
    # Prepare chart data (simplified for mobile)
    chart_data = None
    if trade.status == "closed" and trade.exit_time:
        chart_data = {
            "entry": {
                "time": trade.entry_time.isoformat(),
                "price": trade.entry_price
            },
            "exit": {
                "time": trade.exit_time.isoformat(),
                "price": trade.exit_price
            }
        }
    
    return MobileResponse(
        data=TradeDetailsMobile(
            summary=summary,
            metrics=metrics,
            notes=trade.notes,
            tags=trade.tags or [],
            strategy=trade.strategy,
            chart_data=chart_data,
            related_trades=related_trades
        )
    )


@router.post("/quick-add", response_model=MobileResponse[Dict[str, str]])
async def quick_add_trade(
    request: QuickTradeRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Quick trade entry for mobile."""
    try:
        # Create trade
        result = await db.execute(
            text("""
                INSERT INTO trades (
                    user_id, symbol, type, shares, entry_price,
                    entry_time, status, notes, tags
                ) VALUES (
                    :user_id, :symbol, :type, :shares, :entry_price,
                    :entry_time, 'open', :notes, :tags
                )
                RETURNING id
            """),
            {
                "user_id": current_user.id,
                "symbol": request.symbol.upper(),
                "type": request.type,
                "shares": request.shares,
                "entry_price": request.entry_price,
                "entry_time": request.entry_time or datetime.utcnow(),
                "notes": request.notes,
                "tags": request.tags
            }
        )
        
        trade_id = result.scalar()
        await db.commit()
        
        # Send push notification
        await _send_trade_notification(
            current_user,
            f"Trade opened: {request.type.upper()} {request.shares} {request.symbol} @ ${request.entry_price:.2f}",
            db
        )
        
        return MobileResponse(
            data={
                "trade_id": str(trade_id),
                "message": "Trade added successfully"
            }
        )
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"Failed to add trade: {str(e)}")


@router.put("/{trade_id}", response_model=MobileResponse[Dict[str, str]])
async def update_trade(
    trade_id: str,
    request: TradeUpdateRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Update trade (close or modify)."""
    try:
        # Verify ownership
        check = await db.execute(
            text("SELECT 1 FROM trades WHERE id = :id AND user_id = :user_id"),
            {"id": trade_id, "user_id": current_user.id}
        )
        if not check.scalar():
            from fastapi import HTTPException
            raise HTTPException(404, "Trade not found")
        
        # Build update query
        updates = []
        params = {"trade_id": trade_id}
        
        if request.exit_price is not None:
            updates.append("exit_price = :exit_price")
            updates.append("status = 'closed'")
            params["exit_price"] = request.exit_price
            
            if request.exit_time:
                updates.append("exit_time = :exit_time")
                params["exit_time"] = request.exit_time
            else:
                updates.append("exit_time = NOW()")
        
        if request.notes is not None:
            updates.append("notes = :notes")
            params["notes"] = request.notes
        
        if request.tags is not None:
            updates.append("tags = :tags")
            params["tags"] = request.tags
        
        if updates:
            query = f"UPDATE trades SET {', '.join(updates)} WHERE id = :trade_id"
            await db.execute(text(query), params)
            await db.commit()
        
        return MobileResponse(
            data={
                "message": "Trade updated successfully"
            }
        )
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"Failed to update trade: {str(e)}")


@router.get("/symbols/recent", response_model=MobileResponse[List[str]])
async def get_recent_symbols(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[str]]:
    """Get recently traded symbols for quick entry."""
    result = await db.execute(
        text("""
            SELECT DISTINCT symbol
            FROM trades
            WHERE user_id = :user_id
            ORDER BY MAX(COALESCE(exit_time, entry_time)) DESC
            LIMIT :limit
        """),
        {
            "user_id": current_user.id,
            "limit": limit
        }
    )
    
    symbols = [row.symbol for row in result]
    
    return MobileResponse(data=symbols)


# Helper function
async def _send_trade_notification(user: User, message: str, db: AsyncSession):
    """Send push notification for trade events."""
    # Get active devices with push tokens
    result = await db.execute(
        text("""
            SELECT device_id, push_token, device_type
            FROM mobile_devices
            WHERE user_id = :user_id
            AND is_active = TRUE
            AND push_token IS NOT NULL
            AND push_notifications_enabled = TRUE
        """),
        {"user_id": user.id}
    )
    
    for device in result:
        # Queue push notification
        # This would integrate with a push notification service
        pass