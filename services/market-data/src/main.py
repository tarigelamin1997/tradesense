import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
import yfinance as yf
import redis
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense Market Data Service",
    description="Real-time market data and caching",
    version="1.0.0"
)

# CORS configuration
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:8000",
    "https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app",
    "https://frontend-jj8nosjl0-tarig-ahmeds-projects.vercel.app",
    "https://frontend-*.vercel.app",
    "https://*.vercel.app",
    "https://tradesense.vercel.app",
    "https://tradesense-*.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    redis_client = None

# Cache settings
CACHE_TTL = 300  # 5 minutes for market data
QUOTE_CACHE_TTL = 60  # 1 minute for real-time quotes

# Pydantic models
class Quote(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime

class HistoricalData(BaseModel):
    symbol: str
    period: str
    data: List[Dict[str, float]]

class MarketSummary(BaseModel):
    indices: Dict[str, Quote]
    top_gainers: List[Quote]
    top_losers: List[Quote]
    timestamp: datetime

# Helper functions
def get_cache_key(prefix: str, identifier: str) -> str:
    """Generate cache key"""
    return f"{prefix}:{identifier}"

def cache_data(key: str, data: dict, ttl: int = CACHE_TTL):
    """Cache data in Redis"""
    if redis_client:
        try:
            redis_client.setex(key, ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.error(f"Cache write error: {e}")

def get_cached_data(key: str) -> Optional[dict]:
    """Get data from cache"""
    if redis_client:
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
    return None

async def fetch_quote(symbol: str) -> Quote:
    """Fetch real-time quote for a symbol"""
    cache_key = get_cache_key("quote", symbol)
    
    # Check cache first
    cached = get_cached_data(cache_key)
    if cached:
        return Quote(**cached)
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        quote = Quote(
            symbol=symbol,
            price=info.get('regularMarketPrice', 0),
            change=info.get('regularMarketChange', 0),
            change_percent=info.get('regularMarketChangePercent', 0),
            volume=info.get('regularMarketVolume', 0),
            timestamp=datetime.utcnow()
        )
        
        # Cache the quote
        cache_data(cache_key, quote.dict(), QUOTE_CACHE_TTL)
        
        return quote
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote for {symbol}")

async def fetch_historical(symbol: str, period: str = "1mo") -> HistoricalData:
    """Fetch historical data for a symbol"""
    cache_key = get_cache_key("historical", f"{symbol}:{period}")
    
    # Check cache
    cached = get_cached_data(cache_key)
    if cached:
        return HistoricalData(**cached)
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.isoformat(),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        historical = HistoricalData(
            symbol=symbol,
            period=period,
            data=data
        )
        
        # Cache the data
        cache_data(cache_key, historical.dict())
        
        return historical
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data")

# Routes
@app.get("/")
async def root():
    return {"service": "Market Data Service", "status": "operational"}

@app.get("/health")
async def health():
    redis_status = "healthy"
    if redis_client:
        try:
            redis_client.ping()
        except:
            redis_status = "unhealthy"
    else:
        redis_status = "unavailable"
    
    return {
        "status": "healthy" if redis_status in ["healthy", "unavailable"] else "degraded",
        "cache": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/market-data/quote/{symbol}", response_model=Quote)
async def get_quote(symbol: str):
    """Get real-time quote for a symbol"""
    return await fetch_quote(symbol.upper())

@app.get("/market-data/quotes", response_model=List[Quote])
async def get_multiple_quotes(symbols: str):
    """Get quotes for multiple symbols (comma-separated)"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    # Fetch quotes concurrently
    quotes = await asyncio.gather(
        *[fetch_quote(symbol) for symbol in symbol_list],
        return_exceptions=True
    )
    
    # Filter out errors
    valid_quotes = [q for q in quotes if isinstance(q, Quote)]
    return valid_quotes

@app.get("/market-data/historical/{symbol}", response_model=HistoricalData)
async def get_historical(symbol: str, period: str = "1mo"):
    """Get historical data for a symbol"""
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Valid periods: {valid_periods}")
    
    return await fetch_historical(symbol.upper(), period)

@app.get("/market-data/summary", response_model=MarketSummary)
async def get_market_summary():
    """Get market summary with major indices"""
    # Major indices
    indices_symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT"]  # S&P 500, Dow, Nasdaq, Russell
    
    # Fetch index quotes
    index_quotes = await asyncio.gather(
        *[fetch_quote(symbol) for symbol in indices_symbols],
        return_exceptions=True
    )
    
    indices = {}
    for i, symbol in enumerate(indices_symbols):
        if isinstance(index_quotes[i], Quote):
            name = {
                "^GSPC": "S&P 500",
                "^DJI": "Dow Jones",
                "^IXIC": "Nasdaq",
                "^RUT": "Russell 2000"
            }.get(symbol, symbol)
            indices[name] = index_quotes[i]
    
    # For demo, return static top gainers/losers
    # In production, this would fetch real data
    return MarketSummary(
        indices=indices,
        top_gainers=[],
        top_losers=[],
        timestamp=datetime.utcnow()
    )

@app.post("/market-data/refresh/{symbol}")
async def refresh_quote(symbol: str, background_tasks: BackgroundTasks):
    """Force refresh quote for a symbol"""
    cache_key = get_cache_key("quote", symbol.upper())
    
    # Delete from cache
    if redis_client:
        redis_client.delete(cache_key)
    
    # Fetch new quote in background
    background_tasks.add_task(fetch_quote, symbol.upper())
    
    return {"message": f"Refresh initiated for {symbol}"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Market Data Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)