import pandas as pd


def assess_risk(
    df: pd.DataFrame, account_size: float, risk_per_trade: float, max_daily_loss: float
) -> dict:
    """Simple risk assessment based on historical PnL."""
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df = df.dropna(subset=["pnl"])
    stats = {}
    avg_loss = df[df["pnl"] < 0]["pnl"].mean() if not df.empty else 0
    recommended_size = account_size * risk_per_trade / abs(avg_loss) if avg_loss else 0
    if recommended_size > account_size:
        recommended_size = account_size

    stats["recommended_position_size"] = recommended_size
    stats["max_daily_loss"] = max_daily_loss
    daily_pnl = df.groupby(df["exit_time"].dt.date)["pnl"].sum()
    if any(daily_pnl < -max_daily_loss):
        stats["warning"] = "Historical trades exceed your max daily loss."
    else:
        stats["warning"] = ""
    return stats
