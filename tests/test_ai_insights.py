import pandas as pd
from ai_insights import detect_outliers_zscore


def test_detect_outliers_zscore_flags_extreme_values():
    df = pd.DataFrame({
        'pnl': [10, 12, 11, 9, 200],
        'symbol': ['A', 'A', 'A', 'A', 'A'],
        'entry_time': pd.to_datetime(['2024-01-01']*5),
        'exit_time': pd.to_datetime(['2024-01-01']*5),
        'entry_price': [1]*5,
        'exit_price': [1]*5,
        'qty': [1]*5,
        'direction': ['long']*5,
        'trade_type': ['f']*5,
        'broker': ['demo']*5,
    })

    result = detect_outliers_zscore(df, column='pnl', threshold=1.5)
    outliers = result[result['outlier']]
    assert len(outliers) == 1
    assert outliers.iloc[0]['pnl'] == 200
