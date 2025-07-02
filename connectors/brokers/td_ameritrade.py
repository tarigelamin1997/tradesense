import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import time
from urllib.parse import urlencode
from ..base import ConnectorBase

class TDAmeritudeConnector(ConnectorBase):
    """TD Ameritrade API connector for individual accounts."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = None
        self.access_token = None
        self.refresh_token = None
        self.base_url = "https://api.tdameritrade.com/v1"
        self.redirect_uri = "https://localhost"

    @property
    def connector_type(self) -> str:
        return "broker_api"

    @property
    def supported_formats(self) -> List[str]:
        return ["api", "json"]

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with TD Ameritrade using OAuth2."""
        try:
            self.api_key = credentials.get('api_key')
            auth_code = credentials.get('auth_code')

            if not self.api_key or not auth_code:
                return False

            # Exchange authorization code for access token
            token_url = f"{self.base_url}/oauth2/token"
            data = {
                'grant_type': 'authorization_code',
                'refresh_token': '',
                'access_type': 'offline',
                'code': auth_code,
                'client_id': f"{self.api_key}@AMER.OAUTHAP",
                'redirect_uri': self.redirect_uri
            }

            response = requests.post(token_url, data=data)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                self.authenticated = True
                return True

            return False

        except Exception as e:
            print(f"TD Ameritrade authentication error: {e}")
            return False

    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token."""
        if not self.refresh_token or not self.api_key:
            return False

        try:
            token_url = f"{self.base_url}/oauth2/token"
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'access_type': 'offline',
                'client_id': f"{self.api_key}@AMER.OAUTHAP"
            }

            response = requests.post(token_url, data=data)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                if 'refresh_token' in token_data:
                    self.refresh_token = token_data.get('refresh_token')
                return True

            return False

        except Exception:
            return False

    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from TD Ameritrade."""
        if not self.authenticated:
            raise Exception("Not authenticated with TD Ameritrade")

        try:
            # Get account info first
            accounts_url = f"{self.base_url}/accounts"
            headers = {'Authorization': f'Bearer {self.access_token}'}

            accounts_response = requests.get(accounts_url, headers=headers)

            if accounts_response.status_code == 401:
                # Try to refresh token
                if self.refresh_access_token():
                    headers = {'Authorization': f'Bearer {self.access_token}'}
                    accounts_response = requests.get(accounts_url, headers=headers)
                else:
                    raise Exception("Token expired and refresh failed")

            if accounts_response.status_code != 200:
                raise Exception(f"Failed to get accounts: {accounts_response.text}")

            accounts = accounts_response.json()

            all_trades = []

            for account in accounts:
                account_id = account['securitiesAccount']['accountId']

                # Get transactions (which include trades)
                transactions_url = f"{self.base_url}/accounts/{account_id}/transactions"
                params = {'type': 'TRADE'}

                if start_date:
                    params['startDate'] = start_date.strftime('%Y-%m-%d')
                if end_date:
                    params['endDate'] = end_date.strftime('%Y-%m-%d')

                transactions_response = requests.get(transactions_url, headers=headers, params=params)

                if transactions_response.status_code == 200:
                    transactions = transactions_response.json()

                    for transaction in transactions:
                        if transaction.get('type') in ['BUY', 'SELL']:
                            trade_data = {
                                'transaction_id': transaction.get('transactionId'),
                                'account_id': account_id,
                                'symbol': transaction.get('transactionItem', {}).get('instrument', {}).get('symbol'),
                                'action': transaction.get('type'),
                                'quantity': transaction.get('transactionItem', {}).get('amount', 0),
                                'price': transaction.get('transactionItem', {}).get('price', 0),
                                'commission': transaction.get('fees', {}).get('commission', 0),
                                'date': transaction.get('transactionDate'),
                                'settlement_date': transaction.get('settlementDate'),
                                'raw_data': transaction
                            }

                            if not symbol or trade_data['symbol'] == symbol:
                                all_trades.append(trade_data)

            return all_trades

        except Exception as e:
            raise Exception(f"Error fetching TD Ameritrade trades: {e}")

    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize TD Ameritrade data to standard format."""
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
                'account_id': trade.get('account_id'),
                'broker': 'TD Ameritrade',
                'fees': float(trade.get('commission', 0)),
                'settlement_date': pd.to_datetime(trade.get('settlement_date')) if trade.get('settlement_date') else None
            }
            normalized_trades.append(normalized_trade)

        df = pd.DataFrame(normalized_trades)

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

        return df

    def get_required_config(self) -> List[str]:
        """Return required configuration for TD Ameritrade."""
        return ['api_key', 'auth_code']

    def get_optional_params(self) -> List[str]:
        """Return optional parameters."""
        return ['account_id']

    def get_auth_url(self) -> str:
        """Get OAuth authorization URL for TD Ameritrade."""
        if not self.api_key:
            raise Exception("API key required to generate auth URL")

        auth_url = (
            f"https://auth.tdameritrade.com/auth?"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"client_id={self.api_key}%40AMER.OAUTHAP"
        )

        return auth_url