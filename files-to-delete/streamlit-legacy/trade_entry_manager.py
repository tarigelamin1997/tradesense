import pandas as pd
import numpy as np
import streamlit as st
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TradeEntryManager:
    """Manages trade data entry and analysis."""

    def __init__(self):
        self.trades = []
        self.required_columns = [
            'symbol', 'entry_time', 'exit_time', 
            'entry_price', 'exit_price', 'pnl', 'direction'
        ]

    def add_file_trades(self, df: pd.DataFrame, source: str) -> Dict[str, Any]:
        """Add trades from uploaded file."""
        try:
            # Validate required columns
            missing_cols = [col for col in self.required_columns if col not in df.columns]
            if missing_cols:
                return {
                    'status': 'error',
                    'message': f'Missing required columns: {", ".join(missing_cols)}'
                }

            # Basic data validation
            df_clean = df.dropna(subset=self.required_columns)
            trades_added = len(df_clean)

            # Store trades
            self.trades.extend(df_clean.to_dict('records'))

            return {
                'status': 'success',
                'trades_added': trades_added,
                'message': f'Successfully added {trades_added} trades'
            }

        except Exception as e:
            logger.error(f"Error adding trades: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error processing trades: {str(e)}'
            }

    def get_all_trades_dataframe(self) -> pd.DataFrame:
        """Get all trades as DataFrame."""
        if not self.trades:
            return pd.DataFrame()

        return pd.DataFrame(self.trades)

    def get_unified_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics for all trades."""
        try:
            df = self.get_all_trades_dataframe()
            if df.empty:
                return {}

            # Convert numeric columns
            numeric_cols = ['entry_price', 'exit_price', 'pnl']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Basic statistics
            total_trades = len(df)
            wins = len(df[df['pnl'] > 0])
            losses = len(df[df['pnl'] < 0])
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

            total_pnl = df['pnl'].sum()
            gross_profit = df[df['pnl'] > 0]['pnl'].sum()
            gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit if gross_profit > 0 else 0

            avg_win = df[df['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
            avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losses > 0 else 0

            # Calculate streaks
            streaks = self._calculate_streaks(df)

            # Duration stats
            duration_stats = self._calculate_duration_stats(df)

            # Median results
            median_results = {
                'median_pnl': df['pnl'].median(),
                'median_win': df[df['pnl'] > 0]['pnl'].median() if wins > 0 else 0,
                'median_loss': df[df['pnl'] < 0]['pnl'].median() if losses > 0 else 0
            }

            # KPIs
            kpis = {
                'total_trades': total_trades,
                'win_rate_percent': win_rate,
                'gross_pnl': gross_profit - gross_loss,
                'net_pnl_after_commission': total_pnl,
                'total_commission': 0,  # Placeholder
                'max_single_trade_win': df['pnl'].max(),
                'max_single_trade_loss': df['pnl'].min(),
                'average_rr': abs(avg_win / avg_loss) if avg_loss != 0 else 0
            }

            # Basic stats
            basic_stats = {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'expectancy': df['pnl'].mean(),
                'average_win': avg_win,
                'average_loss': avg_loss,
                'max_drawdown': self._calculate_max_drawdown(df),
                'sharpe_ratio': self._calculate_sharpe_ratio(df)
            }

            return {
                'basic_stats': basic_stats,
                'kpis': kpis,
                'streaks': streaks,
                'trade_duration_stats': duration_stats,
                'median_results': median_results,
                'symbol_performance': self._get_symbol_performance(df),
                'monthly_performance': self._get_monthly_performance(df)
            }

        except Exception as e:
            logger.error(f"Analytics calculation error: {str(e)}")
            return {}

    def _calculate_streaks(self, df: pd.DataFrame) -> Dict[str, int]:
        """Calculate win/loss streaks."""
        try:
            if df.empty:
                return {'max_win_streak': 0, 'max_loss_streak': 0}

            # Sort by exit_time if available
            if 'exit_time' in df.columns:
                try:
                    df_sorted = df.copy()
                    df_sorted['exit_time'] = pd.to_datetime(df_sorted['exit_time'], errors='coerce')
                    df_sorted = df_sorted.dropna(subset=['exit_time']).sort_values('exit_time')
                except:
                    df_sorted = df
            else:
                df_sorted = df

            current_win_streak = 0
            current_loss_streak = 0
            max_win_streak = 0
            max_loss_streak = 0

            for pnl in df_sorted['pnl']:
                if pd.notna(pnl):
                    if pnl > 0:  # Win
                        current_win_streak += 1
                        current_loss_streak = 0
                        max_win_streak = max(max_win_streak, current_win_streak)
                    elif pnl < 0:  # Loss
                        current_loss_streak += 1
                        current_win_streak = 0
                        max_loss_streak = max(max_loss_streak, current_loss_streak)

            return {
                'max_win_streak': max_win_streak,
                'max_loss_streak': max_loss_streak
            }
        except Exception as e:
            logger.error(f"Streak calculation error: {str(e)}")
            return {'max_win_streak': 0, 'max_loss_streak': 0}

    def _calculate_duration_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate trade duration statistics."""
        try:
            if 'entry_time' not in df.columns or 'exit_time' not in df.columns:
                return {}

            df_duration = df.copy()
            df_duration['entry_time'] = pd.to_datetime(df_duration['entry_time'], errors='coerce')
            df_duration['exit_time'] = pd.to_datetime(df_duration['exit_time'], errors='coerce')

            # Calculate durations in minutes
            durations = (df_duration['exit_time'] - df_duration['entry_time']).dt.total_seconds() / 60
            durations = durations.dropna()

            if durations.empty:
                return {}

            return {
                'average_minutes': durations.mean(),
                'median_minutes': durations.median(),
                'min_minutes': durations.min(),
                'max_minutes': durations.max()
            }
        except Exception as e:
            logger.error(f"Duration calculation error: {str(e)}")
            return {}

    def _calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """Calculate maximum drawdown."""
        try:
            if df.empty:
                return 0

            cumulative_pnl = df['pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            return abs(drawdown.min())
        except Exception as e:
            logger.error(f"Max drawdown calculation error: {str(e)}")
            return 0

    def _calculate_sharpe_ratio(self, df: pd.DataFrame) -> float:
        """Calculate Sharpe ratio."""
        try:
            if df.empty or df['pnl'].std() == 0:
                return 0

            mean_return = df['pnl'].mean()
            std_return = df['pnl'].std()
            return mean_return / std_return if std_return != 0 else 0
        except Exception as e:
            logger.error(f"Sharpe ratio calculation error: {str(e)}")
            return 0

    def _get_symbol_performance(self, df: pd.DataFrame) -> List[Dict]:
        """Get performance by symbol."""
        try:
            if 'symbol' not in df.columns:
                return []

            symbol_stats = []
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol]
                total_trades = len(symbol_df)
                total_pnl = symbol_df['pnl'].sum()
                wins = len(symbol_df[symbol_df['pnl'] > 0])
                win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

                gross_profit = symbol_df[symbol_df['pnl'] > 0]['pnl'].sum()
                gross_loss = abs(symbol_df[symbol_df['pnl'] < 0]['pnl'].sum())
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit if gross_profit > 0 else 0

                symbol_stats.append({
                    'symbol': symbol,
                    'trades': total_trades,
                    'pnl': total_pnl,
                    'win_rate': win_rate,
                    'profit_factor': profit_factor
                })

            return symbol_stats
        except Exception as e:
            logger.error(f"Symbol performance calculation error: {str(e)}")
            return []

    def _get_monthly_performance(self, df: pd.DataFrame) -> List[Dict]:
        """Get monthly performance breakdown."""
        try:
            if 'exit_time' not in df.columns:
                return []

            df_monthly = df.copy()
            df_monthly['exit_time'] = pd.to_datetime(df_monthly['exit_time'], errors='coerce')
            df_monthly = df_monthly.dropna(subset=['exit_time'])

            if df_monthly.empty:
                return []

            df_monthly['month_year'] = df_monthly['exit_time'].dt.to_period('M')

            monthly_stats = []
            for period in df_monthly['month_year'].unique():
                period_df = df_monthly[df_monthly['month_year'] == period]
                monthly_stats.append({
                    'period': str(period),
                    'trades': len(period_df),
                    'pnl': period_df['pnl'].sum(),
                    'win_rate': (len(period_df[period_df['pnl'] > 0]) / len(period_df) * 100) if len(period_df) > 0 else 0
                })

            return sorted(monthly_stats, key=lambda x: x['period'])
        except Exception as e:
            logger.error(f"Monthly performance calculation error: {str(e)}")
            return []


# Global instance
trade_manager = TradeEntryManager()