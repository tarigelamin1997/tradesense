
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from backend.models.trade import Trade
from backend.models.playbook import Playbook
from backend.db.connection import get_db_connection
from backend.core.security import get_current_user

router = APIRouter()

class PlaybookComparisonRequest(BaseModel):
    playbooks: List[str]

class PlaybookMetrics(BaseModel):
    playbook_name: str
    total_trades: int
    win_rate: float
    profit_factor: float
    average_return: float
    max_drawdown: float
    sharpe_ratio: float
    total_pnl: float
    avg_trade_duration: float
    largest_win: float
    largest_loss: float
    consecutive_wins: int
    consecutive_losses: int

class MonthlyReturn(BaseModel):
    month: str
    return_: float = 0.0

class PerformanceComparison(BaseModel):
    playbook_name: str
    monthly_returns: List[MonthlyReturn]

class RiskAnalysis(BaseModel):
    playbook_name: str
    var_95: float
    var_99: float
    expected_shortfall: float
    volatility: float

class ComparisonResponse(BaseModel):
    metrics: List[PlaybookMetrics]
    performance_comparison: List[PerformanceComparison]
    risk_analysis: List[RiskAnalysis]

def calculate_playbook_metrics(trades_df: pd.DataFrame, playbook_name: str) -> PlaybookMetrics:
    """Calculate comprehensive metrics for a playbook."""
    if trades_df.empty:
        return PlaybookMetrics(
            playbook_name=playbook_name,
            total_trades=0,
            win_rate=0.0,
            profit_factor=0.0,
            average_return=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            total_pnl=0.0,
            avg_trade_duration=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            consecutive_wins=0,
            consecutive_losses=0
        )
    
    # Basic metrics
    total_trades = len(trades_df)
    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] < 0]
    
    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    average_return = trades_df['pnl'].mean()
    
    # Profit factor
    gross_profits = winning_trades['pnl'].sum() if not winning_trades.empty else 0
    gross_losses = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 1
    profit_factor = gross_profits / gross_losses if gross_losses > 0 else 0
    
    # Drawdown calculation
    cumulative_pnl = trades_df['pnl'].cumsum()
    running_max = cumulative_pnl.expanding().max()
    drawdown = (cumulative_pnl - running_max) / running_max.abs()
    max_drawdown = drawdown.min() if not drawdown.empty else 0
    
    # Sharpe ratio (assuming daily returns)
    if len(trades_df) > 1:
        returns = trades_df['pnl'] / trades_df['pnl'].abs().mean()  # Normalized returns
        sharpe_ratio = returns.mean() / returns.std() if returns.std() > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Trade duration
    if 'entry_time' in trades_df.columns and 'exit_time' in trades_df.columns:
        trades_df['duration'] = pd.to_datetime(trades_df['exit_time']) - pd.to_datetime(trades_df['entry_time'])
        avg_trade_duration = trades_df['duration'].dt.total_seconds().mean() / 3600  # hours
    else:
        avg_trade_duration = 0
    
    # Largest win/loss
    largest_win = trades_df['pnl'].max() if not trades_df.empty else 0
    largest_loss = trades_df['pnl'].min() if not trades_df.empty else 0
    
    # Consecutive wins/losses
    trades_df['is_win'] = trades_df['pnl'] > 0
    consecutive_wins = 0
    consecutive_losses = 0
    current_wins = 0
    current_losses = 0
    
    for is_win in trades_df['is_win']:
        if is_win:
            current_wins += 1
            current_losses = 0
            consecutive_wins = max(consecutive_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            consecutive_losses = max(consecutive_losses, current_losses)
    
    return PlaybookMetrics(
        playbook_name=playbook_name,
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        average_return=average_return,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe_ratio,
        total_pnl=total_pnl,
        avg_trade_duration=avg_trade_duration,
        largest_win=largest_win,
        largest_loss=largest_loss,
        consecutive_wins=consecutive_wins,
        consecutive_losses=consecutive_losses
    )

def calculate_monthly_returns(trades_df: pd.DataFrame) -> List[MonthlyReturn]:
    """Calculate monthly returns for performance comparison."""
    if trades_df.empty or 'exit_time' not in trades_df.columns:
        return []
    
    trades_df['exit_date'] = pd.to_datetime(trades_df['exit_time'])
    trades_df['year_month'] = trades_df['exit_date'].dt.to_period('M')
    
    monthly_pnl = trades_df.groupby('year_month')['pnl'].sum()
    
    # Convert to percentage returns (assuming starting capital)
    starting_capital = 100000  # Default assumption
    monthly_returns = []
    
    for period, pnl in monthly_pnl.items():
        return_pct = (pnl / starting_capital) * 100
        monthly_returns.append(MonthlyReturn(
            month=str(period),
            return_=return_pct
        ))
    
    return monthly_returns

def calculate_risk_metrics(trades_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate risk metrics for the playbook."""
    if trades_df.empty:
        return {
            'var_95': 0.0,
            'var_99': 0.0,
            'expected_shortfall': 0.0,
            'volatility': 0.0
        }
    
    returns = trades_df['pnl'] / trades_df['pnl'].abs().mean()  # Normalized returns
    
    # Value at Risk
    var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
    var_99 = np.percentile(returns, 1) if len(returns) > 0 else 0
    
    # Expected Shortfall (Conditional VaR)
    below_var_95 = returns[returns <= var_95]
    expected_shortfall = below_var_95.mean() if len(below_var_95) > 0 else 0
    
    # Volatility
    volatility = returns.std() if len(returns) > 1 else 0
    
    return {
        'var_95': float(var_95),
        'var_99': float(var_99),
        'expected_shortfall': float(expected_shortfall),
        'volatility': float(volatility)
    }

@router.get("/available")
async def get_available_playbooks(current_user: dict = Depends(get_current_user)):
    """Get list of available playbooks for comparison."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get playbooks that have associated trades
            cursor.execute("""
                SELECT DISTINCT p.name
                FROM playbooks p
                JOIN trades t ON t.playbook_id = p.id
                WHERE t.user_id = ?
                ORDER BY p.name
            """, (current_user['user_id'],))
            
            playbooks = [row[0] for row in cursor.fetchall()]
            return {"playbooks": playbooks}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch playbooks: {str(e)}")

@router.post("/compare", response_model=ComparisonResponse)
async def compare_playbooks(
    request: PlaybookComparisonRequest,
    current_user: dict = Depends(get_current_user)
):
    """Compare multiple playbooks with comprehensive analytics."""
    try:
        if len(request.playbooks) < 2:
            raise HTTPException(status_code=400, detail="At least 2 playbooks required for comparison")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            metrics = []
            performance_comparison = []
            risk_analysis = []
            
            for playbook_name in request.playbooks:
                # Get trades for this playbook
                cursor.execute("""
                    SELECT t.* FROM trades t
                    JOIN playbooks p ON t.playbook_id = p.id
                    WHERE p.name = ? AND t.user_id = ?
                    ORDER BY t.exit_time
                """, (playbook_name, current_user['user_id']))
                
                rows = cursor.fetchall()
                if not rows:
                    continue
                
                # Convert to DataFrame
                columns = [description[0] for description in cursor.description]
                trades_df = pd.DataFrame(rows, columns=columns)
                
                # Calculate metrics
                playbook_metrics = calculate_playbook_metrics(trades_df, playbook_name)
                metrics.append(playbook_metrics)
                
                # Calculate monthly returns
                monthly_returns = calculate_monthly_returns(trades_df)
                performance_comparison.append(PerformanceComparison(
                    playbook_name=playbook_name,
                    monthly_returns=monthly_returns
                ))
                
                # Calculate risk metrics
                risk_metrics = calculate_risk_metrics(trades_df)
                risk_analysis.append(RiskAnalysis(
                    playbook_name=playbook_name,
                    **risk_metrics
                ))
            
            return ComparisonResponse(
                metrics=metrics,
                performance_comparison=performance_comparison,
                risk_analysis=risk_analysis
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare playbooks: {str(e)}")

@router.get("/{playbook_name}/optimization")
async def get_playbook_optimization(
    playbook_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get optimization recommendations for a specific playbook."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get trades for analysis
            cursor.execute("""
                SELECT t.* FROM trades t
                JOIN playbooks p ON t.playbook_id = p.id
                WHERE p.name = ? AND t.user_id = ?
            """, (playbook_name, current_user['user_id']))
            
            rows = cursor.fetchall()
            if not rows:
                raise HTTPException(status_code=404, detail="Playbook not found or no trades")
            
            columns = [description[0] for description in cursor.description]
            trades_df = pd.DataFrame(rows, columns=columns)
            
            # Calculate current metrics
            current_metrics = calculate_playbook_metrics(trades_df, playbook_name)
            
            # Generate recommendations (simplified analysis)
            recommendations = []
            
            # Win rate analysis
            if current_metrics.win_rate < 0.6:
                recommendations.append({
                    "type": "entry_timing",
                    "description": "Consider improving entry timing signals to increase win rate",
                    "potential_improvement": 0.15,
                    "confidence": 0.75
                })
            
            # Profit factor analysis
            if current_metrics.profit_factor < 1.5:
                recommendations.append({
                    "type": "exit_strategy",
                    "description": "Optimize exit strategy to improve profit factor",
                    "potential_improvement": 0.25,
                    "confidence": 0.80
                })
            
            # Drawdown analysis
            if abs(current_metrics.max_drawdown) > 0.15:
                recommendations.append({
                    "type": "risk_management",
                    "description": "Implement stricter risk management to reduce drawdown",
                    "potential_improvement": 0.30,
                    "confidence": 0.85
                })
            
            return {
                "playbook_name": playbook_name,
                "current_metrics": current_metrics,
                "recommendations": recommendations,
                "suggested_parameters": [
                    {
                        "parameter": "position_size",
                        "current_value": "Fixed",
                        "suggested_value": "Risk-based (2% per trade)",
                        "reasoning": "Improve risk-adjusted returns"
                    }
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization: {str(e)}")
