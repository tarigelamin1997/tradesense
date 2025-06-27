
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
