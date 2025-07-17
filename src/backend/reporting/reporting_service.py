"""
Advanced reporting service for TradeSense.
Handles report generation, scheduling, and custom analytics.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, and_, or_, func
import pandas as pd
import numpy as np
from enum import Enum
import json
import uuid
from io import BytesIO
import asyncio

from app.core.db.session import get_db
from app.models.user import User
from app.core.cache import redis_client


class ReportType(str, Enum):
    """Types of reports available."""
    PERFORMANCE_SUMMARY = "performance_summary"
    TRADE_ANALYSIS = "trade_analysis"
    RISK_METRICS = "risk_metrics"
    TAX_REPORT = "tax_report"
    MONTHLY_STATEMENT = "monthly_statement"
    YEAR_END_SUMMARY = "year_end_summary"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report output formats."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class MetricType(str, Enum):
    """Types of metrics for custom reports."""
    TOTAL_PNL = "total_pnl"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    AVERAGE_WIN = "average_win"
    AVERAGE_LOSS = "average_loss"
    BEST_TRADE = "best_trade"
    WORST_TRADE = "worst_trade"
    TOTAL_TRADES = "total_trades"
    WINNING_TRADES = "winning_trades"
    LOSING_TRADES = "losing_trades"
    AVERAGE_HOLD_TIME = "average_hold_time"
    RISK_REWARD_RATIO = "risk_reward_ratio"
    EXPECTANCY = "expectancy"
    VOLATILITY = "volatility"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"
    ALPHA = "alpha"
    BETA = "beta"


class GroupBy(str, Enum):
    """Grouping options for reports."""
    SYMBOL = "symbol"
    STRATEGY = "strategy"
    SECTOR = "sector"
    TIME_OF_DAY = "time_of_day"
    DAY_OF_WEEK = "day_of_week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    TAG = "tag"
    ASSET_TYPE = "asset_type"


class ReportingService:
    """Service for generating advanced reports."""
    
    def __init__(self):
        self.report_templates = self._load_report_templates()
    
    async def generate_report(
        self,
        user: User,
        report_type: ReportType,
        date_range: Dict[str, datetime],
        filters: Optional[Dict[str, Any]] = None,
        group_by: Optional[List[GroupBy]] = None,
        metrics: Optional[List[MetricType]] = None,
        format: ReportFormat = ReportFormat.PDF,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive report."""
        report_id = str(uuid.uuid4())
        
        # Get report data based on type
        if report_type == ReportType.PERFORMANCE_SUMMARY:
            data = await self._generate_performance_summary(
                user, date_range, filters, db
            )
        elif report_type == ReportType.TRADE_ANALYSIS:
            data = await self._generate_trade_analysis(
                user, date_range, filters, group_by, db
            )
        elif report_type == ReportType.RISK_METRICS:
            data = await self._generate_risk_metrics(
                user, date_range, filters, db
            )
        elif report_type == ReportType.TAX_REPORT:
            data = await self._generate_tax_report(
                user, date_range, filters, db
            )
        elif report_type == ReportType.MONTHLY_STATEMENT:
            data = await self._generate_monthly_statement(
                user, date_range, db
            )
        elif report_type == ReportType.YEAR_END_SUMMARY:
            data = await self._generate_year_end_summary(
                user, date_range, db
            )
        elif report_type == ReportType.CUSTOM:
            data = await self._generate_custom_report(
                user, date_range, filters, group_by, metrics, db
            )
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        # Format report
        report_file = await self._format_report(data, report_type, format)
        
        # Save report metadata
        await self._save_report_metadata(
            report_id, user.id, report_type, format, db
        )
        
        return {
            "report_id": report_id,
            "type": report_type,
            "format": format,
            "data": data,
            "file": report_file,
            "generated_at": datetime.utcnow()
        }
    
    async def _generate_performance_summary(
        self,
        user: User,
        date_range: Dict[str, datetime],
        filters: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate performance summary report."""
        # Get trades data
        trades_query = """
            SELECT 
                id, symbol, type, entry_time, exit_time,
                entry_price, exit_price, shares, pnl,
                EXTRACT(EPOCH FROM (exit_time - entry_time))/3600 as hold_hours
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
            AND exit_time BETWEEN :start_date AND :end_date
        """
        
        params = {
            "user_id": user.id,
            "start_date": date_range["start"],
            "end_date": date_range["end"]
        }
        
        # Apply filters
        if filters:
            if "symbols" in filters:
                trades_query += " AND symbol = ANY(:symbols)"
                params["symbols"] = filters["symbols"]
            if "min_pnl" in filters:
                trades_query += " AND pnl >= :min_pnl"
                params["min_pnl"] = filters["min_pnl"]
        
        result = await db.execute(text(trades_query), params)
        trades = pd.DataFrame(result.fetchall())
        
        if trades.empty:
            return self._empty_performance_summary()
        
        # Calculate metrics
        total_pnl = trades["pnl"].sum()
        total_trades = len(trades)
        winning_trades = trades[trades["pnl"] > 0]
        losing_trades = trades[trades["pnl"] < 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        avg_win = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades["pnl"].sum() / losing_trades["pnl"].sum()) if len(losing_trades) > 0 and losing_trades["pnl"].sum() != 0 else 0
        
        # Calculate Sharpe ratio
        daily_returns = trades.groupby(trades["exit_time"].dt.date)["pnl"].sum()
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        
        # Calculate maximum drawdown
        cumulative_pnl = trades.sort_values("exit_time")["pnl"].cumsum()
        max_drawdown = self._calculate_max_drawdown(cumulative_pnl)
        
        # Best and worst trades
        best_trade = trades.loc[trades["pnl"].idxmax()]
        worst_trade = trades.loc[trades["pnl"].idxmin()]
        
        # Time analysis
        avg_hold_time = trades["hold_hours"].mean()
        
        # Symbol breakdown
        symbol_stats = trades.groupby("symbol").agg({
            "pnl": ["sum", "count", "mean"],
            "id": "count"
        }).round(2)
        
        return {
            "overview": {
                "total_pnl": round(total_pnl, 2),
                "total_trades": total_trades,
                "win_rate": round(win_rate, 2),
                "profit_factor": round(profit_factor, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "avg_hold_time_hours": round(avg_hold_time, 2)
            },
            "best_trade": {
                "symbol": best_trade["symbol"],
                "pnl": best_trade["pnl"],
                "date": best_trade["exit_time"]
            },
            "worst_trade": {
                "symbol": worst_trade["symbol"],
                "pnl": worst_trade["pnl"],
                "date": worst_trade["exit_time"]
            },
            "symbol_breakdown": symbol_stats.to_dict(),
            "daily_pnl": daily_returns.to_dict(),
            "cumulative_pnl": cumulative_pnl.to_dict()
        }
    
    async def _generate_trade_analysis(
        self,
        user: User,
        date_range: Dict[str, datetime],
        filters: Optional[Dict[str, Any]],
        group_by: Optional[List[GroupBy]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate detailed trade analysis report."""
        # Get trades with extended information
        query = """
            SELECT 
                t.*,
                EXTRACT(HOUR FROM entry_time) as entry_hour,
                EXTRACT(DOW FROM entry_time) as day_of_week,
                EXTRACT(MONTH FROM entry_time) as month,
                EXTRACT(QUARTER FROM entry_time) as quarter,
                EXTRACT(YEAR FROM entry_time) as year,
                CASE 
                    WHEN pnl > 0 THEN 'win'
                    WHEN pnl < 0 THEN 'loss'
                    ELSE 'breakeven'
                END as outcome
            FROM trades t
            WHERE user_id = :user_id
            AND status = 'closed'
            AND exit_time BETWEEN :start_date AND :end_date
        """
        
        params = {
            "user_id": user.id,
            "start_date": date_range["start"],
            "end_date": date_range["end"]
        }
        
        result = await db.execute(text(query), params)
        trades_df = pd.DataFrame(result.fetchall())
        
        if trades_df.empty:
            return {"message": "No trades found in the specified period"}
        
        analysis = {"overall": self._analyze_trades(trades_df)}
        
        # Group analysis
        if group_by:
            for group in group_by:
                if group == GroupBy.SYMBOL:
                    analysis["by_symbol"] = self._analyze_by_group(trades_df, "symbol")
                elif group == GroupBy.TIME_OF_DAY:
                    analysis["by_hour"] = self._analyze_by_group(trades_df, "entry_hour")
                elif group == GroupBy.DAY_OF_WEEK:
                    analysis["by_day"] = self._analyze_by_group(trades_df, "day_of_week")
                elif group == GroupBy.MONTH:
                    analysis["by_month"] = self._analyze_by_group(trades_df, "month")
                elif group == GroupBy.STRATEGY:
                    analysis["by_strategy"] = self._analyze_by_group(trades_df, "strategy")
        
        # Pattern analysis
        analysis["patterns"] = self._analyze_patterns(trades_df)
        
        # Streak analysis
        analysis["streaks"] = self._analyze_streaks(trades_df)
        
        return analysis
    
    async def _generate_risk_metrics(
        self,
        user: User,
        date_range: Dict[str, datetime],
        filters: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate risk metrics report."""
        # Get portfolio value history
        portfolio_query = """
            SELECT date, portfolio_value
            FROM portfolio_history
            WHERE user_id = :user_id
            AND date BETWEEN :start_date AND :end_date
            ORDER BY date
        """
        
        result = await db.execute(
            text(portfolio_query),
            {
                "user_id": user.id,
                "start_date": date_range["start"],
                "end_date": date_range["end"]
            }
        )
        
        portfolio_df = pd.DataFrame(result.fetchall())
        
        if portfolio_df.empty:
            return {"message": "No portfolio history found"}
        
        # Calculate returns
        portfolio_df["returns"] = portfolio_df["portfolio_value"].pct_change()
        portfolio_df["log_returns"] = np.log(portfolio_df["portfolio_value"] / portfolio_df["portfolio_value"].shift(1))
        
        # Risk metrics
        volatility = portfolio_df["returns"].std() * np.sqrt(252)  # Annualized
        downside_deviation = portfolio_df[portfolio_df["returns"] < 0]["returns"].std() * np.sqrt(252)
        
        # Value at Risk (VaR)
        var_95 = np.percentile(portfolio_df["returns"].dropna(), 5)
        var_99 = np.percentile(portfolio_df["returns"].dropna(), 1)
        
        # Conditional Value at Risk (CVaR)
        cvar_95 = portfolio_df[portfolio_df["returns"] <= var_95]["returns"].mean()
        cvar_99 = portfolio_df[portfolio_df["returns"] <= var_99]["returns"].mean()
        
        # Maximum drawdown analysis
        cumulative_returns = (1 + portfolio_df["returns"]).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        max_drawdown = drawdown.min()
        max_drawdown_duration = self._calculate_drawdown_duration(drawdown)
        
        # Risk-adjusted returns
        sharpe_ratio = self._calculate_sharpe_ratio(portfolio_df["returns"].dropna())
        sortino_ratio = self._calculate_sortino_ratio(portfolio_df["returns"].dropna())
        calmar_ratio = self._calculate_calmar_ratio(
            portfolio_df["returns"].dropna(), 
            max_drawdown
        )
        
        # Beta calculation (vs market proxy)
        # This is simplified - in production would use actual market data
        market_beta = 1.0  # Placeholder
        
        return {
            "volatility_metrics": {
                "daily_volatility": round(portfolio_df["returns"].std(), 4),
                "annualized_volatility": round(volatility, 4),
                "downside_deviation": round(downside_deviation, 4),
                "skewness": round(portfolio_df["returns"].skew(), 4),
                "kurtosis": round(portfolio_df["returns"].kurtosis(), 4)
            },
            "value_at_risk": {
                "var_95_daily": round(var_95, 4),
                "var_99_daily": round(var_99, 4),
                "cvar_95_daily": round(cvar_95, 4),
                "cvar_99_daily": round(cvar_99, 4)
            },
            "drawdown_analysis": {
                "max_drawdown": round(max_drawdown, 4),
                "max_drawdown_duration_days": max_drawdown_duration,
                "current_drawdown": round(drawdown.iloc[-1], 4)
            },
            "risk_adjusted_returns": {
                "sharpe_ratio": round(sharpe_ratio, 2),
                "sortino_ratio": round(sortino_ratio, 2),
                "calmar_ratio": round(calmar_ratio, 2),
                "information_ratio": None,  # Requires benchmark
                "treynor_ratio": None  # Requires beta
            },
            "market_risk": {
                "beta": market_beta,
                "correlation_to_market": None  # Requires market data
            }
        }
    
    async def _generate_tax_report(
        self,
        user: User,
        date_range: Dict[str, datetime],
        filters: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate tax report with realized gains/losses."""
        # Get all closed trades for the period
        query = """
            SELECT 
                symbol, entry_time, exit_time,
                entry_price, exit_price, shares,
                pnl, type,
                CASE 
                    WHEN exit_time - entry_time > INTERVAL '1 year' THEN 'long_term'
                    ELSE 'short_term'
                END as tax_treatment
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
            AND exit_time BETWEEN :start_date AND :end_date
            ORDER BY exit_time
        """
        
        result = await db.execute(
            text(query),
            {
                "user_id": user.id,
                "start_date": date_range["start"],
                "end_date": date_range["end"]
            }
        )
        
        trades_df = pd.DataFrame(result.fetchall())
        
        if trades_df.empty:
            return {"message": "No closed trades found for tax period"}
        
        # Separate by tax treatment
        short_term = trades_df[trades_df["tax_treatment"] == "short_term"]
        long_term = trades_df[trades_df["tax_treatment"] == "long_term"]
        
        # Calculate totals
        short_term_gains = short_term[short_term["pnl"] > 0]["pnl"].sum()
        short_term_losses = abs(short_term[short_term["pnl"] < 0]["pnl"].sum())
        long_term_gains = long_term[long_term["pnl"] > 0]["pnl"].sum()
        long_term_losses = abs(long_term[long_term["pnl"] < 0]["pnl"].sum())
        
        # Net calculations
        net_short_term = short_term_gains - short_term_losses
        net_long_term = long_term_gains - long_term_losses
        total_net = net_short_term + net_long_term
        
        # Wash sale analysis (simplified)
        wash_sales = self._identify_wash_sales(trades_df)
        
        return {
            "summary": {
                "short_term_gains": round(short_term_gains, 2),
                "short_term_losses": round(short_term_losses, 2),
                "net_short_term": round(net_short_term, 2),
                "long_term_gains": round(long_term_gains, 2),
                "long_term_losses": round(long_term_losses, 2),
                "net_long_term": round(net_long_term, 2),
                "total_net": round(total_net, 2)
            },
            "trades": {
                "short_term": short_term.to_dict("records"),
                "long_term": long_term.to_dict("records")
            },
            "wash_sales": wash_sales,
            "quarterly_breakdown": self._quarterly_tax_breakdown(trades_df),
            "form_8949_data": self._format_for_8949(trades_df)
        }
    
    async def _generate_custom_report(
        self,
        user: User,
        date_range: Dict[str, datetime],
        filters: Optional[Dict[str, Any]],
        group_by: Optional[List[GroupBy]],
        metrics: Optional[List[MetricType]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate custom report based on user specifications."""
        # Base query
        base_query = """
            SELECT *
            FROM trades
            WHERE user_id = :user_id
            AND status = 'closed'
            AND exit_time BETWEEN :start_date AND :end_date
        """
        
        params = {
            "user_id": user.id,
            "start_date": date_range["start"],
            "end_date": date_range["end"]
        }
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if key == "symbols" and value:
                    base_query += " AND symbol = ANY(:symbols)"
                    params["symbols"] = value
                elif key == "min_pnl":
                    base_query += " AND pnl >= :min_pnl"
                    params["min_pnl"] = value
                elif key == "max_pnl":
                    base_query += " AND pnl <= :max_pnl"
                    params["max_pnl"] = value
                elif key == "strategy" and value:
                    base_query += " AND strategy = :strategy"
                    params["strategy"] = value
        
        result = await db.execute(text(base_query), params)
        trades_df = pd.DataFrame(result.fetchall())
        
        if trades_df.empty:
            return {"message": "No data found for custom report"}
        
        # Calculate requested metrics
        report_data = {}
        
        if metrics:
            calculated_metrics = {}
            for metric in metrics:
                calculated_metrics[metric] = self._calculate_metric(
                    trades_df, metric
                )
            report_data["metrics"] = calculated_metrics
        
        # Apply grouping
        if group_by:
            grouped_data = {}
            for group in group_by:
                if group == GroupBy.SYMBOL:
                    grouped_data["by_symbol"] = self._group_and_calculate(
                        trades_df, "symbol", metrics
                    )
                elif group == GroupBy.MONTH:
                    trades_df["month"] = trades_df["exit_time"].dt.to_period("M")
                    grouped_data["by_month"] = self._group_and_calculate(
                        trades_df, "month", metrics
                    )
                # Add other groupings as needed
            
            report_data["grouped_analysis"] = grouped_data
        
        # Add raw data if requested
        if filters and filters.get("include_raw_data", False):
            report_data["raw_trades"] = trades_df.to_dict("records")
        
        return report_data
    
    # Helper methods
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0 or returns.std() == 0:
            return 0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio."""
        if len(returns) == 0:
            return 0
        
        excess_returns = returns - risk_free_rate / 252
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
        
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    def _calculate_calmar_ratio(self, returns: pd.Series, max_drawdown: float) -> float:
        """Calculate Calmar ratio."""
        if max_drawdown == 0:
            return 0
        
        annual_return = (1 + returns.mean()) ** 252 - 1
        return annual_return / abs(max_drawdown)
    
    def _calculate_max_drawdown(self, cumulative_pnl: pd.Series) -> float:
        """Calculate maximum drawdown."""
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max
        return abs(drawdown.min()) if len(drawdown) > 0 else 0
    
    def _calculate_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calculate maximum drawdown duration in days."""
        # Find periods where drawdown < 0
        in_drawdown = drawdown < 0
        
        # Calculate consecutive days in drawdown
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def _analyze_trades(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a set of trades."""
        total_trades = len(trades_df)
        winning_trades = trades_df[trades_df["pnl"] > 0]
        losing_trades = trades_df[trades_df["pnl"] < 0]
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            "total_pnl": trades_df["pnl"].sum(),
            "avg_pnl": trades_df["pnl"].mean(),
            "avg_win": winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0,
            "avg_loss": losing_trades["pnl"].mean() if len(losing_trades) > 0 else 0,
            "largest_win": winning_trades["pnl"].max() if len(winning_trades) > 0 else 0,
            "largest_loss": losing_trades["pnl"].min() if len(losing_trades) > 0 else 0
        }
    
    def _analyze_by_group(self, trades_df: pd.DataFrame, group_col: str) -> Dict[str, Any]:
        """Analyze trades grouped by a column."""
        grouped = trades_df.groupby(group_col)
        
        results = {}
        for name, group in grouped:
            results[str(name)] = self._analyze_trades(group)
        
        return results
    
    def _analyze_patterns(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading patterns."""
        trades_df = trades_df.sort_values("exit_time")
        
        # Win/loss sequences
        outcomes = trades_df["pnl"].apply(lambda x: "W" if x > 0 else "L")
        
        # Find consecutive wins/losses
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for outcome in outcomes:
            if outcome == "W":
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        # Time-based patterns
        trades_df["hour"] = trades_df["entry_time"].dt.hour
        trades_df["day_of_week"] = trades_df["entry_time"].dt.dayofweek
        
        hourly_performance = trades_df.groupby("hour")["pnl"].agg(["mean", "count"])
        daily_performance = trades_df.groupby("day_of_week")["pnl"].agg(["mean", "count"])
        
        return {
            "consecutive_patterns": {
                "max_consecutive_wins": max_consecutive_wins,
                "max_consecutive_losses": max_consecutive_losses
            },
            "time_patterns": {
                "best_hour": hourly_performance["mean"].idxmax() if len(hourly_performance) > 0 else None,
                "worst_hour": hourly_performance["mean"].idxmin() if len(hourly_performance) > 0 else None,
                "best_day": daily_performance["mean"].idxmax() if len(daily_performance) > 0 else None,
                "worst_day": daily_performance["mean"].idxmin() if len(daily_performance) > 0 else None
            },
            "hourly_breakdown": hourly_performance.to_dict(),
            "daily_breakdown": daily_performance.to_dict()
        }
    
    def _analyze_streaks(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze winning and losing streaks."""
        trades_df = trades_df.sort_values("exit_time")
        
        streaks = []
        current_streak = {"type": None, "count": 0, "total_pnl": 0, "trades": []}
        
        for _, trade in trades_df.iterrows():
            outcome = "win" if trade["pnl"] > 0 else "loss"
            
            if current_streak["type"] == outcome:
                current_streak["count"] += 1
                current_streak["total_pnl"] += trade["pnl"]
                current_streak["trades"].append(trade["id"])
            else:
                if current_streak["count"] > 0:
                    streaks.append(current_streak.copy())
                
                current_streak = {
                    "type": outcome,
                    "count": 1,
                    "total_pnl": trade["pnl"],
                    "trades": [trade["id"]]
                }
        
        if current_streak["count"] > 0:
            streaks.append(current_streak)
        
        # Find longest streaks
        winning_streaks = [s for s in streaks if s["type"] == "win"]
        losing_streaks = [s for s in streaks if s["type"] == "loss"]
        
        longest_win_streak = max(winning_streaks, key=lambda x: x["count"]) if winning_streaks else None
        longest_loss_streak = max(losing_streaks, key=lambda x: x["count"]) if losing_streaks else None
        
        return {
            "all_streaks": streaks,
            "longest_win_streak": longest_win_streak,
            "longest_loss_streak": longest_loss_streak,
            "average_win_streak": np.mean([s["count"] for s in winning_streaks]) if winning_streaks else 0,
            "average_loss_streak": np.mean([s["count"] for s in losing_streaks]) if losing_streaks else 0
        }
    
    def _identify_wash_sales(self, trades_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify potential wash sales (simplified)."""
        wash_sales = []
        
        # Group by symbol
        for symbol in trades_df["symbol"].unique():
            symbol_trades = trades_df[trades_df["symbol"] == symbol].sort_values("exit_time")
            
            for i, trade in symbol_trades.iterrows():
                if trade["pnl"] < 0:  # Loss trade
                    # Check for repurchase within 30 days
                    repurchase_window_start = trade["exit_time"] - timedelta(days=30)
                    repurchase_window_end = trade["exit_time"] + timedelta(days=30)
                    
                    potential_wash = symbol_trades[
                        (symbol_trades.index != i) &
                        (symbol_trades["entry_time"] >= repurchase_window_start) &
                        (symbol_trades["entry_time"] <= repurchase_window_end)
                    ]
                    
                    if not potential_wash.empty:
                        wash_sales.append({
                            "loss_trade_id": trade["id"],
                            "loss_amount": trade["pnl"],
                            "symbol": symbol,
                            "potential_wash_trades": potential_wash["id"].tolist()
                        })
        
        return wash_sales
    
    def _quarterly_tax_breakdown(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Break down tax obligations by quarter."""
        trades_df["quarter"] = trades_df["exit_time"].dt.quarter
        trades_df["year"] = trades_df["exit_time"].dt.year
        
        quarterly = trades_df.groupby(["year", "quarter", "tax_treatment"])["pnl"].sum()
        
        return quarterly.to_dict()
    
    def _format_for_8949(self, trades_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Format trades for IRS Form 8949."""
        formatted = []
        
        for _, trade in trades_df.iterrows():
            formatted.append({
                "description": f"{trade['shares']} shares {trade['symbol']}",
                "date_acquired": trade["entry_time"].strftime("%m/%d/%Y"),
                "date_sold": trade["exit_time"].strftime("%m/%d/%Y"),
                "proceeds": round(trade["exit_price"] * trade["shares"], 2),
                "cost_basis": round(trade["entry_price"] * trade["shares"], 2),
                "gain_loss": round(trade["pnl"], 2),
                "tax_treatment": trade["tax_treatment"]
            })
        
        return formatted
    
    def _calculate_metric(self, trades_df: pd.DataFrame, metric: MetricType) -> Any:
        """Calculate a specific metric."""
        if metric == MetricType.TOTAL_PNL:
            return trades_df["pnl"].sum()
        elif metric == MetricType.WIN_RATE:
            total = len(trades_df)
            wins = len(trades_df[trades_df["pnl"] > 0])
            return (wins / total * 100) if total > 0 else 0
        elif metric == MetricType.PROFIT_FACTOR:
            gains = trades_df[trades_df["pnl"] > 0]["pnl"].sum()
            losses = abs(trades_df[trades_df["pnl"] < 0]["pnl"].sum())
            return gains / losses if losses > 0 else 0
        elif metric == MetricType.AVERAGE_WIN:
            wins = trades_df[trades_df["pnl"] > 0]["pnl"]
            return wins.mean() if len(wins) > 0 else 0
        elif metric == MetricType.AVERAGE_LOSS:
            losses = trades_df[trades_df["pnl"] < 0]["pnl"]
            return losses.mean() if len(losses) > 0 else 0
        elif metric == MetricType.BEST_TRADE:
            return trades_df["pnl"].max()
        elif metric == MetricType.WORST_TRADE:
            return trades_df["pnl"].min()
        elif metric == MetricType.TOTAL_TRADES:
            return len(trades_df)
        elif metric == MetricType.WINNING_TRADES:
            return len(trades_df[trades_df["pnl"] > 0])
        elif metric == MetricType.LOSING_TRADES:
            return len(trades_df[trades_df["pnl"] < 0])
        # Add more metrics as needed
        else:
            return None
    
    def _group_and_calculate(
        self, 
        trades_df: pd.DataFrame, 
        group_col: str, 
        metrics: Optional[List[MetricType]]
    ) -> Dict[str, Any]:
        """Group data and calculate metrics for each group."""
        grouped = trades_df.groupby(group_col)
        
        results = {}
        for name, group in grouped:
            group_metrics = {}
            
            if metrics:
                for metric in metrics:
                    group_metrics[metric] = self._calculate_metric(group, metric)
            else:
                # Default metrics
                group_metrics = {
                    "total_trades": len(group),
                    "total_pnl": group["pnl"].sum(),
                    "win_rate": self._calculate_metric(group, MetricType.WIN_RATE),
                    "avg_pnl": group["pnl"].mean()
                }
            
            results[str(name)] = group_metrics
        
        return results
    
    async def _format_report(self, data: Dict[str, Any], report_type: ReportType, format: ReportFormat) -> bytes:
        """Format report data into requested format."""
        if format == ReportFormat.JSON:
            return json.dumps(data, default=str).encode()
        
        elif format == ReportFormat.CSV:
            # Convert to CSV format
            output = BytesIO()
            
            # Handle different data structures
            if "trades" in data:
                df = pd.DataFrame(data["trades"])
                df.to_csv(output, index=False)
            else:
                # Flatten nested data for CSV
                flattened = self._flatten_dict(data)
                df = pd.DataFrame([flattened])
                df.to_csv(output, index=False)
            
            return output.getvalue()
        
        elif format == ReportFormat.EXCEL:
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write different sections to different sheets
                for key, value in data.items():
                    if isinstance(value, dict) and any(isinstance(v, (list, dict)) for v in value.values()):
                        # Complex nested data
                        df = pd.DataFrame(value)
                        df.to_excel(writer, sheet_name=key[:31])  # Excel sheet name limit
                    elif isinstance(value, list):
                        df = pd.DataFrame(value)
                        df.to_excel(writer, sheet_name=key[:31])
                    else:
                        # Simple key-value pairs
                        df = pd.DataFrame([{"Metric": k, "Value": v} for k, v in value.items()])
                        df.to_excel(writer, sheet_name=key[:31], index=False)
            
            return output.getvalue()
        
        elif format == ReportFormat.HTML:
            # Generate HTML report
            html = self._generate_html_report(data, report_type)
            return html.encode()
        
        elif format == ReportFormat.PDF:
            # Generate PDF (would use a library like ReportLab or WeasyPrint)
            # For now, return a placeholder
            return b"PDF generation not implemented"
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _generate_html_report(self, data: Dict[str, Any], report_type: ReportType) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TradeSense {report_type.value.replace('_', ' ').title()}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ margin: 10px 0; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>{report_type.value.replace('_', ' ').title()}</h1>
            <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        """
        
        # Add content based on data structure
        for section, content in data.items():
            html += f"<h2>{section.replace('_', ' ').title()}</h2>"
            
            if isinstance(content, dict):
                html += "<div class='section'>"
                for key, value in content.items():
                    if isinstance(value, (int, float)):
                        css_class = "positive" if value > 0 else "negative" if value < 0 else ""
                        html += f"<div class='metric'><strong>{key}:</strong> <span class='{css_class}'>{value}</span></div>"
                    else:
                        html += f"<div class='metric'><strong>{key}:</strong> {value}</div>"
                html += "</div>"
            
            elif isinstance(content, list) and content:
                # Create table
                html += "<table>"
                
                # Headers
                html += "<tr>"
                for key in content[0].keys():
                    html += f"<th>{key}</th>"
                html += "</tr>"
                
                # Rows
                for row in content:
                    html += "<tr>"
                    for value in row.values():
                        html += f"<td>{value}</td>"
                    html += "</tr>"
                
                html += "</table>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    async def _save_report_metadata(
        self,
        report_id: str,
        user_id: str,
        report_type: ReportType,
        format: ReportFormat,
        db: AsyncSession
    ):
        """Save report metadata to database."""
        await db.execute(
            text("""
                INSERT INTO generated_reports (
                    id, user_id, report_type, format, generated_at
                ) VALUES (
                    :id, :user_id, :report_type, :format, NOW()
                )
            """),
            {
                "id": report_id,
                "user_id": user_id,
                "report_type": report_type,
                "format": format
            }
        )
        await db.commit()
    
    def _empty_performance_summary(self) -> Dict[str, Any]:
        """Return empty performance summary structure."""
        return {
            "overview": {
                "total_pnl": 0,
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "avg_hold_time_hours": 0
            },
            "best_trade": None,
            "worst_trade": None,
            "symbol_breakdown": {},
            "daily_pnl": {},
            "cumulative_pnl": {}
        }
    
    def _load_report_templates(self) -> Dict[str, Any]:
        """Load predefined report templates."""
        return {
            "day_trader": {
                "metrics": [
                    MetricType.TOTAL_PNL,
                    MetricType.WIN_RATE,
                    MetricType.AVERAGE_WIN,
                    MetricType.AVERAGE_LOSS,
                    MetricType.PROFIT_FACTOR
                ],
                "group_by": [GroupBy.SYMBOL, GroupBy.TIME_OF_DAY]
            },
            "swing_trader": {
                "metrics": [
                    MetricType.TOTAL_PNL,
                    MetricType.WIN_RATE,
                    MetricType.AVERAGE_HOLD_TIME,
                    MetricType.RISK_REWARD_RATIO
                ],
                "group_by": [GroupBy.SYMBOL, GroupBy.SECTOR]
            },
            "risk_focused": {
                "metrics": [
                    MetricType.MAX_DRAWDOWN,
                    MetricType.SHARPE_RATIO,
                    MetricType.SORTINO_RATIO,
                    MetricType.VOLATILITY
                ],
                "group_by": [GroupBy.MONTH]
            }
        }
    
    async def schedule_report(
        self,
        user: User,
        report_config: Dict[str, Any],
        schedule: str,  # daily, weekly, monthly
        db: AsyncSession
    ) -> str:
        """Schedule a recurring report."""
        schedule_id = str(uuid.uuid4())
        
        await db.execute(
            text("""
                INSERT INTO scheduled_reports (
                    id, user_id, report_config, schedule, 
                    next_run, is_active, created_at
                ) VALUES (
                    :id, :user_id, :config, :schedule,
                    :next_run, TRUE, NOW()
                )
            """),
            {
                "id": schedule_id,
                "user_id": user.id,
                "config": json.dumps(report_config),
                "schedule": schedule,
                "next_run": self._calculate_next_run(schedule)
            }
        )
        
        await db.commit()
        return schedule_id
    
    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time for scheduled report."""
        now = datetime.utcnow()
        
        if schedule == "daily":
            # Next day at 6 AM UTC
            next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif schedule == "weekly":
            # Next Monday at 6 AM UTC
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 6:
                days_until_monday = 7
            next_run = now + timedelta(days=days_until_monday)
            next_run = next_run.replace(hour=6, minute=0, second=0, microsecond=0)
        
        elif schedule == "monthly":
            # First day of next month at 6 AM UTC
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_run = now.replace(month=now.month + 1, day=1)
            next_run = next_run.replace(hour=6, minute=0, second=0, microsecond=0)
        
        else:
            raise ValueError(f"Invalid schedule: {schedule}")
        
        return next_run


# Global reporting service instance
reporting_service = ReportingService()
