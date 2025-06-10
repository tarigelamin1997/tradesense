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
    if returns.empty:
        sharpe = 0
    else:
        std = returns.std()
        if std == 0 or np.isnan(std):
            sharpe = 0
        else:
            sharpe = np.sqrt(252) * returns.mean() / std

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


def median_results(df: pd.DataFrame) -> dict:
    """Return median PnL statistics."""
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    return {
        "median_pnl": df["pnl"].median() if not df.empty else 0,
        "median_win": wins["pnl"].median() if not wins.empty else 0,
        "median_loss": losses["pnl"].median() if not losses.empty else 0,
    }


def profit_factor_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate profit factor for each trading symbol."""
    if df.empty:
        return pd.DataFrame(columns=["symbol", "profit_factor"])

    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl", "symbol"])

    def _pf(group: pd.DataFrame) -> float:
        wins = group[group["pnl"] > 0]["pnl"].sum()
        losses = group[group["pnl"] <= 0]["pnl"].sum()
        return wins / abs(losses) if losses != 0 else np.inf

    result = (
        df.groupby("symbol")
        .apply(_pf)
        .reset_index(name="profit_factor")
        .sort_values("symbol")
    )
    return result


def trade_duration_stats(df: pd.DataFrame) -> dict:
    """Calculate statistics on trade durations in minutes."""
    if df.empty:
        return {"average_minutes": 0, "max_minutes": 0, "min_minutes": 0, "median_minutes": 0}

    df = df.copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
    df = df.dropna(subset=["entry_time", "exit_time"])
    durations = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 60
    return {
        "average_minutes": durations.mean() if not durations.empty else 0,
        "max_minutes": durations.max() if not durations.empty else 0,
        "min_minutes": durations.min() if not durations.empty else 0,
        "median_minutes": durations.median() if not durations.empty else 0,
    }


def max_streaks(df: pd.DataFrame) -> dict:
    """Return the longest consecutive win and loss streaks."""
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])

    max_win = 0
    max_loss = 0
    current_win = 0
    current_loss = 0
    for pnl in df["pnl"]:
        if pnl > 0:
            current_win += 1
            current_loss = 0
        else:
            current_loss += 1
            current_win = 0
        max_win = max(max_win, current_win)
        max_loss = max(max_loss, current_loss)

    return {"max_win_streak": max_win, "max_loss_streak": max_loss}


def rolling_metrics(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Compute rolling win rate and profit factor over a trade window."""
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])
    results = []
    for end in range(window, len(df) + 1):
        window_df = df.iloc[end - window : end]
        stats = compute_basic_stats(window_df)
        results.append(
            {
                "end_index": end - 1,
                "win_rate": stats["win_rate"],
                "profit_factor": stats["profit_factor"],
            }
        )
    return pd.DataFrame(results)


def calculate_kpis(df: pd.DataFrame, commission_per_trade: float = 3.5) -> dict:
    """Calculate key performance indicators including commission costs."""
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])
    
    if df.empty:
        return {
            "total_trades": 0,
            "win_rate_percent": 0,
            "average_rr": 0,
            "net_pnl_after_commission": 0,
            "max_single_trade_loss": 0,
            "max_single_trade_win": 0,
            "total_commission": 0
        }
    
    # Total number of trades
    total_trades = len(df)
    
    # Total commission
    total_commission = total_trades * commission_per_trade
    
    # Net PnL after commission
    gross_pnl = df["pnl"].sum()
    net_pnl_after_commission = gross_pnl - total_commission
    
    # Win rate %
    winning_trades = df[df["pnl"] > 0]
    losing_trades = df[df["pnl"] <= 0]
    win_rate_percent = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
    
    # Average RR (Reward to Risk ratio)
    avg_win = winning_trades["pnl"].mean() if not winning_trades.empty else 0
    avg_loss = abs(losing_trades["pnl"].mean()) if not losing_trades.empty else 0
    average_rr = avg_win / avg_loss if avg_loss != 0 else np.inf
    
    # Max single trade loss and win
    max_single_trade_loss = df["pnl"].min()
    max_single_trade_win = df["pnl"].max()
    
    return {
        "total_trades": total_trades,
        "win_rate_percent": win_rate_percent,
        "average_rr": average_rr,
        "net_pnl_after_commission": net_pnl_after_commission,
        "max_single_trade_loss": max_single_trade_loss,
        "max_single_trade_win": max_single_trade_win,
        "total_commission": total_commission,
        "gross_pnl": gross_pnl
    }
