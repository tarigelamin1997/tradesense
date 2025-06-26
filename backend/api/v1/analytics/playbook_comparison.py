
"""
Playbook Comparison Analytics API
Provides comprehensive comparison metrics between different playbooks
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pandas as pd

from backend.core.db.session import get_db
from backend.models.trade import Trade
from backend.models.playbook import Playbook
from backend.analytics.performance import (
    calculate_win_rate, calculate_profit_factor, 
    calculate_expectancy, calculate_sharpe_ratio
)
from backend.analytics.streaks import calculate_win_loss_streaks
from backend.analytics.equity import calculate_max_drawdown

router = APIRouter()

@router.get("/compare")
async def compare_playbooks(
    playbook_ids: List[str] = Query(..., description="List of playbook IDs to compare"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: str = Depends(lambda: "demo_user"),
    db: Session = Depends(get_db)
):
    """Compare multiple playbooks across key performance metrics."""
    
    try:
        # Validate playbooks exist
        playbooks = db.query(Playbook).filter(
            and_(
                Playbook.id.in_(playbook_ids),
                Playbook.user_id == user_id
            )
        ).all()
        
        if len(playbooks) != len(playbook_ids):
            raise HTTPException(status_code=404, detail="One or more playbooks not found")
        
        comparison_data = []
        
        for playbook in playbooks:
            # Get trades for this playbook
            query = db.query(Trade).filter(
                and_(
                    Trade.user_id == user_id,
                    Trade.playbook_id == playbook.id
                )
            )
            
            if start_date:
                query = query.filter(Trade.entry_time >= start_date)
            if end_date:
                query = query.filter(Trade.entry_time <= end_date)
                
            trades = query.all()
            
            if not trades:
                comparison_data.append({
                    "playbook_id": playbook.id,
                    "playbook_name": playbook.name,
                    "total_trades": 0,
                    "win_rate": 0,
                    "profit_factor": 0,
                    "expectancy": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0,
                    "total_pnl": 0,
                    "avg_win": 0,
                    "avg_loss": 0,
                    "max_consecutive_wins": 0,
                    "max_consecutive_losses": 0,
                    "monthly_performance": []
                })
                continue
            
            # Calculate metrics
            pnls = [t.pnl for t in trades]
            win_rate = calculate_win_rate(trades)
            profit_factor = calculate_profit_factor(trades)
            expectancy = calculate_expectancy(trades)
            
            # Calculate streak data
            streak_data = calculate_win_loss_streaks(trades)
            
            # Calculate drawdown
            max_dd = calculate_max_drawdown(trades)
            
            # Calculate additional metrics
            winning_trades = [t.pnl for t in trades if t.pnl > 0]
            losing_trades = [t.pnl for t in trades if t.pnl < 0]
            
            avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0
            
            # Monthly performance breakdown
            trades_df = pd.DataFrame([{
                'entry_time': t.entry_time,
                'pnl': t.pnl
            } for t in trades])
            
            monthly_perf = []
            if not trades_df.empty:
                trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
                trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
                monthly_data = trades_df.groupby('month').agg({
                    'pnl': ['sum', 'count']
                }).round(2)
                
                for month, data in monthly_data.iterrows():
                    monthly_perf.append({
                        'month': str(month),
                        'pnl': float(data[('pnl', 'sum')]),
                        'trades': int(data[('pnl', 'count')])
                    })
            
            comparison_data.append({
                "playbook_id": playbook.id,
                "playbook_name": playbook.name,
                "description": playbook.description,
                "total_trades": len(trades),
                "win_rate": round(win_rate, 2),
                "profit_factor": round(profit_factor, 2),
                "expectancy": round(expectancy, 2),
                "sharpe_ratio": round(calculate_sharpe_ratio(trades), 2),
                "max_drawdown": round(max_dd, 2),
                "total_pnl": round(sum(pnls), 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "max_consecutive_wins": streak_data.get('max_consecutive_wins', 0),
                "max_consecutive_losses": streak_data.get('max_consecutive_losses', 0),
                "monthly_performance": monthly_perf,
                "risk_adjusted_return": round((sum(pnls) / max(abs(max_dd), 1)) if max_dd != 0 else sum(pnls), 2)
            })
        
        # Calculate relative rankings
        if len(comparison_data) > 1:
            metrics_to_rank = ['win_rate', 'profit_factor', 'expectancy', 'sharpe_ratio', 'total_pnl']
            
            for metric in metrics_to_rank:
                sorted_data = sorted(comparison_data, key=lambda x: x[metric], reverse=True)
                for i, item in enumerate(sorted_data):
                    # Find the item in original list and add rank
                    for original_item in comparison_data:
                        if original_item['playbook_id'] == item['playbook_id']:
                            original_item[f'{metric}_rank'] = i + 1
                            break
        
        return {
            "comparison_data": comparison_data,
            "summary": {
                "total_playbooks": len(comparison_data),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "best_performer": max(comparison_data, key=lambda x: x['total_pnl'])['playbook_name'] if comparison_data else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing playbooks: {str(e)}")

@router.get("/correlation-matrix")
async def get_playbook_correlation_matrix(
    playbook_ids: List[str] = Query(...),
    user_id: str = Depends(lambda: "demo_user"),
    db: Session = Depends(get_db)
):
    """Calculate correlation matrix between playbook performances."""
    
    try:
        correlation_data = {}
        
        for playbook_id in playbook_ids:
            trades = db.query(Trade).filter(
                and_(
                    Trade.user_id == user_id,
                    Trade.playbook_id == playbook_id
                )
            ).order_by(Trade.entry_time).all()
            
            if trades:
                # Create daily PnL series
                trades_df = pd.DataFrame([{
                    'date': t.entry_time.date(),
                    'pnl': t.pnl
                } for t in trades])
                
                daily_pnl = trades_df.groupby('date')['pnl'].sum()
                correlation_data[playbook_id] = daily_pnl
        
        if len(correlation_data) < 2:
            return {"correlation_matrix": {}, "message": "Need at least 2 playbooks with trades"}
        
        # Create correlation matrix
        df = pd.DataFrame(correlation_data).fillna(0)
        correlation_matrix = df.corr().round(3)
        
        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "playbook_ids": list(correlation_data.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating correlation: {str(e)}")

@router.get("/performance-over-time")
async def get_performance_over_time(
    playbook_ids: List[str] = Query(...),
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    user_id: str = Depends(lambda: "demo_user"),
    db: Session = Depends(get_db)
):
    """Get performance trends over time for multiple playbooks."""
    
    try:
        performance_data = {}
        
        for playbook_id in playbook_ids:
            playbook = db.query(Playbook).filter(
                and_(Playbook.id == playbook_id, Playbook.user_id == user_id)
            ).first()
            
            if not playbook:
                continue
                
            trades = db.query(Trade).filter(
                and_(
                    Trade.user_id == user_id,
                    Trade.playbook_id == playbook_id
                )
            ).order_by(Trade.entry_time).all()
            
            if not trades:
                continue
            
            trades_df = pd.DataFrame([{
                'entry_time': t.entry_time,
                'pnl': t.pnl
            } for t in trades])
            
            trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
            
            # Group by period
            if period == "daily":
                trades_df['period'] = trades_df['entry_time'].dt.date
            elif period == "weekly":
                trades_df['period'] = trades_df['entry_time'].dt.to_period('W')
            else:  # monthly
                trades_df['period'] = trades_df['entry_time'].dt.to_period('M')
            
            period_data = trades_df.groupby('period').agg({
                'pnl': ['sum', 'count', 'mean']
            }).round(2)
            
            period_performance = []
            cumulative_pnl = 0
            
            for period_key, data in period_data.iterrows():
                period_pnl = float(data[('pnl', 'sum')])
                cumulative_pnl += period_pnl
                
                period_performance.append({
                    'period': str(period_key),
                    'pnl': period_pnl,
                    'cumulative_pnl': round(cumulative_pnl, 2),
                    'trade_count': int(data[('pnl', 'count')]),
                    'avg_pnl': float(data[('pnl', 'mean')])
                })
            
            performance_data[playbook_id] = {
                'playbook_name': playbook.name,
                'performance': period_performance
            }
        
        return {
            "performance_data": performance_data,
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance over time: {str(e)}")
