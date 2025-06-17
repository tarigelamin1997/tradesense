
import requests
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import json
from ..base import ConnectorBase


class ETradeConnector(ConnectorBase):
    """E*TRADE API connector for individual accounts."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.client_key = None
        self.client_secret = None
        self.access_token = None
        self.access_secret = None
        self.base_url = "https://api.etrade.com/v1"
        self.sandbox_url = "https://etwssandbox.etrade.com/v1"
        self.sandbox_mode = config.get('sandbox', False) if config else False
    
    @property
    def connector_type(self) -> str:
        return "broker_api"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["api", "json"]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with E*TRADE using OAuth1."""
        try:
            self.client_key = credentials.get('client_key')
            self.client_secret = credentials.get('client_secret')
            self.access_token = credentials.get('access_token')
            self.access_secret = credentials.get('access_secret')
            
            if not all([self.client_key, self.client_secret, self.access_token, self.access_secret]):
                return False
            
            # Test authentication by getting account list
            base_url = self.sandbox_url if self.sandbox_mode else self.base_url
            test_url = f"{base_url}/account/list"
            
            # E*TRADE uses OAuth1 - this is a simplified version
            # In production, you'd use a proper OAuth1 library like requests-oauthlib
            headers = {
                'Authorization': f'OAuth oauth_consumer_key="{self.client_key}", oauth_token="{self.access_token}"'
            }
            
            response = requests.get(test_url, headers=headers)
            
            if response.status_code == 200:
                self.authenticated = True
                return True
            
            return False
            
        except Exception as e:
            print(f"E*TRADE authentication error: {e}")
            return False
    
    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from E*TRADE."""
        if not self.authenticated:
            raise Exception("Not authenticated with E*TRADE")
        
        try:
            base_url = self.sandbox_url if self.sandbox_mode else self.base_url
            
            # Get account list first
            accounts_url = f"{base_url}/account/list"
            headers = {
                'Authorization': f'OAuth oauth_consumer_key="{self.client_key}", oauth_token="{self.access_token}"'
            }
            
            accounts_response = requests.get(accounts_url, headers=headers)
            
            if accounts_response.status_code != 200:
                raise Exception(f"Failed to get accounts: {accounts_response.text}")
            
            accounts_data = accounts_response.json()
            accounts = accounts_data.get('AccountListResponse', {}).get('Accounts', {}).get('Account', [])
            
            all_trades = []
            
            for account in accounts:
                account_key = account.get('accountIdKey')
                
                # Get transactions for this account
                transactions_url = f"{base_url}/account/{account_key}/transactions"
                
                params = {}
                if start_date:
                    params['startDate'] = start_date.strftime('%m%d%Y')
                if end_date:
                    params['endDate'] = end_date.strftime('%m%d%Y')
                
                transactions_response = requests.get(transactions_url, headers=headers, params=params)
                
                if transactions_response.status_code == 200:
                    transactions_data = transactions_response.json()
                    transactions = transactions_data.get('TransactionListResponse', {}).get('Transaction', [])
                    
                    if not isinstance(transactions, list):
                        transactions = [transactions]
                    
                    for transaction in transactions:
                        if transaction.get('transactionType') in ['Bought', 'Sold']:
                            trade_data = {
                                'transaction_id': transaction.get('transactionId'),
                                'account_key': account_key,
                                'symbol': transaction.get('brokerage', {}).get('product', {}).get('symbol'),
                                'action': 'BUY' if transaction.get('transactionType') == 'Bought' else 'SELL',
                                'quantity': transaction.get('brokerage', {}).get('quantity', 0),
                                'price': transaction.get('brokerage', {}).get('price', 0),
                                'commission': transaction.get('brokerage', {}).get('commission', 0),
                                'date': transaction.get('transactionDate'),
                                'raw_data': transaction
                            }
                            
                            if not symbol or trade_data['symbol'] == symbol:
                                all_trades.append(trade_data)
            
            return all_trades
            
        except Exception as e:
            raise Exception(f"Error fetching E*TRADE trades: {e}")
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize E*TRADE data to standard format."""
        if not raw_data:
            return pd.DataFrame()
        
        normalized_trades = []
        
        for trade in raw_data:
            normalized_trade = {
                'symbol': trade.get('symbol', ''),
                'side': 'buy' if trade.get('action') == 'BUY' else 'sell',
                'quantity': abs(float(trade.get('quantity', 0))),
                'price': float(trade.get('price', 0)),
                'commission': float(trade.get('commission', 0)),
                'timestamp': pd.to_datetime(trade.get('date')),
                'trade_id': trade.get('transaction_id'),
                'account_id': trade.get('account_key'),
                'broker': 'E*TRADE',
                'fees': float(trade.get('commission', 0))
            }
            normalized_trades.append(normalized_trade)
        
        df = pd.DataFrame(normalized_trades)
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        return df
    
    def get_required_config(self) -> List[str]:
        """Return required configuration for E*TRADE."""
        return ['client_key', 'client_secret', 'access_token', 'access_secret']
