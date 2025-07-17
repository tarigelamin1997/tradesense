"""
Mobile-optimized analytics endpoints.
Provides lightweight, chart-ready data for mobile visualization.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from core.db.session import get_db
from models.user import User
from api.mobile.base import (
    MobileResponse, RequireAuth, format_currency, format_percentage
)
from sqlalchemy import text


router = APIRouter(prefix="/api/mobile/v1/analytics")


class ChartDataPoint(BaseModel):
    """Single data point for charts."""
    timestamp: datetime
    value: float
    label: Optional[str] = None


class MobileChartData(BaseModel):
    """Chart data optimized for mobile rendering."""
    type: str  # line, bar, pie, etc.
    data_points: List[ChartDataPoint]
    metadata: Dict[str, Any]


class PerformanceSnapshot(BaseModel):
    """Quick performance snapshot."""
    total_pnl: Dict[str, Any]
    total_pnl_percent: Dict[str, Any]
    win_rate: Dict[str, Any]
    profit_factor: float
    sharpe_ratio: Optional[float]
    best_day: Dict[str, Any]
    worst_day: Dict[str, Any]
    current_streak: Dict[str, Any]


class MobileAnalyticsSummary(BaseModel):
    """Complete analytics summary for mobile."""
    performance: PerformanceSnapshot
    charts: Dict[str, MobileChartData]
    top_winners: List[Dict[str, Any]]
    top_losers: List[Dict[str, Any]]
    symbol_breakdown: List[Dict[str, Any]]
    trading_activity: Dict[str, Any]


@router.get("/dashboard", response_model=MobileResponse[MobileAnalyticsSummary])
async def get_analytics_dashboard(
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y|all)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MobileAnalyticsSummary]:
    """Get complete analytics dashboard for mobile."""
    # Calculate date range
    now = datetime.utcnow()
    if timeframe == "7d":
        since = now - timedelta(days=7)
    elif timeframe == "30d":
        since = now - timedelta(days=30)
    elif timeframe == "90d":
        since = now - timedelta(days=90)
    elif timeframe == "1y":
        since = now - timedelta(days=365)
    else:
        since = None
    
    # Get performance snapshot
    performance = await _get_performance_snapshot(current_user.id, since, db)
    
    # Get chart data
    equity_chart = await _get_equity_curve(current_user.id, since, db)
    daily_pnl_chart = await _get_daily_pnl_chart(current_user.id, since, db)
    win_loss_chart = await _get_win_loss_distribution(current_user.id, since, db)
    
    # Get top trades
    top_winners = await _get_top_trades(current_user.id, since, "winners", 5, db)
    top_losers = await _get_top_trades(current_user.id, since, "losers", 5, db)
    
    # Get symbol breakdown
    symbol_breakdown = await _get_symbol_breakdown(current_user.id, since, db)
    
    # Get trading activity
    trading_activity = await _get_trading_activity(current_user.id, since, db)
    
    return MobileResponse(
        data=MobileAnalyticsSummary(
            performance=performance,
            charts={
                "equity": equity_chart,
                "daily_pnl": daily_pnl_chart,
                "win_loss": win_loss_chart
            },
            top_winners=top_winners,
            top_losers=top_losers,
            symbol_breakdown=symbol_breakdown,
            trading_activity=trading_activity
        )
    )


@router.get("/equity-curve", response_model=MobileResponse[MobileChartData])
async def get_equity_curve(
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y|all)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MobileChartData]:
    """Get equity curve data for charting."""
    since = _get_timeframe_start(timeframe)
    chart = await _get_equity_curve(current_user.id, since, db)
    return MobileResponse(data=chart)


@router.get("/win-rate-trend", response_model=MobileResponse[MobileChartData])
async def get_win_rate_trend(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[MobileChartData]:
    """Get win rate trend over time."""
    # Determine grouping
    if period == "daily":
        date_trunc = "day"
        min_trades = 1
    elif period == "weekly":
        date_trunc = "week"
        min_trades = 3
    else:
        date_trunc = "month"
        min_trades = 10
    
    query = f"""
        WITH period_stats AS (
            SELECT 
                DATE_TRUNC('{date_trunc}', exit_time) as period,
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
            AND exit_time >= NOW() - INTERVAL '1 year'
            GROUP BY DATE_TRUNC('{date_trunc}', exit_time)
            HAVING COUNT(*) >= :min_trades
        )
        SELECT 
            period,
            ROUND(wins::numeric / total_trades * 100, 2) as win_rate
        FROM period_stats
        ORDER BY period
    """
    
    result = await db.execute(
        text(query),
        {
            "user_id": current_user.id,
            "min_trades": min_trades
        }
    )
    
    data_points = []
    for row in result:
        data_points.append(ChartDataPoint(
            timestamp=row.period,
            value=float(row.win_rate),
            label=f"{row.win_rate}%"
        ))
    
    return MobileResponse(
        data=MobileChartData(
            type="line",
            data_points=data_points,
            metadata={
                "period": period,
                "y_axis": "Win Rate %",
                "min_trades_filter": min_trades
            }
        )
    )


@router.get("/symbol-performance", response_model=MobileResponse[List[Dict[str, Any]]])
async def get_symbol_performance(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("pnl", regex="^(pnl|trades|win_rate)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[Dict[str, Any]]]:
    """Get performance breakdown by symbol."""
    order_by = {
        "pnl": "total_pnl DESC",
        "trades": "trade_count DESC",
        "win_rate": "win_rate DESC"
    }[sort_by]
    
    query = f"""
        SELECT 
            symbol,
            COUNT(*) as trade_count,
            SUM(pnl) as total_pnl,
            COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
            COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
            AVG(pnl) as avg_pnl,
            MAX(pnl) as best_trade,
            MIN(pnl) as worst_trade,
            ROUND(
                COUNT(CASE WHEN pnl > 0 THEN 1 END)::numeric / 
                NULLIF(COUNT(*), 0) * 100, 
                2
            ) as win_rate
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
        GROUP BY symbol
        ORDER BY {order_by}
        LIMIT :limit
    """
    
    result = await db.execute(
        text(query),
        {
            "user_id": current_user.id,
            "limit": limit
        }
    )
    
    symbols = []
    for row in result:
        symbols.append({
            "symbol": row.symbol,
            "stats": {
                "trade_count": row.trade_count,
                "total_pnl": format_currency(row.total_pnl),
                "avg_pnl": format_currency(row.avg_pnl),
                "win_rate": format_percentage(row.win_rate),
                "wins": row.wins,
                "losses": row.losses,
                "best_trade": format_currency(row.best_trade),
                "worst_trade": format_currency(row.worst_trade)
            }
        })
    
    return MobileResponse(data=symbols)


@router.get("/time-analysis", response_model=MobileResponse[Dict[str, Any]])
async def get_time_analysis(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, Any]]:
    """Analyze trading performance by time of day and day of week."""
    # Performance by hour
    hour_query = """
        SELECT 
            EXTRACT(HOUR FROM entry_time) as hour,
            COUNT(*) as trades,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
        GROUP BY EXTRACT(HOUR FROM entry_time)
        ORDER BY hour
    """
    
    hour_result = await db.execute(
        text(hour_query),
        {"user_id": current_user.id}
    )
    
    hourly_data = []
    for row in hour_result:
        hourly_data.append({
            "hour": int(row.hour),
            "trades": row.trades,
            "avg_pnl": float(row.avg_pnl or 0),
            "total_pnl": float(row.total_pnl or 0)
        })
    
    # Performance by day of week
    dow_query = """
        SELECT 
            EXTRACT(DOW FROM entry_time) as day_of_week,
            TO_CHAR(entry_time, 'Day') as day_name,
            COUNT(*) as trades,
            AVG(pnl) as avg_pnl,
            SUM(pnl) as total_pnl,
            COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
        GROUP BY EXTRACT(DOW FROM entry_time), TO_CHAR(entry_time, 'Day')
        ORDER BY day_of_week
    """
    
    dow_result = await db.execute(
        text(dow_query),
        {"user_id": current_user.id}
    )
    
    daily_data = []
    for row in dow_result:
        win_rate = (row.wins / row.trades * 100) if row.trades > 0 else 0
        daily_data.append({
            "day": row.day_name.strip(),
            "trades": row.trades,
            "avg_pnl": format_currency(row.avg_pnl or 0),
            "total_pnl": format_currency(row.total_pnl or 0),
            "win_rate": format_percentage(win_rate)
        })
    
    return MobileResponse(
        data={
            "by_hour": hourly_data,
            "by_day": daily_data,
            "best_hour": max(hourly_data, key=lambda x: x['avg_pnl'])['hour'] if hourly_data else None,
            "best_day": max(daily_data, key=lambda x: x['avg_pnl']['value'])['day'] if daily_data else None
        }
    )


# Helper functions
def _get_timeframe_start(timeframe: str) -> Optional[datetime]:
    """Get start date for timeframe."""
    now = datetime.utcnow()
    if timeframe == "7d":
        return now - timedelta(days=7)
    elif timeframe == "30d":
        return now - timedelta(days=30)
    elif timeframe == "90d":
        return now - timedelta(days=90)
    elif timeframe == "1y":
        return now - timedelta(days=365)
    return None


async def _get_performance_snapshot(
    user_id: str,
    since: Optional[datetime],
    db: AsyncSession
) -> PerformanceSnapshot:
    """Get performance snapshot."""
    # Base query
    query = """
        SELECT 
            SUM(pnl) as total_pnl,
            COUNT(*) as total_trades,
            COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
            COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
            AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
            AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
            MAX(pnl) as max_win,
            MIN(pnl) as min_loss,
            STDDEV(pnl) as pnl_stddev
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND exit_time >= :since"
        params["since"] = since
    
    result = await db.execute(text(query), params)
    stats = result.first()
    
    # Calculate derived metrics
    win_rate = 0
    profit_factor = 0
    total_pnl_percent = 0
    
    if stats.total_trades > 0:
        win_rate = (stats.wins / stats.total_trades) * 100
        
        if stats.avg_loss and stats.avg_loss != 0:
            profit_factor = abs((stats.avg_win * stats.wins) / (stats.avg_loss * stats.losses))
        
        # Get initial capital for percentage calculation
        capital_result = await db.execute(
            text("""
                SELECT starting_capital
                FROM users
                WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        starting_capital = capital_result.scalar() or 100000
        total_pnl_percent = (stats.total_pnl / starting_capital) * 100 if stats.total_pnl else 0
    
    # Get best/worst day
    daily_query = """
        SELECT 
            DATE(exit_time) as date,
            SUM(pnl) as daily_pnl
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
    """
    
    if since:
        daily_query += " AND exit_time >= :since"
    
    daily_query += """
        GROUP BY DATE(exit_time)
        ORDER BY daily_pnl DESC
    """
    
    daily_result = await db.execute(text(daily_query), params)
    daily_pnls = list(daily_result)
    
    best_day = {"date": None, "pnl": format_currency(0)}
    worst_day = {"date": None, "pnl": format_currency(0)}
    
    if daily_pnls:
        best = daily_pnls[0]
        worst = daily_pnls[-1]
        best_day = {
            "date": best.date,
            "pnl": format_currency(best.daily_pnl)
        }
        worst_day = {
            "date": worst.date,
            "pnl": format_currency(worst.daily_pnl)
        }
    
    # Get current streak
    streak_query = """
        WITH ordered_trades AS (
            SELECT 
                pnl,
                CASE WHEN pnl > 0 THEN 1 ELSE -1 END as result,
                ROW_NUMBER() OVER (ORDER BY exit_time DESC) as rn
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
            ORDER BY exit_time DESC
            LIMIT 20
        ),
        streak_calc AS (
            SELECT 
                result,
                COUNT(*) as streak_length
            FROM ordered_trades
            WHERE result = (SELECT result FROM ordered_trades WHERE rn = 1)
            AND rn = 1 + (SELECT COUNT(*) FROM ordered_trades ot2 
                         WHERE ot2.rn < ordered_trades.rn 
                         AND ot2.result != ordered_trades.result)
            GROUP BY result
        )
        SELECT result, streak_length FROM streak_calc
    """
    
    streak_result = await db.execute(text(streak_query), {"user_id": user_id})
    streak_row = streak_result.first()
    
    current_streak = {"type": "none", "count": 0}
    if streak_row:
        current_streak = {
            "type": "winning" if streak_row.result > 0 else "losing",
            "count": streak_row.streak_length
        }
    
    # Calculate Sharpe ratio (simplified)
    sharpe_ratio = None
    if stats.pnl_stddev and stats.pnl_stddev > 0:
        # Assuming daily returns, annualized
        sharpe_ratio = (stats.total_pnl / stats.total_trades) / stats.pnl_stddev * (252 ** 0.5)
        sharpe_ratio = round(sharpe_ratio, 2)
    
    return PerformanceSnapshot(
        total_pnl=format_currency(stats.total_pnl or 0),
        total_pnl_percent=format_percentage(total_pnl_percent),
        win_rate=format_percentage(win_rate),
        profit_factor=round(profit_factor, 2),
        sharpe_ratio=sharpe_ratio,
        best_day=best_day,
        worst_day=worst_day,
        current_streak=current_streak
    )


async def _get_equity_curve(
    user_id: str,
    since: Optional[datetime],
    db: AsyncSession
) -> MobileChartData:
    """Get equity curve data."""
    query = """
        WITH cumulative AS (
            SELECT 
                exit_time,
                SUM(pnl) OVER (ORDER BY exit_time) as cumulative_pnl
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND exit_time >= :since"
        params["since"] = since
    
    query += """
            ORDER BY exit_time
        )
        SELECT 
            DATE(exit_time) as date,
            MAX(cumulative_pnl) as equity
        FROM cumulative
        GROUP BY DATE(exit_time)
        ORDER BY date
    """
    
    result = await db.execute(text(query), params)
    
    data_points = []
    for row in result:
        data_points.append(ChartDataPoint(
            timestamp=row.date,
            value=float(row.equity),
            label=f"${row.equity:,.0f}"
        ))
    
    return MobileChartData(
        type="line",
        data_points=data_points,
        metadata={
            "y_axis": "Account Equity",
            "smoothing": True,
            "fill": True
        }
    )


async def _get_daily_pnl_chart(
    user_id: str,
    since: Optional[datetime],
    db: AsyncSession
) -> MobileChartData:
    """Get daily P&L chart data."""
    query = """
        SELECT 
            DATE(exit_time) as date,
            SUM(pnl) as daily_pnl
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND exit_time >= :since"
        params["since"] = since
    
    query += """
        GROUP BY DATE(exit_time)
        ORDER BY date
    """
    
    result = await db.execute(text(query), params)
    
    data_points = []
    for row in result:
        data_points.append(ChartDataPoint(
            timestamp=row.date,
            value=float(row.daily_pnl),
            label=f"${row.daily_pnl:,.0f}"
        ))
    
    return MobileChartData(
        type="bar",
        data_points=data_points,
        metadata={
            "y_axis": "Daily P&L",
            "positive_color": "#10b981",
            "negative_color": "#ef4444"
        }
    )


async def _get_win_loss_distribution(
    user_id: str,
    since: Optional[datetime],
    db: AsyncSession
) -> MobileChartData:
    """Get win/loss distribution."""
    query = """
        SELECT 
            COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
            COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
            COUNT(CASE WHEN pnl = 0 THEN 1 END) as breakeven
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND exit_time >= :since"
        params["since"] = since
    
    result = await db.execute(text(query), params)
    stats = result.first()
    
    data_points = [
        ChartDataPoint(
            timestamp=datetime.utcnow(),
            value=float(stats.wins or 0),
            label=f"Wins ({stats.wins})"
        ),
        ChartDataPoint(
            timestamp=datetime.utcnow(),
            value=float(stats.losses or 0),
            label=f"Losses ({stats.losses})"
        )
    ]
    
    if stats.breakeven:
        data_points.append(ChartDataPoint(
            timestamp=datetime.utcnow(),
            value=float(stats.breakeven),
            label=f"Breakeven ({stats.breakeven})"
        ))
    
    return MobileChartData(
        type="pie",
        data_points=data_points,
        metadata={
            "colors": ["#10b981", "#ef4444", "#6b7280"]
        }
    )


async def _get_top_trades(
    user_id: str,
    since: Optional[datetime],
    trade_type: str,
    limit: int,
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """Get top winning or losing trades."""
    order = "DESC" if trade_type == "winners" else "ASC"
    
    query = f"""
        SELECT 
            symbol, pnl, exit_time,
            ROUND(pnl / (entry_price * shares) * 100, 2) as pnl_percent
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
        AND pnl {'>' if trade_type == 'winners' else '<'} 0
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND exit_time >= :since"
        params["since"] = since
    
    query += f"""
        ORDER BY pnl {order}
        LIMIT :limit
    """
    params["limit"] = limit
    
    result = await db.execute(text(query), params)
    
    trades = []
    for row in result:
        trades.append({
            "symbol": row.symbol,
            "pnl": format_currency(row.pnl),
            "pnl_percent": format_percentage(row.pnl_percent),
            "date": row.exit_time.date()
        })
    
    return trades


async def _get_symbol_breakdown(
    user_id: str,
    since: Optional[datetime],
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """Get P&L breakdown by symbol."""
    query = """
        SELECT 
            symbol,
            COUNT(*) as trades,
            SUM(pnl) as total_pnl
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND exit_time >= :since"
        params["since"] = since
    
    query += """
        GROUP BY symbol
        ORDER BY total_pnl DESC
        LIMIT 10
    """
    
    result = await db.execute(text(query), params)
    
    symbols = []
    for row in result:
        symbols.append({
            "symbol": row.symbol,
            "trades": row.trades,
            "pnl": format_currency(row.total_pnl)
        })
    
    return symbols


async def _get_trading_activity(
    user_id: str,
    since: Optional[datetime],
    db: AsyncSession
) -> Dict[str, Any]:
    """Get trading activity summary."""
    query = """
        SELECT 
            COUNT(DISTINCT DATE(entry_time)) as trading_days,
            COUNT(*) as total_trades,
            COUNT(DISTINCT symbol) as unique_symbols,
            AVG(EXTRACT(EPOCH FROM (exit_time - entry_time))/3600) as avg_hold_hours
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
    """
    
    params = {"user_id": user_id}
    
    if since:
        query += " AND entry_time >= :since"
        params["since"] = since
    
    result = await db.execute(text(query), params)
    stats = result.first()
    
    # Calculate trades per day
    trades_per_day = 0
    if stats.trading_days > 0:
        trades_per_day = stats.total_trades / stats.trading_days
    
    return {
        "trading_days": stats.trading_days or 0,
        "total_trades": stats.total_trades or 0,
        "trades_per_day": round(trades_per_day, 1),
        "unique_symbols": stats.unique_symbols or 0,
        "avg_hold_time_hours": round(stats.avg_hold_hours or 0, 1)
    }