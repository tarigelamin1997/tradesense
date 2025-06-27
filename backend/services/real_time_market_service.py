
"""
Real-time Market Data Service for TradeSense
Provides live market feeds and real-time context for trades
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import websocket
import requests
from sqlalchemy.orm import Session
from backend.core.db.session import get_db
from backend.models.trade import Trade

logger = logging.getLogger(__name__)

class RealTimeMarketService:
    """Service for real-time market data integration"""
    
    def __init__(self):
        self.active_connections = {}
        self.market_data_cache = {}
        self.subscribers = {}
        
    async def get_live_quote(self, symbol: str) -> Dict[str, Any]:
        """Get live quote for a symbol"""
        try:
            # Using Alpha Vantage API (free tier)
            api_key = "demo"  # Replace with actual API key
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
            
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                return {
                    "symbol": symbol,
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%"),
                    "volume": int(quote.get("06. volume", 0)),
                    "timestamp": datetime.now().isoformat(),
                    "market_state": self._determine_market_state()
                }
        except Exception as e:
            logger.error(f"Error fetching live quote for {symbol}: {e}")
            
        return self._get_fallback_quote(symbol)
    
    def _determine_market_state(self) -> str:
        """Determine current market state"""
        now = datetime.now()
        hour = now.hour
        
        # Simple US market hours check (9:30 AM - 4:00 PM ET)
        if 9 <= hour < 16:
            return "open"
        elif 16 <= hour < 20:
            return "after_hours"
        else:
            return "closed"
    
    def _get_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback quote when API fails"""
        return {
            "symbol": symbol,
            "price": 100.0,  # Mock price
            "change": 0.5,
            "change_percent": "0.50%",
            "volume": 1000000,
            "timestamp": datetime.now().isoformat(),
            "market_state": "demo_mode"
        }
    
    async def get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get market sentiment indicators"""
        try:
            # Mock sentiment data - replace with real sentiment API
            sentiment_score = 0.65  # Range: -1 to 1
            
            return {
                "symbol": symbol,
                "sentiment_score": sentiment_score,
                "sentiment_label": self._get_sentiment_label(sentiment_score),
                "fear_greed_index": 45,  # 0-100 scale
                "volatility_percentile": 72,
                "news_sentiment": "neutral",
                "social_sentiment": "bullish",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching sentiment for {symbol}: {e}")
            return {"error": str(e)}
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.3:
            return "bullish"
        elif score < -0.3:
            return "bearish"
        else:
            return "neutral"
    
    async def get_market_regime(self) -> Dict[str, Any]:
        """Determine current market regime"""
        return {
            "regime": "trending",  # trending, ranging, volatile, calm
            "volatility_regime": "normal",  # low, normal, high, extreme
            "trend_strength": 0.7,  # 0-1 scale
            "support_level": 95.5,
            "resistance_level": 105.2,
            "market_phase": "mid_session",
            "timestamp": datetime.now().isoformat()
        }
    
    async def enhance_trade_with_market_context(self, trade_data: Dict) -> Dict:
        """Enhance trade data with real-time market context"""
        symbol = trade_data.get("symbol", "")
        
        if symbol:
            # Get live market data
            quote = await self.get_live_quote(symbol)
            sentiment = await self.get_market_sentiment(symbol)
            regime = await self.get_market_regime()
            
            # Add market context
            trade_data["market_context"] = {
                "live_quote": quote,
                "sentiment": sentiment,
                "regime": regime,
                "context_timestamp": datetime.now().isoformat()
            }
        
        return trade_data
    
    def subscribe_to_symbol(self, symbol: str, callback):
        """Subscribe to real-time updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
    
    async def start_real_time_feed(self, symbols: List[str]):
        """Start real-time data feed for symbols"""
        logger.info(f"Starting real-time feed for {symbols}")
        
        # Mock real-time feed - replace with actual WebSocket connection
        while True:
            for symbol in symbols:
                try:
                    quote = await self.get_live_quote(symbol)
                    
                    # Notify subscribers
                    if symbol in self.subscribers:
                        for callback in self.subscribers[symbol]:
                            await callback(quote)
                            
                except Exception as e:
                    logger.error(f"Error in real-time feed for {symbol}: {e}")
            
            await asyncio.sleep(5)  # Update every 5 seconds

# Global service instance
real_time_market_service = RealTimeMarketService()
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from backend.core.db.session import get_db
from backend.models.trade import Trade
import logging

logger = logging.getLogger(__name__)

class RealTimeMarketService:
    """Enhanced real-time market data service with multiple providers"""
    
    def __init__(self):
        self.active_subscriptions = {}
        self.market_cache = {}
        self.websocket_connections = {}
        
    async def connect_to_feed(self, provider: str = "alpha_vantage") -> bool:
        """Connect to real-time market data feed"""
        try:
            if provider == "alpha_vantage":
                return await self._connect_alpha_vantage()
            elif provider == "yahoo_finance":
                return await self._connect_yahoo_finance()
            elif provider == "polygon":
                return await self._connect_polygon()
            else:
                logger.error(f"Unsupported provider: {provider}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {provider}: {e}")
            return False
    
    async def _connect_alpha_vantage(self) -> bool:
        """Connect to Alpha Vantage real-time feed"""
        # Alpha Vantage WebSocket connection
        url = "wss://ws.finnhub.io/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    self.websocket_connections["alpha_vantage"] = ws
                    logger.info("Connected to Alpha Vantage WebSocket")
                    return True
        except Exception as e:
            logger.error(f"Alpha Vantage connection failed: {e}")
            return False
    
    async def _connect_yahoo_finance(self) -> bool:
        """Connect to Yahoo Finance data feed"""
        # Yahoo Finance doesn't have official WebSocket, using REST API polling
        self.websocket_connections["yahoo_finance"] = "polling"
        logger.info("Yahoo Finance polling mode enabled")
        return True
    
    async def _connect_polygon(self) -> bool:
        """Connect to Polygon.io WebSocket"""
        url = "wss://socket.polygon.io/stocks"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(url) as ws:
                    self.websocket_connections["polygon"] = ws
                    logger.info("Connected to Polygon WebSocket")
                    return True
        except Exception as e:
            logger.error(f"Polygon connection failed: {e}")
            return False
    
    async def subscribe_to_symbol(self, symbol: str, provider: str = "yahoo_finance") -> bool:
        """Subscribe to real-time data for a specific symbol"""
        try:
            if provider == "yahoo_finance":
                return await self._subscribe_yahoo(symbol)
            elif provider == "alpha_vantage":
                return await self._subscribe_alpha_vantage(symbol)
            elif provider == "polygon":
                return await self._subscribe_polygon(symbol)
            return False
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol} on {provider}: {e}")
            return False
    
    async def _subscribe_yahoo(self, symbol: str) -> bool:
        """Subscribe to Yahoo Finance data"""
        self.active_subscriptions[symbol] = {
            "provider": "yahoo_finance",
            "subscribed_at": datetime.now(timezone.utc),
            "last_update": None
        }
        
        # Start polling task
        asyncio.create_task(self._poll_yahoo_data(symbol))
        logger.info(f"Subscribed to {symbol} on Yahoo Finance")
        return True
    
    async def _poll_yahoo_data(self, symbol: str):
        """Poll Yahoo Finance API for data"""
        while symbol in self.active_subscriptions:
            try:
                # Simulate API call to Yahoo Finance
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            await self._process_market_data(symbol, data, "yahoo_finance")
                
                # Wait 5 seconds before next poll
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error polling Yahoo data for {symbol}: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _process_market_data(self, symbol: str, data: Dict, provider: str):
        """Process incoming market data"""
        try:
            # Extract relevant data based on provider
            if provider == "yahoo_finance":
                processed_data = self._process_yahoo_data(data)
            elif provider == "alpha_vantage":
                processed_data = self._process_alpha_vantage_data(data)
            elif provider == "polygon":
                processed_data = self._process_polygon_data(data)
            else:
                return
            
            # Update cache
            self.market_cache[symbol] = {
                "data": processed_data,
                "timestamp": datetime.now(timezone.utc),
                "provider": provider
            }
            
            # Update subscription
            if symbol in self.active_subscriptions:
                self.active_subscriptions[symbol]["last_update"] = datetime.now(timezone.utc)
            
            logger.debug(f"Updated market data for {symbol} from {provider}")
            
        except Exception as e:
            logger.error(f"Error processing market data for {symbol}: {e}")
    
    def _process_yahoo_data(self, data: Dict) -> Dict:
        """Process Yahoo Finance data format"""
        try:
            chart = data.get("chart", {}).get("result", [{}])[0]
            meta = chart.get("meta", {})
            
            return {
                "symbol": meta.get("symbol"),
                "price": meta.get("regularMarketPrice"),
                "change": meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0),
                "change_percent": ((meta.get("regularMarketPrice", 0) - meta.get("previousClose", 1)) / meta.get("previousClose", 1)) * 100,
                "volume": meta.get("regularMarketVolume"),
                "market_cap": meta.get("marketCap"),
                "pe_ratio": meta.get("trailingPE"),
                "fifty_two_week_high": meta.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": meta.get("fiftyTwoWeekLow"),
                "market_state": meta.get("marketState", "REGULAR")
            }
        except Exception as e:
            logger.error(f"Error processing Yahoo data: {e}")
            return {}
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get cached market data for symbol"""
        return self.market_cache.get(symbol)
    
    def get_all_subscriptions(self) -> Dict:
        """Get all active subscriptions"""
        return self.active_subscriptions.copy()
    
    async def unsubscribe_from_symbol(self, symbol: str) -> bool:
        """Unsubscribe from symbol"""
        if symbol in self.active_subscriptions:
            del self.active_subscriptions[symbol]
            if symbol in self.market_cache:
                del self.market_cache[symbol]
            logger.info(f"Unsubscribed from {symbol}")
            return True
        return False
    
    async def get_market_context_for_trade(self, symbol: str, trade_time: datetime) -> Dict:
        """Get market context around trade time"""
        try:
            # Get current market data
            current_data = self.get_market_data(symbol)
            if not current_data:
                # Subscribe if not already subscribed
                await self.subscribe_to_symbol(symbol)
                await asyncio.sleep(2)  # Wait for initial data
                current_data = self.get_market_data(symbol)
            
            return {
                "symbol": symbol,
                "trade_time": trade_time,
                "market_price_at_analysis": current_data.get("price") if current_data else None,
                "market_state": current_data.get("market_state", "UNKNOWN") if current_data else "UNKNOWN",
                "volume": current_data.get("volume") if current_data else None,
                "volatility_indicator": self._calculate_volatility_indicator(current_data) if current_data else None,
                "market_trend": self._determine_market_trend(current_data) if current_data else None,
                "support_resistance": self._calculate_support_resistance(symbol) if current_data else None
            }
        except Exception as e:
            logger.error(f"Error getting market context for {symbol}: {e}")
            return {"error": str(e)}
    
    def _calculate_volatility_indicator(self, market_data: Dict) -> str:
        """Calculate volatility indicator from market data"""
        try:
            change_percent = abs(market_data.get("change_percent", 0))
            if change_percent > 5:
                return "HIGH"
            elif change_percent > 2:
                return "MEDIUM"
            else:
                return "LOW"
        except:
            return "UNKNOWN"
    
    def _determine_market_trend(self, market_data: Dict) -> str:
        """Determine market trend from data"""
        try:
            change_percent = market_data.get("change_percent", 0)
            if change_percent > 1:
                return "BULLISH"
            elif change_percent < -1:
                return "BEARISH"
            else:
                return "SIDEWAYS"
        except:
            return "UNKNOWN"
    
    def _calculate_support_resistance(self, symbol: str) -> Dict:
        """Calculate basic support and resistance levels"""
        try:
            market_data = self.get_market_data(symbol)
            if not market_data:
                return {}
            
            current_price = market_data.get("price", 0)
            high_52w = market_data.get("fifty_two_week_high", current_price)
            low_52w = market_data.get("fifty_two_week_low", current_price)
            
            # Simple support/resistance calculation
            resistance = current_price + (high_52w - current_price) * 0.3
            support = current_price - (current_price - low_52w) * 0.3
            
            return {
                "support": round(support, 2),
                "resistance": round(resistance, 2),
                "current_price": current_price,
                "distance_to_support": round(((current_price - support) / current_price) * 100, 2),
                "distance_to_resistance": round(((resistance - current_price) / current_price) * 100, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating support/resistance for {symbol}: {e}")
            return {}

# Global instance
market_service = RealTimeMarketService()
