import pandas as pd
import numpy as np


def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Calculate core trading performance statistics."""
    # Ensure PnL is numeric to avoid comparison errors
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    win_rate = len(wins) / len(df) * 100 if len(df) else 0
    avg_win = wins["pnl"].mean() if not wins.empty else 0
    avg_loss = losses["pnl"].mean() if not losses.empty else 0
    reward_risk = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
    expectancy = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss
    profit_factor = (
        wins["pnl"].sum() / abs(losses["pnl"].sum()) if not losses.empty else np.inf
    )
    equity_curve = df["pnl"].cumsum()
    max_drawdown = (equity_curve.cummax() - equity_curve).max()
    returns = equity_curve.pct_change().dropna()
    sharpe = np.sqrt(252) * returns.mean() / returns.std() if not returns.empty else 0

    return {
        "win_rate": win_rate,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "reward_risk": reward_risk,
        "expectancy": expectancy,
        "max_drawdown": max_drawdown,
        "profit_factor": profit_factor,
        "sharpe_ratio": sharpe,
        "equity_curve": equity_curve,
    }


def performance_over_time(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Return P&L and win rate aggregated by period."""
    if df.empty:
        return pd.DataFrame(columns=["period", "pnl", "win_rate"])

    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl", "exit_time"])

    period = df["exit_time"].dt.to_period(freq).dt.to_timestamp()
    grouped = df.groupby(period)
    pnl = grouped["pnl"].sum()
    win_rate = grouped.apply(lambda g: (g["pnl"] > 0).mean() * 100)

    result = pd.DataFrame({"period": pnl.index, "pnl": pnl.values, "win_rate": win_rate.values})
    return result


def histogram_data(df: pd.DataFrame, column: str, bins: int = 20) -> pd.DataFrame:
    """Return histogram counts for a numeric column."""
    if column not in df.columns or df.empty:
        return pd.DataFrame({"bin": [], "count": []})

    data = pd.to_numeric(df[column], errors="coerce").dropna()
    counts, edges = np.histogram(data, bins=bins)
    midpoints = (edges[:-1] + edges[1:]) / 2
    return pd.DataFrame({"bin": midpoints, "count": counts})


def heatmap_data(df: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    """Return a pivot table counting occurrences for heatmap display."""
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return pd.DataFrame()

    return pd.crosstab(df[y_col], df[x_col])
