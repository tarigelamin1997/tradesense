import pandas as pd
from pathlib import Path
from typing import Union, IO, Any
from .base_importer import BaseImporter, REQUIRED_COLUMNS

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
            if isinstance(file_obj, str):
                file_name = file_obj.lower()
                if file_name.endswith(('.csv', '.txt')):
                    df = pd.read_csv(file_obj)
                elif file_name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_obj)
                else:
                    raise ValueError(f"Unsupported file format: {file_name}")
            else:
                file_name = getattr(file_obj, 'name', '').lower()
                if file_name.endswith(('.csv', '.txt')):
                    df = pd.read_csv(file_obj)
                elif file_name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_obj)
                else:
                    raise ValueError(f"Unsupported file format: {file_name}")
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}") from e

        if not self.validate_columns(df):
            # return raw df for mapping step
            return df

        return df[REQUIRED_COLUMNS]
