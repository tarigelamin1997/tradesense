from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import os
from ..base import ConnectorBase
from data_import.base_importer import REQUIRED_COLUMNS

class CSVConnector(ConnectorBase):
    """Connector for CSV files."""

    @property
    def connector_type(self) -> str:
        return "csv"

    @property
    def supported_formats(self) -> List[str]:
        return ["csv", "xlsx", "xls"]

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """For CSV files, authentication means checking file access."""
        file_path = credentials.get('file_path', '')

        if not file_path:
            return False

        try:
            # Check if file exists and is readable
            if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                self.config['file_path'] = file_path
                self.authenticated = True
                return True
        except Exception:
            pass

        return False

    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trades from CSV file."""
        if not self.authenticated:
            raise ValueError("CSV connector not authenticated. Provide valid file_path.")

        file_path = self.config['file_path']

        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")

            # Apply filters if provided
            if start_date and 'entry_time' in df.columns:
                df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
                df = df[df['entry_time'] >= start_date]

            if end_date and 'exit_time' in df.columns:
                df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
                df = df[df['exit_time'] <= end_date]

            if symbol and 'symbol' in df.columns:
                df = df[df['symbol'].str.upper() == symbol.upper()]

            return df.to_dict('records')

        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")

    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize CSV data to universal format."""
        if not raw_data:
            from models.trade_model import UniversalTradeDataModel
            return pd.DataFrame(columns=UniversalTradeDataModel.get_schema_columns())

        df = pd.DataFrame(raw_data)

        # Enhanced column mapping for common CSV formats
        column_mapping = {
            # Common variations
            'Symbol': 'symbol', 'SYMBOL': 'symbol', 'Instrument': 'symbol',
            'Entry Time': 'entry_time', 'EntryTime': 'entry_time', 'Open Time': 'entry_time',
            'Exit Time': 'exit_time', 'ExitTime': 'exit_time', 'Close Time': 'exit_time',
            'Entry Price': 'entry_price', 'EntryPrice': 'entry_price', 'Open Price': 'entry_price',
            'Exit Price': 'exit_price', 'ExitPrice': 'exit_price', 'Close Price': 'exit_price',
            'Quantity': 'qty', 'QTY': 'qty', 'Size': 'qty', 'Volume': 'qty',
            'Direction': 'direction', 'Side': 'direction', 'Type': 'direction',
            'P&L': 'pnl', 'PnL': 'pnl', 'Profit': 'pnl', 'Realized P&L': 'pnl',
            'Trade Type': 'trade_type', 'TradeType': 'trade_type', 'Product': 'trade_type',
            'Broker': 'broker', 'Account': 'broker', 'Platform': 'broker',
            'Notes': 'notes', 'Comment': 'notes', 'Description': 'notes',
            'Commission': 'commission', 'Fee': 'commission', 'Fees': 'commission',
            'Stop Loss': 'stop_loss', 'StopLoss': 'stop_loss', 'SL': 'stop_loss',
            'Take Profit': 'take_profit', 'TakeProfit': 'take_profit', 'TP': 'take_profit'
        }

        # Apply mapping
        df = df.rename(columns=column_mapping)

        # Set defaults for missing required fields
        from models.trade_model import UniversalTradeDataModel
        required_cols = UniversalTradeDataModel().get_required_columns()

        # Add missing required columns with defaults
        if 'trade_type' not in df.columns:
            df['trade_type'] = 'futures'  # Default type
        if 'broker' not in df.columns:
            df['broker'] = 'Unknown'
        if 'data_source' not in df.columns:
            df['data_source'] = 'csv'

        # Convert data types with error handling
        try:
            df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
            df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
            df['entry_price'] = pd.to_numeric(df['entry_price'], errors='coerce')
            df['exit_price'] = pd.to_numeric(df['exit_price'], errors='coerce')
            df['qty'] = pd.to_numeric(df['qty'], errors='coerce')
            df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')

            # Optional numeric fields
            if 'commission' in df.columns:
                df['commission'] = pd.to_numeric(df['commission'], errors='coerce')
            if 'stop_loss' in df.columns:
                df['stop_loss'] = pd.to_numeric(df['stop_loss'], errors='coerce')
            if 'take_profit' in df.columns:
                df['take_profit'] = pd.to_numeric(df['take_profit'], errors='coerce')

        except Exception as e:
            raise ValueError(f"Data type conversion failed: {str(e)}")

        # Ensure all required columns are present
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Return with all available columns from universal schema
        available_cols = [col for col in UniversalTradeDataModel.get_schema_columns() if col in df.columns]
        return df[available_cols]

    def get_required_config(self) -> List[str]:
        """CSV connector requires file path."""
        return ['file_path']

    def get_optional_params(self) -> List[str]:
        """Optional parameters for CSV processing."""
        return ['column_mapping', 'delimiter', 'encoding']