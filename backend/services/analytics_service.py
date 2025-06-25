
"""
Advanced analytics service for trade performance analysis
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from backend.models.trade import Trade, TradeAnalytics
from backend.db.connection import db_manager
import logging
from functools import lru_cache
import redis
import json

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.cache_ttl = 300  # 5 minutes
    
    async def get_user_analytics(self, user_id: int, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive analytics for a user"""
        cache_key = f"analytics:{user_id}:{start_date}:{end_date}"
        
        # Try cache first
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        async with db_manager.get_connection() as conn:
            # Build query filters
            filters = [Trade.user_id == user_id, Trade.status == 'closed']
            if start_date:
                filters.append(Trade.entry_time >= start_date)
            if end_date:
                filters.append(Trade.entry_time <= end_date)
            
            # Get trades data
            trades_query = """
                SELECT * FROM trades 
                WHERE user_id = $1 AND status = 'closed'
                AND ($2::timestamp IS NULL OR entry_time >= $2)
                AND ($3::timestamp IS NULL OR entry_time <= $3)
                ORDER BY entry_time
            """
            
            trades = await conn.fetch(trades_query, user_id, start_date, end_date)
            
            if not trades:
                return {"error": "No trades found"}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([dict(trade) for trade in trades])
            
            # Calculate comprehensive analytics
            analytics = {
                "overview": self._calculate_overview(df),
                "performance_metrics": self._calculate_performance_metrics(df),
                "risk_metrics": self._calculate_risk_metrics(df),
                "behavioral_analysis": await self._calculate_behavioral_metrics(df, user_id),
                "time_analysis": self._calculate_time_analysis(df),
                "strategy_performance": self._calculate_strategy_performance(df),
                "monthly_performance": self._calculate_monthly_performance(df),
                "drawdown_analysis": self._calculate_drawdown_analysis(df)
            }
            
            # Cache results
            self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(analytics, default=str))
            
            return analytics
    
    def _calculate_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic overview metrics"""
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        total_pnl = df['pnl'].sum()
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": round(total_pnl, 2),
            "average_pnl_per_trade": round(total_pnl / total_trades, 2) if total_trades > 0 else 0,
            "best_trade": df['pnl'].max(),
            "worst_trade": df['pnl'].min(),
            "profit_factor": self._calculate_profit_factor(df)
        }
    
    def _calculate_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate advanced performance metrics"""
        returns = df['pnl'].values
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        if len(returns) > 1:
            excess_returns = returns - (0.02 / 252)  # Daily risk-free rate
            sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Sortino ratio
        negative_returns = returns[returns < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else 0
        sortino_ratio = np.mean(returns) / downside_deviation if downside_deviation > 0 else 0
        
        # Maximum consecutive wins/losses
        max_consecutive_wins = self._max_consecutive(df['pnl'] > 0)
        max_consecutive_losses = self._max_consecutive(df['pnl'] < 0)
        
        return {
            "sharpe_ratio": round(sharpe_ratio, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "average_win": round(df[df['pnl'] > 0]['pnl'].mean(), 2) if len(df[df['pnl'] > 0]) > 0 else 0,
            "average_loss": round(df[df['pnl'] < 0]['pnl'].mean(), 2) if len(df[df['pnl'] < 0]) > 0 else 0,
            "largest_win": df['pnl'].max(),
            "largest_loss": df['pnl'].min(),
            "expectancy": self._calculate_expectancy(df)
        }
    
    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate risk management metrics"""
        # Value at Risk (VaR) at 95% confidence
        var_95 = np.percentile(df['pnl'], 5)
        
        # Maximum drawdown
        cumulative_pnl = df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        return {
            "var_95": round(var_95, 2),
            "max_drawdown": round(max_drawdown, 2),
            "risk_of_ruin": self._calculate_risk_of_ruin(df),
            "kelly_criterion": self._calculate_kelly_criterion(df),
            "position_sizing_consistency": self._calculate_position_consistency(df)
        }
    
    async def _calculate_behavioral_metrics(self, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
        """Calculate behavioral trading patterns"""
        # This would integrate with your behavioral engine
        revenge_trades = 0
        overconfident_trades = 0
        
        # Detect revenge trading (quick trades after losses)
        for i in range(1, len(df)):
            prev_trade = df.iloc[i-1]
            current_trade = df.iloc[i]
            
            if prev_trade['pnl'] < 0:
                time_diff = (current_trade['entry_time'] - prev_trade['exit_time']).total_seconds() / 60
                if time_diff < 30:  # Within 30 minutes
                    revenge_trades += 1
        
        return {
            "revenge_trades": revenge_trades,
            "overconfident_trades": overconfident_trades,
            "emotional_control_score": max(0, 100 - (revenge_trades / len(df) * 100)),
            "discipline_score": self._calculate_discipline_score(df)
        }
    
    def _calculate_profit_factor(self, df: pd.DataFrame) -> float:
        """Calculate profit factor"""
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        return round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0
    
    def _calculate_expectancy(self, df: pd.DataFrame) -> float:
        """Calculate trade expectancy"""
        win_rate = len(df[df['pnl'] > 0]) / len(df)
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if len(df[df['pnl'] > 0]) > 0 else 0
        avg_loss = abs(df[df['pnl'] < 0]['pnl'].mean()) if len(df[df['pnl'] < 0]) > 0 else 0
        
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        return round(expectancy, 2)
    
    def _max_consecutive(self, condition_series) -> int:
        """Calculate maximum consecutive occurrences"""
        groups = (condition_series != condition_series.shift()).cumsum()
        return condition_series.groupby(groups).sum().max() if len(condition_series) > 0 else 0
    
    # Additional helper methods...
