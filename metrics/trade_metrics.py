
"""
Trade-level metrics calculation for individual trades.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TradeMetrics:
    """Container for individual trade metrics."""
    duration_minutes: float
    duration_hours: float
    profit_loss: float
    return_percentage: float
    commission_impact: float
    is_winner: bool
    gross_return: float
    net_return: float
    risk_reward_ratio: Optional[float] = None
    mae: Optional[float] = None  # Maximum Adverse Excursion
    mfe: Optional[float] = None  # Maximum Favorable Excursion


def calculate_trade_metrics(trade: Dict[str, Any], estimated_commission: float = 2.0) -> TradeMetrics:
    """
    Calculate comprehensive metrics for a single trade.
    
    Args:
        trade: Dictionary containing trade data
        estimated_commission: Estimated commission per trade if not provided
    
    Returns:
        TradeMetrics object with calculated metrics
    """
    
    # Parse times
    entry_time = pd.to_datetime(trade['entry_time'])
    exit_time = pd.to_datetime(trade['exit_time'])
    
    # Calculate duration
    duration = exit_time - entry_time
    duration_minutes = duration.total_seconds() / 60
    duration_hours = duration_minutes / 60
    
    # Get basic trade data
    entry_price = float(trade['entry_price'])
    exit_price = float(trade['exit_price'])
    quantity = float(trade['qty'])
    direction = trade['direction'].lower()
    
    # Calculate P&L
    if direction == 'long':
        price_diff = exit_price - entry_price
    else:  # short
        price_diff = entry_price - exit_price
    
    gross_pnl = price_diff * quantity
    
    # Commission handling
    commission = trade.get('commission', estimated_commission)
    if commission is None:
        commission = estimated_commission
    
    net_pnl = gross_pnl - commission
    
    # Calculate returns
    capital_at_risk = entry_price * quantity
    gross_return = (gross_pnl / capital_at_risk) * 100 if capital_at_risk > 0 else 0
    net_return = (net_pnl / capital_at_risk) * 100 if capital_at_risk > 0 else 0
    
    # Commission impact
    commission_impact = (commission / capital_at_risk) * 100 if capital_at_risk > 0 else 0
    
    # Win/Loss determination
    is_winner = net_pnl > 0
    
    # Risk-reward ratio (if stop loss and take profit are available)
    risk_reward_ratio = None
    if trade.get('stop_loss') and trade.get('take_profit'):
        stop_loss = float(trade['stop_loss'])
        take_profit = float(trade['take_profit'])
        
        if direction == 'long':
            risk = entry_price - stop_loss
            reward = take_profit - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - take_profit
        
        if risk > 0:
            risk_reward_ratio = reward / risk
    
    return TradeMetrics(
        duration_minutes=duration_minutes,
        duration_hours=duration_hours,
        profit_loss=net_pnl,
        return_percentage=net_return,
        commission_impact=commission_impact,
        is_winner=is_winner,
        gross_return=gross_return,
        net_return=net_return,
        risk_reward_ratio=risk_reward_ratio
    )


def calculate_batch_trade_metrics(df: pd.DataFrame, estimated_commission: float = 2.0) -> pd.DataFrame:
    """
    Calculate metrics for all trades in a DataFrame.
    
    Args:
        df: DataFrame with trade data
        estimated_commission: Default commission if not provided
    
    Returns:
        DataFrame with additional metric columns
    """
    metrics_list = []
    
    for _, trade in df.iterrows():
        try:
            metrics = calculate_trade_metrics(trade.to_dict(), estimated_commission)
            metrics_dict = {
                'duration_minutes': metrics.duration_minutes,
                'duration_hours': metrics.duration_hours,
                'return_percentage': metrics.return_percentage,
                'commission_impact': metrics.commission_impact,
                'is_winner': metrics.is_winner,
                'gross_return': metrics.gross_return,
                'net_return': metrics.net_return,
                'risk_reward_ratio': metrics.risk_reward_ratio
            }
            metrics_list.append(metrics_dict)
        except Exception as e:
            # Handle invalid trades
            metrics_list.append({
                'duration_minutes': np.nan,
                'duration_hours': np.nan,
                'return_percentage': np.nan,
                'commission_impact': np.nan,
                'is_winner': False,
                'gross_return': np.nan,
                'net_return': np.nan,
                'risk_reward_ratio': np.nan
            })
    
    metrics_df = pd.DataFrame(metrics_list)
    return pd.concat([df, metrics_df], axis=1)


def analyze_trade_tags(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze performance by trade tags and execution type.
    
    Args:
        df: DataFrame with trade data and metrics
    
    Returns:
        Dictionary with tag-based analysis
    """
    analysis = {}
    
    # Execution type analysis
    if 'execution_type' in df.columns:
        exec_analysis = df.groupby('execution_type').agg({
            'is_winner': ['count', 'sum', 'mean'],
            'return_percentage': 'mean',
            'pnl': 'sum'
        }).round(2)
        analysis['execution_type'] = exec_analysis
    
    # Strategy tag analysis
    if 'strategy_tag' in df.columns and df['strategy_tag'].notna().any():
        strategy_analysis = df.groupby('strategy_tag').agg({
            'is_winner': ['count', 'sum', 'mean'],
            'return_percentage': 'mean',
            'pnl': 'sum'
        }).round(2)
        analysis['strategy_tag'] = strategy_analysis
    
    # Confidence score analysis
    if 'confidence_score' in df.columns and df['confidence_score'].notna().any():
        confidence_analysis = df.groupby('confidence_score').agg({
            'is_winner': ['count', 'sum', 'mean'],
            'return_percentage': 'mean',
            'pnl': 'sum'
        }).round(2)
        analysis['confidence_score'] = confidence_analysis
    
    return analysis
