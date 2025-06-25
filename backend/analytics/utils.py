
"""
Analytics Utilities Module

Contains helper functions for analytics calculations:
- Safe mathematical operations
- Data validation
- Formatting utilities
- Common calculations
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import math


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling division by zero
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Value to return if denominator is zero
        
    Returns:
        Division result or default value
    """
    if denominator == 0 or denominator is None:
        return default
    
    try:
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def round_percentage(value: float, decimals: int = 2) -> float:
    """
    Round percentage value to specified decimal places
    
    Args:
        value: Percentage value to round
        decimals: Number of decimal places
        
    Returns:
        Rounded percentage
    """
    if value is None or math.isnan(value) or math.isinf(value):
        return 0.0
    
    return round(float(value), decimals)


def format_currency(amount: float, symbol: str = "$") -> str:
    """
    Format currency amount with symbol and commas
    
    Args:
        amount: Amount to format
        symbol: Currency symbol
        
    Returns:
        Formatted currency string
    """
    if amount is None or math.isnan(amount) or math.isinf(amount):
        return f"{symbol}0.00"
    
    if amount >= 0:
        return f"{symbol}{amount:,.2f}"
    else:
        return f"-{symbol}{abs(amount):,.2f}"


def calculate_trade_duration(entry_time: datetime, exit_time: Optional[datetime]) -> Optional[float]:
    """
    Calculate trade duration in hours
    
    Args:
        entry_time: Trade entry timestamp
        exit_time: Trade exit timestamp (None for open trades)
        
    Returns:
        Duration in hours or None for open trades
    """
    if not exit_time or not entry_time:
        return None
    
    try:
        duration = exit_time - entry_time
        return duration.total_seconds() / 3600  # Convert to hours
    except (TypeError, AttributeError):
        return None


def validate_trade_data(trade: Dict[str, Any]) -> bool:
    """
    Validate trade data structure and required fields
    
    Args:
        trade: Trade dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['symbol', 'direction', 'quantity', 'entry_price', 'entry_time']
    
    # Check required fields exist
    for field in required_fields:
        if field not in trade or trade[field] is None:
            return False
    
    # Validate data types and ranges
    try:
        # Numeric validations
        if float(trade['quantity']) <= 0:
            return False
        
        if float(trade['entry_price']) <= 0:
            return False
        
        # Direction validation
        if trade['direction'] not in ['long', 'short']:
            return False
        
        # Date validation
        if not isinstance(trade['entry_time'], datetime):
            return False
        
        # Exit time should be after entry time if provided
        if (trade.get('exit_time') and 
            isinstance(trade['exit_time'], datetime) and
            trade['exit_time'] <= trade['entry_time']):
            return False
        
        return True
        
    except (ValueError, TypeError, AttributeError):
        return False


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change
    """
    if old_value == 0:
        return 100.0 if new_value > 0 else -100.0 if new_value < 0 else 0.0
    
    return ((new_value - old_value) / abs(old_value)) * 100


def moving_average(values: List[float], window: int) -> List[float]:
    """
    Calculate moving average of values
    
    Args:
        values: List of values
        window: Moving average window size
        
    Returns:
        List of moving averages
    """
    if len(values) < window:
        return []
    
    moving_averages = []
    for i in range(window - 1, len(values)):
        window_average = sum(values[i - window + 1:i + 1]) / window
        moving_averages.append(window_average)
    
    return moving_averages


def standard_deviation(values: List[float]) -> float:
    """
    Calculate standard deviation of values
    
    Args:
        values: List of values
        
    Returns:
        Standard deviation
    """
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


def percentile(values: List[float], percentile: float) -> float:
    """
    Calculate percentile of values
    
    Args:
        values: List of values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    index = (percentile / 100) * (len(sorted_values) - 1)
    
    if index.is_integer():
        return sorted_values[int(index)]
    else:
        lower_index = int(index)
        upper_index = lower_index + 1
        weight = index - lower_index
        
        return (sorted_values[lower_index] * (1 - weight) + 
                sorted_values[upper_index] * weight)


def remove_outliers(values: List[float], method: str = 'iqr') -> List[float]:
    """
    Remove outliers from values using specified method
    
    Args:
        values: List of values
        method: Outlier detection method ('iqr' or 'zscore')
        
    Returns:
        Values with outliers removed
    """
    if len(values) < 3:
        return values
    
    if method == 'iqr':
        q1 = percentile(values, 25)
        q3 = percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return [v for v in values if lower_bound <= v <= upper_bound]
    
    elif method == 'zscore':
        mean = sum(values) / len(values)
        std_dev = standard_deviation(values)
        
        if std_dev == 0:
            return values
        
        z_threshold = 3.0
        return [
            v for v in values 
            if abs((v - mean) / std_dev) <= z_threshold
        ]
    
    return values


def compound_growth_rate(initial_value: float, final_value: float, periods: int) -> float:
    """
    Calculate compound annual growth rate (CAGR)
    
    Args:
        initial_value: Starting value
        final_value: Ending value  
        periods: Number of periods
        
    Returns:
        Compound growth rate as percentage
    """
    if initial_value <= 0 or periods <= 0:
        return 0.0
    
    try:
        cagr = (pow(final_value / initial_value, 1.0 / periods) - 1) * 100
        return cagr
    except (ValueError, ZeroDivisionError):
        return 0.0


def is_trading_day(date: datetime) -> bool:
    """
    Check if date is a trading day (Monday-Friday)
    
    Args:
        date: Date to check
        
    Returns:
        True if trading day, False if weekend
    """
    return date.weekday() < 5  # Monday=0, Sunday=6


def next_trading_day(date: datetime) -> datetime:
    """
    Get next trading day after given date
    
    Args:
        date: Starting date
        
    Returns:
        Next trading day
    """
    next_day = date + timedelta(days=1)
    
    while not is_trading_day(next_day):
        next_day += timedelta(days=1)
    
    return next_day
