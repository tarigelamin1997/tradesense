import pandas as pd
from pathlib import Path
from typing import Union, IO, Any
from .base_importer import BaseImporter, REQUIRED_COLUMNS

class FuturesImporter(BaseImporter):
    """Importer for futures trade history CSV/Excel files."""

    def load(self, file_path: Union[str, IO[Any]]) -> pd.DataFrame:
        try:
            if isinstance(file_path, str):
                ext = Path(file_path).suffix.lower()
            else:
                ext = Path(getattr(file_path, 'name', '')).suffix.lower()

            if ext in ('.xlsx', '.xls'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")

        if not self.validate_columns(df):
            # return raw df for mapping step
            return df

        return df[REQUIRED_COLUMNS]
