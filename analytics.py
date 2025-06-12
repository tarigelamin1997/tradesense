import pandas as pd
import numpy as np


def compute_basic_stats(df: pd.DataFrame) -> dict:
    """Compute basic trading statistics."""
    if df.empty:
        # Create a proper equity curve with timestamps to prevent infinite extent warnings
        default_dates = pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D')
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "reward_risk": 0.0,
            "equity_curve": pd.Series([0.0, 0.0], index=default_dates)
        }

    df = df.copy()
    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
    df = df.dropna(subset=['pnl'])

    if df.empty:
        # Create a proper equity curve with timestamps to prevent infinite extent warnings
        default_dates = pd.date_range(start=pd.Timestamp.now(), periods=2, freq='D')
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "reward_risk": 0.0,
            "equity_curve": pd.Series([0.0, 0.0], index=default_dates)
        }

    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]
    win_rate = len(wins) / len(df) * 100 if len(df) else 0.0

    # Handle edge cases with safe numeric operations - ensure no infinite values
    avg_win = float(wins["pnl"].mean()) if not wins.empty and not wins["pnl"].isna().all() else 0.0
    avg_loss = float(losses["pnl"].mean()) if not losses.empty and not losses["pnl"].isna().all() else 0.0

    # Prevent infinite reward_risk
    if avg_loss != 0 and not np.isnan(avg_loss) and not np.isnan(avg_win):
        reward_risk = abs(avg_win / avg_loss)
        reward_risk = min(reward_risk, 999.99)  # Cap at reasonable max
    else:
        reward_risk = 0.0

    expectancy = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss
    expectancy = expectancy if not np.isnan(expectancy) else 0.0

    wins_sum = float(wins["pnl"].sum()) if not wins.empty else 0.0
    losses_sum = float(abs(losses["pnl"].sum())) if not losses.empty else 0.0

    # Prevent infinite profit_factor
    if losses_sum != 0:
        profit_factor = wins_sum / losses_sum
        profit_factor = min(profit_factor, 999.99)  # Cap at reasonable max
    else:
        profit_factor = 0.0 if wins_sum == 0 else 999.99

    # Create equity curve with proper datetime index
    if 'exit_time' in df.columns:
        df_sorted = df.sort_values('exit_time')
        equity_curve = df_sorted['pnl'].cumsum()
        equity_curve.index = pd.to_datetime(df_sorted['exit_time'])
    else:
        # Fallback to numeric index with at least 2 points
        equity_curve = df['pnl'].cumsum()
        if len(equity_curve) == 1:
            # Duplicate the point to ensure we have at least 2 points
            equity_curve = pd.concat([equity_curve, equity_curve])

    max_drawdown = float((equity_curve.cummax() - equity_curve).max()) if not equity_curve.empty else 0.0

    returns = equity_curve.pct_change().dropna()
    if returns.empty or returns.isna().all():
        sharpe = 0.0
    else:
        std = returns.std()
        mean_return = returns.mean()
        if std == 0 or np.isnan(std) or np.isnan(mean_return):
            sharpe = 0.0
        else:
            sharpe = float(np.sqrt(252) * mean_return / std)
            # Cap Sharpe ratio at reasonable bounds
            sharpe = max(min(sharpe, 10.0), -10.0)

    return {
        "win_rate": float(win_rate) if not np.isnan(win_rate) else 0.0,
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
        # Return a DataFrame with valid date range to prevent infinite extent warnings
        default_date = pd.Timestamp.now().normalize()
        return pd.DataFrame({
            "period": [default_date, default_date + pd.Timedelta(days=1)], 
            "pnl": [0.0, 0.0], 
            "win_rate": [0.0, 0.0]
        })

    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
    df = df.dropna(subset=["pnl", "exit_time"])

    if df.empty:
        # Return a DataFrame with valid date range to prevent infinite extent warnings
        default_date = pd.Timestamp.now().normalize()
        return pd.DataFrame({
            "period": [default_date, default_date + pd.Timedelta(days=1)], 
            "pnl": [0.0, 0.0], 
            "win_rate": [0.0, 0.0]
        })

    try:
        period = df["exit_time"].dt.to_period(freq).dt.to_timestamp()
        grouped = df.groupby(period)
        pnl = grouped["pnl"].sum()
        win_rate = grouped.apply(lambda g: float((g["pnl"] > 0).mean() * 100))

        # Ensure no infinite or NaN values
        pnl = pnl.fillna(0.0)
        win_rate = win_rate.fillna(0.0)

        # Ensure finite values only
        pnl_values = [float(x) if np.isfinite(x) else 0.0 for x in pnl.values]
        wr_values = [float(x) if np.isfinite(x) else 0.0 for x in win_rate.values]

        result = pd.DataFrame({
            "period": pnl.index, 
            "pnl": pnl_values, 
            "win_rate": wr_values
        })

        # Ensure we have at least 2 data points for proper charting
        if len(result) == 1:
            result = pd.concat([result, result.copy()], ignore_index=True)
            result.iloc[1, result.columns.get_loc('period')] = result.iloc[0]['period'] + pd.Timedelta(days=1)

        return result
    except Exception:
        # Return a DataFrame with valid date range to prevent infinite extent warnings
        default_date = pd.Timestamp.now().normalize()
        return pd.DataFrame({
            "period": [default_date, default_date + pd.Timedelta(days=1)], 
            "pnl": [0.0, 0.0], 
            "win_rate": [0.0, 0.0]
        })


def median_results(df: pd.DataFrame) -> dict:
    """Return median PnL statistics."""
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])

    if df.empty:
        return {
            "median_pnl": 0.0,
            "median_win": 0.0,
            "median_loss": 0.0,
        }

    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]

    median_pnl = float(df["pnl"].median()) if not df.empty else 0.0
    median_win = float(wins["pnl"].median()) if not wins.empty else 0.0
    median_loss = float(losses["pnl"].median()) if not losses.empty else 0.0

    return {
        "median_pnl": median_pnl,
        "median_win": median_win,
        "median_loss": median_loss,
    }


def profit_factor_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate profit factor for each trading symbol."""
    if df.empty:
        # Return a DataFrame with one default row to prevent infinite extent warnings
        return pd.DataFrame({
            "symbol": ["No Data"],
            "profit_factor": [0.0]
        })

    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl", "symbol"])

    if df.empty:
        return pd.DataFrame({
            "symbol": ["No Data"],
            "profit_factor": [0.0]
        })

    def _pf(group: pd.DataFrame) -> float:
        wins = group[group["pnl"] > 0]["pnl"].sum()
        losses = group[group["pnl"] <= 0]["pnl"].sum()
        if losses != 0:
            pf = wins / abs(losses)
            return min(pf, 999.99)  # Cap at reasonable max
        else:
            return 999.99 if wins > 0 else 0.0

    result = (
        df.groupby("symbol")
        .apply(_pf, include_groups=False)
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

    if df.empty or len(df) < window:
        # Return a DataFrame with valid range to prevent infinite extent warnings
        return pd.DataFrame({
            "end_index": [0.0, 1.0],
            "win_rate": [0.0, 0.0],
            "profit_factor": [0.0, 0.0]
        })

    results = []
    for end in range(window, len(df) + 1):
        window_df = df.iloc[end - window : end]
        stats = compute_basic_stats(window_df)

        # Ensure finite values only
        win_rate = stats["win_rate"] if np.isfinite(stats["win_rate"]) else 0.0
        profit_factor = stats["profit_factor"] if np.isfinite(stats["profit_factor"]) else 0.0

        results.append(
            {
                "end_index": float(end - 1),
                "win_rate": win_rate,
                "profit_factor": profit_factor,
            }
        )

    result_df = pd.DataFrame(results)

    # Ensure we have at least 2 data points for proper charting
    if len(result_df) == 1:
        result_df = pd.concat([result_df, result_df.copy()], ignore_index=True)
        result_df.iloc[1, result_df.columns.get_loc('end_index')] = result_df.iloc[0]['end_index'] + 1

    return result_df


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