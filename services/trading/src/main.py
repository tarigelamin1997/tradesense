import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import httpx
import uvicorn
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense Trading Service",
    description="Trade management and portfolio tracking",
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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/trading_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Auth service URL
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")

# Models
class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    symbol = Column(String)
    action = Column(String)  # buy/sell
    quantity = Column(Float)
    price = Column(Float)
    total = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    symbol = Column(String)
    quantity = Column(Float)
    avg_price = Column(Float)
    current_value = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")

# Pydantic models
class TradeCreate(BaseModel):
    symbol: str
    action: str
    quantity: float
    price: float

class TradeResponse(BaseModel):
    id: str
    symbol: str
    action: str
    quantity: float
    price: float
    total: float
    created_at: datetime

class PortfolioResponse(BaseModel):
    symbol: str
    quantity: float
    avg_price: float
    current_value: float
    updated_at: datetime

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

# Routes
@app.get("/")
async def root():
    return {"service": "Trading Service", "status": "operational"}

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

@app.post("/trades", response_model=TradeResponse)
async def create_trade(
    trade: TradeCreate,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Create trade
    db_trade = Trade(
        id=f"trade_{datetime.utcnow().timestamp()}",
        user_id=username,
        symbol=trade.symbol,
        action=trade.action,
        quantity=trade.quantity,
        price=trade.price,
        total=trade.quantity * trade.price
    )
    
    db.add(db_trade)
    
    # Update portfolio
    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == username,
        Portfolio.symbol == trade.symbol
    ).first()
    
    if portfolio_item:
        if trade.action == "buy":
            new_quantity = portfolio_item.quantity + trade.quantity
            portfolio_item.avg_price = (
                (portfolio_item.quantity * portfolio_item.avg_price + trade.quantity * trade.price) 
                / new_quantity
            )
            portfolio_item.quantity = new_quantity
        else:  # sell
            portfolio_item.quantity -= trade.quantity
            if portfolio_item.quantity <= 0:
                db.delete(portfolio_item)
    else:
        if trade.action == "buy":
            portfolio_item = Portfolio(
                user_id=username,
                symbol=trade.symbol,
                quantity=trade.quantity,
                avg_price=trade.price,
                current_value=trade.quantity * trade.price
            )
            db.add(portfolio_item)
    
    db.commit()
    db.refresh(db_trade)
    
    return db_trade

@app.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 100
):
    trades = db.query(Trade).filter(Trade.user_id == username).order_by(Trade.created_at.desc()).limit(limit).all()
    return trades

@app.get("/portfolio", response_model=List[PortfolioResponse])
async def get_portfolio(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == username).all()
    return portfolio

@app.get("/portfolio/value")
async def get_portfolio_value(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == username).all()
    total_value = sum(item.current_value for item in portfolio)
    
    return {
        "total_value": total_value,
        "positions": len(portfolio),
        "updated_at": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Trading Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)