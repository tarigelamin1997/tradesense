
"""
Equity Analytics Module

Contains equity curve generation and drawdown analysis functions:
- Equity curve calculation
- Maximum drawdown analysis
- Rolling returns
- Balance progression
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from .utils import safe_divide


def generate_equity_curve(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate equity curve from trade data
    
    Args:
        trades: List of trade dictionaries with 'pnl' and 'entry_time' fields
        
    Returns:
        List of equity points with timestamp and cumulative balance
    """
    if not trades:
        return []
    
    # Sort trades by entry time
    sorted_trades = sorted(trades, key=lambda x: x.get('entry_time', datetime.min))
    
    equity_curve = []
    cumulative_pnl = 0.0
    
    for trade in sorted_trades:
        pnl = trade.get('pnl', 0)
        if pnl is not None:
            cumulative_pnl += pnl
        
        equity_curve.append({
            'timestamp': trade.get('entry_time'),
            'balance': cumulative_pnl,
            'trade_pnl': pnl,
            'trade_id': trade.get('id')
        })
    
    return equity_curve


def calculate_drawdown(equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate drawdown from equity curve
    
    Args:
        equity_curve: List of equity points from generate_equity_curve()
        
    Returns:
        List of drawdown points with percentage and absolute drawdown
    """
    if not equity_curve:
        return []
    
    drawdown_curve = []
    peak_balance = equity_curve[0]['balance']
    
    for point in equity_curve:
        balance = point['balance']
        
        # Update peak if we have a new high
        if balance > peak_balance:
            peak_balance = balance
        
        # Calculate drawdown
        absolute_drawdown = balance - peak_balance
        percentage_drawdown = safe_divide(absolute_drawdown, peak_balance) * 100 if peak_balance != 0 else 0
        
        drawdown_curve.append({
            'timestamp': point['timestamp'],
            'balance': balance,
            'peak_balance': peak_balance,
            'absolute_drawdown': absolute_drawdown,
            'percentage_drawdown': percentage_drawdown
        })
    
    return drawdown_curve


def calculate_max_drawdown(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate maximum drawdown metrics
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with max drawdown statistics
    """
    equity_curve = generate_equity_curve(trades)
    
    if not equity_curve:
        return {
            'max_drawdown_amount': 0.0,
            'max_drawdown_percentage': 0.0,
            'drawdown_start': None,
            'drawdown_end': None,
            'recovery_date': None
        }
    
    drawdown_curve = calculate_drawdown(equity_curve)
    
    # Find maximum drawdown
    max_dd_point = min(drawdown_curve, key=lambda x: x['percentage_drawdown'])
    
    # Find drawdown period
    drawdown_start = None
    drawdown_end = max_dd_point['timestamp']
    recovery_date = None
    
    # Find start of drawdown period
    for i, point in enumerate(drawdown_curve):
        if point['timestamp'] == max_dd_point['timestamp']:
            # Look backwards for the peak
            for j in range(i, -1, -1):
                if drawdown_curve[j]['absolute_drawdown'] == 0:
                    drawdown_start = drawdown_curve[j]['timestamp']
                    break
            break
    
    # Find recovery date
    max_dd_balance = max_dd_point['peak_balance']
    for point in drawdown_curve:
        if (point['timestamp'] > drawdown_end and 
            point['balance'] >= max_dd_balance):
            recovery_date = point['timestamp']
            break
    
    return {
        'max_drawdown_amount': max_dd_point['absolute_drawdown'],
        'max_drawdown_percentage': max_dd_point['percentage_drawdown'],
        'drawdown_start': drawdown_start,
        'drawdown_end': drawdown_end,
        'recovery_date': recovery_date
    }


def calculate_rolling_returns(trades: List[Dict[str, Any]], window_days: int = 30) -> List[Dict[str, Any]]:
    """
    Calculate rolling returns over specified window
    
    Args:
        trades: List of trade dictionaries
        window_days: Rolling window size in days
        
    Returns:
        List of rolling return points
    """
    if not trades:
        return []
    
    # Convert to DataFrame for easier rolling calculations
    df = pd.DataFrame([
        {
            'date': trade.get('entry_time'),
            'pnl': trade.get('pnl', 0)
        }
        for trade in trades if trade.get('entry_time')
    ])
    
    if df.empty:
        return []
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df = df.set_index('date')
    
    # Resample to daily and sum PnL
    daily_pnl = df.resample('D')['pnl'].sum().fillna(0)
    
    # Calculate rolling returns
    rolling_returns = daily_pnl.rolling(window=window_days).sum()
    
    return [
        {
            'date': date.to_pydatetime(),
            'rolling_return': return_value,
            'window_days': window_days
        }
        for date, return_value in rolling_returns.items()
        if not pd.isna(return_value)
    ]


def calculate_balance_progression(trades: List[Dict[str, Any]], starting_balance: float = 10000) -> List[Dict[str, Any]]:
    """
    Calculate account balance progression over time
    
    Args:
        trades: List of trade dictionaries
        starting_balance: Initial account balance
        
    Returns:
        List of balance progression points
    """
    equity_curve = generate_equity_curve(trades)
    
    return [
        {
            'timestamp': point['timestamp'],
            'balance': starting_balance + point['balance'],
            'pnl_change': point['trade_pnl'],
            'total_pnl': point['balance']
        }
        for point in equity_curve
    ]
