"""
Mobile market data and watchlist endpoints.
Provides real-time quotes, market movers, and watchlist management.
"""

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import json
import asyncio

from app.core.db.session import get_db
from app.models.user import User
from src.backend.api.mobile.base import (
    MobileResponse, MobilePaginatedResponse, MobilePaginationParams,
    get_pagination_params, create_paginated_response, RequireAuth,
    format_currency, format_percentage, create_etag, check_etag
)
from sqlalchemy import text


router = APIRouter(prefix="/api/mobile/v1/market")


class MarketStatus(str, Enum):
    """Market trading status."""
    PRE_MARKET = "pre_market"
    OPEN = "open"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"


class Quote(BaseModel):
    """Stock quote for mobile."""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    high: float
    low: float
    open: float
    previous_close: float
    timestamp: datetime
    
    # Formatted values
    price_formatted: Dict[str, Any]
    change_formatted: Dict[str, Any]
    change_percent_formatted: Dict[str, Any]
    market_cap_formatted: Optional[Dict[str, Any]]


class MarketMover(BaseModel):
    """Top gaining/losing stocks."""
    symbol: str
    name: str
    price: float
    change_percent: float
    volume: int
    
    # Formatted values
    price_formatted: Dict[str, Any]
    change_percent_formatted: Dict[str, Any]


class WatchlistItem(BaseModel):
    """Watchlist item with quote data."""
    id: str
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    notes: Optional[str]
    alerts_enabled: bool
    position: Optional[Dict[str, Any]]  # Current position if any
    
    # Formatted values
    price_formatted: Dict[str, Any]
    change_formatted: Dict[str, Any]
    change_percent_formatted: Dict[str, Any]


class MarketOverview(BaseModel):
    """Market overview data."""
    status: MarketStatus
    indices: List[Quote]
    top_gainers: List[MarketMover]
    top_losers: List[MarketMover]
    most_active: List[MarketMover]
    market_breadth: Dict[str, Any]


class ChartData(BaseModel):
    """Price chart data for mobile."""
    symbol: str
    interval: str  # 1m, 5m, 1h, 1d, etc.
    data: List[Dict[str, Any]]  # OHLCV data
    indicators: Optional[Dict[str, List[float]]]  # SMA, RSI, etc.


class AddToWatchlistRequest(BaseModel):
    """Add symbol to watchlist."""
    symbol: str
    notes: Optional[str] = None
    enable_alerts: bool = True


class SearchResult(BaseModel):
    """Symbol search result."""
    symbol: str
    name: str
    type: str  # stock, etf, crypto, etc.
    exchange: str
    

@router.get("/status", response_model=MobileResponse[Dict[str, Any]])
async def get_market_status(
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, Any]]:
    """Get current market status and hours."""
    now = datetime.utcnow()
    current_time = now.time()
    
    # Simplified market hours (NYSE)
    # Real implementation would check holidays, half days, etc.
    market_open = datetime.strptime("09:30", "%H:%M").time()
    market_close = datetime.strptime("16:00", "%H:%M").time()
    pre_market_start = datetime.strptime("04:00", "%H:%M").time()
    after_hours_end = datetime.strptime("20:00", "%H:%M").time()
    
    if now.weekday() >= 5:  # Weekend
        status = MarketStatus.CLOSED
        next_open = now + timedelta(days=(7 - now.weekday()))
        next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
    elif current_time < pre_market_start:
        status = MarketStatus.CLOSED
        next_open = now.replace(hour=4, minute=0, second=0, microsecond=0)
    elif current_time < market_open:
        status = MarketStatus.PRE_MARKET
        next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    elif current_time < market_close:
        status = MarketStatus.OPEN
        next_open = None
    elif current_time < after_hours_end:
        status = MarketStatus.AFTER_HOURS
        next_open = (now + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
    else:
        status = MarketStatus.CLOSED
        next_open = (now + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
    
    return MobileResponse(
        data={
            "status": status,
            "current_time": now,
            "next_open": next_open,
            "regular_hours": {
                "open": "09:30 EST",
                "close": "16:00 EST"
            },
            "extended_hours": {
                "pre_market": "04:00 - 09:30 EST",
                "after_hours": "16:00 - 20:00 EST"
            }
        }
    )


@router.get("/overview", response_model=MobileResponse[MarketOverview])
async def get_market_overview(
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MarketOverview]:
    """Get market overview with indices and movers."""
    # Get market status
    status_response = await get_market_status(db)
    status = status_response.data["status"]
    
    # Get major indices
    indices_query = """
        SELECT DISTINCT ON (symbol)
            symbol, name, price, 
            price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) as change,
            high, low, open, volume, timestamp
        FROM market_data
        WHERE symbol IN ('SPY', 'QQQ', 'DIA', 'IWM', 'VIX')
        ORDER BY symbol, timestamp DESC
    """
    
    indices_result = await db.execute(text(indices_query))
    indices = []
    
    for row in indices_result:
        change_percent = (row.change / (row.price - row.change) * 100) if row.change else 0
        indices.append(Quote(
            symbol=row.symbol,
            name=row.name,
            price=row.price,
            change=row.change or 0,
            change_percent=change_percent,
            volume=row.volume,
            market_cap=None,
            pe_ratio=None,
            high=row.high,
            low=row.low,
            open=row.open,
            previous_close=row.price - (row.change or 0),
            timestamp=row.timestamp,
            price_formatted=format_currency(row.price),
            change_formatted=format_currency(row.change or 0),
            change_percent_formatted=format_percentage(change_percent),
            market_cap_formatted=None
        ))
    
    # Get top gainers
    gainers_query = """
        WITH price_changes AS (
            SELECT DISTINCT ON (symbol)
                symbol, name, price, volume,
                (price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
                LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) * 100 as change_percent
            FROM market_data
            WHERE timestamp >= NOW() - INTERVAL '1 day'
            ORDER BY symbol, timestamp DESC
        )
        SELECT symbol, name, price, change_percent, volume
        FROM price_changes
        WHERE change_percent > 0
        ORDER BY change_percent DESC
        LIMIT 5
    """
    
    gainers_result = await db.execute(text(gainers_query))
    top_gainers = []
    
    for row in gainers_result:
        top_gainers.append(MarketMover(
            symbol=row.symbol,
            name=row.name,
            price=row.price,
            change_percent=row.change_percent,
            volume=row.volume,
            price_formatted=format_currency(row.price),
            change_percent_formatted=format_percentage(row.change_percent)
        ))
    
    # Get top losers
    losers_query = """
        WITH price_changes AS (
            SELECT DISTINCT ON (symbol)
                symbol, name, price, volume,
                (price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
                LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) * 100 as change_percent
            FROM market_data
            WHERE timestamp >= NOW() - INTERVAL '1 day'
            ORDER BY symbol, timestamp DESC
        )
        SELECT symbol, name, price, change_percent, volume
        FROM price_changes
        WHERE change_percent < 0
        ORDER BY change_percent
        LIMIT 5
    """
    
    losers_result = await db.execute(text(losers_query))
    top_losers = []
    
    for row in losers_result:
        top_losers.append(MarketMover(
            symbol=row.symbol,
            name=row.name,
            price=row.price,
            change_percent=row.change_percent,
            volume=row.volume,
            price_formatted=format_currency(row.price),
            change_percent_formatted=format_percentage(row.change_percent)
        ))
    
    # Get most active
    active_query = """
        SELECT DISTINCT ON (symbol)
            symbol, name, price, volume,
            (price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
            LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) * 100 as change_percent
        FROM market_data
        WHERE timestamp >= NOW() - INTERVAL '1 day'
        ORDER BY symbol, timestamp DESC, volume DESC
        LIMIT 5
    """
    
    active_result = await db.execute(text(active_query))
    most_active = []
    
    for row in active_result:
        most_active.append(MarketMover(
            symbol=row.symbol,
            name=row.name,
            price=row.price,
            change_percent=row.change_percent or 0,
            volume=row.volume,
            price_formatted=format_currency(row.price),
            change_percent_formatted=format_percentage(row.change_percent or 0)
        ))
    
    # Calculate market breadth
    breadth_query = """
        WITH price_changes AS (
            SELECT 
                CASE 
                    WHEN price > LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) THEN 'advancing'
                    WHEN price < LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) THEN 'declining'
                    ELSE 'unchanged'
                END as direction
            FROM market_data
            WHERE timestamp >= NOW() - INTERVAL '1 day'
        )
        SELECT 
            COUNT(CASE WHEN direction = 'advancing' THEN 1 END) as advancing,
            COUNT(CASE WHEN direction = 'declining' THEN 1 END) as declining,
            COUNT(CASE WHEN direction = 'unchanged' THEN 1 END) as unchanged
        FROM price_changes
    """
    
    breadth_result = await db.execute(text(breadth_query))
    breadth = breadth_result.first()
    
    market_breadth = {
        "advancing": breadth.advancing or 0,
        "declining": breadth.declining or 0,
        "unchanged": breadth.unchanged or 0,
        "ratio": round(breadth.advancing / breadth.declining, 2) if breadth.declining > 0 else 0
    }
    
    return MobileResponse(
        data=MarketOverview(
            status=status,
            indices=indices,
            top_gainers=top_gainers,
            top_losers=top_losers,
            most_active=most_active,
            market_breadth=market_breadth
        )
    )


@router.get("/quote/{symbol}", response_model=MobileResponse[Quote])
async def get_quote(
    symbol: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Quote]:
    """Get real-time quote for a symbol."""
    query = """
        WITH latest_quote AS (
            SELECT 
                symbol, name, price, high, low, open, volume,
                market_cap, pe_ratio, timestamp
            FROM market_data
            WHERE symbol = :symbol
            ORDER BY timestamp DESC
            LIMIT 1
        ),
        previous_close AS (
            SELECT price
            FROM market_data
            WHERE symbol = :symbol
            AND DATE(timestamp) < CURRENT_DATE
            ORDER BY timestamp DESC
            LIMIT 1
        )
        SELECT 
            lq.*,
            COALESCE(pc.price, lq.open) as previous_close
        FROM latest_quote lq
        LEFT JOIN previous_close pc ON TRUE
    """
    
    result = await db.execute(
        text(query),
        {"symbol": symbol.upper()}
    )
    
    row = result.first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, f"Quote not found for {symbol}")
    
    change = row.price - row.previous_close
    change_percent = (change / row.previous_close * 100) if row.previous_close else 0
    
    return MobileResponse(
        data=Quote(
            symbol=row.symbol,
            name=row.name,
            price=row.price,
            change=change,
            change_percent=change_percent,
            volume=row.volume,
            market_cap=row.market_cap,
            pe_ratio=row.pe_ratio,
            high=row.high,
            low=row.low,
            open=row.open,
            previous_close=row.previous_close,
            timestamp=row.timestamp,
            price_formatted=format_currency(row.price),
            change_formatted=format_currency(change),
            change_percent_formatted=format_percentage(change_percent),
            market_cap_formatted=format_currency(row.market_cap) if row.market_cap else None
        )
    )


@router.get("/chart/{symbol}", response_model=MobileResponse[ChartData])
async def get_chart_data(
    symbol: str,
    interval: str = Query("1d", regex="^(1m|5m|15m|30m|1h|4h|1d|1w|1M)$"),
    period: str = Query("1M", regex="^(1d|5d|1M|3M|6M|1y|5y)$"),
    indicators: Optional[str] = Query(None, description="Comma-separated indicators: sma20,sma50,rsi"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[ChartData]:
    """Get chart data for technical analysis."""
    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "1d":
        since = now - timedelta(days=1)
    elif period == "5d":
        since = now - timedelta(days=5)
    elif period == "1M":
        since = now - timedelta(days=30)
    elif period == "3M":
        since = now - timedelta(days=90)
    elif period == "6M":
        since = now - timedelta(days=180)
    elif period == "1y":
        since = now - timedelta(days=365)
    else:  # 5y
        since = now - timedelta(days=365 * 5)
    
    # Get OHLCV data
    # This is simplified - real implementation would aggregate by interval
    query = """
        SELECT 
            DATE_TRUNC(:interval, timestamp) as time,
            FIRST_VALUE(open) OVER w as open,
            MAX(high) OVER w as high,
            MIN(low) OVER w as low,
            LAST_VALUE(price) OVER w as close,
            SUM(volume) OVER w as volume
        FROM market_data
        WHERE symbol = :symbol
        AND timestamp >= :since
        WINDOW w AS (PARTITION BY DATE_TRUNC(:interval, timestamp) ORDER BY timestamp)
        ORDER BY time
    """
    
    # Map interval strings to PostgreSQL intervals
    interval_map = {
        "1m": "minute",
        "5m": "5 minutes",
        "15m": "15 minutes",
        "30m": "30 minutes",
        "1h": "hour",
        "4h": "4 hours",
        "1d": "day",
        "1w": "week",
        "1M": "month"
    }
    
    result = await db.execute(
        text(query),
        {
            "symbol": symbol.upper(),
            "since": since,
            "interval": interval_map[interval]
        }
    )
    
    data = []
    prices = []  # For indicator calculations
    
    for row in result:
        data.append({
            "time": row.time.isoformat(),
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume
        })
        prices.append(row.close)
    
    # Calculate indicators if requested
    indicators_data = {}
    if indicators and prices:
        indicator_list = indicators.split(',')
        
        # Simple Moving Averages
        for indicator in indicator_list:
            if indicator.startswith('sma'):
                period = int(indicator[3:])
                sma_values = _calculate_sma(prices, period)
                indicators_data[indicator] = sma_values
            
            elif indicator == 'rsi':
                rsi_values = _calculate_rsi(prices, 14)
                indicators_data['rsi'] = rsi_values
    
    return MobileResponse(
        data=ChartData(
            symbol=symbol.upper(),
            interval=interval,
            data=data,
            indicators=indicators_data if indicators_data else None
        )
    )


@router.get("/watchlist")
async def get_watchlist(
    pagination: MobilePaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's watchlist with real-time quotes."""
    # Get watchlist items
    query = """
        WITH watchlist_symbols AS (
            SELECT 
                w.id, w.symbol, w.notes, w.alerts_enabled, w.created_at,
                md.name, md.price, md.timestamp,
                LAG(md.price) OVER (PARTITION BY w.symbol ORDER BY md.timestamp) as prev_price
            FROM watchlist w
            JOIN (
                SELECT DISTINCT ON (symbol)
                    symbol, name, price, timestamp
                FROM market_data
                ORDER BY symbol, timestamp DESC
            ) md ON w.symbol = md.symbol
            WHERE w.user_id = :user_id
            ORDER BY w.position, w.created_at DESC
        ),
        user_positions AS (
            SELECT 
                symbol,
                SUM(CASE WHEN type = 'long' THEN shares ELSE -shares END) as shares,
                AVG(entry_price) as avg_cost
            FROM trades
            WHERE user_id = :user_id
            AND status = 'open'
            GROUP BY symbol
        )
        SELECT 
            ws.*,
            up.shares,
            up.avg_cost,
            up.shares * ws.price as position_value
        FROM watchlist_symbols ws
        LEFT JOIN user_positions up ON ws.symbol = up.symbol
    """
    
    # Count query
    count_query = "SELECT COUNT(*) FROM watchlist WHERE user_id = :user_id"
    
    # Apply pagination
    query += " LIMIT :limit OFFSET :offset"
    
    result = await db.execute(
        text(query),
        {
            "user_id": current_user.id,
            "limit": pagination.limit,
            "offset": pagination.offset
        }
    )
    
    count_result = await db.execute(
        text(count_query),
        {"user_id": current_user.id}
    )
    total = count_result.scalar()
    
    items = []
    for row in result:
        change = row.price - (row.prev_price or row.price)
        change_percent = (change / row.prev_price * 100) if row.prev_price else 0
        
        position = None
        if row.shares:
            unrealized_pnl = (row.price - row.avg_cost) * row.shares
            position = {
                "shares": row.shares,
                "avg_cost": format_currency(row.avg_cost),
                "value": format_currency(row.position_value),
                "unrealized_pnl": format_currency(unrealized_pnl)
            }
        
        items.append(WatchlistItem(
            id=str(row.id),
            symbol=row.symbol,
            name=row.name,
            price=row.price,
            change=change,
            change_percent=change_percent,
            notes=row.notes,
            alerts_enabled=row.alerts_enabled,
            position=position,
            price_formatted=format_currency(row.price),
            change_formatted=format_currency(change),
            change_percent_formatted=format_percentage(change_percent)
        ))
    
    return create_paginated_response(
        items=[item.dict() for item in items],
        total=total,
        pagination=pagination
    )


@router.post("/watchlist", response_model=MobileResponse[Dict[str, str]])
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Add symbol to watchlist."""
    try:
        # Check if already in watchlist
        existing = await db.execute(
            text("""
                SELECT 1 FROM watchlist
                WHERE user_id = :user_id
                AND symbol = :symbol
            """),
            {
                "user_id": current_user.id,
                "symbol": request.symbol.upper()
            }
        )
        
        if existing.scalar():
            from fastapi import HTTPException
            raise HTTPException(400, "Symbol already in watchlist")
        
        # Get current position for ordering
        position_result = await db.execute(
            text("""
                SELECT COALESCE(MAX(position), 0) + 1 as next_position
                FROM watchlist
                WHERE user_id = :user_id
            """),
            {"user_id": current_user.id}
        )
        next_position = position_result.scalar()
        
        # Add to watchlist
        result = await db.execute(
            text("""
                INSERT INTO watchlist (
                    user_id, symbol, notes, alerts_enabled, position
                ) VALUES (
                    :user_id, :symbol, :notes, :alerts_enabled, :position
                )
                RETURNING id
            """),
            {
                "user_id": current_user.id,
                "symbol": request.symbol.upper(),
                "notes": request.notes,
                "alerts_enabled": request.enable_alerts,
                "position": next_position
            }
        )
        
        watchlist_id = result.scalar()
        await db.commit()
        
        return MobileResponse(
            data={
                "id": str(watchlist_id),
                "message": f"{request.symbol} added to watchlist"
            }
        )
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"Failed to add to watchlist: {str(e)}")


@router.delete("/watchlist/{symbol}", response_model=MobileResponse[Dict[str, str]])
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, str]]:
    """Remove symbol from watchlist."""
    result = await db.execute(
        text("""
            DELETE FROM watchlist
            WHERE user_id = :user_id
            AND symbol = :symbol
        """),
        {
            "user_id": current_user.id,
            "symbol": symbol.upper()
        }
    )
    
    if result.rowcount == 0:
        from fastapi import HTTPException
        raise HTTPException(404, "Symbol not in watchlist")
    
    await db.commit()
    
    return MobileResponse(
        data={"message": f"{symbol} removed from watchlist"}
    )


@router.get("/search", response_model=MobileResponse[List[SearchResult]])
async def search_symbols(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[SearchResult]]:
    """Search for symbols by name or ticker."""
    search_term = f"%{q.upper()}%"
    
    query = """
        SELECT DISTINCT ON (symbol)
            symbol, name, asset_type, exchange
        FROM market_data
        WHERE symbol ILIKE :search_term
        OR name ILIKE :search_term
        ORDER BY symbol, timestamp DESC
        LIMIT :limit
    """
    
    result = await db.execute(
        text(query),
        {
            "search_term": search_term,
            "limit": limit
        }
    )
    
    results = []
    for row in result:
        results.append(SearchResult(
            symbol=row.symbol,
            name=row.name,
            type=row.asset_type or "stock",
            exchange=row.exchange or "NASDAQ"
        ))
    
    return MobileResponse(data=results)


@router.websocket("/stream")
async def market_stream(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time market data."""
    await websocket.accept()
    
    # Get user from token
    try:
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        from app.core.auth import decode_access_token
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # Subscribe to symbols
    subscribed_symbols = set()
    
    try:
        while True:
            # Receive messages
            data = await websocket.receive_json()
            
            if data.get("action") == "subscribe":
                symbols = data.get("symbols", [])
                subscribed_symbols.update(symbols)
                
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": list(subscribed_symbols)
                })
            
            elif data.get("action") == "unsubscribe":
                symbols = data.get("symbols", [])
                subscribed_symbols.difference_update(symbols)
                
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": symbols
                })
            
            # Send real-time updates for subscribed symbols
            if subscribed_symbols:
                # In production, this would connect to a real-time data feed
                # For now, simulate with database polling
                quotes = await _get_realtime_quotes(subscribed_symbols, db)
                
                await websocket.send_json({
                    "type": "quotes",
                    "data": quotes
                })
            
            # Rate limit
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


# Helper functions
def _calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
    """Calculate Simple Moving Average."""
    sma = []
    for i in range(len(prices)):
        if i < period - 1:
            sma.append(None)
        else:
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma.append(round(avg, 2))
    return sma


def _calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return [None] * len(prices)
    
    rsi = [None] * period
    
    # Calculate initial average gain/loss
    gains = []
    losses = []
    
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    # Calculate RSI
    for i in range(period, len(prices)):
        change = prices[i] - prices[i - 1]
        
        if change > 0:
            gain = change
            loss = 0
        else:
            gain = 0
            loss = abs(change)
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(round(100 - (100 / (1 + rs)), 2))
    
    return rsi


async def _get_realtime_quotes(
    symbols: set,
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """Get real-time quotes for symbols."""
    query = """
        SELECT DISTINCT ON (symbol)
            symbol, price, 
            price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) as change,
            volume, timestamp
        FROM market_data
        WHERE symbol = ANY(:symbols)
        ORDER BY symbol, timestamp DESC
    """
    
    result = await db.execute(
        text(query),
        {"symbols": list(symbols)}
    )
    
    quotes = []
    for row in result:
        change_percent = (row.change / (row.price - row.change) * 100) if row.change else 0
        quotes.append({
            "symbol": row.symbol,
            "price": row.price,
            "change": row.change or 0,
            "change_percent": round(change_percent, 2),
            "volume": row.volume,
            "timestamp": row.timestamp.isoformat()
        })
    
    return quotes
