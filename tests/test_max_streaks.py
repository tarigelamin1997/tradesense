import pandas as pd
from analytics import max_streaks


def test_max_streaks_basic():
    pnl_values = [100, 200, -50, -50, -100, 150, 150, 150, -30]
    df = pd.DataFrame({
        "symbol": ["ES"] * len(pnl_values),
        "entry_time": ["2024-01-01"] * len(pnl_values),
        "exit_time": ["2024-01-01"] * len(pnl_values),
        "entry_price": [1] * len(pnl_values),
        "exit_price": [1] * len(pnl_values),
        "qty": [1] * len(pnl_values),
        "direction": ["long"] * len(pnl_values),
        "pnl": pnl_values,
        "trade_type": ["d"] * len(pnl_values),
        "broker": ["Demo"] * len(pnl_values),
    })

    streaks = max_streaks(df)
    assert streaks["max_win_streak"] == 3
    assert streaks["max_loss_streak"] == 3
