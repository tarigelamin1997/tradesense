import pandas as pd
from analytics import median_results


def test_median_results_basic():
    data = [
        ["ES", "2023-01-01", "2023-01-01", 1, 1, 1, "long", 100, "daytrade", "Demo"],
        ["ES", "2023-01-02", "2023-01-02", 1, 1, 1, "long", -50, "daytrade", "Demo"],
        ["ES", "2023-01-03", "2023-01-03", 1, 1, 1, "long", 200, "daytrade", "Demo"],
        ["ES", "2023-01-04", "2023-01-04", 1, 1, 1, "long", -100, "daytrade", "Demo"],
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

    res = median_results(df)
    assert res["median_pnl"] == 25
    assert res["median_win"] == 150
    assert res["median_loss"] == -75
