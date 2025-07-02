import pandas as pd
from analytics import performance_over_time


def test_performance_monthly():
    df = pd.DataFrame({
        'symbol': ['ES', 'ES', 'ES'],
        'entry_time': ['2024-01-01', '2024-02-01', '2024-02-15'],
        'exit_time': ['2024-01-01', '2024-02-01', '2024-02-15'],
        'entry_price': [1, 1, 1],
        'exit_price': [2, 0, 3],
        'qty': [1, 1, 1],
        'direction': ['long', 'short', 'long'],
        'pnl': [10, -5, 20],
        'trade_type': ['f', 'f', 'f'],
        'broker': ['D', 'D', 'D'],
    })
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    perf = performance_over_time(df, freq='M')
    assert list(perf['pnl']) == [10, 15]
