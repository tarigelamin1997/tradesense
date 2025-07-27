"""
Filters Module

Contains functions for filtering trade data based on various criteria:
- Date range filtering
- Symbol filtering  
- Strategy filtering
- Tag-based filtering
- Complex multi-criteria filtering
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def apply_trade_filters(
    trades: List[Dict[str, Any]], 
    filters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Apply multiple filters to trade data
    
    Args:
        trades: List of trade dictionaries
        filters: Dictionary of filter criteria
        
    Returns:
        Filtered list of trades
    """
    filtered_trades = trades.copy()
    
    # Date range filter
    if filters.get('start_date'):
        filtered_trades = filter_by_date_range(
            filtered_trades, 
            start_date=filters['start_date']
        )
    
    if filters.get('end_date'):
        filtered_trades = filter_by_date_range(
            filtered_trades, 
            end_date=filters['end_date']
        )
    
    # Symbol filter (support both 'symbol' and 'symbols')
    symbols = filters.get('symbols') or filters.get('symbol')
    if symbols:
        if not isinstance(symbols, list):
            symbols = [symbols]
        filtered_trades = filter_trades_by_symbol(filtered_trades, symbols)
    
    # Strategy filter (support both 'strategy' and 'strategies')
    strategies = filters.get('strategies') or filters.get('strategy')
    if strategies:
        if not isinstance(strategies, list):
            strategies = [strategies]
        filtered_trades = filter_by_strategy(filtered_trades, strategies)
    
    # Tags filter
    if filters.get('tags'):
        filtered_trades = filter_by_tags(filtered_trades, filters['tags'])
    
    # PnL range filter
    if filters.get('min_pnl') is not None:
        filtered_trades = [
            t for t in filtered_trades 
            if (getattr(t, 'pnl', None) if not isinstance(t, dict) else t.get('pnl', 0)) >= filters['min_pnl']
        ]
    
    if filters.get('max_pnl') is not None:
        filtered_trades = [
            t for t in filtered_trades 
            if (getattr(t, 'pnl', None) if not isinstance(t, dict) else t.get('pnl', 0)) <= filters['max_pnl']
        ]
    
    # Confidence score filter
    if filters.get('min_confidence'):
        filtered_trades = [
            t for t in filtered_trades 
            if (getattr(t, 'confidence_score', None) if not isinstance(t, dict) else t.get('confidence_score', 0)) >= filters['min_confidence']
        ]
    
    if filters.get('max_confidence'):
        filtered_trades = [
            t for t in filtered_trades 
            if (getattr(t, 'confidence_score', None) if not isinstance(t, dict) else t.get('confidence_score', 10)) <= filters['max_confidence']
        ]
    
    # Trade status filter
    if filters.get('status'):
        if filters['status'] == 'open':
            filtered_trades = [
                t for t in filtered_trades 
                if not (getattr(t, 'exit_time', None) if not isinstance(t, dict) else t.get('exit_time'))
            ]
        elif filters['status'] == 'closed':
            filtered_trades = [
                t for t in filtered_trades 
                if (getattr(t, 'exit_time', None) if not isinstance(t, dict) else t.get('exit_time'))
            ]
    
    return filtered_trades


def filter_by_date_range(
    trades: List[Dict[str, Any]], 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Filter trades by date range
    
    Args:
        trades: List of trade dictionaries
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        Filtered trades within date range
    """
    filtered = trades
    
    if start_date:
        filtered = [
            t for t in filtered 
            if (getattr(t, 'entry_time', None) if not isinstance(t, dict) else t.get('entry_time')) and (getattr(t, 'entry_time', None) if not isinstance(t, dict) else t.get('entry_time')) >= start_date
        ]
    
    if end_date:
        filtered = [
            t for t in filtered 
            if (getattr(t, 'entry_time', None) if not isinstance(t, dict) else t.get('entry_time')) and (getattr(t, 'entry_time', None) if not isinstance(t, dict) else t.get('entry_time')) <= end_date
        ]
    
    return filtered


def filter_trades_by_symbol(trades: List[Dict[str, Any]], symbols: List[str]) -> List[Dict[str, Any]]:
    """
    Filter trades by a list of trading symbols (case insensitive)
    """
    symbols_upper = [s.upper() for s in symbols]
    return [
        t for t in trades
        if (getattr(t, 'symbol', None) if not isinstance(t, dict) else t.get('symbol', '')).upper() in symbols_upper
    ]


def filter_by_strategy(trades: List[Dict[str, Any]], strategies: List[str]) -> List[Dict[str, Any]]:
    """
    Filter trades by a list of strategy tags (case insensitive)
    """
    strategies_lower = [s.lower() for s in strategies]
    return [
        t for t in trades
        if t.get('strategy_tag', '').lower() in strategies_lower
    ]


def filter_by_tags(trades: List[Dict[str, Any]], tags: List[str]) -> List[Dict[str, Any]]:
    """
    Filter trades by tags (any tag match)
    
    Args:
        trades: List of trade dictionaries
        tags: List of tags to filter by
        
    Returns:
        Trades containing any of the specified tags
    """
    filtered_trades = []
    
    for trade in trades:
        trade_tags = trade.get('tags', [])
        
        # Handle string tags (comma-separated)
        if isinstance(trade_tags, str):
            trade_tags = [tag.strip() for tag in trade_tags.split(',')]
        
        # Check if any filter tag matches trade tags
        if any(tag in trade_tags for tag in tags):
            filtered_trades.append(trade)
    
    return filtered_trades


def filter_winning_trades(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter only winning trades
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Only profitable trades
    """
    return [t for t in trades if t.get('pnl', 0) > 0]


def filter_losing_trades(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter only losing trades
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Only losing trades
    """
    return [t for t in trades if t.get('pnl', 0) < 0]


def filter_by_trade_size(
    trades: List[Dict[str, Any]], 
    min_size: Optional[float] = None,
    max_size: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Filter trades by position size
    
    Args:
        trades: List of trade dictionaries
        min_size: Minimum position size
        max_size: Maximum position size
        
    Returns:
        Trades within size range
    """
    filtered = trades
    
    if min_size is not None:
        filtered = [
            t for t in filtered 
            if t.get('quantity', 0) >= min_size
        ]
    
    if max_size is not None:
        filtered = [
            t for t in filtered 
            if t.get('quantity', 0) <= max_size
        ]
    
    return filtered


def filter_by_weekday(trades: List[Dict[str, Any]], weekdays: List[int]) -> List[Dict[str, Any]]:
    """
    Filter trades by day of week
    
    Args:
        trades: List of trade dictionaries
        weekdays: List of weekday numbers (0=Monday, 6=Sunday)
        
    Returns:
        Trades occurring on specified weekdays
    """
    return [
        t for t in trades 
        if (t.get('entry_time') and 
            t['entry_time'].weekday() in weekdays)
    ]


def filter_by_time_range(
    trades: List[Dict[str, Any]], 
    start_time: str, 
    end_time: str
) -> List[Dict[str, Any]]:
    """
    Filter trades by time of day
    
    Args:
        trades: List of trade dictionaries
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        
    Returns:
        Trades within time range
    """
    from datetime import time
    
    start_time_obj = time.fromisoformat(start_time)
    end_time_obj = time.fromisoformat(end_time)
    
    return [
        t for t in trades 
        if (t.get('entry_time') and 
            start_time_obj <= t['entry_time'].time() <= end_time_obj)
    ]


def filter_by_symbol(trades, symbol):
    """
    Backward compatibility: filter trades by a single symbol (case insensitive).
    """
    return filter_trades_by_symbol(trades, [symbol])


__all__ = [
    'apply_trade_filters',
    'filter_by_date_range',
    'filter_by_symbol',
    'filter_trades_by_symbol',
    'filter_by_strategy',
    'filter_by_tags',
    'filter_winning_trades',
    'filter_losing_trades',
    'filter_by_trade_size',
    'filter_by_weekday',
    'filter_by_time_range',
    'filter_trades_by_strategy',
]
