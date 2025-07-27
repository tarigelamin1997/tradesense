import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import httpx
import uvicorn
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sklearn.linear_model import LinearRegression
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense Analytics Service",
    description="Advanced analytics and pattern recognition",
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

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/analytics_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")
TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://trading:8000")

# Models
class AnalyticsData(Base):
    __tablename__ = "analytics"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    metric_type = Column(String)
    data = Column(JSON)
    calculated_at = Column(DateTime, default=datetime.utcnow)

class Pattern(Base):
    __tablename__ = "patterns"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    pattern_type = Column(String)
    symbol = Column(String)
    confidence = Column(Float)
    details = Column(JSON)
    detected_at = Column(DateTime, default=datetime.utcnow)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")

# Pydantic models
class PerformanceMetrics(BaseModel):
    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    profitable_trades: int

class PatternDetection(BaseModel):
    pattern_type: str
    symbol: str
    confidence: float
    action: str
    details: Dict[str, Any]

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth dependency
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    
    # Verify with auth service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/auth/verify",
                params={"token": token}
            )
            data = response.json()
            if not data.get("valid"):
                raise HTTPException(status_code=401, detail="Invalid token")
            return data.get("username")
        except:
            raise HTTPException(status_code=503, detail="Auth service unavailable")

# Helper functions
async def get_user_trades(username: str, token: str):
    """Fetch user trades from trading service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{TRADING_SERVICE_URL}/trades",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.json()
        except:
            return []

def calculate_performance(trades: List[Dict]) -> PerformanceMetrics:
    """Calculate performance metrics from trades"""
    if not trades:
        return PerformanceMetrics(
            total_return=0.0,
            win_rate=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            total_trades=0,
            profitable_trades=0
        )
    
    df = pd.DataFrame(trades)
    
    # Calculate metrics
    total_trades = len(df)
    
    # Simple P&L calculation (would be more complex in real app)
    df['pnl'] = df.apply(lambda x: x['total'] if x['action'] == 'sell' else -x['total'], axis=1)
    total_return = df['pnl'].sum()
    
    profitable_trades = len(df[df['pnl'] > 0])
    win_rate = profitable_trades / total_trades if total_trades > 0 else 0
    
    # Simplified Sharpe ratio (annualized)
    if len(df) > 1:
        returns = df['pnl'].pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Max drawdown
    cumulative = df['pnl'].cumsum()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0
    
    return PerformanceMetrics(
        total_return=float(total_return),
        win_rate=float(win_rate),
        sharpe_ratio=float(sharpe_ratio),
        max_drawdown=float(max_drawdown),
        total_trades=total_trades,
        profitable_trades=profitable_trades
    )

def detect_patterns(trades: List[Dict]) -> List[PatternDetection]:
    """Detect trading patterns using simple algorithms"""
    patterns = []
    
    if len(trades) < 5:
        return patterns
    
    df = pd.DataFrame(trades)
    
    # Group by symbol
    for symbol in df['symbol'].unique():
        symbol_trades = df[df['symbol'] == symbol].sort_values('created_at')
        
        if len(symbol_trades) >= 3:
            # Simple momentum pattern
            prices = symbol_trades['price'].values
            if len(prices) >= 3:
                recent_trend = np.polyfit(range(len(prices[-3:])), prices[-3:], 1)[0]
                
                if recent_trend > 0:
                    patterns.append(PatternDetection(
                        pattern_type="momentum_up",
                        symbol=symbol,
                        confidence=min(abs(recent_trend) * 10, 0.9),
                        action="consider_buy",
                        details={"trend_strength": float(recent_trend)}
                    ))
                elif recent_trend < 0:
                    patterns.append(PatternDetection(
                        pattern_type="momentum_down",
                        symbol=symbol,
                        confidence=min(abs(recent_trend) * 10, 0.9),
                        action="consider_sell",
                        details={"trend_strength": float(recent_trend)}
                    ))
    
    return patterns

# Routes
@app.get("/")
async def root():
    return {"service": "Analytics Service", "status": "operational"}

@app.get("/health")
async def health():
    try:
        # Check database connection
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/analytics/performance", response_model=PerformanceMetrics)
async def get_performance(
    username: str = Depends(verify_token),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # Get trades from trading service
    trades = await get_user_trades(username, authorization.split(" ")[1])
    
    # Calculate performance
    metrics = calculate_performance(trades)
    
    # Store in database
    analytics_data = AnalyticsData(
        id=f"perf_{datetime.utcnow().timestamp()}",
        user_id=username,
        metric_type="performance",
        data=metrics.dict()
    )
    db.add(analytics_data)
    db.commit()
    
    return metrics

@app.get("/analytics/patterns", response_model=List[PatternDetection])
async def get_patterns(
    username: str = Depends(verify_token),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # Get trades from trading service
    trades = await get_user_trades(username, authorization.split(" ")[1])
    
    # Detect patterns
    patterns = detect_patterns(trades)
    
    # Store detected patterns
    for pattern in patterns:
        db_pattern = Pattern(
            id=f"pattern_{datetime.utcnow().timestamp()}_{pattern.symbol}",
            user_id=username,
            pattern_type=pattern.pattern_type,
            symbol=pattern.symbol,
            confidence=pattern.confidence,
            details=pattern.details
        )
        db.add(db_pattern)
    
    db.commit()
    
    return patterns

@app.get("/analytics/summary")
async def get_analytics_summary(
    username: str = Depends(verify_token),
    authorization: str = Header(None)
):
    # Get trades
    trades = await get_user_trades(username, authorization.split(" ")[1])
    
    # Calculate everything
    performance = calculate_performance(trades)
    patterns = detect_patterns(trades)
    
    return {
        "performance": performance.dict(),
        "patterns": [p.dict() for p in patterns],
        "trade_count": len(trades),
        "last_updated": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Analytics Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)