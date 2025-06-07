import pytest
import pandas as pd
import numpy as np
from analytics import compute_basic_stats


def test_compute_basic_stats_known_data():
    data = [
        ['ES','2023-01-01','2023-01-01',1,1,1,'long',100,'daytrade','Demo'],
        ['ES','2023-01-02','2023-01-02',1,1,1,'long',-50,'daytrade','Demo'],
        ['ES','2023-01-03','2023-01-03',1,1,1,'long',200,'daytrade','Demo'],
        ['ES','2023-01-04','2023-01-04',1,1,1,'long',-100,'daytrade','Demo'],
    ]
    cols = ['symbol','entry_time','exit_time','entry_price','exit_price','qty','direction','pnl','trade_type','broker']
    df = pd.DataFrame(data, columns=cols)

    stats = compute_basic_stats(df)

    assert stats['win_rate'] == 50.0
    assert stats['average_win'] == 150.0
    assert stats['average_loss'] == -75.0
    assert stats['reward_risk'] == 2.0
    assert stats['expectancy'] == 37.5
    assert stats['profit_factor'] == 2.0
    assert stats['max_drawdown'] == 100
    # approximate due to floating point operations
    assert stats['sharpe_ratio'] == pytest.approx(6.3835034744, rel=1e-6)

