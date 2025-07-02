import pandas as pd
from data_import import FuturesImporter
from data_import.base_importer import REQUIRED_COLUMNS


def test_load_sample_csv():
    importer = FuturesImporter()
    df = importer.load('sample_data/futures_sample.csv')
    assert isinstance(df, pd.DataFrame)
    # should have required columns and at least one row
    assert len(df) > 0
    for col in REQUIRED_COLUMNS:
        assert col in df.columns

