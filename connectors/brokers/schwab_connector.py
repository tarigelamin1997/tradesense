
import requests
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
from ..base import ConnectorBase


class SchwabConnector(ConnectorBase):
    """Charles Schwab API connector for individual accounts."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = None
        self.access_token = None
        self.refresh_token = None
        self.base_url = "https://api.schwabapi.com/trader/v1"
        self.auth_url = "https://api.schwabapi.com/v1/oauth/authorize"
        self.token_url = "https://api.schwabapi.com/v1/oauth/token"
    
    @property
    def connector_type(self) -> str:
        return "broker_api"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["api", "json"]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Schwab using OAuth2."""
        try:
            self.api_key = credentials.get('client_id')
            client_secret = credentials.get('client_secret')
            auth_code = credentials.get('auth_code')
            
            if not all([self.api_key, client_secret, auth_code]):
                return False
            
            # Exchange authorization code for access token
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'client_id': self.api_key,
                'client_secret': client_secret,
                'redirect_uri': 'https://localhost'
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                self.authenticated = True
                return True
            
            return False
            
        except Exception as e:
            print(f"Schwab authentication error: {e}")
            return False
    
    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from Schwab."""
        if not self.authenticated:
            raise Exception("Not authenticated with Schwab")
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            # Get account numbers
            accounts_url = f"{self.base_url}/accounts/accountNumbers"
            accounts_response = requests.get(accounts_url, headers=headers)
            
            if accounts_response.status_code != 200:
                raise Exception(f"Failed to get accounts: {accounts_response.text}")
            
            accounts = accounts_response.json()
            all_trades = []
            
            for account in accounts:
                account_hash = account.get('hashValue')
                
                # Get transactions
                transactions_url = f"{self.base_url}/accounts/{account_hash}/transactions"
                params = {'types': 'TRADE'}
                
                if start_date:
                    params['startDate'] = start_date.strftime('%Y-%m-%d')
                if end_date:
                    params['endDate'] = end_date.strftime('%Y-%m-%d')
                
                transactions_response = requests.get(transactions_url, headers=headers, params=params)
                
                if transactions_response.status_code == 200:
                    transactions = transactions_response.json()
                    
                    for transaction in transactions:
                        if transaction.get('type') == 'TRADE':
                            trade_data = {
                                'transaction_id': transaction.get('transactionId'),
                                'account_hash': account_hash,
                                'symbol': transaction.get('transactionItem', {}).get('instrument', {}).get('symbol'),
                                'action': transaction.get('transactionItem', {}).get('instruction'),
                                'quantity': transaction.get('transactionItem', {}).get('amount', 0),
                                'price': transaction.get('transactionItem', {}).get('price', 0),
                                'commission': transaction.get('fees', {}).get('commission', 0),
                                'date': transaction.get('transactionDate'),
                                'raw_data': transaction
                            }
                            
                            if not symbol or trade_data['symbol'] == symbol:
                                all_trades.append(trade_data)
            
            return all_trades
            
        except Exception as e:
            raise Exception(f"Error fetching Schwab trades: {e}")
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize Schwab data to standard format."""
        if not raw_data:
            return pd.DataFrame()
        
        normalized_trades = []
        
        for trade in raw_data:
            normalized_trade = {
                'symbol': trade.get('symbol', ''),
                'side': 'buy' if trade.get('action') in ['BUY', 'BUY_TO_OPEN'] else 'sell',
                'quantity': abs(float(trade.get('quantity', 0))),
                'price': float(trade.get('price', 0)),
                'commission': float(trade.get('commission', 0)),
                'timestamp': pd.to_datetime(trade.get('date')),
                'trade_id': trade.get('transaction_id'),
                'account_id': trade.get('account_hash'),
                'broker': 'Charles Schwab',
                'fees': float(trade.get('commission', 0))
            }
            normalized_trades.append(normalized_trade)
        
        df = pd.DataFrame(normalized_trades)
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        return df
    
    def get_required_config(self) -> List[str]:
        """Return required configuration for Schwab."""
        return ['client_id', 'client_secret', 'auth_code']


class SchwabCSVConnector(ConnectorBase):
    """Schwab CSV file connector for downloaded statements."""
    
    @property
    def connector_type(self) -> str:
        return "csv_import"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["csv"]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """No authentication needed for CSV files."""
        self.authenticated = True
        return True
    
    def fetch_trades(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """Load trades from Schwab CSV export."""
        try:
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to list of dictionaries
            trades = df.to_dict('records')
            return trades
            
        except Exception as e:
            raise Exception(f"Error reading Schwab CSV: {e}")
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize Schwab CSV data to standard format."""
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # Schwab CSV column mapping (adjust based on actual format)
        column_mapping = {
            'Symbol': 'symbol',
            'Quantity': 'quantity',
            'Price': 'price',
            'Action': 'side',
            'Date': 'timestamp',
            'Fees & Comm': 'commission'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Standardize data
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if 'side' in df.columns:
            df['side'] = df['side'].str.lower().map({'buy': 'buy', 'sell': 'sell'})
        
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').abs()
        
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        
        if 'commission' in df.columns:
            df['commission'] = pd.to_numeric(df['commission'], errors='coerce').fillna(0)
        
        df['broker'] = 'Charles Schwab'
        
        return df.dropna(subset=['symbol', 'timestamp']).sort_values('timestamp')
