import pandas as pd
from typing import Union, IO, Any
from .base_importer import BaseImporter, REQUIRED_COLUMNS, OPTIONAL_COLUMNS
from .utils import load_trade_data

class FuturesImporter(BaseImporter):
    """Importer for futures trade history CSV/Excel files."""

    def load(self, file_obj: Union[str, IO[Any]]) -> pd.DataFrame:
        """Load futures trades from a CSV or Excel file.

        Parameters
        ----------
        file_obj : str or file-like object
            Path to the file or an object with a ``read`` method.
        """
        try:
            df = load_trade_data(file_obj)
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}") from e

        if not self.validate_columns(df):
            # return raw df for mapping step
            return df

        cols = REQUIRED_COLUMNS + [c for c in OPTIONAL_COLUMNS if c in df.columns]
        return df[cols]
