import pandas as pd
from data_import import FuturesImporter
from analytics import aggregate_by_account

def test_merge_multiple_files_account_stats(tmp_path):
    csv1 = tmp_path / "t1.csv"
    csv2 = tmp_path / "t2.csv"
    cols = ['symbol','entry_time','exit_time','entry_price','exit_price','qty','direction','pnl','trade_type','broker','account']
    data1 = [
        ['ES','2024-01-01','2024-01-01',1,2,1,'long',100,'f','D','ACC1'],
        ['ES','2024-01-01','2024-01-01',1,2,1,'long',-50,'f','D','ACC1']
    ]
    data2 = [
        ['ES','2024-01-02','2024-01-02',1,2,1,'long',20,'f','D','ACC2'],
        ['ES','2024-01-03','2024-01-03',1,2,1,'long',30,'f','D','ACC1']
    ]
    pd.DataFrame(data1, columns=cols).to_csv(csv1, index=False)
    pd.DataFrame(data2, columns=cols).to_csv(csv2, index=False)

    imp = FuturesImporter()
    df = pd.concat([imp.load(str(csv1)), imp.load(str(csv2))], ignore_index=True)
    summary = aggregate_by_account(df)
    res = summary.set_index('account')['pnl'].to_dict()
    assert res['ACC1'] == 80
    assert res['ACC2'] == 20
