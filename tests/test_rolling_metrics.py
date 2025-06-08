import pandas as pd
from analytics import rolling_metrics


def test_rolling_metrics_basic():
    pnl = [10, -5, 20, -10, 5]
    df = pd.DataFrame({
        "symbol": ["ES"] * len(pnl),
        "entry_time": ["2024-01-01"] * len(pnl),
        "exit_time": ["2024-01-01"] * len(pnl),
        "entry_price": [1] * len(pnl),
        "exit_price": [1] * len(pnl),
        "qty": [1] * len(pnl),
        "direction": ["long"] * len(pnl),
        "pnl": pnl,
        "trade_type": ["d"] * len(pnl),
        "broker": ["Demo"] * len(pnl),
    })

    roll = rolling_metrics(df, window=3)
    assert len(roll) == 3
    assert roll.loc[0, "win_rate"] == 66.66666666666666
    assert roll.loc[0, "profit_factor"] == 6
