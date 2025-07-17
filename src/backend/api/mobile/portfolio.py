"""
Mobile portfolio management endpoints.
Provides portfolio overview, positions, and performance metrics.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from core.db.session import get_db
from models.user import User
from src.backend.api.mobile.base import (
    MobileResponse, RequireAuth, format_currency, format_percentage
)
from sqlalchemy import text


router = APIRouter(prefix="/api/mobile/v1/portfolio")


class AssetType(str, Enum):
    """Types of assets in portfolio."""
    STOCK = "stock"
    OPTION = "option"
    CRYPTO = "crypto"
    FOREX = "forex"
    FUTURES = "futures"


class Position(BaseModel):
    """Portfolio position."""
    id: str
    symbol: str
    asset_type: AssetType
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    realized_pnl: float
    total_pnl: float
    open_trades: int
    last_trade_date: datetime
    
    # Formatted values
    market_value_formatted: Dict[str, Any]
    unrealized_pnl_formatted: Dict[str, Any]
    unrealized_pnl_percent_formatted: Dict[str, Any]
    total_pnl_formatted: Dict[str, Any]


class PortfolioSummary(BaseModel):
    """Portfolio overview for mobile."""
    total_value: Dict[str, Any]
    cash_balance: Dict[str, Any]
    buying_power: Dict[str, Any]
    day_pnl: Dict[str, Any]
    day_pnl_percent: Dict[str, Any]
    total_pnl: Dict[str, Any]
    total_pnl_percent: Dict[str, Any]
    positions_count: int
    margin_used: Optional[Dict[str, Any]] = None
    

class PortfolioAllocation(BaseModel):
    """Portfolio allocation breakdown."""
    by_asset_type: List[Dict[str, Any]]
    by_sector: List[Dict[str, Any]]
    by_symbol: List[Dict[str, Any]]
    concentration_risk: Dict[str, Any]


class PortfolioHistory(BaseModel):
    """Historical portfolio value."""
    date: datetime
    value: float
    cash: float
    positions_value: float
    daily_pnl: Optional[float]
    daily_pnl_percent: Optional[float]


@router.get("/summary", response_model=MobileResponse[PortfolioSummary])
async def get_portfolio_summary(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[PortfolioSummary]:
    """Get portfolio summary for mobile dashboard."""
    # Get account summary
    account_query = """
        SELECT 
            cash_balance,
            starting_capital,
            margin_available,
            margin_used
        FROM trading_accounts
        WHERE user_id = :user_id
        AND is_primary = TRUE
    """
    
    account_result = await db.execute(
        text(account_query),
        {"user_id": current_user.id}
    )
    account = account_result.first()
    
    if not account:
        # Create default account if none exists
        cash_balance = 100000.0
        starting_capital = 100000.0
        margin_available = 0
        margin_used = 0
    else:
        cash_balance = account.cash_balance
        starting_capital = account.starting_capital
        margin_available = account.margin_available or 0
        margin_used = account.margin_used or 0
    
    # Get current positions value
    positions_query = """
        WITH current_positions AS (
            SELECT 
                symbol,
                SUM(CASE WHEN type = 'long' THEN shares ELSE -shares END) as net_shares,
                AVG(entry_price) as avg_cost
            FROM trades
            WHERE user_id = :user_id
            AND status = 'open'
            GROUP BY symbol
            HAVING SUM(CASE WHEN type = 'long' THEN shares ELSE -shares END) != 0
        ),
        market_prices AS (
            SELECT DISTINCT ON (symbol) 
                symbol, price as current_price
            FROM market_data
            ORDER BY symbol, timestamp DESC
        )
        SELECT 
            COUNT(*) as positions_count,
            SUM(cp.net_shares * mp.current_price) as positions_value,
            SUM((mp.current_price - cp.avg_cost) * cp.net_shares) as unrealized_pnl
        FROM current_positions cp
        JOIN market_prices mp ON cp.symbol = mp.symbol
    """
    
    positions_result = await db.execute(
        text(positions_query),
        {"user_id": current_user.id}
    )
    positions_data = positions_result.first()
    
    positions_count = positions_data.positions_count or 0
    positions_value = positions_data.positions_value or 0
    unrealized_pnl = positions_data.unrealized_pnl or 0
    
    # Calculate total portfolio value
    total_value = cash_balance + positions_value
    
    # Get today's P&L
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    day_pnl_query = """
        SELECT 
            SUM(pnl) as realized_pnl
        FROM trades
        WHERE user_id = :user_id
        AND status = 'closed'
        AND exit_time >= :today_start
    """
    
    day_pnl_result = await db.execute(
        text(day_pnl_query),
        {"user_id": current_user.id, "today_start": today_start}
    )
    day_realized_pnl = day_pnl_result.scalar() or 0
    
    # Get yesterday's closing value for day change
    yesterday_query = """
        SELECT portfolio_value
        FROM portfolio_history
        WHERE user_id = :user_id
        AND date = :yesterday
    """
    
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()
    yesterday_result = await db.execute(
        text(yesterday_query),
        {"user_id": current_user.id, "yesterday": yesterday}
    )
    yesterday_value = yesterday_result.scalar() or total_value
    
    # Calculate day change
    day_pnl = total_value - yesterday_value
    day_pnl_percent = (day_pnl / yesterday_value * 100) if yesterday_value > 0 else 0
    
    # Calculate total P&L
    total_pnl = total_value - starting_capital
    total_pnl_percent = (total_pnl / starting_capital * 100) if starting_capital > 0 else 0
    
    # Calculate buying power
    buying_power = cash_balance + margin_available
    
    return MobileResponse(
        data=PortfolioSummary(
            total_value=format_currency(total_value),
            cash_balance=format_currency(cash_balance),
            buying_power=format_currency(buying_power),
            day_pnl=format_currency(day_pnl),
            day_pnl_percent=format_percentage(day_pnl_percent),
            total_pnl=format_currency(total_pnl),
            total_pnl_percent=format_percentage(total_pnl_percent),
            positions_count=positions_count,
            margin_used=format_currency(margin_used) if margin_used > 0 else None
        )
    )


@router.get("/positions", response_model=MobileResponse[List[Position]])
async def get_positions(
    asset_type: Optional[AssetType] = None,
    sort_by: str = Query("value", regex="^(value|pnl|symbol|percent)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[Position]]:
    """Get current portfolio positions."""
    # Build query for open positions
    query = """
        WITH current_positions AS (
            SELECT 
                symbol,
                MIN(id) as first_trade_id,
                SUM(CASE WHEN type = 'long' THEN shares ELSE -shares END) as net_shares,
                AVG(entry_price) as avg_cost,
                COUNT(*) as open_trades,
                MAX(entry_time) as last_trade_date,
                SUM(CASE WHEN type = 'long' THEN entry_price * shares 
                         ELSE -entry_price * shares END) / 
                SUM(CASE WHEN type = 'long' THEN shares ELSE -shares END) as weighted_avg_cost
            FROM trades
            WHERE user_id = :user_id
            AND status = 'open'
    """
    
    if asset_type:
        query += " AND asset_type = :asset_type"
    
    query += """
            GROUP BY symbol
            HAVING SUM(CASE WHEN type = 'long' THEN shares ELSE -shares END) != 0
        ),
        market_prices AS (
            SELECT DISTINCT ON (symbol) 
                symbol, 
                price as current_price,
                asset_type
            FROM market_data
            ORDER BY symbol, timestamp DESC
        ),
        realized_pnl AS (
            SELECT 
                symbol,
                SUM(pnl) as total_realized
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
            GROUP BY symbol
        )
        SELECT 
            cp.first_trade_id as id,
            cp.symbol,
            COALESCE(mp.asset_type, 'stock') as asset_type,
            cp.net_shares as quantity,
            cp.weighted_avg_cost as avg_cost,
            mp.current_price,
            cp.net_shares * mp.current_price as market_value,
            (mp.current_price - cp.weighted_avg_cost) * cp.net_shares as unrealized_pnl,
            COALESCE(rp.total_realized, 0) as realized_pnl,
            cp.open_trades,
            cp.last_trade_date
        FROM current_positions cp
        JOIN market_prices mp ON cp.symbol = mp.symbol
        LEFT JOIN realized_pnl rp ON cp.symbol = rp.symbol
    """
    
    # Apply sorting
    if sort_by == "value":
        query += " ORDER BY market_value DESC"
    elif sort_by == "pnl":
        query += " ORDER BY unrealized_pnl DESC"
    elif sort_by == "symbol":
        query += " ORDER BY cp.symbol"
    elif sort_by == "percent":
        query += " ORDER BY (mp.current_price - cp.weighted_avg_cost) / cp.weighted_avg_cost DESC"
    
    params = {"user_id": current_user.id}
    if asset_type:
        params["asset_type"] = asset_type
    
    result = await db.execute(text(query), params)
    
    positions = []
    for row in result:
        unrealized_pnl_percent = (
            (row.unrealized_pnl / (row.avg_cost * row.quantity) * 100)
            if row.avg_cost > 0 and row.quantity > 0
            else 0
        )
        
        total_pnl = row.unrealized_pnl + row.realized_pnl
        
        positions.append(Position(
            id=str(row.id),
            symbol=row.symbol,
            asset_type=row.asset_type,
            quantity=row.quantity,
            avg_cost=row.avg_cost,
            current_price=row.current_price,
            market_value=row.market_value,
            unrealized_pnl=row.unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            realized_pnl=row.realized_pnl,
            total_pnl=total_pnl,
            open_trades=row.open_trades,
            last_trade_date=row.last_trade_date,
            market_value_formatted=format_currency(row.market_value),
            unrealized_pnl_formatted=format_currency(row.unrealized_pnl),
            unrealized_pnl_percent_formatted=format_percentage(unrealized_pnl_percent),
            total_pnl_formatted=format_currency(total_pnl)
        ))
    
    return MobileResponse(data=positions)


@router.get("/allocation", response_model=MobileResponse[PortfolioAllocation])
async def get_portfolio_allocation(
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[PortfolioAllocation]:
    """Get portfolio allocation breakdown."""
    # Get positions with values
    positions_query = """
        WITH current_positions AS (
            SELECT 
                t.symbol,
                md.asset_type,
                md.sector,
                SUM(CASE WHEN t.type = 'long' THEN t.shares ELSE -t.shares END) as net_shares,
                md.price as current_price
            FROM trades t
            JOIN (
                SELECT DISTINCT ON (symbol) 
                    symbol, price, asset_type, sector
                FROM market_data
                ORDER BY symbol, timestamp DESC
            ) md ON t.symbol = md.symbol
            WHERE t.user_id = :user_id
            AND t.status = 'open'
            GROUP BY t.symbol, md.asset_type, md.sector, md.price
            HAVING SUM(CASE WHEN t.type = 'long' THEN t.shares ELSE -t.shares END) != 0
        )
        SELECT 
            symbol,
            COALESCE(asset_type, 'stock') as asset_type,
            COALESCE(sector, 'Other') as sector,
            net_shares * current_price as market_value
        FROM current_positions
    """
    
    result = await db.execute(
        text(positions_query),
        {"user_id": current_user.id}
    )
    
    # Calculate allocations
    by_asset_type = {}
    by_sector = {}
    by_symbol = {}
    total_value = 0
    
    for row in result:
        value = row.market_value
        total_value += value
        
        # By asset type
        if row.asset_type not in by_asset_type:
            by_asset_type[row.asset_type] = 0
        by_asset_type[row.asset_type] += value
        
        # By sector
        if row.sector not in by_sector:
            by_sector[row.sector] = 0
        by_sector[row.sector] += value
        
        # By symbol
        by_symbol[row.symbol] = value
    
    # Convert to percentages and format
    asset_type_allocation = []
    for asset_type, value in sorted(by_asset_type.items(), key=lambda x: x[1], reverse=True):
        percentage = (value / total_value * 100) if total_value > 0 else 0
        asset_type_allocation.append({
            "type": asset_type,
            "value": format_currency(value),
            "percentage": format_percentage(percentage)
        })
    
    sector_allocation = []
    for sector, value in sorted(by_sector.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (value / total_value * 100) if total_value > 0 else 0
        sector_allocation.append({
            "sector": sector,
            "value": format_currency(value),
            "percentage": format_percentage(percentage)
        })
    
    symbol_allocation = []
    for symbol, value in sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (value / total_value * 100) if total_value > 0 else 0
        symbol_allocation.append({
            "symbol": symbol,
            "value": format_currency(value),
            "percentage": format_percentage(percentage)
        })
    
    # Calculate concentration risk
    max_position_percent = 0
    if by_symbol and total_value > 0:
        max_position_value = max(by_symbol.values())
        max_position_percent = max_position_value / total_value * 100
    
    concentration_risk = {
        "status": "high" if max_position_percent > 25 else "medium" if max_position_percent > 15 else "low",
        "max_position_percent": format_percentage(max_position_percent),
        "recommendation": (
            "Consider reducing position size" if max_position_percent > 25
            else "Monitor concentration" if max_position_percent > 15
            else "Well diversified"
        )
    }
    
    return MobileResponse(
        data=PortfolioAllocation(
            by_asset_type=asset_type_allocation,
            by_sector=sector_allocation,
            by_symbol=symbol_allocation,
            concentration_risk=concentration_risk
        )
    )


@router.get("/history", response_model=MobileResponse[List[PortfolioHistory]])
async def get_portfolio_history(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[List[PortfolioHistory]]:
    """Get historical portfolio values."""
    since = datetime.utcnow() - timedelta(days=days)
    
    query = """
        SELECT 
            date,
            portfolio_value as value,
            cash_balance as cash,
            positions_value,
            daily_pnl,
            daily_pnl_percent
        FROM portfolio_history
        WHERE user_id = :user_id
        AND date >= :since
        ORDER BY date
    """
    
    result = await db.execute(
        text(query),
        {
            "user_id": current_user.id,
            "since": since.date()}
    )
    
    history = []
    for row in result:
        history.append(PortfolioHistory(
            date=row.date,
            value=row.value,
            cash=row.cash,
            positions_value=row.positions_value,
            daily_pnl=row.daily_pnl,
            daily_pnl_percent=row.daily_pnl_percent
        ))
    
    # If no history, create synthetic data from trades
    if not history:
        synthetic_query = """
            WITH daily_changes AS (
                SELECT 
                    DATE(exit_time) as date,
                    SUM(pnl) as daily_pnl
                FROM trades
                WHERE user_id = :user_id
                AND status = 'closed'
                AND exit_time >= :since
                GROUP BY DATE(exit_time)
            ),
            cumulative AS (
                SELECT 
                    date,
                    daily_pnl,
                    SUM(daily_pnl) OVER (ORDER BY date) as cumulative_pnl
                FROM daily_changes
            )
            SELECT 
                date,
                :starting_capital + cumulative_pnl as value,
                :starting_capital as cash,
                cumulative_pnl as positions_value,
                daily_pnl,
                CASE 
                    WHEN LAG(cumulative_pnl) OVER (ORDER BY date) IS NULL THEN 0
                    ELSE daily_pnl / (:starting_capital + LAG(cumulative_pnl) OVER (ORDER BY date)) * 100
                END as daily_pnl_percent
            FROM cumulative
            ORDER BY date
        """
        
        # Get starting capital
        capital_result = await db.execute(
            text("SELECT starting_capital FROM users WHERE id = :user_id"),
            {"user_id": current_user.id}
        )
        starting_capital = capital_result.scalar() or 100000
        
        synthetic_result = await db.execute(
            text(synthetic_query),
            {
                "user_id": current_user.id,
                "since": since,
                "starting_capital": starting_capital
            }
        )
        
        for row in synthetic_result:
            history.append(PortfolioHistory(
                date=row.date,
                value=row.value,
                cash=row.cash,
                positions_value=row.positions_value,
                daily_pnl=row.daily_pnl,
                daily_pnl_percent=row.daily_pnl_percent
            ))
    
    return MobileResponse(data=history)


@router.get("/performance", response_model=MobileResponse[Dict[str, Any]])
async def get_portfolio_performance(
    timeframe: str = Query("30d", regex="^(7d|30d|90d|1y|all)$"),
    current_user: User = Depends(RequireAuth),
    db: AsyncSession = Depends(get_db)
) -> MobileResponse[Dict[str, Any]]:
    """Get detailed portfolio performance metrics."""
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
    
    # Get performance metrics
    metrics_query = """
        WITH period_data AS (
            SELECT 
                MIN(portfolio_value) as min_value,
                MAX(portfolio_value) as max_value,
                STDDEV(daily_pnl_percent) as volatility,
                AVG(daily_pnl_percent) as avg_daily_return,
                COUNT(CASE WHEN daily_pnl > 0 THEN 1 END) as winning_days,
                COUNT(CASE WHEN daily_pnl < 0 THEN 1 END) as losing_days,
                COUNT(*) as total_days
            FROM portfolio_history
            WHERE user_id = :user_id
    """
    
    if since:
        metrics_query += " AND date >= :since"
    
    metrics_query += """
        ),
        trade_metrics AS (
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                MAX(pnl) as best_trade,
                MIN(pnl) as worst_trade
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
    """
    
    if since:
        metrics_query += " AND exit_time >= :since"
    
    metrics_query += """
        )
        SELECT 
            pd.*,
            tm.*,
            (SELECT portfolio_value FROM portfolio_history WHERE user_id = :user_id ORDER BY date DESC LIMIT 1) as current_value,
            (SELECT portfolio_value FROM portfolio_history WHERE user_id = :user_id 
    """
    
    if since:
        metrics_query += " AND date >= :since"
    
    metrics_query += " ORDER BY date LIMIT 1) as starting_value FROM period_data pd, trade_metrics tm"
    
    params = {"user_id": current_user.id}
    if since:
        params["since"] = since.date()
    
    result = await db.execute(text(metrics_query), params)
    metrics = result.first()
    
    if not metrics or not metrics.current_value:
        # Return default metrics if no data
        return MobileResponse(
            data={
                "timeframe": timeframe,
                "return": format_percentage(0),
                "max_drawdown": format_percentage(0),
                "sharpe_ratio": 0,
                "win_rate": format_percentage(0),
                "profit_factor": 0,
                "best_day": format_currency(0),
                "worst_day": format_currency(0),
                "volatility": format_percentage(0)
            }
        )
    
    # Calculate returns
    period_return = (
        ((metrics.current_value - metrics.starting_value) / metrics.starting_value * 100)
        if metrics.starting_value else 0
    )
    
    # Calculate max drawdown
    max_drawdown = (
        ((metrics.max_value - metrics.min_value) / metrics.max_value * 100)
        if metrics.max_value else 0
    )
    
    # Calculate Sharpe ratio (simplified)
    sharpe_ratio = 0
    if metrics.volatility and metrics.volatility > 0:
        # Annualize based on timeframe
        periods_per_year = 252  # Trading days
        annualized_return = metrics.avg_daily_return * periods_per_year
        annualized_volatility = metrics.volatility * (periods_per_year ** 0.5)
        risk_free_rate = 2.0  # Assume 2% risk-free rate
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
    
    # Calculate win rate
    win_rate = (
        (metrics.winning_trades / metrics.total_trades * 100)
        if metrics.total_trades else 0
    )
    
    # Calculate profit factor
    profit_factor = (
        abs((metrics.avg_win * metrics.winning_trades) / 
            (metrics.avg_loss * (metrics.total_trades - metrics.winning_trades)))
        if metrics.avg_loss and metrics.winning_trades else 0
    )
    
    return MobileResponse(
        data={
            "timeframe": timeframe,
            "return": format_percentage(period_return),
            "max_drawdown": format_percentage(max_drawdown),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "win_rate": format_percentage(win_rate),
            "profit_factor": round(profit_factor, 2),
            "best_trade": format_currency(metrics.best_trade or 0),
            "worst_trade": format_currency(metrics.worst_trade or 0),
            "volatility": format_percentage(metrics.volatility or 0),
            "winning_days": metrics.winning_days or 0,
            "losing_days": metrics.losing_days or 0,
            "total_trades": metrics.total_trades or 0
        }
    )
