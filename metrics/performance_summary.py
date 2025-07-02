
"""
Aggregate performance metrics and summary statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics."""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # P&L metrics
    total_pnl: float
    gross_profit: float
    gross_loss: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Ratios
    profit_factor: float
    expectancy: float
    avg_win_loss_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_percent: float
    recovery_factor: float
    
    # Streak metrics
    max_win_streak: int
    max_loss_streak: int
    current_streak: int
    current_streak_type: str
    
    # Duration metrics
    avg_trade_duration: float
    median_trade_duration: float
    
    # Return metrics
    total_return_percent: float
    
    # Advanced metrics (with defaults)
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    annualized_return: Optional[float] = None


class PerformanceSummary:
    """Calculate comprehensive performance summary for trade data."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with trade DataFrame.
        
        Args:
            df: DataFrame containing trade data with required columns
        """
        self.df = df.copy()
        self.metrics = None
        self._validate_data()
        
    def _validate_data(self):
        """Validate that required columns exist."""
        required_cols = ['pnl', 'entry_time', 'exit_time']
        missing_cols = [col for col in required_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def calculate_all_metrics(self) -> PerformanceMetrics:
        """Calculate all performance metrics."""
        
        # Basic trade statistics
        total_trades = len(self.df)
        pnl_series = pd.to_numeric(self.df['pnl'], errors='coerce').dropna()
        
        if len(pnl_series) == 0:
            raise ValueError("No valid P&L data found")
        
        winning_trades = len(pnl_series[pnl_series > 0])
        losing_trades = len(pnl_series[pnl_series < 0])
        win_rate = (winning_trades / len(pnl_series)) * 100 if len(pnl_series) > 0 else 0
        
        # P&L calculations
        total_pnl = pnl_series.sum()
        gross_profit = pnl_series[pnl_series > 0].sum()
        gross_loss = abs(pnl_series[pnl_series < 0].sum())
        
        avg_win = pnl_series[pnl_series > 0].mean() if winning_trades > 0 else 0
        avg_loss = abs(pnl_series[pnl_series < 0].mean()) if losing_trades > 0 else 0
        
        largest_win = pnl_series.max()
        largest_loss = pnl_series.min()
        
        # Ratios
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        expectancy = pnl_series.mean() if len(pnl_series) > 0 else 0
        avg_win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf') if avg_win > 0 else 0
        
        # Drawdown calculations
        cumulative_pnl = pnl_series.cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = running_max - cumulative_pnl
        max_drawdown = drawdown.max()
        max_drawdown_percent = (max_drawdown / running_max.max() * 100) if running_max.max() > 0 else 0
        
        # Recovery factor
        recovery_factor = total_pnl / max_drawdown if max_drawdown > 0 else float('inf') if total_pnl > 0 else 0
        
        # Streak calculations
        streaks = self._calculate_streaks(pnl_series)
        
        # Duration metrics
        duration_metrics = self._calculate_duration_metrics()
        
        # Advanced ratios
        sharpe_ratio = self._calculate_sharpe_ratio(pnl_series)
        sortino_ratio = self._calculate_sortino_ratio(pnl_series)
        calmar_ratio = self._calculate_calmar_ratio(pnl_series, max_drawdown_percent)
        
        # Return metrics
        initial_capital = self._estimate_initial_capital()
        total_return_percent = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
        annualized_return = self._calculate_annualized_return(total_return_percent)
        
        self.metrics = PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_win_loss_ratio=avg_win_loss_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            recovery_factor=recovery_factor,
            max_win_streak=streaks['max_win_streak'],
            max_loss_streak=streaks['max_loss_streak'],
            current_streak=streaks['current_streak'],
            current_streak_type=streaks['current_streak_type'],
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            avg_trade_duration=duration_metrics['avg_duration'],
            median_trade_duration=duration_metrics['median_duration'],
            total_return_percent=total_return_percent,
            annualized_return=annualized_return
        )
        
        return self.metrics
    
    def _calculate_streaks(self, pnl_series: pd.Series) -> Dict[str, Any]:
        """Calculate win/loss streaks."""
        if len(pnl_series) == 0:
            return {
                'max_win_streak': 0,
                'max_loss_streak': 0,
                'current_streak': 0,
                'current_streak_type': 'none'
            }
        
        streaks = []
        current_streak = 1
        current_type = 'win' if pnl_series.iloc[0] > 0 else 'loss'
        
        for i in range(1, len(pnl_series)):
            is_win = pnl_series.iloc[i] > 0
            if (is_win and current_type == 'win') or (not is_win and current_type == 'loss'):
                current_streak += 1
            else:
                streaks.append((current_type, current_streak))
                current_streak = 1
                current_type = 'win' if is_win else 'loss'
        
        streaks.append((current_type, current_streak))
        
        win_streaks = [length for streak_type, length in streaks if streak_type == 'win']
        loss_streaks = [length for streak_type, length in streaks if streak_type == 'loss']
        
        return {
            'max_win_streak': max(win_streaks) if win_streaks else 0,
            'max_loss_streak': max(loss_streaks) if loss_streaks else 0,
            'current_streak': current_streak,
            'current_streak_type': current_type
        }
    
    def _calculate_duration_metrics(self) -> Dict[str, float]:
        """Calculate trade duration metrics."""
        try:
            entry_times = pd.to_datetime(self.df['entry_time'])
            exit_times = pd.to_datetime(self.df['exit_time'])
            durations = (exit_times - entry_times).dt.total_seconds() / 3600  # hours
            
            return {
                'avg_duration': durations.mean(),
                'median_duration': durations.median()
            }
        except:
            return {'avg_duration': 0, 'median_duration': 0}
    
    def _calculate_sharpe_ratio(self, pnl_series: pd.Series, risk_free_rate: float = 0.02) -> Optional[float]:
        """Calculate Sharpe ratio."""
        if len(pnl_series) < 2:
            return None
        
        returns = pnl_series / pnl_series.abs().mean() if pnl_series.abs().mean() > 0 else pnl_series
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        if returns.std() == 0:
            return None
        
        return excess_returns.mean() / returns.std() * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, pnl_series: pd.Series, risk_free_rate: float = 0.02) -> Optional[float]:
        """Calculate Sortino ratio."""
        if len(pnl_series) < 2:
            return None
        
        returns = pnl_series / pnl_series.abs().mean() if pnl_series.abs().mean() > 0 else pnl_series
        excess_returns = returns - (risk_free_rate / 252)
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) == 0 or negative_returns.std() == 0:
            return None
        
        downside_deviation = negative_returns.std()
        return excess_returns.mean() / downside_deviation * np.sqrt(252)
    
    def _calculate_calmar_ratio(self, pnl_series: pd.Series, max_drawdown_percent: float) -> Optional[float]:
        """Calculate Calmar ratio."""
        if max_drawdown_percent == 0:
            return None
        
        annualized_return = self._calculate_annualized_return((pnl_series.sum() / self._estimate_initial_capital()) * 100)
        
        if annualized_return is None:
            return None
        
        return annualized_return / max_drawdown_percent
    
    def _estimate_initial_capital(self) -> float:
        """Estimate initial capital from trade data."""
        try:
            if 'qty' in self.df.columns and 'entry_price' in self.df.columns:
                position_values = pd.to_numeric(self.df['qty'], errors='coerce') * pd.to_numeric(self.df['entry_price'], errors='coerce')
                return position_values.median() * 10  # Assume 10x leverage or similar
            else:
                # Fallback estimate
                pnl_series = pd.to_numeric(self.df['pnl'], errors='coerce').dropna()
                return abs(pnl_series).sum() * 20  # Conservative estimate
        except:
            return 100000  # Default fallback
    
    def _calculate_annualized_return(self, total_return_percent: float) -> Optional[float]:
        """Calculate annualized return."""
        try:
            entry_times = pd.to_datetime(self.df['entry_time'])
            exit_times = pd.to_datetime(self.df['exit_time'])
            
            total_days = (exit_times.max() - entry_times.min()).days
            if total_days <= 0:
                return None
            
            years = total_days / 365.25
            return (1 + total_return_percent / 100) ** (1 / years) - 1 if years > 0 else None
        except:
            return None
    
    def get_summary_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary for easy display."""
        if self.metrics is None:
            self.calculate_all_metrics()
        
        return {
            'Basic Metrics': {
                'Total Trades': self.metrics.total_trades,
                'Win Rate (%)': round(self.metrics.win_rate, 2),
                'Winning Trades': self.metrics.winning_trades,
                'Losing Trades': self.metrics.losing_trades,
            },
            'P&L Metrics': {
                'Total P&L ($)': round(self.metrics.total_pnl, 2),
                'Gross Profit ($)': round(self.metrics.gross_profit, 2),
                'Gross Loss ($)': round(self.metrics.gross_loss, 2),
                'Average Win ($)': round(self.metrics.avg_win, 2),
                'Average Loss ($)': round(self.metrics.avg_loss, 2),
                'Largest Win ($)': round(self.metrics.largest_win, 2),
                'Largest Loss ($)': round(self.metrics.largest_loss, 2),
            },
            'Performance Ratios': {
                'Profit Factor': round(self.metrics.profit_factor, 2),
                'Expectancy ($)': round(self.metrics.expectancy, 2),
                'Avg Win/Loss Ratio': round(self.metrics.avg_win_loss_ratio, 2),
                'Recovery Factor': round(self.metrics.recovery_factor, 2),
            },
            'Risk Metrics': {
                'Max Drawdown ($)': round(self.metrics.max_drawdown, 2),
                'Max Drawdown (%)': round(self.metrics.max_drawdown_percent, 2),
                'Sharpe Ratio': round(self.metrics.sharpe_ratio, 2) if self.metrics.sharpe_ratio else 'N/A',
                'Sortino Ratio': round(self.metrics.sortino_ratio, 2) if self.metrics.sortino_ratio else 'N/A',
            },
            'Streaks': {
                'Max Win Streak': self.metrics.max_win_streak,
                'Max Loss Streak': self.metrics.max_loss_streak,
                'Current Streak': f"{self.metrics.current_streak} ({self.metrics.current_streak_type})",
            },
            'Duration': {
                'Avg Trade Duration (hrs)': round(self.metrics.avg_trade_duration, 2),
                'Median Trade Duration (hrs)': round(self.metrics.median_trade_duration, 2),
            },
            'Returns': {
                'Total Return (%)': round(self.metrics.total_return_percent, 2),
                'Annualized Return (%)': round(self.metrics.annualized_return * 100, 2) if self.metrics.annualized_return else 'N/A',
            }
        }
