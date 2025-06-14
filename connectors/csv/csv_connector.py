
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
        """Normalize CSV data to standard format."""
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # Apply column mapping if specified in config
        column_mapping = self.config.get('column_mapping', {})
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist with defaults
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                if col == 'trade_type':
                    df[col] = 'manual'
                elif col == 'broker':
                    df[col] = 'csv_import'
                elif col == 'pnl' and all(c in df.columns for c in ['entry_price', 'exit_price', 'qty', 'direction']):
                    # Calculate P&L if missing
                    def calc_pnl(row):
                        try:
                            entry = float(row['entry_price'])
                            exit_price = float(row['exit_price'])
                            qty = float(row['qty'])
                            direction = str(row['direction']).lower()
                            
                            if direction in ['long', 'buy']:
                                return (exit_price - entry) * qty
                            elif direction in ['short', 'sell']:
                                return (entry - exit_price) * qty
                            else:
                                return 0
                        except:
                            return 0
                    
                    df[col] = df.apply(calc_pnl, axis=1)
                else:
                    df[col] = None
        
        # Clean and validate data types
        if 'entry_time' in df.columns:
            df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
        if 'exit_time' in df.columns:
            df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
        
        # Numeric columns
        numeric_cols = ['entry_price', 'exit_price', 'qty', 'pnl']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # String columns
        if 'symbol' in df.columns:
            df['symbol'] = df['symbol'].astype(str).str.upper()
        if 'direction' in df.columns:
            df['direction'] = df['direction'].astype(str).str.lower()
            df['direction'] = df['direction'].replace({'buy': 'long', 'sell': 'short'})
        
        return df
    
    def get_required_config(self) -> List[str]:
        """CSV connector requires file path."""
        return ['file_path']
    
    def get_optional_params(self) -> List[str]:
        """Optional parameters for CSV processing."""
        return ['column_mapping', 'delimiter', 'encoding']
