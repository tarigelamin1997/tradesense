import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import pandas as pd
import numpy as np
from cachetools import TTLCache

from backend.models.trade import Trade
from backend.db.connection import get_db
from backend.services.behavioral_analytics import BehavioralAnalyticsService

# Import analytics modules
from backend.analytics.performance import (
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
    calculate_sharpe_ratio
)
from backend.analytics.equity import calculate_max_drawdown
from backend.analytics.streaks import (
    find_longest_streak,
    calculate_average_duration
)
from backend.analytics.filters import filter_trades_by_symbol
from backend.analytics.utils import safe_divide, calculate_percentage

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=300)  # 5-minute cache
        self.behavioral_service = BehavioralAnalyticsService()

    async def get_user_analytics(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a user"""
        cache_key = f"analytics_{user_id}_{start_date}_{end_date}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            db = next(get_db())

            # Base query
            query = db.query(Trade).filter(Trade.user_id == user_id)

            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if end_date:
                query = query.filter(Trade.entry_time <= end_date)

            trades = query.all()

            if not trades:
                return {"error": "No trades found for the specified period"}

            # Convert to DataFrame for analysis
            df = pd.DataFrame([{
                'symbol': t.symbol,
                'direction': t.direction,
                'quantity': t.quantity,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'entry_time': t.entry_time,
                'exit_time': t.exit_time,
                'pnl': t.pnl or 0,
                'commission': t.commission or 0,
                'net_pnl': t.net_pnl or t.pnl or 0,
                'strategy_tag': t.strategy_tag,
                'confidence_score': t.confidence_score
            } for t in trades])

            analytics = await self._calculate_comprehensive_analytics(df)

            # Cache the results
            self.cache[cache_key] = analytics

            return analytics

        except Exception as e:
            logger.error(f"Analytics calculation failed: {str(e)}")
            return {"error": f"Analytics calculation failed: {str(e)}"}
        finally:
            db.close()

    async def _calculate_comprehensive_analytics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive trading analytics"""

        # Basic metrics
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        win_rate = calculate_win_rate(winning_trades, total_trades)

        # P&L metrics
        total_pnl = df['pnl'].sum()
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = calculate_profit_factor(gross_profit, gross_loss)

        # Risk metrics
        max_drawdown = calculate_max_drawdown(df['pnl'])
        sharpe_ratio = calculate_sharpe_ratio(df['pnl'])

        # Performance over time
        equity_curve = df['pnl'].cumsum().tolist()

        # Symbol breakdown
        symbol_stats = self._calculate_symbol_breakdown(df)

        # Strategy performance
        strategy_stats = self._calculate_strategy_breakdown(df)

        # Tag analytics
        tag_stats = self._calculate_tag_breakdown(df)

        # Time-based analysis
        time_analysis = self._calculate_time_analysis(df)

        # Advanced metrics
        advanced_metrics = self._calculate_advanced_metrics(df)

        # Behavioral analytics
        trades_data = df.to_dict('records')
        behavioral_metrics = self.behavioral_service.analyze_behavioral_patterns(trades_data)

        return {
            # Basic metrics
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),

            # P&L metrics
            'total_pnl': round(total_pnl, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 999,
            'average_win': round(df[df['pnl'] > 0]['pnl'].mean(), 2) if winning_trades > 0 else 0,
            'average_loss': round(df[df['pnl'] < 0]['pnl'].mean(), 2) if losing_trades > 0 else 0,
            'largest_win': round(df['pnl'].max(), 2),
            'largest_loss': round(df['pnl'].min(), 2),

            # Risk metrics
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'expectancy': round(df['pnl'].mean(), 2),

            # Performance tracking
            'equity_curve': equity_curve,
            'monthly_returns': self._calculate_monthly_returns(df),

            # Breakdowns
            'symbol_breakdown': symbol_stats,
            'strategy_breakdown': strategy_stats,
            'tag_breakdown': tag_stats,
            'time_analysis': time_analysis,

            # Advanced analytics
            **advanced_metrics,

            # Behavioral analytics (NEW)
            'behavioral_metrics': behavioral_metrics
        }

    def _calculate_max_drawdown(self, pnl_series: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = pnl_series.cumsum()
        running_max = cumulative.expanding().max()
        drawdown = running_max - cumulative
        return drawdown.max()

    def _calculate_sharpe_ratio(self, pnl_series: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        if len(pnl_series) < 2 or pnl_series.std() == 0:
            return 0
        return pnl_series.mean() / pnl_series.std() * np.sqrt(252)  # Annualized

    def _calculate_symbol_breakdown(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate performance by symbol"""
        symbol_stats = []

        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]

            stats = {
                'symbol': symbol,
                'trades': len(symbol_df),
                'win_rate': round(len(symbol_df[symbol_df['pnl'] > 0]) / len(symbol_df) * 100, 1),
                'total_pnl': round(symbol_df['pnl'].sum(), 2),
                'avg_pnl': round(symbol_df['pnl'].mean(), 2),
                'profit_factor': self._calculate_profit_factor(symbol_df['pnl'])
            }
            symbol_stats.append(stats)

        return sorted(symbol_stats, key=lambda x: x['total_pnl'], reverse=True)

    def _calculate_strategy_breakdown(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate performance by strategy"""
        strategy_stats = []

        strategies = df['strategy_tag'].dropna().unique()
        for strategy in strategies:
            strategy_df = df[df['strategy_tag'] == strategy]

            stats = {
                'strategy': strategy,
                'trades': len(strategy_df),
                'win_rate': round(len(strategy_df[strategy_df['pnl'] > 0]) / len(strategy_df) * 100, 1),
                'total_pnl': round(strategy_df['pnl'].sum(), 2),
                'avg_pnl': round(strategy_df['pnl'].mean(), 2),
                'profit_factor': self._calculate_profit_factor(strategy_df['pnl'])
            }
            strategy_stats.append(stats)

        return sorted(strategy_stats, key=lambda x: x['total_pnl'], reverse=True)

    def _calculate_tag_breakdown(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate performance by tag"""
        tag_stats = {}

        # Process tags from each trade
        for _, trade in df.iterrows():
            if pd.notna(trade.get('tags')) and isinstance(trade['tags'], list):
                for tag in trade['tags']:
                    if tag not in tag_stats:
                        tag_stats[tag] = {
                            'trades': [],
                            'pnl_list': []
                        }
                    tag_stats[tag]['trades'].append(trade)
                    tag_stats[tag]['pnl_list'].append(trade['pnl'])

        # Calculate stats for each tag
        tag_breakdown = []
        for tag, data in tag_stats.items():
            pnl_series = pd.Series(data['pnl_list'])
            wins = len(pnl_series[pnl_series > 0])
            total_trades = len(pnl_series)

            stats = {
                'tag': tag,
                'trades': total_trades,
                'win_rate': round(wins / total_trades * 100, 1) if total_trades > 0 else 0,
                'total_pnl': round(pnl_series.sum(), 2),
                'avg_pnl': round(pnl_series.mean(), 2),
                'profit_factor': self._calculate_profit_factor(pnl_series)
            }
            tag_breakdown.append(stats)

        return sorted(tag_breakdown, key=lambda x: x['total_pnl'], reverse=True)

    def _calculate_time_analysis(self, df: pd.DataFrame) -> Dict:
        """Analyze performance by time periods"""
        df['hour'] = pd.to_datetime(df['entry_time']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['entry_time']).dt.day_name()

        hourly_pnl = df.groupby('hour')['pnl'].agg(['sum', 'count', 'mean']).round(2)
        daily_pnl = df.groupby('day_of_week')['pnl'].agg(['sum', 'count', 'mean']).round(2)

        return {
            'best_trading_hour': int(hourly_pnl['sum'].idxmax()),
            'worst_trading_hour': int(hourly_pnl['sum'].idxmin()),
            'best_trading_day': daily_pnl['sum'].idxmax(),
            'worst_trading_day': daily_pnl['sum'].idxmin(),
            'hourly_performance': hourly_pnl.to_dict('index'),
            'daily_performance': daily_pnl.to_dict('index')
        }

    def _calculate_monthly_returns(self, df: pd.DataFrame) -> List[Dict]:
        """Calculate monthly returns"""
        df['month'] = pd.to_datetime(df['entry_time']).dt.to_period('M')
        monthly = df.groupby('month')['pnl'].sum().round(2)

        return [
            {'month': str(month), 'pnl': pnl}
            for month, pnl in monthly.items()
        ]

    def _calculate_profit_factor(self, pnl_series: pd.Series) -> float:
        """Calculate profit factor for a series"""
        gross_profit = pnl_series[pnl_series > 0].sum()
        gross_loss = abs(pnl_series[pnl_series < 0].sum())
        return round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999

    def _calculate_advanced_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate advanced trading metrics"""

        # Consecutive wins/losses
        df['win'] = df['pnl'] > 0
        df['streak'] = (df['win'] != df['win'].shift()).cumsum()
        win_streaks = df[df['win']].groupby('streak').size()
        loss_streaks = df[~df['win']].groupby('streak').size()

        # Trade duration analysis (if exit_time exists)
        durations = []
        if 'exit_time' in df.columns:
            df['duration'] = pd.to_datetime(df['exit_time']) - pd.to_datetime(df['entry_time'])
            durations = df['duration'].dt.total_seconds() / 3600  # Convert to hours

        return {
            'max_consecutive_wins': int(win_streaks.max()) if not win_streaks.empty else 0,
            'max_consecutive_losses': int(loss_streaks.max()) if not loss_streaks.empty else 0,
            'avg_trade_duration_hours': round(np.mean(durations), 2) if durations else 0,
            'median_trade_duration_hours': round(np.median(durations), 2) if durations else 0,
            'total_commissions': round(df['commission'].sum(), 2),
            'net_profit_after_commissions': round(df['net_pnl'].sum(), 2)
        }