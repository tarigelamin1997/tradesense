import pandas as pd
from data_import import FuturesImporter
from data_import.base_importer import REQUIRED_COLUMNS


def test_load_sample_csv():
    importer = FuturesImporter()
    df = importer.load('sample_data/futures_sample.csv')
    assert isinstance(df, pd.DataFrame)
    # should have 30 rows and required columns only
    assert df.shape == (30, len(REQUIRED_COLUMNS))
    assert list(df.columns) == REQUIRED_COLUMNS

