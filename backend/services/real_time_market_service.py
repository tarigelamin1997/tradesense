
import asyncio
import websockets
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiohttp
from sqlalchemy.orm import Session
from backend.core.db.session import get_db

@dataclass
class MarketData:
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    change_percent: Optional[float] = None

@dataclass
class MarketSentiment:
    symbol: str
    sentiment_score: float  # -1 to 1
    fear_greed_index: int   # 0 to 100
    volatility_index: float
    news_sentiment: float
    timestamp: datetime

class RealTimeMarketService:
    def __init__(self):
        self.active_subscriptions: Dict[str, List[Callable]] = {}
        self.market_data_cache: Dict[str, MarketData] = {}
        self.sentiment_cache: Dict[str, MarketSentiment] = {}
        self.logger = logging.getLogger(__name__)
        self.ws_connection = None
        
    async def connect_to_feed(self):
        """Connect to real-time market data feed"""
        try:
            # Using Alpha Vantage WebSocket (free tier available)
            self.ws_connection = await websockets.connect(
                "wss://ws.finnhub.io?token=YOUR_API_KEY"
            )
            self.logger.info("Connected to real-time market data feed")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_updates())
            
        except Exception as e:
            self.logger.error(f"Failed to connect to market feed: {e}")
            # Fallback to polling mode
            asyncio.create_task(self._polling_fallback())
    
    async def _listen_for_updates(self):
        """Listen for WebSocket updates"""
        try:
            async for message in self.ws_connection:
                data = json.loads(message)
                await self._process_market_update(data)
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
            await self._polling_fallback()
    
    async def _polling_fallback(self):
        """Fallback to polling when WebSocket fails"""
        while True:
            try:
                await self._fetch_market_data_batch()
                await asyncio.sleep(30)  # Poll every 30 seconds
            except Exception as e:
                self.logger.error(f"Polling error: {e}")
                await asyncio.sleep(60)
    
    async def _fetch_market_data_batch(self):
        """Fetch market data for all subscribed symbols"""
        if not self.active_subscriptions:
            return
            
        symbols = list(self.active_subscriptions.keys())
        
        # Batch fetch from Alpha Vantage
        async with aiohttp.ClientSession() as session:
            for symbol in symbols:
                try:
                    url = f"https://www.alphavantage.co/query"
                    params = {
                        'function': 'GLOBAL_QUOTE',
                        'symbol': symbol,
                        'apikey': 'YOUR_API_KEY'
                    }
                    
                    async with session.get(url, params=params) as response:
                        data = await response.json()
                        await self._process_alpha_vantage_data(symbol, data)
                        
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {e}")
    
    async def _process_market_update(self, data: dict):
        """Process incoming market data update"""
        try:
            if data.get('type') == 'trade':
                symbol = data.get('s')
                price = float(data.get('p', 0))
                volume = int(data.get('v', 0))
                
                market_data = MarketData(
                    symbol=symbol,
                    price=price,
                    volume=volume,
                    timestamp=datetime.now()
                )
                
                self.market_data_cache[symbol] = market_data
                await self._notify_subscribers(symbol, market_data)
                
        except Exception as e:
            self.logger.error(f"Error processing market update: {e}")
    
    async def _process_alpha_vantage_data(self, symbol: str, data: dict):
        """Process Alpha Vantage API response"""
        try:
            quote = data.get('Global Quote', {})
            if not quote:
                return
                
            price = float(quote.get('05. price', 0))
            change_percent = float(quote.get('10. change percent', '0%').rstrip('%'))
            
            market_data = MarketData(
                symbol=symbol,
                price=price,
                volume=0,  # Not available in global quote
                change_percent=change_percent,
                timestamp=datetime.now()
            )
            
            self.market_data_cache[symbol] = market_data
            await self._notify_subscribers(symbol, market_data)
            
        except Exception as e:
            self.logger.error(f"Error processing Alpha Vantage data: {e}")
    
    async def _notify_subscribers(self, symbol: str, data: MarketData):
        """Notify all subscribers of symbol updates"""
        if symbol in self.active_subscriptions:
            for callback in self.active_subscriptions[symbol]:
                try:
                    await callback(data)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback: {e}")
    
    def subscribe_to_symbol(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates for a symbol"""
        if symbol not in self.active_subscriptions:
            self.active_subscriptions[symbol] = []
        
        self.active_subscriptions[symbol].append(callback)
        
        # If WebSocket is connected, subscribe to the symbol
        if self.ws_connection:
            asyncio.create_task(self._subscribe_websocket_symbol(symbol))
    
    async def _subscribe_websocket_symbol(self, symbol: str):
        """Subscribe to symbol via WebSocket"""
        try:
            subscribe_msg = {
                'type': 'subscribe',
                'symbol': symbol
            }
            await self.ws_connection.send(json.dumps(subscribe_msg))
        except Exception as e:
            self.logger.error(f"Error subscribing to {symbol}: {e}")
    
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
        """Get current cached price for symbol"""
        if symbol in self.market_data_cache:
            return self.market_data_cache[symbol].price
        return None
    
    def get_market_sentiment(self, symbol: str) -> Optional[MarketSentiment]:
        """Get current market sentiment for symbol"""
        return self.sentiment_cache.get(symbol)
    
    async def fetch_market_sentiment(self, symbol: str) -> MarketSentiment:
        """Fetch current market sentiment data"""
        try:
            # Simulate sentiment analysis (in production, use real APIs)
            sentiment = MarketSentiment(
                symbol=symbol,
                sentiment_score=0.1,  # Slightly bullish
                fear_greed_index=55,  # Neutral
                volatility_index=0.25,
                news_sentiment=0.05,
                timestamp=datetime.now()
            )
            
            self.sentiment_cache[symbol] = sentiment
            return sentiment
            
        except Exception as e:
            self.logger.error(f"Error fetching sentiment for {symbol}: {e}")
            return MarketSentiment(
                symbol=symbol,
                sentiment_score=0.0,
                fear_greed_index=50,
                volatility_index=0.2,
                news_sentiment=0.0,
                timestamp=datetime.now()
            )
    
    async def get_trade_context(self, symbol: str, entry_time: datetime) -> Dict:
        """Get market context at time of trade entry"""
        market_data = self.market_data_cache.get(symbol)
        sentiment = await self.fetch_market_sentiment(symbol)
        
        return {
            'current_price': market_data.price if market_data else None,
            'price_change_percent': market_data.change_percent if market_data else None,
            'sentiment_score': sentiment.sentiment_score,
            'fear_greed_index': sentiment.fear_greed_index,
            'volatility_index': sentiment.volatility_index,
            'market_hours': self._is_market_hours(),
            'session_type': self._get_market_session()
        }
    
    def _is_market_hours(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        # Simplified - assumes EST market hours
        if now.weekday() >= 5:  # Weekend
            return False
        
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def _get_market_session(self) -> str:
        """Get current market session type"""
        now = datetime.now()
        hour = now.hour
        
        if 4 <= hour < 9:
            return "pre_market"
        elif 9 <= hour < 16:
            return "regular"
        elif 16 <= hour < 20:
            return "after_hours"
        else:
            return "closed"

# Global instance
market_service = RealTimeMarketService()
