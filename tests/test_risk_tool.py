import pandas as pd
import pytest
from risk_tool import assess_risk


def test_recommended_position_size():
    data = [
        ['ES', '2024-01-01', '2024-01-01', 100, 110, 1, 'long', 100, 'daytrade', 'Demo'],
        ['ES', '2024-01-01', '2024-01-01', 100, 90, 1, 'short', -10, 'daytrade', 'Demo'],
        ['ES', '2024-01-02', '2024-01-02', 100, 80, 1, 'short', -20, 'daytrade', 'Demo'],
    ]
    cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price',
            'qty', 'direction', 'pnl', 'trade_type', 'broker']
    df = pd.DataFrame(data, columns=cols)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    stats = assess_risk(
        df,
        account_size=10000,
        risk_per_trade=0.02,
        max_daily_loss=500,
    )

    expected_size = 10000 * 0.02 / 15
    assert stats['recommended_position_size'] == pytest.approx(expected_size)
    assert stats['warning'] == ''


def test_max_daily_loss_warning():
    data = [
        ['ES', '2024-01-01', '2024-01-01', 100, 95, 1, 'short', -60, 'daytrade', 'Demo'],
        ['ES', '2024-01-01', '2024-01-01', 100, 95, 1, 'short', -50, 'daytrade', 'Demo'],
        ['ES', '2024-01-02', '2024-01-02', 100, 105, 1, 'long', 100, 'daytrade', 'Demo'],
    ]
    cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price',
            'qty', 'direction', 'pnl', 'trade_type', 'broker']
    df = pd.DataFrame(data, columns=cols)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    stats = assess_risk(
        df,
        account_size=10000,
        risk_per_trade=0.02,
        max_daily_loss=100,
    )

    assert stats['warning'] == 'Historical trades exceed your max daily loss.'


def test_empty_dataframe():
    cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price',
            'qty', 'direction', 'pnl', 'trade_type', 'broker']
    df = pd.DataFrame(columns=cols)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    stats = assess_risk(
        df,
        account_size=10000,
        risk_per_trade=0.02,
        max_daily_loss=100,
    )

    assert stats['recommended_position_size'] == 0
    assert stats['warning'] == ''


def test_all_winning_trades():
    data = [
        ['ES', '2024-01-01', '2024-01-01', 100, 110, 1, 'long', 10, 'daytrade', 'Demo'],
        ['ES', '2024-01-02', '2024-01-02', 100, 115, 1, 'long', 15, 'daytrade', 'Demo'],
    ]
    cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'qty', 'direction', 'pnl', 'trade_type', 'broker']
    df = pd.DataFrame(data, columns=cols)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])

    stats = assess_risk(
        df,
        account_size=10000,
        risk_per_trade=0.02,
        max_daily_loss=500,
    )

    assert stats['recommended_position_size'] == 0
    assert stats['warning'] == ''
