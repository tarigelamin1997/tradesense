import pandas as pd
from st_aggrid import GridOptionsBuilder


def compute_trade_result(df: pd.DataFrame) -> pd.DataFrame:
    """Add trade_result column indicating win or loss.

    PnL values may come in as strings from uploaded CSV files. We coerce to
    numeric so comparisons don't raise type errors. Invalid values become ``NaN``
    and are treated as losses to avoid misleading results.
    """
    df = df.copy()
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    df["trade_result"] = df["pnl"].apply(
        lambda x: "Win" if pd.notna(x) and x >= 0 else "Loss"
    )
    return df


def get_grid_options(df: pd.DataFrame) -> dict:
    """Build AgGrid options with grouping and multi-sort enabled."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(sortable=True, enableRowGroup=True)
    gb.configure_column("symbol", rowGroup=True, hide=True)
    gb.configure_column("direction", rowGroup=True, hide=True)
    gb.configure_column("trade_result", rowGroup=True, hide=True)
    gb.configure_grid_options(suppressMultiSort=False)
    gb.configure_selection("single")
    return gb.build()


def trade_detail(row: pd.Series) -> dict:
    """Return additional trade metrics for detail view."""
    pnl = float(row.get("pnl", 0))
    mae = pnl if pnl < 0 else 0
    mfe = pnl if pnl > 0 else 0
    duration = pd.to_datetime(row["exit_time"]) - pd.to_datetime(row["entry_time"])
    return {"mae": mae, "mfe": mfe, "duration": duration, "notes": row.get("notes", "")}
