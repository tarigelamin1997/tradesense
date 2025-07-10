
"""
TradeSense Analytics Module

Centralized analytics calculations for trading metrics, equity curves, 
performance analysis, and behavioral insights.

This module provides reusable, composable functions for calculating
trading analytics that can be used across different consumers:
- REST API endpoints
- Dashboard components  
- Report generators
- PDF exports
- Mobile APIs

All functions are pure and stateless for easy testing and scaling.
"""

from .performance import (
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
    calculate_risk_reward_metrics,
    calculate_sharpe_ratio
)

from .equity import (
    generate_equity_curve,
    calculate_drawdown,
    calculate_max_drawdown,
    calculate_rolling_returns
)

from .streaks import (
    calculate_win_loss_streaks,
    calculate_max_consecutive_wins,
    calculate_max_consecutive_losses,
    analyze_streak_patterns,
    calculate_average_duration
)

from .filters import (
    apply_trade_filters,
    filter_by_date_range,
    filter_by_symbol,
    filter_by_strategy,
    filter_by_tags
)

from .utils import (
    safe_divide,
    round_percentage,
    format_currency,
    calculate_trade_duration,
    validate_trade_data
)

__all__ = [
    # Performance metrics
    'calculate_win_rate',
    'calculate_profit_factor', 
    'calculate_expectancy',
    'calculate_risk_reward_metrics',
    'calculate_sharpe_ratio',
    
    # Equity and drawdown
    'generate_equity_curve',
    'calculate_drawdown',
    'calculate_max_drawdown',
    'calculate_rolling_returns',
    
    # Streak analysis
    'calculate_win_loss_streaks',
    'calculate_max_consecutive_wins',
    'calculate_max_consecutive_losses',
    'analyze_streak_patterns',
    
    # Filtering
    'apply_trade_filters',
    'filter_by_date_range',
    'filter_by_symbol',
    'filter_by_strategy',
    'filter_by_tags',
    
    # Utilities
    'safe_divide',
    'round_percentage',
    'format_currency',
    'calculate_trade_duration',
    'validate_trade_data'
]
