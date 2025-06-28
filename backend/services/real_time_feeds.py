
import asyncio
import websockets
import json
from typing import Dict, List, Callable
from datetime import datetime
import logging
from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RealTimeMarketFeed:
    """Real-time market data feed manager"""
    
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.active_symbols: set = set()
        
    async def connect_to_data_provider(self):
        """Connect to market data provider (e.g., Alpha Vantage, IEX Cloud)"""
        try:
            # Example: Alpha Vantage WebSocket connection
            uri = f"wss://ws.finnhub.io?token={settings.FINNHUB_API_KEY}"
            self.websocket = await websockets.connect(uri)
            logger.info("Connected to Finnhub WebSocket")
            
            # Start listening for messages
            await self._listen_for_updates()
            
        except Exception as e:
            logger.error(f"Failed to connect to market data: {e}")
            
    async def _listen_for_updates(self):
        """Listen for real-time market updates"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_market_update(data)
        except Exception as e:
            logger.error(f"Error listening for updates: {e}")
            
    async def _process_market_update(self, data: dict):
        """Process incoming market data and notify subscribers"""
        if data.get('type') == 'trade':
            symbol = data.get('s', '').upper()
            price = data.get('p', 0)
            volume = data.get('v', 0)
            timestamp = data.get('t', int(datetime.now().timestamp() * 1000))
            
            market_update = {
                'symbol': symbol,
                'price': price,
                'volume': volume,
                'timestamp': timestamp,
                'change': self._calculate_change(symbol, price)
            }
            
            # Notify all subscribers
            if symbol in self.subscribers:
                for callback in self.subscribers[symbol]:
                    await callback(market_update)
                    
    def subscribe_to_symbol(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        self.active_symbols.add(symbol)
        
        # Send subscription message to data provider
        subscription_msg = {
            'type': 'subscribe',
            'symbol': symbol
        }
        asyncio.create_task(self._send_subscription(subscription_msg))
        
    async def _send_subscription(self, msg: dict):
        """Send subscription message to data provider"""
        try:
            await self.websocket.send(json.dumps(msg))
        except Exception as e:
            logger.error(f"Failed to send subscription: {e}")
            
    def _calculate_change(self, symbol: str, current_price: float) -> dict:
        """Calculate price change and percentage"""
        # This would typically use previous price from cache/database
        # Simplified for demonstration
        return {
            'absolute': 0.0,
            'percentage': 0.0,
            'direction': 'neutral'
        }

# Global instance
market_feed = RealTimeMarketFeed()
