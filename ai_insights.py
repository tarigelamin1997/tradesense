import pandas as pd
import numpy as np


def detect_outliers_zscore(df: pd.DataFrame, column: str = "pnl", threshold: float = 3.0) -> pd.DataFrame:
    """Flag outlier trades based on z-score.

    Returns a copy of ``df`` with additional ``zscore`` and ``outlier`` columns.
    Trades where ``|zscore| > threshold`` are marked as outliers.
    """
    if df.empty:
        result = df.copy()
        result["zscore"] = []
        result["outlier"] = []
        return result

    numeric = pd.to_numeric(df[column], errors="coerce")
    z = (numeric - numeric.mean()) / numeric.std(ddof=0)

    result = df.copy()
    result["zscore"] = z
    result["outlier"] = z.abs() > threshold
    return result


def _call_llm_api(prompt: str) -> str:
    """Placeholder for a call to an LLM API."""
    # TODO: integrate with OpenAI or another provider
    return f"LLM response for: {prompt[:50]}..."


def summarize_trades(df: pd.DataFrame) -> str:
    """Generate a simple summary for the given trades using a placeholder LLM."""
    if df.empty:
        return ""
    prompt = f"Summarize the following trades: {df.to_dict(orient='records')}"
    return _call_llm_api(prompt)
