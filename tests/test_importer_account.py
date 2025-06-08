import pandas as pd
from data_import import FuturesImporter
from data_import.base_importer import REQUIRED_COLUMNS, OPTIONAL_COLUMNS

def test_load_with_optional_account(tmp_path):
    csv = tmp_path / "trades.csv"
    data = [
        ["ES", "2024-01-01", "2024-01-01", 1, 2, 1, "long", 100, "futures", "Demo", "ACC1"]
    ]
    cols = REQUIRED_COLUMNS + ["account"]
    pd.DataFrame(data, columns=cols).to_csv(csv, index=False)

    importer = FuturesImporter()
    df = importer.load(str(csv))
    for col in REQUIRED_COLUMNS:
        assert col in df.columns
    assert "account" in df.columns
