
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from backend.api.deps import get_db, get_current_user
from backend.models.trade import Trade
from backend.models.playbook import Playbook
from backend.analytics.performance import (
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
    calculate_sharpe_ratio
)
from backend.analytics.equity import calculate_max_drawdown


async def get_playbook_metrics(
    playbook_name: str,
    time_range: str = "6M",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive metrics for a specific playbook"""
    
    # Calculate date range
    end_date = datetime.now()
    if time_range == "1M":
        start_date = end_date - timedelta(days=30)
    elif time_range == "3M":
        start_date = end_date - timedelta(days=90)
    elif time_range == "6M":
        start_date = end_date - timedelta(days=180)
    elif time_range == "1Y":
        start_date = end_date - timedelta(days=365)
    else:  # ALL
        start_date = datetime(2020, 1, 1)
    
    # Get trades for this playbook
    trades_query = db.query(Trade).filter(
        and_(
            Trade.user_id == current_user["sub"],
            Trade.playbook_name == playbook_name,
            Trade.entry_time >= start_date,
            Trade.entry_time <= end_date,
            Trade.exit_time.isnot(None)  # Only completed trades
        )
    )
    
    trades = trades_query.all()
    
    if not trades:
        raise HTTPException(status_code=404, detail="No trades found for this playbook")
    
    # Convert trades to list of dicts for analytics functions
    trade_data = []
    for trade in trades:
        pnl = (trade.exit_price - trade.entry_price) * trade.quantity
        if trade.side.lower() == 'short':
            pnl = -pnl
            
        trade_data.append({
            'pnl': pnl,
            'entry_time': trade.entry_time,
            'exit_time': trade.exit_time,
            'quantity': trade.quantity,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price
        })
    
    # Calculate metrics
    total_trades = len(trade_data)
    win_rate = calculate_win_rate(trade_data)
    profit_factor = calculate_profit_factor(trade_data)
    expectancy = calculate_expectancy(trade_data)
    
    # Calculate P&L metrics
    total_pnl = sum(t['pnl'] for t in trade_data)
    winning_trades = [t for t in trade_data if t['pnl'] > 0]
    losing_trades = [t for t in trade_data if t['pnl'] < 0]
    
    avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
    
    # Calculate equity curve for drawdown and Sharpe
    equity_curve = []
    running_balance = 0
    
    sorted_trades = sorted(trade_data, key=lambda x: x['exit_time'])
    for trade in sorted_trades:
        running_balance += trade['pnl']
        equity_curve.append({
            'date': trade['exit_time'].strftime('%Y-%m-%d'),
            'value': running_balance
        })
    
    max_drawdown = calculate_max_drawdown(equity_curve) if equity_curve else 0
    
    # Calculate Sharpe ratio (simplified)
    if equity_curve and len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1]['value'] != 0:
                daily_return = (equity_curve[i]['value'] - equity_curve[i-1]['value']) / abs(equity_curve[i-1]['value'])
                returns.append(daily_return)
        
        sharpe_ratio = calculate_sharpe_ratio(returns) if returns else 0
    else:
        sharpe_ratio = 0
    
    # Calculate monthly returns for consistency analysis
    monthly_returns = []
    monthly_pnl = {}
    
    for trade in sorted_trades:
        month_key = trade['exit_time'].strftime('%Y-%m')
        if month_key not in monthly_pnl:
            monthly_pnl[month_key] = 0
        monthly_pnl[month_key] += trade['pnl']
    
    monthly_returns = list(monthly_pnl.values())
    
    return {
        'totalTrades': total_trades,
        'winRate': win_rate,
        'profitFactor': profit_factor,
        'expectancy': expectancy,
        'maxDrawdown': max_drawdown,
        'sharpeRatio': sharpe_ratio,
        'avgWin': avg_win,
        'avgLoss': avg_loss,
        'totalPnL': total_pnl,
        'monthlyReturns': monthly_returns,
        'equityCurve': equity_curve
    }
