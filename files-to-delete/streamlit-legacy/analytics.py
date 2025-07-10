import pandas as pd
import numpy as np
import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import centralized logging
try:
    from logging_manager import log_error, log_warning, log_info, LogCategory
    CENTRALIZED_LOGGING = True
except ImportError:
    # Fallback to basic logging if centralized logging not available
    CENTRALIZED_LOGGING = False
    logging.basicConfig(
        filename='analytics.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'
    )
    logger = logging.getLogger(__name__)

def log_debug_info(context: str, data):
    """Log debug information to file instead of UI."""
    if CENTRALIZED_LOGGING:
        log_info(f"Analytics debug - {context}", 
                details={"data": str(data)[:1000]}, 
                category=LogCategory.DATA_PROCESSING)
    else:
        logger.debug(f"{context}: {data}")

def format_currency(value, default="–"):
    """Format currency values with $ and 2 decimal places."""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return default
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return default

def format_percentage(value, default="–"):
    """Format percentage values with % and 1 decimal place."""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return default
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return default

def format_number(value, decimals=2, default="–"):
    """Format general numbers with specified decimal places."""
    try:
        if pd.isna(value) or not np.isfinite(value):
            return default
        return f"{float(value):,.{decimals}f}"
    except (ValueError, TypeError):
        return default

@st.cache_data
def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Compute basic trading statistics."""
    try:
        log_debug_info("compute_basic_stats input dtypes", df.dtypes.to_dict())
        log_debug_info("compute_basic_stats sample data", df.head().to_dict())

        if df.empty:
            if CENTRALIZED_LOGGING:
                log_warning("Empty dataframe passed to compute_basic_stats", 
                           category=LogCategory.DATA_PROCESSING)
            else:
                logger.warning("Empty dataframe passed to compute_basic_stats")
            return {}
    except Exception as e:
        error_msg = f"Error in compute_basic_stats initialization: {str(e)}"
        if CENTRALIZED_LOGGING:
            log_error(error_msg, 
                     details={"error_type": type(e).__name__, "dataframe_shape": df.shape if not df.empty else "empty"},
                     category=LogCategory.DATA_PROCESSING)
        else:
            logger.error(error_msg)
        return {}

    # Clean PnL data
    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])
    df = df[np.isfinite(df['pnl'])]

    if df.empty:
        logger.warning("No valid PnL data after cleaning")
        return {}

    log_debug_info("Cleaned PnL data", df['pnl'].describe().to_dict())

    winning_trades = df[df['pnl'] > 0]
    losing_trades = df[df['pnl'] < 0]

    total_trades = len(df)
    winning_count = len(winning_trades)
    losing_count = len(losing_trades)

    # Win rate
    win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0

    # Average win/loss
    avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0

    # Reward to risk ratio
    reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    # Expectancy
    expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)

    # Profit factor
    gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
    gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    # Max drawdown
    cumulative_pnl = df['pnl'].cumsum()
    running_max = cumulative_pnl.expanding().max()
    drawdown = running_max - cumulative_pnl
    max_drawdown = drawdown.max()

    # Sharpe ratio (simplified)
    if len(df) > 1:
        returns_std = df['pnl'].std()
        sharpe_ratio = df['pnl'].mean() / returns_std if returns_std > 0 else 0
    else:
        sharpe_ratio = 0

    stats = {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'average_win': avg_win,
        'average_loss': avg_loss,
        'reward_risk': reward_risk,
        'expectancy': expectancy,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'equity_curve': cumulative_pnl
    }

    log_debug_info("Computed stats", stats)
    return stats

@st.cache_data
def performance_over_time(df: pd.DataFrame, freq: str = 'M') -> pd.DataFrame:
    """Compute performance metrics over time periods."""
    log_debug_info("performance_over_time input", f"df shape: {df.shape}, freq: {freq}")

    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Clean PnL data more thoroughly
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    # Remove infinite values
    df = df[np.isfinite(df['pnl'])]
    df = df[df['pnl'] != np.inf]
    df = df[df['pnl'] != -np.inf]

    if 'exit_time' not in df.columns:
        logger.warning("exit_time column missing")
        return pd.DataFrame()

    # Clean exit_time data
    df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
    df = df.dropna(subset=['exit_time'])

    # Remove rows with invalid dates (like NaT or extreme dates)
    valid_date_mask = (df['exit_time'] > pd.Timestamp('1970-01-01')) & (df['exit_time'] < pd.Timestamp('2100-01-01'))
    df = df[valid_date_mask]

    if df.empty:
        logger.warning("No valid data after cleaning in performance_over_time")
        return pd.DataFrame()

    try:
        # Group by time period
        df['period'] = df['exit_time'].dt.to_period(freq)
        df = df.dropna(subset=['period'])  # Remove any NaT periods

        if df.empty:
            logger.warning("No valid periods after conversion")
            return pd.DataFrame()

        grouped = df.groupby('period')

        if len(grouped) == 0:
            logger.warning("No groups found after grouping")
            return pd.DataFrame()

        # Calculate metrics safely
        periods = []
        trades = []
        pnls = []
        win_rates = []

        for period, group in grouped:
            if len(group) > 0:
                periods.append(period)
                trades.append(len(group))
                group_pnl = group['pnl'].sum()
                pnls.append(group_pnl if np.isfinite(group_pnl) else 0)

                # Calculate win rate safely
                wins = (group['pnl'] > 0).sum()
                total = len(group)
                win_rate = (wins / total * 100) if total > 0 else 0
                win_rates.append(win_rate if np.isfinite(win_rate) else 0)

        if len(periods) == 0:
            logger.warning("No valid periods collected")
            return pd.DataFrame()

        result = pd.DataFrame({
            'period': periods,
            'trades': trades,
            'pnl': pnls,
            'win_rate': win_rates
        })

        # Final check for any remaining infinite values
        for col in ['pnl', 'win_rate']:
            if col in result.columns:
                result[col] = result[col].replace([np.inf, -np.inf], 0)
                result[col] = result[col].fillna(0)

        log_debug_info("performance_over_time result", result.to_dict())
        return result

    except Exception as e:
        logger.error(f"Error in performance_over_time: {str(e)}")
        return pd.DataFrame()

def median_results(df: pd.DataFrame) -> dict:
    """Calculate median trading results."""
    log_debug_info("median_results input", f"df shape: {df.shape}")

    if df.empty:
        return {'median_pnl': 0, 'median_win': 0, 'median_loss': 0}

    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    winning_trades = df[df['pnl'] > 0]
    losing_trades = df[df['pnl'] < 0]

    result = {
        'median_pnl': df['pnl'].median(),
        'median_win': winning_trades['pnl'].median() if not winning_trades.empty else 0,
        'median_loss': losing_trades['pnl'].median() if not losing_trades.empty else 0
    }

    log_debug_info("median_results", result)
    return result

def profit_factor_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate profit factor for each symbol."""
    log_debug_info("profit_factor_by_symbol input", f"df shape: {df.shape}")

    if df.empty or 'symbol' not in df.columns:
        return pd.DataFrame(columns=['symbol', 'profit_factor'])

    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    def calc_pf(group):
        wins = group[group['pnl'] > 0]['pnl'].sum()
        losses = abs(group[group['pnl'] < 0]['pnl'].sum())
        return wins / losses if losses > 0 else 0

    result = df.groupby('symbol').apply(calc_pf).reset_index()
    result.columns = ['symbol', 'profit_factor']

    log_debug_info("profit_factor_by_symbol result", result.to_dict())
    return result

def trade_duration_stats(df: pd.DataFrame) -> dict:
    """Calculate trade duration statistics."""
    log_debug_info("trade_duration_stats input", f"df shape: {df.shape}")

    if df.empty or 'entry_time' not in df.columns or 'exit_time' not in df.columns:
        return {'average_minutes': 0, 'min_minutes': 0, 'max_minutes': 0, 'median_minutes': 0}

    df = df.copy()
    df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
    df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
    df = df.dropna(subset=['entry_time', 'exit_time'])

    if df.empty:
        return {'average_minutes': 0, 'min_minutes': 0, 'max_minutes': 0, 'median_minutes': 0}

    df['duration'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 60

    result = {
        'average_minutes': df['duration'].mean(),
        'min_minutes': df['duration'].min(),
        'max_minutes': df['duration'].max(),
        'median_minutes': df['duration'].median()
    }

    log_debug_info("trade_duration_stats", result)
    return result

def max_streaks(df: pd.DataFrame) -> dict:
    """Calculate maximum winning and losing streaks."""
    log_debug_info("max_streaks input", f"df shape: {df.shape}")

    if df.empty:
        return {'max_win_streak': 0, 'max_loss_streak': 0}

    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    if df.empty:
        return {'max_win_streak': 0, 'max_loss_streak': 0}

    df = df.sort_values('exit_time' if 'exit_time' in df.columns else df.index)
    df['is_win'] = df['pnl'] > 0

    # Calculate streaks
    df['streak_id'] = (df['is_win'] != df['is_win'].shift()).cumsum()
    streaks = df.groupby(['streak_id', 'is_win']).size()

    win_streaks = streaks[streaks.index.get_level_values(1) == True]
    loss_streaks = streaks[streaks.index.get_level_values(1) == False]

    result = {
        'max_win_streak': win_streaks.max() if not win_streaks.empty else 0,
        'max_loss_streak': loss_streaks.max() if not loss_streaks.empty else 0
    }

    log_debug_info("max_streaks", result)
    return result

def rolling_metrics(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Calculate rolling metrics over a specified window."""
    log_debug_info("rolling_metrics input", f"df shape: {df.shape}, window: {window}")

    if df.empty:
        log_debug_info("rolling_metrics", "Empty dataframe")
        return pd.DataFrame()

    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    # Additional cleaning to prevent infinite values
    df = df[np.isfinite(df['pnl'])]
    df = df[df['pnl'] != np.inf]
    df = df[df['pnl'] != -np.inf]

    # Remove extreme outliers that could cause infinite values
    if not df.empty:
        q99 = df['pnl'].quantile(0.99)
        q1 = df['pnl'].quantile(0.01)
        if np.isfinite(q99) and np.isfinite(q1):
            # Cap values to prevent infinite calculations
            max_val = abs(q99 - q1) * 100  # Allow up to 100x IQR
            df = df[abs(df['pnl']) <= max_val]

    # Check again after cleaning
    if df.empty or len(df) < window:
        log_debug_info("rolling_metrics", f"Insufficient data after cleaning: {len(df)} < {window}")
        return pd.DataFrame()

    # Sort by exit_time if available, otherwise by index
    if 'exit_time' in df.columns:
        df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
        df = df.dropna(subset=['exit_time'])
        if df.empty or len(df) < window:
            return pd.DataFrame()
        df = df.sort_values('exit_time')
    else:
        df = df.sort_index()

    rolling_data = []
    for i in range(window, len(df) + 1):
        subset = df.iloc[i-window:i]

        # Ensure subset has valid data
        if subset.empty or len(subset) != window:
            continue

        wins = (subset['pnl'] > 0).sum()
        win_rate = wins / window * 100

        winning_trades = subset[subset['pnl'] > 0]
        losing_trades = subset[subset['pnl'] < 0]

        gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0

        # Calculate profit factor with safety checks
        if gross_loss > 0 and np.isfinite(gross_loss) and np.isfinite(gross_profit):
            profit_factor = gross_profit / gross_loss
            # Cap profit factor to reasonable values to prevent chart issues
            profit_factor = min(max(profit_factor, 0), 50.0)  # Cap between 0 and 50
        elif gross_profit > 0 and gross_loss == 0:
            profit_factor = 10.0  # Reasonable upper bound for all-winning periods
        else:
            profit_factor = 0.0

        # Ensure values are finite and reasonable
        if not np.isfinite(win_rate) or win_rate < 0 or win_rate > 100:
            win_rate = 0.0
        if not np.isfinite(profit_factor) or profit_factor < 0:
            profit_factor = 0.0

        rolling_data.append({
            'end_index': i,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        })

    if not rolling_data:
        log_debug_info("rolling_metrics", "No valid rolling data generated")
        return pd.DataFrame()

    result = pd.DataFrame(rolling_data)

    # Final validation of result data
    if not result.empty:
        # Remove any remaining infinite values
        result = result.replace([np.inf, -np.inf], np.nan)
        result = result.dropna()

        # Ensure reasonable ranges
        if 'win_rate' in result.columns:
            result['win_rate'] = result['win_rate'].clip(0, 100)
        if 'profit_factor' in result.columns:
            result['profit_factor'] = result['profit_factor'].clip(0, 50)

    log_debug_info("rolling_metrics result", f"Generated {len(result)} rolling periods")
    return result

def calculate_kpis(df: pd.DataFrame, commission_per_trade: float = 3.5) -> dict:
    """Calculate key performance indicators."""
    log_debug_info("calculate_kpis input", f"df shape: {df.shape}, commission: {commission_per_trade}")

    if df.empty:
        return {
            'total_trades': 0,
            'gross_pnl': 0,
            'total_commission': 0,
            'net_pnl_after_commission': 0,
            'win_rate_percent': 0,
            'max_single_trade_win': 0,
            'max_single_trade_loss': 0,
            'average_rr': 0
        }

    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    total_trades = len(df)
    gross_pnl = df['pnl'].sum()
    total_commission = total_trades * commission_per_trade
    net_pnl = gross_pnl - total_commission

    winning_trades = df[df['pnl'] > 0]
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

    max_win = df['pnl'].max() if not df.empty else 0
    max_loss = df['pnl'].min() if not df.empty else 0

    # Simple R:R calculation
    avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
    avg_loss = abs(df[df['pnl'] < 0]['pnl'].mean()) if len(df[df['pnl'] < 0]) > 0 else 0
    average_rr = avg_win / avg_loss if avg_loss > 0 else 0

    kpis = {
        'total_trades': total_trades,
        'gross_pnl': gross_pnl,
        'total_commission': total_commission,
        'net_pnl_after_commission': net_pnl,
        'win_rate_percent': win_rate,
        'max_single_trade_win': max_win,
        'max_single_trade_loss': max_loss,
        'average_rr': average_rr
    }

    log_debug_info("calculate_kpis result", kpis)
    return kpis