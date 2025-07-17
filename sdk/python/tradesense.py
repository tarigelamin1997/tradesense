"""
TradeSense Python SDK
Official Python client for the TradeSense API
"""

import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import json
from urllib.parse import urljoin, urlencode


class TradeSenseError(Exception):
    """Base exception for TradeSense SDK errors."""
    pass


class AuthenticationError(TradeSenseError):
    """Raised when authentication fails."""
    pass


class APIError(TradeSenseError):
    """Raised when API returns an error."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TradeSenseClient:
    """Main client for interacting with the TradeSense API."""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.tradesense.com"):
        """
        Initialize the TradeSense client.
        
        Args:
            api_key: Your TradeSense API key (or use environment variable TRADESENSE_API_KEY)
            base_url: Base URL for the API (default: https://api.tradesense.com)
        """
        self.api_key = api_key or os.environ.get('TRADESENSE_API_KEY')
        if not self.api_key:
            raise AuthenticationError("API key is required")
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'TradeSense-Python-SDK/1.0.0'
        })
        
        # Initialize sub-clients
        self.trades = TradesClient(self)
        self.analytics = AnalyticsClient(self)
        self.journal = JournalClient(self)
        self.account = AccountClient(self)
        self.experiments = ExperimentsClient(self)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Union[Dict, List]:
        """Make an HTTP request to the API."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid API key or authentication failed")
            
            error_msg = f"API request failed: {e}"
            if e.response.content:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
            
            raise APIError(error_msg, e.response.status_code, e.response.json() if e.response.content else None)
        
        except requests.exceptions.RequestException as e:
            raise TradeSenseError(f"Request failed: {e}")
    
    def get(self, endpoint: str, params: Dict = None) -> Union[Dict, List]:
        """Make a GET request."""
        return self._request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict = None) -> Union[Dict, List]:
        """Make a POST request."""
        return self._request('POST', endpoint, json=data)
    
    def put(self, endpoint: str, data: Dict = None) -> Union[Dict, List]:
        """Make a PUT request."""
        return self._request('PUT', endpoint, json=data)
    
    def delete(self, endpoint: str) -> Union[Dict, List]:
        """Make a DELETE request."""
        return self._request('DELETE', endpoint)


class TradesClient:
    """Client for trade-related operations."""
    
    def __init__(self, client: TradeSenseClient):
        self.client = client
    
    def list(self, 
             start_date: Optional[str] = None,
             end_date: Optional[str] = None,
             symbol: Optional[str] = None,
             limit: int = 100,
             offset: int = 0) -> List[Dict]:
        """List trades with optional filters."""
        params = {
            'limit': limit,
            'offset': offset
        }
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if symbol:
            params['symbol'] = symbol
        
        return self.client.get('/api/v1/trades', params=params)
    
    def create(self, trade: Dict) -> Dict:
        """Create a new trade."""
        required_fields = ['symbol', 'entry_date', 'entry_price', 'quantity', 'trade_type']
        for field in required_fields:
            if field not in trade:
                raise ValueError(f"Missing required field: {field}")
        
        return self.client.post('/api/v1/trades', data=trade)
    
    def get(self, trade_id: str) -> Dict:
        """Get a specific trade by ID."""
        return self.client.get(f'/api/v1/trades/{trade_id}')
    
    def update(self, trade_id: str, updates: Dict) -> Dict:
        """Update an existing trade."""
        return self.client.put(f'/api/v1/trades/{trade_id}', data=updates)
    
    def delete(self, trade_id: str) -> Dict:
        """Delete a trade."""
        return self.client.delete(f'/api/v1/trades/{trade_id}')
    
    def bulk_create(self, trades: List[Dict]) -> Dict:
        """Create multiple trades at once."""
        return self.client.post('/api/v1/trades/bulk', data={'trades': trades})
    
    def import_csv(self, file_path: str, broker: str = 'generic') -> Dict:
        """Import trades from a CSV file."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            # Temporarily remove Content-Type header for multipart upload
            headers = self.client.session.headers.copy()
            del headers['Content-Type']
            
            response = requests.post(
                f"{self.client.base_url}/api/v1/trades/import",
                headers=headers,
                files=files,
                data={'broker': broker}
            )
            response.raise_for_status()
            return response.json()


class AnalyticsClient:
    """Client for analytics operations."""
    
    def __init__(self, client: TradeSenseClient):
        self.client = client
    
    def overview(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Get analytics overview."""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return self.client.get('/api/v1/analytics/overview', params=params)
    
    def performance(self, timeframe: str = 'all') -> Dict:
        """Get performance metrics."""
        return self.client.get('/api/v1/analytics/performance', params={'timeframe': timeframe})
    
    def win_loss(self) -> Dict:
        """Get win/loss analysis."""
        return self.client.get('/api/v1/analytics/win-loss')
    
    def by_symbol(self) -> List[Dict]:
        """Get analytics grouped by symbol."""
        return self.client.get('/api/v1/analytics/by-symbol')
    
    def by_day_of_week(self) -> Dict:
        """Get analytics by day of week."""
        return self.client.get('/api/v1/analytics/by-day')
    
    def by_time_of_day(self) -> Dict:
        """Get analytics by time of day."""
        return self.client.get('/api/v1/analytics/by-hour')
    
    def streaks(self) -> Dict:
        """Get winning/losing streak analysis."""
        return self.client.get('/api/v1/analytics/streaks')
    
    def risk_metrics(self) -> Dict:
        """Get risk analysis metrics."""
        return self.client.get('/api/v1/analytics/risk')


class JournalClient:
    """Client for journal operations."""
    
    def __init__(self, client: TradeSenseClient):
        self.client = client
    
    def list(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List journal entries."""
        return self.client.get('/api/v1/journal', params={'limit': limit, 'offset': offset})
    
    def create(self, title: str, content: str, mood: Optional[str] = None, tags: List[str] = None) -> Dict:
        """Create a journal entry."""
        data = {
            'title': title,
            'content': content
        }
        if mood:
            data['mood'] = mood
        if tags:
            data['tags'] = tags
        
        return self.client.post('/api/v1/journal', data=data)
    
    def get(self, entry_id: str) -> Dict:
        """Get a specific journal entry."""
        return self.client.get(f'/api/v1/journal/{entry_id}')
    
    def update(self, entry_id: str, updates: Dict) -> Dict:
        """Update a journal entry."""
        return self.client.put(f'/api/v1/journal/{entry_id}', data=updates)
    
    def delete(self, entry_id: str) -> Dict:
        """Delete a journal entry."""
        return self.client.delete(f'/api/v1/journal/{entry_id}')
    
    def search(self, query: str) -> List[Dict]:
        """Search journal entries."""
        return self.client.get('/api/v1/journal/search', params={'q': query})


class AccountClient:
    """Client for account operations."""
    
    def __init__(self, client: TradeSenseClient):
        self.client = client
    
    def profile(self) -> Dict:
        """Get user profile information."""
        return self.client.get('/api/v1/account/profile')
    
    def update_profile(self, updates: Dict) -> Dict:
        """Update user profile."""
        return self.client.put('/api/v1/account/profile', data=updates)
    
    def subscription(self) -> Dict:
        """Get subscription information."""
        return self.client.get('/api/v1/subscription/status')
    
    def usage(self) -> Dict:
        """Get API usage statistics."""
        return self.client.get('/api/v1/account/usage')
    
    def api_keys(self) -> List[Dict]:
        """List API keys."""
        return self.client.get('/api/v1/account/api-keys')
    
    def create_api_key(self, name: str, permissions: List[str] = None) -> Dict:
        """Create a new API key."""
        data = {'name': name}
        if permissions:
            data['permissions'] = permissions
        
        return self.client.post('/api/v1/account/api-keys', data=data)
    
    def revoke_api_key(self, key_id: str) -> Dict:
        """Revoke an API key."""
        return self.client.delete(f'/api/v1/account/api-keys/{key_id}')


class ExperimentsClient:
    """Client for A/B testing operations."""
    
    def __init__(self, client: TradeSenseClient):
        self.client = client
    
    def get_assignments(self) -> List[Dict]:
        """Get experiment assignments for current user."""
        return self.client.get('/api/v1/experiments/assignments')
    
    def get_variant(self, experiment_id: str) -> Optional[Dict]:
        """Get variant assignment for specific experiment."""
        return self.client.get(f'/api/v1/experiments/assignment/{experiment_id}')
    
    def track_conversion(self, experiment_id: str, metric_id: str, value: float = 1.0, metadata: Dict = None) -> Dict:
        """Track a conversion event."""
        data = {
            'experiment_id': experiment_id,
            'metric_id': metric_id,
            'value': value
        }
        if metadata:
            data['metadata'] = metadata
        
        return self.client.post('/api/v1/experiments/track', data=data)


# Convenience functions
def create_client(api_key: str = None) -> TradeSenseClient:
    """Create a TradeSense client instance."""
    return TradeSenseClient(api_key)


# Example usage
if __name__ == "__main__":
    import os
    
    # Initialize client
    client = TradeSenseClient(api_key="your-api-key-here")
    
    # List recent trades
    trades = client.trades.list(limit=10)
    print(f"Found {len(trades)} trades")
    
    # Create a new trade
    new_trade = client.trades.create({
        'symbol': 'AAPL',
        'entry_date': '2024-01-15',
        'entry_price': 150.50,
        'quantity': 100,
        'trade_type': 'long'
    })
    print(f"Created trade: {new_trade['id']}")
    
    # Get analytics
    overview = client.analytics.overview()
    print(f"Total P&L: ${overview['total_pnl']:.2f}")
    print(f"Win Rate: {overview['win_rate']:.1%}")
    
    # Create journal entry
    entry = client.journal.create(
        title="Market Analysis",
        content="Today's market showed strong bullish momentum...",
        mood="confident",
        tags=["analysis", "bullish"]
    )
    print(f"Created journal entry: {entry['id']}")
    
    # Check A/B test assignment
    variant = client.experiments.get_variant('pricing_page_v2')
    if variant:
        print(f"Assigned to variant: {variant['variant_name']}")


import os