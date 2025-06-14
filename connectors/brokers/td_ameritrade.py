
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import time
from urllib.parse import urlencode
from ..base import ConnectorBase

class TDAmeritudeConnector(ConnectorBase):
    """TD Ameritrade API connector for live trading data.
    
    API Documentation: https://developer.tdameritrade.com/apis
    
    Key API Differences:
    - OAuth 2.0 authentication with refresh tokens
    - Rate limiting: 120 requests per minute per token
    - Market data requires separate endpoints
    - Transaction history vs Order history are different
    - Requires client ID registration with TD Ameritrade
    - Uses Unix timestamps for date ranges
    
    Edge Cases:
    - Access tokens expire after 30 minutes
    - Refresh tokens expire after 90 days
    - Paper trading not available - live accounts only
    - Market hours affect data availability
    - Some endpoints require additional permissions
    - Account linking required for live trading data
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://api.tdameritrade.com/v1"
        self.client_id = config.get('client_id', '') if config else ''
        self.access_token = None
        self.refresh_token = config.get('refresh_token', '') if config else ''
        self.account_id = config.get('account_id', '') if config else ''
        self.token_expires_at = 0
        
    @property
    def connector_type(self) -> str:
        return "broker"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["api", "json"]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with TD Ameritrade OAuth 2.0.
        
        TD Ameritrade uses OAuth 2.0 flow:
        1. Initial authorization code (manual process)
        2. Exchange for access/refresh tokens
        3. Use refresh token to get new access tokens
        """
        self.client_id = credentials.get('client_id', '')
        self.refresh_token = credentials.get('refresh_token', '')
        self.account_id = credentials.get('account_id', '')
        
        if not all([self.client_id, self.refresh_token]):
            return False
        
        try:
            # Use refresh token to get access token
            token_url = f"{self.base_url}/oauth2/token"
            
            token_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id
            }
            
            response = requests.post(
                token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                token_response = response.json()
                self.access_token = token_response.get('access_token')
                expires_in = token_response.get('expires_in', 1800)  # 30 minutes default
                self.token_expires_at = time.time() + expires_in
                
                # Test the token by getting account info
                if self._test_token():
                    self.authenticated = True
                    return True
                    
        except Exception as e:
            print(f"TD Ameritrade authentication error: {str(e)}")
        
        return False
    
    def _test_token(self) -> bool:
        """Test access token by making a simple API call."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f"{self.base_url}/accounts",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def _refresh_token_if_needed(self):
        """Refresh access token if it's about to expire."""
        if time.time() >= self.token_expires_at - 300:  # Refresh 5 min before expiry
            self.authenticate({
                'client_id': self.client_id,
                'refresh_token': self.refresh_token,
                'account_id': self.account_id
            })
    
    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from TD Ameritrade API.
        
        Edge Cases:
        - TD API returns transactions, need to filter for trades
        - Options and stocks have different transaction types
        - Corporate actions appear as transactions
        - Fees and dividends are separate transaction types
        - Date range limited to 1 year maximum
        """
        if not self.authenticated:
            raise ValueError("TD Ameritrade connector not authenticated")
        
        self._refresh_token_if_needed()
        
        # Default date range if not provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # TD API limits to 1 year
        if (end_date - start_date).days > 365:
            start_date = end_date - timedelta(days=365)
        
        # Convert to TD API format (ISO 8601)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            # Get transactions from TD API
            params = {
                'type': 'TRADE',  # Filter for trade transactions only
                'startDate': start_date_str,
                'endDate': end_date_str
            }
            
            if symbol:
                params['symbol'] = symbol.upper()
            
            transactions_url = f"{self.base_url}/accounts/{self.account_id}/transactions"
            
            response = requests.get(
                transactions_url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            transactions = response.json()
            
            # Process transactions into trade format
            trades = self._process_td_transactions(transactions)
            
            return trades
            
        except Exception as e:
            raise Exception(f"Failed to fetch TD Ameritrade trades: {str(e)}")
    
    def _process_td_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Process TD Ameritrade transactions into standardized trade format.
        
        TD Transaction Types:
        - TRADE: Stock/ETF trades
        - RECEIVE_AND_DELIVER: Options assignments
        - DIVIDEND_OR_INTEREST: Dividend payments
        - ACH_RECEIPT: Cash deposits
        - And many others...
        """
        trades = []
        
        for transaction in transactions:
            transaction_type = transaction.get('type', '')
            
            # Only process actual trades
            if transaction_type not in ['TRADE', 'RECEIVE_AND_DELIVER']:
                continue
            
            # Extract transaction item (contains the actual trade data)
            transaction_item = transaction.get('transactionItem', {})
            instrument = transaction_item.get('instrument', {})
            
            if not instrument:
                continue
            
            # Determine direction from transaction
            instruction = transaction_item.get('instruction', '')
            amount = float(transaction.get('netAmount', 0))
            
            # Map TD instruction to direction
            direction_map = {
                'BUY': 'long',
                'SELL': 'short',
                'BUY_TO_OPEN': 'long',
                'SELL_TO_OPEN': 'short',
                'BUY_TO_CLOSE': 'long',
                'SELL_TO_CLOSE': 'short'
            }
            
            direction = direction_map.get(instruction, 'long')
            
            trade = {
                'trade_id': str(transaction.get('orderId', transaction.get('transactionId', ''))),
                'symbol': instrument.get('symbol', ''),
                'direction': direction,
                'qty': float(transaction_item.get('amount', 0)),
                'entry_price': float(transaction_item.get('price', 0)),
                'entry_time': transaction.get('transactionDate', ''),
                'commission': abs(float(transaction.get('fees', {}).get('commission', 0))),
                'net_amount': amount,
                'instrument_type': instrument.get('assetType', ''),
                'description': transaction.get('description', ''),
                'account_id': transaction.get('accountId', self.account_id)
            }
            
            # For now, set exit data same as entry (TD doesn't link opening/closing trades)
            trade['exit_price'] = trade['entry_price']
            trade['exit_time'] = trade['entry_time']
            trade['pnl'] = trade['net_amount']  # Net amount includes P&L
            
            trades.append(trade)
        
        return trades
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize TD Ameritrade trade data to universal format."""
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # TD data is already mostly in the right format from processing
        # Just need to ensure consistent column names and data types
        
        # Convert timestamp format
        if 'entry_time' in df.columns:
            df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
        if 'exit_time' in df.columns:
            df['exit_time'] = pd.to_datetime(df['exit_time'], errors='coerce')
        
        # Ensure numeric columns
        numeric_cols = ['entry_price', 'exit_price', 'qty', 'pnl', 'commission', 'net_amount']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Handle quantity for short positions
        if 'direction' in df.columns and 'qty' in df.columns:
            df.loc[df['direction'] == 'short', 'qty'] = -abs(df.loc[df['direction'] == 'short', 'qty'])
        
        return df
    
    def get_required_config(self) -> List[str]:
        """TD Ameritrade requires OAuth credentials."""
        return ['client_id', 'refresh_token', 'account_id']
    
    def get_optional_params(self) -> List[str]:
        """Optional parameters for TD API calls."""
        return ['transaction_type', 'limit', 'start_date', 'end_date']
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information from TD Ameritrade."""
        if not self.authenticated:
            return {}
        
        try:
            self._refresh_token_if_needed()
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}",
                headers=headers,
                params={'fields': 'positions,orders'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Error fetching TD account info: {str(e)}")
        
        return {}
