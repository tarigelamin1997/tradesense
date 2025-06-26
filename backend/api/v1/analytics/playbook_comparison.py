
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.api.deps import get_current_user, get_db
from backend.models.user import User
from backend.models.trade import Trade
from backend.models.playbook import Playbook
from sqlalchemy import func, and_

router = APIRouter()

class PlaybookComparisonRequest(BaseModel):
    playbook_ids: List[str]

class PlaybookMetrics(BaseModel):
    playbook_id: str
    playbook_name: str
    total_trades: int
    win_rate: float
    avg_return: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    expectancy: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float

class PlaybookComparisonResponse(BaseModel):
    playbooks: List[PlaybookMetrics]
    comparison_matrix: List[Dict[str, Any]]

@router.post("/playbook-comparison", response_model=PlaybookComparisonResponse)
async def compare_playbooks(
    request: PlaybookComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare multiple playbooks side by side"""
    
    if len(request.playbook_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 playbooks required for comparison")
    
    # Verify all playbooks belong to the user
    playbooks = db.query(Playbook).filter(
        and_(
            Playbook.id.in_(request.playbook_ids),
            Playbook.user_id == current_user.id
        )
    ).all()
    
    if len(playbooks) != len(request.playbook_ids):
        raise HTTPException(status_code=404, detail="One or more playbooks not found")
    
    playbook_metrics = []
    
    for playbook in playbooks:
        # Get trades for this playbook
        trades = db.query(Trade).filter(
            and_(
                Trade.user_id == current_user.id,
                Trade.playbook_id == playbook.id
            )
        ).all()
        
        if not trades:
            # Include playbook with zero metrics
            playbook_metrics.append(PlaybookMetrics(
                playbook_id=playbook.id,
                playbook_name=playbook.name,
                total_trades=0,
                win_rate=0.0,
                avg_return=0.0,
                total_pnl=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                profit_factor=0.0,
                expectancy=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                largest_win=0.0,
                largest_loss=0.0
            ))
            continue
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        total_pnl = sum(t.pnl for t in trades)
        avg_return = total_pnl / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Expectancy
        avg_win = gross_profit / len(winning_trades) if winning_trades else 0
        avg_loss = gross_loss / len(losing_trades) if losing_trades else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Simple Sharpe ratio approximation (using daily returns)
        returns = [t.pnl for t in trades]
        if len(returns) > 1:
            import statistics
            avg_return_period = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            sharpe_ratio = avg_return_period / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown calculation
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades, key=lambda x: x.entry_time):
            cumulative_pnl += trade.pnl
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            else:
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        # Largest win/loss
        largest_win = max([t.pnl for t in trades]) if trades else 0
        largest_loss = min([t.pnl for t in trades]) if trades else 0
        
        playbook_metrics.append(PlaybookMetrics(
            playbook_id=playbook.id,
            playbook_name=playbook.name,
            total_trades=total_trades,
            win_rate=win_rate,
            avg_return=avg_return,
            total_pnl=total_pnl,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            expectancy=expectancy,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss
        ))
    
    # Create comparison matrix
    metrics_to_compare = [
        'total_trades', 'win_rate', 'avg_return', 'total_pnl', 
        'sharpe_ratio', 'profit_factor', 'expectancy'
    ]
    
    comparison_matrix = []
    for metric in metrics_to_compare:
        values = {}
        for pm in playbook_metrics:
            values[pm.playbook_name] = getattr(pm, metric)
        
        comparison_matrix.append({
            'metric': metric,
            'values': values
        })
    
    return PlaybookComparisonResponse(
        playbooks=playbook_metrics,
        comparison_matrix=comparison_matrix
    )
