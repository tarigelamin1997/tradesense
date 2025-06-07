import pandas as pd
from analytics import compute_basic_stats
from risk_tool import assess_risk


def test_malformed_dates_do_not_crash():
    df = pd.DataFrame({
        'symbol': ['ES', 'NQ'],
        'entry_time': ['2024-01-01T00:00:00', 'bad-date'],
        'exit_time': ['2024-01-01T01:00:00', 'another-bad'],
        'entry_price': [1, 1],
        'exit_price': [2, 2],
        'qty': [1, 1],
        'direction': ['long', 'long'],
        'pnl': [10, -5],
        'trade_type': ['futures', 'futures'],
        'broker': ['Demo', 'Demo'],
    })

    df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce', format='ISO8601')
    df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce', format='ISO8601')
    df = df.dropna(subset=['entry_time', 'exit_time'])

    stats = compute_basic_stats(df)
    risk = assess_risk(df, account_size=1000, risk_per_trade=0.01, max_daily_loss=100)

    assert 'win_rate' in stats
    assert 'recommended_position_size' in risk
