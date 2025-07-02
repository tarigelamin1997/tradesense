
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import time
from ..base import ConnectorBase

class ApexTraderConnector(ConnectorBase):
    """Apex Trader Funding prop firm connector.
    
    API Documentation: https://docs.apextrader.com/api
    
    Key API Differences:
    - Prop firm specific metrics (daily loss limits, profit targets)
    - Challenge vs Live account data separation
    - Real-time risk monitoring integration
    - Different fee structures (no commissions, but profit splits)
    - Account scaling based on performance
    
    Edge Cases:
    - Challenge accounts have different rules than funded accounts
    - Daily loss limits can halt trading
    - Profit targets must be met for payouts
    - Risk violations can result in account termination
    - Different markets have different trading sessions
    - Simulated vs real market data for challenges
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.apextrader.com/v1') if config else 'https://api.apextrader.com/v1'
        self.api_key = None
        self.account_type = None  # 'challenge' or 'funded'
        self.account_id = None
        
    @property
    def connector_type(self) -> str:
        return "prop_firm"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["api", "json"]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with Apex Trader API."""
        self.api_key = credentials.get('api_key', '')
        username = credentials.get('username', '')
        password = credentials.get('password', '')
        
        if not self.api_key:
            return False
        
        try:
            # Test API key and get account info
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/accounts/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                account_data = response.json()
                self.account_id = account_data.get('account_id')
                self.account_type = account_data.get('account_type', 'challenge')
                self.authenticated = True
                return True
                
        except Exception as e:
            print(f"Apex Trader authentication error: {str(e)}")
        
        return False
    
    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from Apex Trader API."""
        if not self.authenticated:
            raise ValueError("Apex Trader connector not authenticated")
        
        # Default date range
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'account_id': self.account_id
        }
        
        if symbol:
            params['symbol'] = symbol.upper()
        
        try:
            response = requests.get(
                f"{self.base_url}/trades",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            trades_data = response.json()
            
            # Get additional account metrics
            metrics = self._get_account_metrics()
            
            # Process trades with prop firm context
            trades = self._process_apex_trades(trades_data.get('trades', []), metrics)
            
            return trades
            
        except Exception as e:
            raise Exception(f"Failed to fetch Apex Trader trades: {str(e)}")
    
    def _get_account_metrics(self) -> Dict[str, Any]:
        """Get prop firm specific account metrics."""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/metrics",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"Error fetching Apex metrics: {str(e)}")
        
        return {}
    
    def _process_apex_trades(self, trades: List[Dict], metrics: Dict) -> List[Dict]:
        """Process Apex Trader trades with prop firm specific data."""
        processed_trades = []
        
        daily_loss_limit = metrics.get('daily_loss_limit', 0)
        max_loss_limit = metrics.get('max_loss_limit', 0)
        profit_target = metrics.get('profit_target', 0)
        
        for trade in trades:
            processed_trade = {
                'trade_id': trade.get('trade_id', ''),
                'symbol': trade.get('symbol', ''),
                'direction': 'long' if trade.get('side') == 'buy' else 'short',
                'qty': float(trade.get('quantity', 0)),
                'entry_price': float(trade.get('entry_price', 0)),
                'exit_price': float(trade.get('exit_price', 0)),
                'entry_time': trade.get('entry_time', ''),
                'exit_time': trade.get('exit_time', ''),
                'pnl': float(trade.get('pnl', 0)),
                'commission': 0.0,  # Prop firms typically don't charge commissions
                
                # Prop firm specific fields
                'account_type': self.account_type,
                'daily_loss_limit': daily_loss_limit,
                'max_loss_limit': max_loss_limit,
                'profit_target': profit_target,
                'risk_violation': trade.get('risk_violation', False),
                'market_session': trade.get('market_session', 'regular'),
                'platform': trade.get('platform', 'apex_trader')
            }
            
            processed_trades.append(processed_trade)
        
        return processed_trades
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize Apex Trader data to universal format."""
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # Convert timestamps
        for time_col in ['entry_time', 'exit_time']:
            if time_col in df.columns:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        
        # Ensure numeric columns
        numeric_cols = ['entry_price', 'exit_price', 'qty', 'pnl', 'commission']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Add prop firm specific calculations
        if 'pnl' in df.columns and 'daily_loss_limit' in df.columns:
            df['daily_loss_breach'] = df['pnl'] < -abs(df['daily_loss_limit'])
            df['max_loss_breach'] = df['pnl'] < -abs(df['max_loss_limit'])
        
        return df
    
    def get_required_config(self) -> List[str]:
        """Apex Trader requires API key and credentials."""
        return ['api_key', 'username', 'password']
    
    def get_optional_params(self) -> List[str]:
        """Optional parameters for Apex API calls."""
        return ['account_type', 'market_session', 'platform']
