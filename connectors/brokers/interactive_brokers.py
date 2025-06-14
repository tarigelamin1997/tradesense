
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import time
from ..base import ConnectorBase

class InteractiveBrokersConnector(ConnectorBase):
    """Interactive Brokers (IB) API connector for live trading data.
    
    API Documentation: https://interactivebrokers.github.io/cpwebapi/
    
    Key API Differences:
    - Uses Client Portal Web API (REST-based)
    - Requires active IB Gateway or TWS session
    - Session-based authentication with tickle endpoint
    - Rate limiting: 5 requests per second per endpoint
    - Market data requires separate subscriptions
    - Position data includes unrealized P&L
    
    Edge Cases:
    - Session expires after 24 hours of inactivity
    - Paper trading vs live accounts have different base URLs
    - Market data may be delayed (15-20 min) without real-time subscription
    - Multi-account users need to specify account ID
    - Some endpoints require SSO re-authentication
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://localhost:5000/v1/api')
        self.session = requests.Session()
        self.session.verify = False  # IB Gateway uses self-signed cert
        self.account_id = None
        self.last_tickle = 0
        
    @property
    def connector_type(self) -> str:
        return "broker"
    
    @property
    def supported_formats(self) -> List[str]:
        return ["api", "json"]
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """Authenticate with IB Client Portal Web API.
        
        Note: IB uses session-based auth, not API keys.
        User must have IB Gateway or TWS running locally.
        """
        try:
            # Check if IB Gateway is accessible
            status_response = self.session.get(
                f"{self.base_url}/iserver/auth/status",
                timeout=10
            )
            
            if status_response.status_code != 200:
                return False
            
            status_data = status_response.json()
            
            # If not authenticated, try to authenticate
            if not status_data.get('authenticated', False):
                auth_response = self.session.post(
                    f"{self.base_url}/iserver/auth/ssodh/init",
                    timeout=10
                )
                
                if auth_response.status_code != 200:
                    return False
            
            # Get account information
            accounts_response = self.session.get(
                f"{self.base_url}/iserver/accounts",
                timeout=10
            )
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                if accounts_data:
                    self.account_id = accounts_data[0]  # Use first account
                    self.authenticated = True
                    self.last_tickle = time.time()
                    return True
                    
        except Exception as e:
            print(f"IB Authentication error: {str(e)}")
        
        return False
    
    def _maintain_session(self):
        """Keep IB session alive with tickle endpoint."""
        if time.time() - self.last_tickle > 300:  # Every 5 minutes
            try:
                self.session.post(f"{self.base_url}/tickle")
                self.last_tickle = time.time()
            except:
                pass
    
    def fetch_trades(self, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    symbol: Optional[str] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Fetch trade data from IB API.
        
        Edge Cases:
        - IB returns executions, not complete trades
        - Need to group executions by order ID
        - Commission data is separate from execution data
        - Market data may be delayed without subscription
        """
        if not self.authenticated:
            raise ValueError("IB connector not authenticated")
        
        self._maintain_session()
        
        # Get executions (IB's term for filled orders)
        executions_endpoint = f"{self.base_url}/iserver/account/{self.account_id}/executions"
        
        # IB API uses days parameter instead of date range
        days = 7  # Default to last 7 days
        if start_date and end_date:
            days = (end_date - start_date).days
            days = max(1, min(days, 365))  # IB limits to 365 days
        
        params = {'days': days}
        
        try:
            response = self.session.get(executions_endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            executions_data = response.json()
            
            # Get positions for additional context
            positions_response = self.session.get(
                f"{self.base_url}/iserver/account/{self.account_id}/positions/0"
            )
            
            positions_data = []
            if positions_response.status_code == 200:
                positions_data = positions_response.json()
            
            # Transform executions to trade format
            trades = self._process_ib_executions(executions_data, positions_data)
            
            # Filter by symbol if specified
            if symbol:
                trades = [t for t in trades if t.get('symbol', '').upper() == symbol.upper()]
            
            return trades
            
        except Exception as e:
            raise Exception(f"Failed to fetch IB trades: {str(e)}")
    
    def _process_ib_executions(self, executions: List[Dict], positions: List[Dict]) -> List[Dict]:
        """Process IB executions into standardized trade format.
        
        IB Edge Cases:
        - Multiple executions per order (partial fills)
        - Buy and sell executions are separate
        - Commission is reported separately
        - Need to calculate P&L from position data
        """
        trades = []
        
        # Group executions by symbol and side to reconstruct trades
        execution_groups = {}
        
        for execution in executions:
            symbol = execution.get('symbol', '')
            side = execution.get('side', '')
            order_id = execution.get('order_id', '')
            
            key = f"{symbol}_{side}_{order_id}"
            
            if key not in execution_groups:
                execution_groups[key] = []
            execution_groups[key].append(execution)
        
        # Convert execution groups to trades
        for group_key, group_executions in execution_groups.items():
            if not group_executions:
                continue
                
            first_execution = group_executions[0]
            
            # Aggregate execution data
            total_quantity = sum(float(ex.get('quantity', 0)) for ex in group_executions)
            total_value = sum(float(ex.get('price', 0)) * float(ex.get('quantity', 0)) 
                            for ex in group_executions)
            avg_price = total_value / total_quantity if total_quantity > 0 else 0
            
            # Calculate commission
            total_commission = sum(float(ex.get('commission', 0)) for ex in group_executions)
            
            trade = {
                'symbol': first_execution.get('symbol', ''),
                'side': first_execution.get('side', ''),
                'quantity': total_quantity,
                'price': avg_price,
                'commission': total_commission,
                'execution_time': first_execution.get('execution_time', ''),
                'order_id': first_execution.get('order_id', ''),
                'account_id': first_execution.get('account_id', ''),
                'exchange': first_execution.get('exchange', ''),
                'currency': first_execution.get('currency', 'USD')
            }
            
            trades.append(trade)
        
        return trades
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Normalize IB trade data to universal format."""
        if not raw_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(raw_data)
        
        # Map IB fields to universal schema
        column_mapping = {
            'symbol': 'symbol',
            'side': 'direction',
            'quantity': 'qty',
            'price': 'entry_price',
            'commission': 'commission',
            'execution_time': 'entry_time',
            'order_id': 'trade_id',
            'currency': 'currency'
        }
        
        # Rename columns
        for ib_col, universal_col in column_mapping.items():
            if ib_col in df.columns:
                df[universal_col] = df[ib_col]
        
        # Standardize direction values
        if 'direction' in df.columns:
            direction_map = {'BUY': 'long', 'SELL': 'short'}
            df['direction'] = df['direction'].map(direction_map).fillna('long')
        
        # Convert timestamp format
        if 'entry_time' in df.columns:
            df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
        
        # Calculate P&L (placeholder - would need position data)
        df['pnl'] = 0.0  # IB requires separate position tracking for P&L
        df['exit_price'] = df['entry_price']  # Placeholder
        df['exit_time'] = df['entry_time']    # Placeholder
        
        # Ensure numeric columns
        numeric_cols = ['entry_price', 'exit_price', 'qty', 'pnl', 'commission']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def get_required_config(self) -> List[str]:
        """IB requires IB Gateway/TWS to be running locally."""
        return ['base_url']  # Usually https://localhost:5000/v1/api
    
    def get_optional_params(self) -> List[str]:
        """Optional parameters for IB API calls."""
        return ['account_id', 'days', 'exchange', 'currency']
