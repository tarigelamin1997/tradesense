
"""
Performance Analytics Module

Contains all core trading performance calculations including:
- Win rate and profit factor
- Risk/reward ratios
- Expectancy and Sharpe ratio
- Average trade metrics
"""

from typing import List, Dict, Any, Optional
import statistics
from .utils import safe_divide


def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
    """
    Calculate win rate as percentage of profitable trades
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Win rate as percentage (0-100)
    """
    if not trades:
        return 0.0
    
    winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
    return (winning_trades / len(trades)) * 100


def calculate_profit_factor(trades: List[Dict[str, Any]]) -> float:
    """
    Calculate profit factor (gross profit / gross loss)
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Profit factor ratio
    """
    if not trades:
        return 0.0
    
    pnl_values = [t.get('pnl', 0) for t in trades]
    gross_profit = sum([pnl for pnl in pnl_values if pnl > 0])
    gross_loss = abs(sum([pnl for pnl in pnl_values if pnl < 0]))
    
    return safe_divide(gross_profit, gross_loss)


def calculate_expectancy(trades: List[Dict[str, Any]]) -> float:
    """
    Calculate expectancy (average PnL per trade)
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Average PnL per trade
    """
    if not trades:
        return 0.0
    
    total_pnl = sum([t.get('pnl', 0) for t in trades])
    return total_pnl / len(trades)


def calculate_risk_reward_metrics(trades: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate comprehensive risk/reward metrics
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary containing risk/reward metrics
    """
    if not trades:
        return {
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'expectancy': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'risk_reward_ratio': 0.0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0
        }
    
    pnl_values = [t.get('pnl', 0) for t in trades]
    winning_trades = [pnl for pnl in pnl_values if pnl > 0]
    losing_trades = [pnl for pnl in pnl_values if pnl < 0]
    
    avg_win = statistics.mean(winning_trades) if winning_trades else 0.0
    avg_loss = statistics.mean(losing_trades) if losing_trades else 0.0
    
    return {
        'win_rate': calculate_win_rate(trades),
        'profit_factor': calculate_profit_factor(trades),
        'expectancy': calculate_expectancy(trades),
        'avg_win': avg_win,
        'avg_loss': abs(avg_loss),
        'risk_reward_ratio': safe_divide(avg_win, abs(avg_loss)),
        'total_pnl': sum(pnl_values),
        'best_trade': max(pnl_values) if pnl_values else 0.0,
        'worst_trade': min(pnl_values) if pnl_values else 0.0
    }


def calculate_sharpe_ratio(trades: List[Dict[str, Any]], risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio for trade returns
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        risk_free_rate: Annual risk-free rate (default 2%)
        
    Returns:
        Sharpe ratio
    """
    if len(trades) < 2:
        return 0.0
    
    returns = [t.get('pnl', 0) for t in trades]
    
    if not returns:
        return 0.0
    
    try:
        avg_return = statistics.mean(returns)
        return_std = statistics.stdev(returns)
        
        if return_std == 0:
            return 0.0
        
        # Convert to annualized assuming daily trades
        excess_return = avg_return - (risk_free_rate / 252)  # Daily risk-free rate
        sharpe = excess_return / return_std * (252 ** 0.5)  # Annualize
        
        return sharpe
    except statistics.StatisticsError:
        return 0.0


def calculate_performance_by_symbol(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate performance metrics grouped by trading symbol
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with symbol-based performance metrics
    """
    symbol_groups = {}
    
    for trade in trades:
        symbol = trade.get('symbol', 'Unknown')
        if symbol not in symbol_groups:
            symbol_groups[symbol] = []
        symbol_groups[symbol].append(trade)
    
    return {
        symbol: calculate_risk_reward_metrics(symbol_trades)
        for symbol, symbol_trades in symbol_groups.items()
    }


def calculate_performance_by_strategy(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate performance metrics grouped by strategy
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with strategy-based performance metrics
    """
    strategy_groups = {}
    
    for trade in trades:
        strategy = trade.get('strategy_tag', 'No Strategy')
        if strategy not in strategy_groups:
            strategy_groups[strategy] = []
        strategy_groups[strategy].append(trade)
    
    return {
        strategy: calculate_risk_reward_metrics(strategy_trades)
        for strategy, strategy_trades in strategy_groups.items()
    }
