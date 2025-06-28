
#!/usr/bin/env python3
"""
Real-time Market Data Service
Connects to multiple free market data APIs to provide live market context
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class MarketDataSource(Enum):
    ALPHA_VANTAGE = "alpha_vantage"
    TWELVE_DATA = "twelve_data"
    YAHOO_FINANCE = "yahoo_finance"
    POLYGON = "polygon"

@dataclass
class MarketQuote:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    source: MarketDataSource
    
@dataclass
class MarketSentiment:
    symbol: str
    sentiment_score: float  # -1 to 1
    news_count: int
    volatility: float
    rsi: float
    ma_signal: str  # "bullish", "bearish", "neutral"
    timestamp: datetime

class RealTimeMarketService:
    """Real-time market data service with multiple data sources."""
    
    def __init__(self, db_path: str = "tradesense.db"):
        self.db_path = db_path
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, MarketQuote] = {}
        self.cache_ttl = 60  # seconds
        self.sources_config = {
            MarketDataSource.ALPHA_VANTAGE: {
                "base_url": "https://www.alphavantage.co/query",
                "api_key": None,  # Free tier available
                "rate_limit": 5  # requests per minute
            },
            MarketDataSource.TWELVE_DATA: {
                "base_url": "https://api.twelvedata.com",
                "api_key": None,  # Free tier: 800 requests/day
                "rate_limit": 8
            },
            MarketDataSource.YAHOO_FINANCE: {
                "base_url": "https://query1.finance.yahoo.com/v8/finance/chart",
                "api_key": None,  # No API key needed
                "rate_limit": 100
            }
        }
        self._init_market_tables()
    
    def _init_market_tables(self):
        """Initialize market data tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Market quotes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_amount REAL,
                    change_percent REAL,
                    volume INTEGER,
                    source TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX(symbol, timestamp)
                )
            """)
            
            # Market sentiment table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    sentiment_score REAL,
                    news_count INTEGER,
                    volatility REAL,
                    rsi REAL,
                    ma_signal TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX(symbol, timestamp)
                )
            """)
            
            # Watchlist table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    symbol TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, symbol)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing market tables: {e}")
    
    async def start_session(self):
        """Start aiohttp session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_quote_yahoo(self, symbol: str) -> Optional[MarketQuote]:
        """Get quote from Yahoo Finance (free, no API key required)."""
        try:
            await self.start_session()
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('chart', {}).get('result', [])
                    
                    if result:
                        meta = result[0].get('meta', {})
                        return MarketQuote(
                            symbol=symbol,
                            price=meta.get('regularMarketPrice', 0.0),
                            change=meta.get('regularMarketPrice', 0.0) - meta.get('previousClose', 0.0),
                            change_percent=((meta.get('regularMarketPrice', 0.0) - meta.get('previousClose', 1.0)) / meta.get('previousClose', 1.0)) * 100,
                            volume=meta.get('regularMarketVolume', 0),
                            timestamp=datetime.now(),
                            source=MarketDataSource.YAHOO_FINANCE
                        )
                        
        except Exception as e:
            logger.error(f"Error fetching Yahoo quote for {symbol}: {e}")
        
        return None
    
    async def get_quote_alpha_vantage(self, symbol: str, api_key: str) -> Optional[MarketQuote]:
        """Get quote from Alpha Vantage (free tier available)."""
        try:
            await self.start_session()
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': api_key
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get('Global Quote', {})
                    
                    if quote:
                        return MarketQuote(
                            symbol=symbol,
                            price=float(quote.get('05. price', 0)),
                            change=float(quote.get('09. change', 0)),
                            change_percent=float(quote.get('10. change percent', '0%').replace('%', '')),
                            volume=int(quote.get('06. volume', 0)),
                            timestamp=datetime.now(),
                            source=MarketDataSource.ALPHA_VANTAGE
                        )
                        
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage quote for {symbol}: {e}")
        
        return None
    
    async def get_quote(self, symbol: str, api_key: Optional[str] = None) -> Optional[MarketQuote]:
        """Get quote with fallback sources."""
        # Check cache first
        cache_key = f"{symbol}_{datetime.now().timestamp() // self.cache_ttl}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try Yahoo Finance first (free, no API key)
        quote = await self.get_quote_yahoo(symbol)
        
        # Fallback to Alpha Vantage if API key provided
        if not quote and api_key:
            quote = await self.get_quote_alpha_vantage(symbol, api_key)
        
        # Cache the result
        if quote:
            self.cache[cache_key] = quote
            await self._store_quote(quote)
        
        return quote
    
    async def _store_quote(self, quote: MarketQuote):
        """Store quote in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO market_quotes 
                (symbol, price, change_amount, change_percent, volume, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                quote.symbol,
                quote.price,
                quote.change,
                quote.change_percent,
                quote.volume,
                quote.source.value
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing quote: {e}")
    
    async def get_market_sentiment(self, symbol: str) -> Optional[MarketSentiment]:
        """Calculate market sentiment based on recent data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent quotes for volatility calculation
            cursor.execute("""
                SELECT price, change_percent, timestamp 
                FROM market_quotes 
                WHERE symbol = ? AND timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
                LIMIT 50
            """, (symbol,))
            
            quotes = cursor.fetchall()
            
            if len(quotes) < 5:
                return None
            
            # Calculate basic sentiment metrics
            prices = [q[0] for q in quotes]
            changes = [q[1] for q in quotes]
            
            # Volatility (standard deviation of price changes)
            avg_change = sum(changes) / len(changes)
            volatility = (sum((c - avg_change) ** 2 for c in changes) / len(changes)) ** 0.5
            
            # Simple RSI calculation
            gains = [c for c in changes if c > 0]
            losses = [abs(c) for c in changes if c < 0]
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 1
            
            rs = avg_gain / avg_loss if avg_loss != 0 else 100
            rsi = 100 - (100 / (1 + rs))
            
            # Moving average signal
            recent_avg = sum(prices[:10]) / min(10, len(prices))
            older_avg = sum(prices[10:20]) / min(10, len(prices[10:20])) if len(prices) > 10 else recent_avg
            
            ma_signal = "bullish" if recent_avg > older_avg else "bearish" if recent_avg < older_avg else "neutral"
            
            # Sentiment score (-1 to 1)
            sentiment_score = 0.0
            sentiment_score += 0.3 * (avg_change / 10)  # Recent performance
            sentiment_score += 0.3 * ((70 - rsi) / 70)  # RSI (inverted, lower RSI = more bullish potential)
            sentiment_score += 0.2 * (1 if ma_signal == "bullish" else -1 if ma_signal == "bearish" else 0)
            sentiment_score += 0.2 * (1 - min(volatility / 5, 1))  # Lower volatility = more confidence
            
            sentiment_score = max(-1, min(1, sentiment_score))
            
            sentiment = MarketSentiment(
                symbol=symbol,
                sentiment_score=sentiment_score,
                news_count=0,  # Would integrate with news API
                volatility=volatility,
                rsi=rsi,
                ma_signal=ma_signal,
                timestamp=datetime.now()
            )
            
            conn.close()
            return sentiment
            
        except Exception as e:
            logger.error(f"Error calculating sentiment for {symbol}: {e}")
            return None
    
    async def get_watchlist_quotes(self, user_id: int) -> List[MarketQuote]:
        """Get quotes for user's watchlist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT symbol FROM market_watchlist WHERE user_id = ?
            """, (user_id,))
            
            symbols = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            quotes = []
            for symbol in symbols:
                quote = await self.get_quote(symbol)
                if quote:
                    quotes.append(quote)
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting watchlist quotes: {e}")
            return []
    
    def add_to_watchlist(self, user_id: int, symbol: str) -> bool:
        """Add symbol to user's watchlist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO market_watchlist (user_id, symbol)
                VALUES (?, ?)
            """, (user_id, symbol.upper()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            return False
    
    def remove_from_watchlist(self, user_id: int, symbol: str) -> bool:
        """Remove symbol from user's watchlist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM market_watchlist WHERE user_id = ? AND symbol = ?
            """, (user_id, symbol.upper()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error removing from watchlist: {e}")
            return False
    
    async def get_market_context_for_trade(self, symbol: str, trade_timestamp: datetime) -> Dict[str, Any]:
        """Get market context at the time of trade."""
        try:
            # Get quote closest to trade time
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT price, change_percent, volume, timestamp
                FROM market_quotes 
                WHERE symbol = ? AND timestamp <= ?
                ORDER BY ABS(julianday(timestamp) - julianday(?))
                LIMIT 1
            """, (symbol, trade_timestamp, trade_timestamp))
            
            quote_data = cursor.fetchone()
            
            # Get sentiment at trade time
            sentiment = await self.get_market_sentiment(symbol)
            
            context = {
                "market_price": quote_data[0] if quote_data else None,
                "market_change": quote_data[1] if quote_data else None,
                "market_volume": quote_data[2] if quote_data else None,
                "sentiment_score": sentiment.sentiment_score if sentiment else None,
                "volatility": sentiment.volatility if sentiment else None,
                "rsi": sentiment.rsi if sentiment else None,
                "ma_signal": sentiment.ma_signal if sentiment else None
            }
            
            conn.close()
            return context
            
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return {}

# Global service instance
market_service = RealTimeMarketService()

async def start_market_data_service():
    """Start the market data service."""
    await market_service.start_session()
    logger.info("Real-time market data service started")

async def stop_market_data_service():
    """Stop the market data service."""
    await market_service.close_session()
    logger.info("Real-time market data service stopped")
