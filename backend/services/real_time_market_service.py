import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None

@dataclass
class MarketSentiment:
    fear_greed_index: int
    vix: float
    trending_symbols: List[str]
    sector_performance: Dict[str, float]
    market_regime: str  # "bullish", "bearish", "sideways", "volatile"

class RealTimeMarketService:
    """Real-time market data service with multiple provider support"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 60  # 1 minute cache
        self.subscribers = {}
        self.active_connections = set()
        self.market_data = {}
        self.sentiment_data = {}
        
        # Demo mode - simulate real market data
        self.demo_mode = True

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache:
            return False

        cached_time = self.cache[key].get('timestamp')
        if not cached_time:
            return False

        return datetime.now() - cached_time < timedelta(seconds=self.cache_ttl)

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
                        change=round(current_price - base_price, 2),
                        change_percent=round(price_change * 100, 2),
                        volume=int(1000000 + (asyncio.get_event_loop().time() % 1000) * 1000),
                        timestamp=datetime.now(),
                        market_cap=50000000000 + hash(symbol) % 100000000000,
                        pe_ratio=15.0 + hash(symbol) % 20
                    )
                    
                    self.market_data[symbol] = market_data
                    
                    # Generate sentiment data
                    sentiment = MarketSentiment(
                        fear_greed_index=45,  # 0-100 scale
                        vix=22.5,
                        trending_symbols=["AAPL", "TSLA", "NVDA", "SPY", "QQQ"],
                        sector_performance={
                            "Technology": 1.2,
                            "Healthcare": 0.8,
                            "Finance": -0.3,
                            "Energy": 2.1,
                            "Consumer": 0.5
                        },
                        market_regime="sideways"
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

    async def get_market_data(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get real-time market data for symbols"""
        cache_key = f"market_data_{','.join(sorted(symbols))}"

        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Alpha Vantage API (free tier)
            market_data = {}

            for symbol in symbols:
                # Simulated data for demo (replace with real API calls)
                market_data[symbol] = MarketData(
                    symbol=symbol,
                    price=150.0 + hash(symbol) % 100,
                    change=(-5.0 + hash(symbol) % 10),
                    change_percent=(-3.0 + hash(symbol) % 6),
                    volume=1000000 + hash(symbol) % 5000000,
                    timestamp=datetime.now(),
                    market_cap=50000000000 + hash(symbol) % 100000000000,
                    pe_ratio=15.0 + hash(symbol) % 20
                )

            # Cache the result
            self.cache[cache_key] = {
                'data': market_data,
                'timestamp': datetime.now()
            }

            return market_data

        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {}
    
    async def get_market_sentiment(self) -> MarketSentiment:
        """Get overall market sentiment indicators"""
        cache_key = "market_sentiment"

        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Simulated sentiment data (replace with real API calls)
            sentiment = MarketSentiment(
                fear_greed_index=45,  # 0-100 scale
                vix=22.5,
                trending_symbols=["AAPL", "TSLA", "NVDA", "SPY", "QQQ"],
                sector_performance={
                    "Technology": 1.2,
                    "Healthcare": 0.8,
                    "Finance": -0.3,
                    "Energy": 2.1,
                    "Consumer": 0.5
                },
                market_regime="sideways"
            )

            # Cache the result
            self.cache[cache_key] = {
                'data': sentiment,
                'timestamp': datetime.now()
            }

            return sentiment

        except Exception as e:
            logger.error(f"Error fetching market sentiment: {e}")
            # Return default sentiment
            return MarketSentiment(
                fear_greed_index=50,
                vix=20.0,
                trending_symbols=[],
                sector_performance={},
                market_regime="neutral"
            )

    async def get_market_sentiment(self, symbol: str) -> Optional[MarketSentiment]:
        """Get current market sentiment for a symbol"""
        return self.sentiment_data.get(symbol)
    
    async def get_economic_calendar(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming economic events"""
        cache_key = f"economic_calendar_{days_ahead}"

        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # Simulated economic events (replace with real API)
            events = [
                {
                    "date": "2025-01-28",
                    "time": "08:30",
                    "event": "GDP Growth Rate Q4",
                    "impact": "high",
                    "forecast": "2.8%",
                    "previous": "3.1%"
                },
                {
                    "date": "2025-01-29",
                    "time": "14:00",
                    "event": "Federal Reserve Interest Rate Decision",
                    "impact": "high",
                    "forecast": "5.25%",
                    "previous": "5.25%"
                },
                {
                    "date": "2025-01-30",
                    "time": "08:30",
                    "event": "Non-Farm Payrolls",
                    "impact": "high",
                    "forecast": "180K",
                    "previous": "199K"
                }
            ]

            # Cache the result
            self.cache[cache_key] = {
                'data': events,
                'timestamp': datetime.now()
            }

            return events

        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []
    
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
            "sentiment_score": sentiment.fear_greed_index,
            "volatility": sentiment.vix,
            "momentum": 0, #sentiment.momentum, - Removed as sentiment no longer has a momentum field
            "support_level": 0, #sentiment.support_level, - Removed as sentiment no longer has a support_level field
            "resistance_level": 0, #sentiment.resistance_level, - Removed as sentiment no longer has a resistance_level field
            "risk_reward": risk_reward,
            "recommendation": self._generate_recommendation(sentiment, price_diff_percent)
        }
    
    def _determine_market_regime(self, sentiment: MarketSentiment) -> str:
        """Determine current market regime"""
        return sentiment.market_regime
        #if sentiment.volatility > 5: - Removed since sentiment no longer has a volatility field
        #    return "high_volatility"
        #elif sentiment.sentiment_score > 0.5: - Removed since sentiment no longer has a sentiment_score field
        #    return "bullish_trending"
        #elif sentiment.sentiment_score < -0.5: - Removed since sentiment no longer has a sentiment_score field
        #    return "bearish_trending"
        #else:
        #    return "sideways_consolidation"
    
    def _calculate_risk_reward(self, entry: float, current: float, support: float, resistance: float) -> Dict[str, float]:
        """Calculate risk/reward metrics"""
        potential_reward = 0
        potential_risk = 0
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
        if pnl_percent > 5 and sentiment.fear_greed_index < 40:
            return "Consider taking profits - sentiment turning negative"
        elif pnl_percent < -3 and sentiment.fear_greed_index > 60:
            return "Hold position - strong positive sentiment"
        elif sentiment.vix > 30:
            return "High volatility detected - manage risk carefully"
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
                #context = await self.analyze_trade_context(trade.symbol, trade.entry_price)
                market_data = await self.get_market_data([trade.symbol])
                if trade.symbol in market_data:
                    trade_market_data = market_data[trade.symbol]
                    context = {
                        "symbol": trade.symbol,
                        "current_price": trade_market_data.price,
                        "entry_price": trade.entry_price,
                        "unrealized_pnl": trade_market_data.price - trade.entry_price,
                        "unrealized_pnl_percent": round(((trade_market_data.price - trade.entry_price) / trade.entry_price) * 100, 2),
                        "market_regime": "N/A",  # Replace with actual market regime logic if needed
                        "sentiment_score": 0,
                        "volatility": 0,
                        "momentum": 0,
                        "support_level": 0,
                        "resistance_level": 0,
                        "risk_reward": {"potential_reward": 0, "potential_risk": 0, "risk_reward_ratio": 0},
                        "recommendation": "N/A"
                    }

                    portfolio_context["symbols"].append(context)
                    portfolio_context["total_unrealized_pnl"] += context["unrealized_pnl"]
            
            return portfolio_context
            
        except Exception as e:
            logger.error(f"Error getting portfolio context: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def get_market_context_tags(self, trade_time: datetime) -> List[str]:
        """Generate market context tags for a trade"""
        tags = []

        # Time-based tags
        if 9 <= trade_time.hour <= 10:
            tags.append("market_open")
        elif 15 <= trade_time.hour <= 16:
            tags.append("market_close")
        elif 11 <= trade_time.hour <= 14:
            tags.append("mid_day")

        # Day-based tags
        if trade_time.weekday() == 0:
            tags.append("monday_gap")
        elif trade_time.weekday() == 4:
            tags.append("friday_close")

        # Add more context tags based on market conditions
        tags.extend(["normal_volume", "low_volatility"])

        return tags

# Global service instance
market_service = RealTimeMarketService()