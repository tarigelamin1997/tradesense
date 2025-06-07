import pandas as pd
from abc import ABC, abstractmethod
from typing import Union, IO, Any

REQUIRED_COLUMNS = [
    'symbol', 'entry_time', 'exit_time', 'entry_price',
    'exit_price', 'qty', 'direction', 'pnl', 'trade_type', 'broker'
]

class BaseImporter(ABC):
    """Abstract base class for trade data importers."""

    @abstractmethod
    def load(self, file_obj: Union[str, IO[Any]]) -> pd.DataFrame:
        """Load and normalize trade data from a file path or file-like object."""
        pass

    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Check if required columns exist."""
        return all(col in df.columns for col in REQUIRED_COLUMNS)

    def map_columns(self, df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """Map user-provided columns to required columns."""
        df = df.rename(columns=mapping)
        if not self.validate_columns(df):
            missing = set(REQUIRED_COLUMNS) - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}")
        return df[REQUIRED_COLUMNS]
