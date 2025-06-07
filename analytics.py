import pandas as pd
import numpy as np


def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Calculate core trading performance statistics."""
    wins = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    win_rate = len(wins) / len(df) * 100 if len(df) else 0
    avg_win = wins['pnl'].mean() if not wins.empty else 0
    avg_loss = losses['pnl'].mean() if not losses.empty else 0
    reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
    expectancy = (win_rate/100) * avg_win + (1 - win_rate/100) * avg_loss
    profit_factor = wins['pnl'].sum() / abs(losses['pnl'].sum()) if not losses.empty else np.inf
    equity_curve = df['pnl'].cumsum()
    max_drawdown = (equity_curve.cummax() - equity_curve).max()
    returns = equity_curve.pct_change().dropna()
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if not returns.empty else 0

    return {
        'win_rate': win_rate,
        'average_win': avg_win,
        'average_loss': avg_loss,
        'reward_risk': reward_risk,
        'expectancy': expectancy,
        'max_drawdown': max_drawdown,
        'profit_factor': profit_factor,
        'sharpe_ratio': sharpe,
        'equity_curve': equity_curve,
    }
