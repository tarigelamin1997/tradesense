import pandas as pd
from app import load_preferences


def build_df():
    return pd.DataFrame({
        'symbol': ['ES', 'NQ'],
        'entry_time': pd.to_datetime(['2024-01-01', '2024-01-02']),
        'exit_time': pd.to_datetime(['2024-01-01', '2024-01-02']),
        'direction': ['long', 'short'],
        'broker': ['A', 'B'],
    })


def test_load_preferences_sets_defaults():
    state = {}
    df = build_df()
    load_preferences(df, state)
    assert state['theme'] == 'Light'
    assert state['account_size'] == 10000.0
    assert state['symbols'] == ['ES', 'NQ']


def test_preferences_persist_on_second_call():
    state = {}
    df = build_df()
    load_preferences(df, state)
    state['theme'] = 'Dark'
    state['risk_per_trade'] = 0.03
    load_preferences(df, state)
    assert state['theme'] == 'Dark'
    assert state['risk_per_trade'] == 0.03
