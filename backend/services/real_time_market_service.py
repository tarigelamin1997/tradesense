import asyncio
import json
import logging
import websockets
from typing import Dict, List, Callable, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    change_percent: float
    bid: float
    ask: float

@dataclass
class MarketSentiment:
    symbol: str
    sentiment_score: float  # -1 to 1
    news_count: int
    social_mentions: int
    analyst_rating: str
    timestamp: datetime

class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_vol"
    LOW_VOLATILITY = "low_vol"

class RealTimeMarketService:
    def __init__(self):
        self.active_subscriptions: Dict[str, List[Callable]] = {}
        self.market_data_cache: Dict[str, MarketData] = {}
        self.sentiment_cache: Dict[str, MarketSentiment] = {}
        self.logger = logging.getLogger(__name__)
        self.ws_connection = None
        self.is_connected = False

    async def connect_to_feed(self):
        """Connect to real-time market data feed"""
        try:
            # For demo purposes, we'll simulate the connection
            # In production, this would connect to Alpha Vantage, IEX Cloud, etc.
            self.is_connected = True
            self.logger.info("Connected to real-time market data feed")

            # Start the simulation
            asyncio.create_task(self._simulate_market_data())

        except Exception as e:
            self.logger.error(f"Failed to connect to market feed: {e}")
            await self._polling_fallback()

    async def _simulate_market_data(self):
        """Simulate real-time market data for demo"""
        import random

        symbols = ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN']
        base_prices = {
            'SPY': 450.0, 'QQQ': 380.0, 'AAPL': 175.0, 'TSLA': 250.0,
            'NVDA': 420.0, 'MSFT': 340.0, 'GOOGL': 140.0, 'AMZN': 150.0
        }

        while self.is_connected:
            for symbol in symbols:
                # Simulate price movement
                base_price = base_prices[symbol]
                price_change = random.uniform(-0.02, 0.02)  # ±2% movement
                new_price = base_price * (1 + price_change)

                market_data = MarketData(
                    symbol=symbol,
                    price=new_price,
                    volume=random.randint(1000, 50000),
                    timestamp=datetime.now(),
                    change_percent=price_change * 100,
                    bid=new_price - 0.01,
                    ask=new_price + 0.01
                )

                await self._process_market_update(market_data)

            await asyncio.sleep(1)  # Update every second

    async def _process_market_update(self, self, data: MarketData):
        """Process incoming market data and notify subscribers"""
        self.market_data_cache[data.symbol] = data

        # Notify subscribers
        if data.symbol in self.active_subscriptions:
            for callback in self.active_subscriptions[data.symbol]:
                try:
                    await callback(data)
                except Exception as e:
                    self.logger.error(f"Error in market data callback: {e}")

    async def subscribe_to_symbol(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates for a specific symbol"""
        if symbol not in self.active_subscriptions:
            self.active_subscriptions[symbol] = []

        self.active_subscriptions[symbol].append(callback)

        # Send current data if available
        if symbol in self.market_data_cache:
            await callback(self.market_data_cache[symbol])

    def unsubscribe_from_symbol(self, symbol: str, callback: Callable):
        """Unsubscribe from symbol updates"""
        if symbol in self.active_subscriptions:
            try:
                self.active_subscriptions[symbol].remove(callback)
                if not self.active_subscriptions[symbol]:
                    del self.active_subscriptions[symbol]
            except ValueError:
                pass

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if symbol in self.market_data_cache:
            return self.market_data_cache[symbol].price
        return None

    def get_market_sentiment(self, symbol: str) -> Optional[MarketSentiment]:
        """Get market sentiment for a symbol"""
        # Simulate sentiment data
        import random

        sentiment = MarketSentiment(
            symbol=symbol,
            sentiment_score=random.uniform(-1, 1),
            news_count=random.randint(0, 20),
            social_mentions=random.randint(0, 1000),
            analyst_rating=random.choice(['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']),
            timestamp=datetime.now()
        )

        self.sentiment_cache[symbol] = sentiment
        return sentiment

    def detect_market_regime(self) -> Dict[str, any]:
        """Detect current market regime based on price action"""
        # Simplified regime detection
        spy_data = self.market_data_cache.get('SPY')
        if not spy_data:
            return {'regime': MarketRegime.SIDEWAYS, 'confidence': 0.5}

        # Simple regime detection based on price change
        if spy_data.change_percent > 1.0:
            regime = MarketRegime.BULL
            confidence = min(abs(spy_data.change_percent) / 2.0, 1.0)
        elif spy_data.change_percent < -1.0:
            regime = MarketRegime.BEAR
            confidence = min(abs(spy_data.change_percent) / 2.0, 1.0)
        else:
            regime = MarketRegime.SIDEWAYS
            confidence = 0.7

        return {
            'regime': regime,
            'confidence': confidence,
            'volatility': abs(spy_data.change_percent),
            'last_update': spy_data.timestamp
        }

    async def _polling_fallback(self):
        """Fallback to polling when WebSocket fails"""
        self.logger.info("Using polling fallback for market data")
        while True:
            try:
                # Simulate polling data
                await self._simulate_market_data()
                await asyncio.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                self.logger.error(f"Polling error: {e}")
                await asyncio.sleep(10)

# Global instance
market_service = RealTimeMarketService()