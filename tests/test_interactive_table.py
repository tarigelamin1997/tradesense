import pandas as pd
from interactive_table import compute_trade_result, get_grid_options, trade_detail


def sample_df():
    return pd.DataFrame({
        'symbol': ['ES', 'ES'],
        'entry_time': ['2024-01-01', '2024-01-02'],
        'exit_time': ['2024-01-01', '2024-01-02'],
        'entry_price': [1, 1],
        'exit_price': [2, 0],
        'qty': [1, 1],
        'direction': ['long', 'short'],
        'pnl': [10, -5],
        'trade_type': ['futures', 'futures'],
        'broker': ['Demo', 'Demo'],
    })


def test_grid_options_grouping_and_sort():
    df = compute_trade_result(sample_df())
    opts = get_grid_options(df)
    symbol_col = next(c for c in opts['columnDefs'] if c['field'] == 'symbol')
    direction_col = next(c for c in opts['columnDefs'] if c['field'] == 'direction')
    result_col = next(c for c in opts['columnDefs'] if c['field'] == 'trade_result')
    assert symbol_col.get('rowGroup') is True
    assert direction_col.get('rowGroup') is True
    assert result_col.get('rowGroup') is True
    assert opts.get('suppressMultiSort') is False


def test_trade_detail_values():
    df = compute_trade_result(sample_df())
    row = df.iloc[0]
    details = trade_detail(row)
    assert details['mfe'] == 10
    assert details['mae'] == 0
    assert 'duration' in details
