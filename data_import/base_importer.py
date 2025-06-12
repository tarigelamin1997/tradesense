import pandas as pd
from abc import ABC, abstractmethod
from typing import Union, IO, Any

REQUIRED_COLUMNS = [
    'symbol', 'entry_time', 'exit_time', 'entry_price',
    'exit_price', 'qty', 'direction', 'pnl', 'trade_type', 'broker'
]

OPTIONAL_COLUMNS = ['notes']

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
        cols = REQUIRED_COLUMNS + [c for c in OPTIONAL_COLUMNS if c in df.columns]
        return df[cols]
    
    def validate_data_quality(self, df: pd.DataFrame) -> dict:
        """Validate data quality and return a detailed report."""
        report = {
            'valid_rows': 0,
            'total_rows': len(df),
            'issues': [],
            'warnings': []
        }
        
        if df.empty:
            report['issues'].append("Dataset is empty")
            return report
        
        # Check for missing values in critical columns
        critical_cols = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price']
        for col in critical_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    report['warnings'].append(f"{col}: {missing_count} missing values")
        
        # Check for invalid dates
        if 'entry_time' in df.columns and 'exit_time' in df.columns:
            try:
                entry_times = pd.to_datetime(df['entry_time'], errors='coerce')
                exit_times = pd.to_datetime(df['exit_time'], errors='coerce')
                invalid_dates = (exit_times <= entry_times).sum()
                if invalid_dates > 0:
                    report['warnings'].append(f"Found {invalid_dates} trades with exit_time <= entry_time")
            except Exception:
                report['issues'].append("Unable to parse datetime columns")
        
        # Check for invalid prices
        price_cols = ['entry_price', 'exit_price']
        for col in price_cols:
            if col in df.columns:
                try:
                    prices = pd.to_numeric(df[col], errors='coerce')
                    negative_prices = (prices <= 0).sum()
                    if negative_prices > 0:
                        report['warnings'].append(f"{col}: {negative_prices} non-positive values")
                except Exception:
                    report['issues'].append(f"Unable to convert {col} to numeric")
        
        # Estimate valid rows after basic cleaning
        valid_mask = pd.Series(True, index=df.index)
        
        # Remove rows with missing critical data
        for col in critical_cols:
            if col in df.columns:
                valid_mask &= df[col].notna()
        
        report['valid_rows'] = valid_mask.sum()
        
        return report
