import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import httpx
import uvicorn
import logging
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense AI Service",
    description="AI-powered trading insights and analysis",
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
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/ai_db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-test"))

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8000")
TRADING_SERVICE_URL = os.getenv("TRADING_SERVICE_URL", "http://trading:8000")
ANALYTICS_SERVICE_URL = os.getenv("ANALYTICS_SERVICE_URL", "http://analytics:8000")

# Models
class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    insight_type = Column(String)  # market_analysis, trade_suggestion, risk_assessment
    content = Column(Text)
    insight_metadata = Column(JSON)  # Changed from metadata to insight_metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    messages = Column(JSON)
    context = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create tables: {e}")

# Pydantic models
class MarketAnalysisRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1d"  # 1d, 1w, 1m
    analysis_type: str = "technical"  # technical, fundamental, sentiment

class MarketAnalysisResponse(BaseModel):
    analysis: str
    recommendations: List[Dict[str, Any]]
    confidence: float
    timestamp: datetime

class TradeSuggestionRequest(BaseModel):
    risk_tolerance: str = "medium"  # low, medium, high
    investment_amount: float
    preferred_sectors: Optional[List[str]] = None

class TradeSuggestionResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    rationale: str
    risk_assessment: str

class AIQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class AIQueryResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    references: Optional[List[str]] = None

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
async def get_user_context(username: str, token: str) -> Dict[str, Any]:
    """Get user trading context from other services"""
    context = {"username": username}
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get portfolio
        try:
            portfolio_resp = await client.get(
                f"{TRADING_SERVICE_URL}/portfolio",
                headers=headers
            )
            context["portfolio"] = portfolio_resp.json()
        except:
            context["portfolio"] = []
        
        # Get performance
        try:
            perf_resp = await client.get(
                f"{ANALYTICS_SERVICE_URL}/analytics/performance",
                headers=headers
            )
            context["performance"] = perf_resp.json()
        except:
            context["performance"] = {}
    
    return context

def generate_market_analysis(symbols: List[str], timeframe: str, analysis_type: str) -> str:
    """Generate AI market analysis"""
    prompt = f"""
    Provide a {analysis_type} analysis for the following symbols: {', '.join(symbols)}
    Timeframe: {timeframe}
    
    Include:
    1. Current market conditions
    2. Key technical/fundamental factors
    3. Potential opportunities and risks
    4. Actionable recommendations
    
    Be concise and data-driven.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional financial analyst providing market insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "Unable to generate analysis at this time."

def generate_trade_suggestions(risk_tolerance: str, amount: float, sectors: List[str], context: Dict) -> Dict:
    """Generate AI trade suggestions based on user profile"""
    portfolio = context.get("portfolio", [])
    performance = context.get("performance", {})
    
    prompt = f"""
    Generate trade suggestions for:
    - Risk tolerance: {risk_tolerance}
    - Investment amount: ${amount}
    - Preferred sectors: {', '.join(sectors) if sectors else 'Any'}
    - Current portfolio: {len(portfolio)} positions
    - Win rate: {performance.get('win_rate', 0):.2%}
    
    Provide 3-5 specific trade ideas with:
    1. Symbol
    2. Action (buy/sell)
    3. Entry price range
    4. Stop loss
    5. Take profit targets
    6. Position size
    7. Rationale
    
    Format as JSON.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional trading advisor. Provide specific, actionable trade suggestions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        # Parse response (in production, would parse JSON properly)
        return {
            "suggestions": [],
            "rationale": response.choices[0].message.content
        }
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return {"suggestions": [], "rationale": "Unable to generate suggestions."}

# Routes
@app.get("/")
async def root():
    return {"service": "AI Service", "status": "operational"}

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
    
    # Check OpenAI
    openai_status = "healthy" if os.getenv("OPENAI_API_KEY") else "not_configured"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "openai": openai_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/ai/market-analysis", response_model=MarketAnalysisResponse)
async def analyze_market(
    request: MarketAnalysisRequest,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get AI-powered market analysis"""
    # Generate analysis
    analysis = generate_market_analysis(
        request.symbols,
        request.timeframe,
        request.analysis_type
    )
    
    # Store insight
    insight = AIInsight(
        id=f"insight_{datetime.utcnow().timestamp()}",
        user_id=username,
        insight_type="market_analysis",
        content=analysis,
        insight_metadata={
            "symbols": request.symbols,
            "timeframe": request.timeframe,
            "analysis_type": request.analysis_type
        }
    )
    db.add(insight)
    db.commit()
    
    return MarketAnalysisResponse(
        analysis=analysis,
        recommendations=[],  # Would parse from analysis
        confidence=0.85,
        timestamp=datetime.utcnow()
    )

@app.post("/ai/trade-suggestions", response_model=TradeSuggestionResponse)
async def get_trade_suggestions(
    request: TradeSuggestionRequest,
    username: str = Depends(verify_token),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get AI-generated trade suggestions"""
    # Get user context
    context = await get_user_context(username, authorization.split(" ")[1])
    
    # Generate suggestions
    result = generate_trade_suggestions(
        request.risk_tolerance,
        request.investment_amount,
        request.preferred_sectors or [],
        context
    )
    
    # Store insight
    insight = AIInsight(
        id=f"insight_{datetime.utcnow().timestamp()}",
        user_id=username,
        insight_type="trade_suggestion",
        content=result["rationale"],
        insight_metadata={
            "risk_tolerance": request.risk_tolerance,
            "investment_amount": request.investment_amount,
            "suggestions": result["suggestions"]
        }
    )
    db.add(insight)
    db.commit()
    
    return TradeSuggestionResponse(
        suggestions=result["suggestions"],
        rationale=result["rationale"],
        risk_assessment=f"Suitable for {request.risk_tolerance} risk tolerance"
    )

@app.post("/ai/query", response_model=AIQueryResponse)
async def query_ai(
    request: AIQueryRequest,
    username: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """General AI query endpoint"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are TradeSense AI, a helpful trading assistant. Provide clear, actionable insights."},
                {"role": "user", "content": request.query}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Store conversation
        conversation = AIConversation(
            id=f"conv_{datetime.utcnow().timestamp()}",
            user_id=username,
            messages=[
                {"role": "user", "content": request.query},
                {"role": "assistant", "content": ai_response}
            ],
            context=request.context or {}
        )
        db.add(conversation)
        db.commit()
        
        return AIQueryResponse(
            response=ai_response,
            suggestions=None,
            references=None
        )
        
    except Exception as e:
        logger.error(f"AI query error: {e}")
        raise HTTPException(status_code=500, detail="AI service error")

@app.get("/ai/insights")
async def get_insights(
    username: str = Depends(verify_token),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get recent AI insights for user"""
    insights = db.query(AIInsight).filter(
        AIInsight.user_id == username
    ).order_by(AIInsight.created_at.desc()).limit(limit).all()
    
    return {
        "insights": [
            {
                "id": insight.id,
                "type": insight.insight_type,
                "content": insight.content,
                "metadata": insight.insight_metadata,
                "created_at": insight.created_at
            }
            for insight in insights
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting AI Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)