import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import io
import csv
from ..base import ConnectorBase


class CSVConnector(ConnectorBase):
    """Enhanced CSV file connector with support for multiple broker formats."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.file_path = None
        self.broker_format = config.get('broker_format', 'generic') if config else 'generic'

        # Define broker-specific column mappings
        self.broker_mappings = {
            'generic': {
                'symbol': ['symbol', 'ticker', 'instrument'],
                'side': ['side', 'action', 'type', 'buy_sell'],
                'quantity': ['quantity', 'qty', 'shares', 'amount'],
                'price': ['price', 'avg_price', 'execution_price'],
                'timestamp': ['timestamp', 'date', 'time', 'datetime', 'trade_date'],
                'commission': ['commission', 'fees', 'cost']
            },
            'interactive_brokers': {
                'symbol': ['Symbol'],
                'side': ['Action'],
                'quantity': ['Quantity'],
                'price': ['Price'],
                'timestamp': ['DateTime'],
                'commission': ['Comm']
            },
            'td_ameritrade': {
                'symbol': ['SYMBOL'],
                'side': ['TRANSACTION TYPE'],
                'quantity': ['QUANTITY'],
                'price': ['PRICE'],
                'timestamp': ['DATE'],
                'commission': ['COMMISSION']
            },
            'schwab': {
                'symbol': ['Symbol'],
                'side': ['Action'],
                'quantity': ['Quantity'],
                'price': ['Price'],
                'timestamp': ['Date'],
                'commission': ['Fees & Comm']
            },
            'etrade': {
                'symbol': ['Symbol'],
                'side': ['Quantity'],  # E*TRADE uses positive/negative quantity
                'quantity': ['Quantity'],
                'price': ['Price'],
                'timestamp': ['Trade Date'],
                'commission': ['Commission']
            },
            'fidelity': {
                'symbol': ['Symbol'],
                'side': ['Action'],
                'quantity': ['Quantity'],
                'price': ['Price'],
                'timestamp': ['Run Date'],
                'commission': ['Commission']
            },
            'robinhood': {
                'symbol': ['Instrument'],
                'side': ['Side'],
                'quantity': ['Quantity'],
                'price': ['Price'],
                'timestamp': ['Created At'],
                'commission': ['Fees']
            },
            'webull': {
                'symbol': ['Symbol'],
                'side': ['Action'],
                'quantity': ['Filled Qty'],
                'price': ['Filled Price'],
                'timestamp': ['Time'],
                'commission': ['Commission']
            },
            'ninja_trader': {
                'symbol': ['Instrument'],
                'side': ['Action'],
                'quantity': ['Qty'],
                'price': ['Price'],
                'timestamp': ['Time'],
                'commission': ['Commission']
            },
            'think_or_swim': {
                'symbol': ['Symbol'],
                'side': ['Action'],
                'quantity': ['Qty'],
                'price': ['Price'],
                'timestamp': ['Date/Time'],
                'commission': ['Commission']
            }
        }

    @property
    def connector_type(self) -> str:
        return "csv_import"

    @property
    def supported_formats(self) -> List[str]:
        return ["csv", "xlsx", "txt"]

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

    def auto_detect_broker_format(self, df: pd.DataFrame) -> str:
        """Auto-detect broker format based on column names."""
        columns = [col.lower() for col in df.columns]

        # Check for specific broker indicators
        if any('thinkorswim' in col.lower() for col in df.columns):
            return 'think_or_swim'
        elif 'DateTime' in df.columns and 'Comm' in df.columns:
            return 'interactive_brokers'
        elif 'TRANSACTION TYPE' in df.columns:
            return 'td_ameritrade'
        elif 'Fees & Comm' in df.columns:
            return 'schwab'
        elif 'Run Date' in df.columns:
            return 'fidelity'
        elif 'Created At' in df.columns and 'Side' in df.columns:
            return 'robinhood'
        elif 'Filled Qty' in df.columns:
            return 'webull'
        elif 'ninja' in str(df.columns).lower():
            return 'ninja_trader'
        else:
            return 'generic'

    def map_columns(self, df: pd.DataFrame, broker_format: str) -> pd.DataFrame:
        """Map broker-specific columns to standard format."""
        if broker_format not in self.broker_mappings:
            broker_format = 'generic'

        mapping = self.broker_mappings[broker_format]

        # Find the best column match for each standard field
        mapped_df = df.copy()
        column_renames = {}

        for standard_field, possible_columns in mapping.items():
            found_column = None

            # Look for exact matches first
            for col in possible_columns:
                if col in df.columns:
                    found_column = col
                    break

            # If no exact match, try case-insensitive
            if not found_column:
                for col in possible_columns:
                    for df_col in df.columns:
                        if col.lower() == df_col.lower():
                            found_column = df_col
                            break
                    if found_column:
                        break

            if found_column and found_column != standard_field:
                column_renames[found_column] = standard_field

        # Apply the column renames
        mapped_df = mapped_df.rename(columns=column_renames)

        return mapped_df

    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize CSV data to standard format with enhanced broker support."""
        if not raw_data:
            from models.trade_model import UniversalTradeDataModel
            return pd.DataFrame(columns=UniversalTradeDataModel.get_schema_columns())

        df = pd.DataFrame(raw_data)

        # Auto-detect broker format if not specified
        if self.broker_format == 'generic':
            detected_format = self.auto_detect_broker_format(df)
            self.broker_format = detected_format

        # Map columns based on detected/specified broker format
        df = self.map_columns(df, self.broker_format)

        # Handle special cases for different brokers
        df = self._handle_broker_specific_formatting(df, self.broker_format)

        # Standardize data types and values
        df = self._standardize_data_types(df)

        # Set broker name
        broker_names = {
            'interactive_brokers': 'Interactive Brokers',
            'td_ameritrade': 'TD Ameritrade',
            'schwab': 'Charles Schwab',
            'etrade': 'E*TRADE',
            'fidelity': 'Fidelity',
            'robinhood': 'Robinhood',
            'webull': 'Webull',
            'ninja_trader': 'NinjaTrader',
            'think_or_swim': 'Think or Swim',
            'generic': 'CSV Import'
        }

        df['broker'] = broker_names.get(self.broker_format, 'CSV Import')

        # Ensure all required columns are present
        from models.trade_model import UniversalTradeDataModel
        required_cols = UniversalTradeDataModel().get_required_columns()
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Return with all available columns from universal schema
        available_cols = [col for col in UniversalTradeDataModel.get_schema_columns() if col in df.columns]
        return df[available_cols].dropna(subset=['symbol', 'entry_time']).sort_values('entry_time')

    def _handle_broker_specific_formatting(self, df: pd.DataFrame, broker_format: str) -> pd.DataFrame:
        """Handle broker-specific data formatting quirks."""
        if broker_format == 'etrade':
            # E*TRADE uses positive/negative quantities instead of buy/sell
            if 'quantity' in df.columns and 'side' not in df.columns:
                df['side'] = df['quantity'].apply(lambda x: 'buy' if float(x) > 0 else 'sell')
                df['quantity'] = df['quantity'].abs()

        elif broker_format == 'interactive_brokers':
            # IB has specific action codes
            if 'side' in df.columns:
                action_map = {
                    'BOT': 'buy', 'SLD': 'sell',
                    'BUY': 'buy', 'SELL': 'sell'
                }
                df['side'] = df['side'].map(action_map).fillna(df['side'])

        elif broker_format == 'td_ameritrade':
            # TD Ameritrade has specific transaction types
            if 'side' in df.columns:
                action_map = {
                    'BUY': 'buy', 'SELL': 'sell',
                    'Buy': 'buy', 'Sell': 'sell'
                }
                df['side'] = df['side'].map(action_map).fillna(df['side'])

        elif broker_format == 'robinhood':
            # Robinhood uses specific side indicators
            if 'side' in df.columns:
                df['side'] = df['side'].str.lower()

        return df

    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types for all columns."""
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df['entry_time'] = df['timestamp'] #added
            df['exit_time'] = df['timestamp'] #added


        # Convert numeric columns
        numeric_columns = ['quantity', 'price', 'commission']
        for col in numeric_columns:
            if col in df.columns:
                # Remove any currency symbols or commas
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.replace('[\$,]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Ensure quantity is positive
        if 'quantity' in df.columns:
            df['quantity'] = df['quantity'].abs()

        # Standardize side values
        if 'side' in df.columns:
            df['side'] = df['side'].astype(str).str.lower()
            side_map = {
                'buy': 'buy', 'b': 'buy', 'bought': 'buy', 'long': 'buy',
                'sell': 'sell', 's': 'sell', 'sold': 'sell', 'short': 'sell'
            }
            df['side'] = df['side'].map(side_map).fillna(df['side'])

        # Fill missing commission with 0
        if 'commission' in df.columns:
            df['commission'] = df['commission'].fillna(0)

        return df

    def get_supported_brokers(self) -> List[str]:
        """Return list of supported broker formats."""
        return list(self.broker_mappings.keys())

    def get_required_config(self) -> List[str]:
        """CSV connector requires file path."""
        return ['file_path']

    def get_optional_params(self) -> List[str]:
        """Optional parameters for CSV processing."""
        return ['column_mapping', 'delimiter', 'encoding', 'broker_format']