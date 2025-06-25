
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
    
    # Symbol filter
    if filters.get('symbol'):
        filtered_trades = filter_by_symbol(filtered_trades, filters['symbol'])
    
    # Strategy filter
    if filters.get('strategy'):
        filtered_trades = filter_by_strategy(filtered_trades, filters['strategy'])
    
    # Tags filter
    if filters.get('tags'):
        filtered_trades = filter_by_tags(filtered_trades, filters['tags'])
    
    # PnL range filter
    if filters.get('min_pnl') is not None:
        filtered_trades = [
            t for t in filtered_trades 
            if t.get('pnl', 0) >= filters['min_pnl']
        ]
    
    if filters.get('max_pnl') is not None:
        filtered_trades = [
            t for t in filtered_trades 
            if t.get('pnl', 0) <= filters['max_pnl']
        ]
    
    # Confidence score filter
    if filters.get('min_confidence'):
        filtered_trades = [
            t for t in filtered_trades 
            if t.get('confidence_score', 0) >= filters['min_confidence']
        ]
    
    if filters.get('max_confidence'):
        filtered_trades = [
            t for t in filtered_trades 
            if t.get('confidence_score', 10) <= filters['max_confidence']
        ]
    
    # Trade status filter
    if filters.get('status'):
        if filters['status'] == 'open':
            filtered_trades = [
                t for t in filtered_trades 
                if not t.get('exit_time')
            ]
        elif filters['status'] == 'closed':
            filtered_trades = [
                t for t in filtered_trades 
                if t.get('exit_time')
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
            if t.get('entry_time') and t['entry_time'] >= start_date
        ]
    
    if end_date:
        filtered = [
            t for t in filtered 
            if t.get('entry_time') and t['entry_time'] <= end_date
        ]
    
    return filtered


def filter_by_symbol(trades: List[Dict[str, Any]], symbol: str) -> List[Dict[str, Any]]:
    """
    Filter trades by trading symbol
    
    Args:
        trades: List of trade dictionaries
        symbol: Symbol to filter by (case insensitive)
        
    Returns:
        Trades matching the symbol
    """
    return [
        t for t in trades 
        if t.get('symbol', '').upper() == symbol.upper()
    ]


def filter_by_strategy(trades: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    """
    Filter trades by strategy tag
    
    Args:
        trades: List of trade dictionaries
        strategy: Strategy name to filter by
        
    Returns:
        Trades matching the strategy
    """
    return [
        t for t in trades 
        if t.get('strategy_tag') == strategy
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
