
import asyncio
import websockets
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiohttp
from cachetools import TTLCache

from backend.models.trade import Trade
from backend.db.connection import get_db

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    symbol: str
    price: float
    volume: int
    change: float
    change_percent: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None

@dataclass
class MarketSentiment:
    symbol: str
    sentiment_score: float  # -1 to 1
    volatility: float
    momentum: float
    support_level: float
    resistance_level: float
    trend_direction: str

class RealTimeMarketService:
    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=60)  # 1-minute cache
        self.subscribers = {}
        self.active_connections = set()
        self.market_data = {}
        self.sentiment_data = {}
        
        # Demo mode - simulate real market data
        self.demo_mode = True
        
    async def start_market_feed(self):
        """Start the real-time market data feed"""
        if self.demo_mode:
            await self._start_demo_feed()
        else:
            await self._start_live_feed()
    
    async def _start_demo_feed(self):
        """Simulate real-time market data for demo purposes"""
        symbols = ["AAPL", "TSLA", "NVDA", "SPY", "QQQ", "MSFT", "GOOGL", "AMZN"]
        
        # Initialize base prices
        base_prices = {
            "AAPL": 175.50, "TSLA": 245.30, "NVDA": 465.20,
            "SPY": 445.80, "QQQ": 385.40, "MSFT": 420.15,
            "GOOGL": 2850.75, "AMZN": 3100.25
        }
        
        while True:
            try:
                for symbol in symbols:
                    # Simulate price movement
                    base_price = base_prices[symbol]
                    price_change = (asyncio.get_event_loop().time() % 10 - 5) * 0.02
                    current_price = base_price * (1 + price_change)
                    
                    market_data = MarketData(
                        symbol=symbol,
                        price=round(current_price, 2),
                        volume=int(1000000 + (asyncio.get_event_loop().time() % 1000) * 1000),
                        change=round(current_price - base_price, 2),
                        change_percent=round(price_change * 100, 2),
                        timestamp=datetime.now(),
                        bid=round(current_price - 0.01, 2),
                        ask=round(current_price + 0.01, 2),
                        high=round(current_price * 1.002, 2),
                        low=round(current_price * 0.998, 2)
                    )
                    
                    self.market_data[symbol] = market_data
                    
                    # Generate sentiment data
                    sentiment = MarketSentiment(
                        symbol=symbol,
                        sentiment_score=round((asyncio.get_event_loop().time() % 20 - 10) / 10, 2),
                        volatility=round(abs(price_change) * 10, 2),
                        momentum=round(price_change * 5, 2),
                        support_level=round(current_price * 0.98, 2),
                        resistance_level=round(current_price * 1.02, 2),
                        trend_direction="bullish" if price_change > 0 else "bearish"
                    )
                    
                    self.sentiment_data[symbol] = sentiment
                    
                    # Notify subscribers
                    await self._notify_subscribers(symbol, market_data, sentiment)
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in demo feed: {e}")
                await asyncio.sleep(5)
    
    async def _start_live_feed(self):
        """Connect to actual market data providers (Alpha Vantage, IEX, etc.)"""
        # Implementation for real market data feeds
        # This would connect to actual APIs like Alpha Vantage, IEX Cloud, etc.
        pass
    
    async def _notify_subscribers(self, symbol: str, market_data: MarketData, sentiment: MarketSentiment):
        """Notify all subscribers about market data updates"""
        if symbol in self.subscribers:
            for callback in self.subscribers[symbol]:
                try:
                    await callback(market_data, sentiment)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe_to_symbol(self, symbol: str, callback):
        """Subscribe to real-time updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
    
    def unsubscribe_from_symbol(self, symbol: str, callback):
        """Unsubscribe from symbol updates"""
        if symbol in self.subscribers:
            self.subscribers[symbol].remove(callback)
    
    async def get_current_price(self, symbol: str) -> Optional[MarketData]:
        """Get current market data for a symbol"""
        return self.market_data.get(symbol)
    
    async def get_market_sentiment(self, symbol: str) -> Optional[MarketSentiment]:
        """Get current market sentiment for a symbol"""
        return self.sentiment_data.get(symbol)
    
    async def analyze_trade_context(self, symbol: str, entry_price: float) -> Dict[str, Any]:
        """Analyze market context for a trade"""
        market_data = await self.get_current_price(symbol)
        sentiment = await self.get_market_sentiment(symbol)
        
        if not market_data or not sentiment:
            return {"error": "Market data not available"}
        
        current_price = market_data.price
        price_diff = current_price - entry_price
        price_diff_percent = (price_diff / entry_price) * 100
        
        # Determine market regime
        regime = self._determine_market_regime(sentiment)
        
        # Calculate risk/reward metrics
        risk_reward = self._calculate_risk_reward(
            entry_price, current_price, 
            sentiment.support_level, sentiment.resistance_level
        )
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "entry_price": entry_price,
            "unrealized_pnl": price_diff,
            "unrealized_pnl_percent": round(price_diff_percent, 2),
            "market_regime": regime,
            "sentiment_score": sentiment.sentiment_score,
            "volatility": sentiment.volatility,
            "momentum": sentiment.momentum,
            "support_level": sentiment.support_level,
            "resistance_level": sentiment.resistance_level,
            "risk_reward": risk_reward,
            "recommendation": self._generate_recommendation(sentiment, price_diff_percent)
        }
    
    def _determine_market_regime(self, sentiment: MarketSentiment) -> str:
        """Determine current market regime"""
        if sentiment.volatility > 5:
            return "high_volatility"
        elif sentiment.sentiment_score > 0.5:
            return "bullish_trending"
        elif sentiment.sentiment_score < -0.5:
            return "bearish_trending"
        else:
            return "sideways_consolidation"
    
    def _calculate_risk_reward(self, entry: float, current: float, support: float, resistance: float) -> Dict[str, float]:
        """Calculate risk/reward metrics"""
        if current > entry:  # Long position
            potential_reward = resistance - current
            potential_risk = current - support
        else:  # Short position
            potential_reward = current - support
            potential_risk = resistance - current
        
        risk_reward_ratio = potential_reward / potential_risk if potential_risk > 0 else 0
        
        return {
            "potential_reward": round(potential_reward, 2),
            "potential_risk": round(potential_risk, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2)
        }
    
    def _generate_recommendation(self, sentiment: MarketSentiment, pnl_percent: float) -> str:
        """Generate trading recommendation based on market context"""
        if pnl_percent > 5 and sentiment.sentiment_score < 0:
            return "Consider taking profits - sentiment turning negative"
        elif pnl_percent < -3 and sentiment.sentiment_score > 0.5:
            return "Hold position - strong positive sentiment"
        elif sentiment.volatility > 8:
            return "High volatility detected - manage risk carefully"
        elif abs(sentiment.momentum) > 3:
            return f"Strong {sentiment.trend_direction} momentum - trend continuation likely"
        else:
            return "Monitor position - neutral market conditions"
    
    async def get_portfolio_context(self, user_id: str) -> Dict[str, Any]:
        """Get real-time context for user's entire portfolio"""
        try:
            db = next(get_db())
            
            # Get open positions (assuming we track them)
            open_trades = db.query(Trade).filter(
                Trade.user_id == user_id,
                Trade.exit_time.is_(None)  # Open positions
            ).all()
            
            portfolio_context = {
                "total_positions": len(open_trades),
                "symbols": [],
                "total_unrealized_pnl": 0,
                "market_exposure": {},
                "risk_metrics": {}
            }
            
            for trade in open_trades:
                context = await self.analyze_trade_context(trade.symbol, trade.entry_price)
                if "error" not in context:
                    portfolio_context["symbols"].append(context)
                    portfolio_context["total_unrealized_pnl"] += context["unrealized_pnl"]
            
            return portfolio_context
            
        except Exception as e:
            logger.error(f"Error getting portfolio context: {e}")
            return {"error": str(e)}
        finally:
            db.close()

# Global service instance
market_service = RealTimeMarketService()
