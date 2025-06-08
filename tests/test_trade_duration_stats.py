import pandas as pd
from analytics import trade_duration_stats


def test_trade_duration_stats_basic():
    data = [
        ["ES", "2024-01-01T00:00:00", "2024-01-01T00:30:00", 1, 1, 1, "long", 10, "d", "Demo"],
        ["ES", "2024-01-01T01:00:00", "2024-01-01T02:00:00", 1, 1, 1, "long", -5, "d", "Demo"],
    ]
    cols = [
        "symbol",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "qty",
        "direction",
        "pnl",
        "trade_type",
        "broker",
    ]
    df = pd.DataFrame(data, columns=cols)

    stats = trade_duration_stats(df)
    assert stats["average_minutes"] == 45
    assert stats["max_minutes"] == 60
    assert stats["min_minutes"] == 30
    assert stats["median_minutes"] == 45
