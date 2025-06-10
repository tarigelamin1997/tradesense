
import pandas as pd
from analytics import profit_factor_by_symbol


def test_profit_factor_by_symbol_basic():
    data = [
        ["ES", "2024-01-01", "2024-01-01", 1, 1, 1, "long", 100, "d", "Demo"],
        ["ES", "2024-01-02", "2024-01-02", 1, 1, 1, "long", -50, "d", "Demo"],
        ["NQ", "2024-01-01", "2024-01-01", 1, 1, 1, "long", 30, "d", "Demo"],
        ["NQ", "2024-01-02", "2024-01-02", 1, 1, 1, "long", -30, "d", "Demo"],
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

    pf = profit_factor_by_symbol(df)
    es_pf = pf.loc[pf["symbol"] == "ES", "profit_factor"].iloc[0]
    nq_pf = pf.loc[pf["symbol"] == "NQ", "profit_factor"].iloc[0]
    assert es_pf == 2
    assert nq_pf == 1
