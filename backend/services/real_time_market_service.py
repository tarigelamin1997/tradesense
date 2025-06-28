import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class RealTimeMarketService:
    """Real-time market data service for TradeSense."""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.is_running = False
        self.market_data: Dict[str, Dict] = {}

    async def start(self):
        """Start the real-time market data service."""
        self.is_running = True
        logger.info("Real-time market service started")

        # Start background tasks
        asyncio.create_task(self._fetch_market_data())
        asyncio.create_task(self._broadcast_updates())

    async def stop(self):
        """Stop the real-time market data service."""
        self.is_running = False
        logger.info("Real-time market service stopped")

    def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates for a symbol."""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)

        # Send current data if available
        if symbol in self.market_data:
            callback(symbol, self.market_data[symbol])

    def unsubscribe(self, symbol: str, callback: Callable):
        """Unsubscribe from real-time updates."""
        if symbol in self.subscribers:
            if callback in self.subscribers[symbol]:
                self.subscribers[symbol].remove(callback)

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        data = self.market_data.get(symbol)
        return data.get('price') if data else None

    async def get_market_summary(self) -> Dict:
        """Get current market summary."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'market_status': 'open' if self._is_market_open() else 'closed',
            'indices': {},
            'volatility': {}
        }

        # Add major indices
        for symbol in ['SPY', 'QQQ', 'IWM', 'VIX']:
            if symbol in self.market_data:
                summary['indices'][symbol] = self.market_data[symbol]

        return summary

    async def _fetch_market_data(self):
        """Background task to fetch market data."""
        while self.is_running:
            try:
                # Simulate market data updates
                await self._simulate_market_data()
                await asyncio.sleep(1)  # Update every second

            except Exception as e:
                logger.error(f"Error fetching market data: {e}")
                await asyncio.sleep(5)

    async def _simulate_market_data(self):
        """Simulate real-time market data (replace with actual data source)."""
        import random

        symbols = ['SPY', 'QQQ', 'IWM', 'VIX', 'AAPL', 'MSFT', 'GOOGL', 'TSLA']

        for symbol in symbols:
            if symbol not in self.market_data:
                base_price = {'SPY': 450, 'QQQ': 350, 'IWM': 180, 'VIX': 20, 
                            'AAPL': 180, 'MSFT': 350, 'GOOGL': 140, 'TSLA': 250}
                self.market_data[symbol] = {
                    'price': base_price.get(symbol, 100),
                    'volume': random.randint(1000000, 10000000),
                    'timestamp': datetime.now().isoformat()
                }

            # Simulate price movement
            current = self.market_data[symbol]['price']
            change = random.uniform(-0.02, 0.02)  # ±2% movement
            new_price = max(current * (1 + change), 0.01)

            self.market_data[symbol].update({
                'price': round(new_price, 2),
                'change': round(new_price - current, 2),
                'change_pct': round((new_price - current) / current * 100, 3),
                'volume': self.market_data[symbol]['volume'] + random.randint(1000, 10000),
                'timestamp': datetime.now().isoformat()
            })

    async def _broadcast_updates(self):
        """Broadcast updates to subscribers."""
        while self.is_running:
            try:
                for symbol, callbacks in self.subscribers.items():
                    if symbol in self.market_data:
                        data = self.market_data[symbol]
                        for callback in callbacks:
                            try:
                                callback(symbol, data)
                            except Exception as e:
                                logger.error(f"Error in callback for {symbol}: {e}")

                await asyncio.sleep(0.1)  # Broadcast every 100ms

            except Exception as e:
                logger.error(f"Error broadcasting updates: {e}")
                await asyncio.sleep(1)

    def _is_market_open(self) -> bool:
        """Check if market is currently open (simplified)."""
        now = datetime.now()
        # Simplified: Monday-Friday, 9:30 AM - 4:00 PM ET
        if now.weekday() >= 5:  # Weekend
            return False

        hour = now.hour
        return 9 <= hour < 16

# Global instance
real_time_market_service = RealTimeMarketService()