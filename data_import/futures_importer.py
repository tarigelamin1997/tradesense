import pandas as pd
from .base_importer import BaseImporter, REQUIRED_COLUMNS

class FuturesImporter(BaseImporter):
    """Importer for futures trade history CSV/Excel files."""

    def load(self, file_path: str) -> pd.DataFrame:
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read file: {e}")

        if not self.validate_columns(df):
            # return raw df for mapping step
            return df

        return df[REQUIRED_COLUMNS]
