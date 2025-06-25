
#!/usr/bin/env python3
"""
TradeSense Backend API Server
FastAPI-based REST API for TradeSense trading analytics
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict, Any
import pandas as pd
import json
import logging
import os
import sys
import jwt
import time
import uuid
from datetime import datetime, timedelta
import numpy as np
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tradesense.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
try:
    from auth import AuthManager
    from analytics import compute_basic_stats, performance_over_time, calculate_kpis
    from data_validation import DataValidator
    from backend.db.connection import DatabaseManager, init_database
    from backend.services.analytics_service import AnalyticsService
    from backend.models.trade import Trade, TradeCreate, TradeResponse
except ImportError as e:
    logger.warning(f"Could not import some modules: {e}")
    AuthManager = None
    DataValidator = None

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 TradeSense API starting up...")
    
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")
    
    # Health check
    if DatabaseManager.health_check():
        logger.info("✅ Database connection healthy")
    else:
        logger.error("❌ Database connection failed")
    
    yield
    
    # Shutdown
    logger.info("🛑 TradeSense API shutting down...")

# FastAPI app with lifespan
app = FastAPI(
    title="TradeSense API",
    description="Advanced Trading Analytics Platform API",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "https://*.replit.dev",
        "https://*.replit.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
analytics_service = AnalyticsService()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class AnalysisRequest(BaseModel):
    data: List[Dict[str, Any]]
    analysis_type: str = "comprehensive"

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str

class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime
    request_id: str

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "tradesense_jwt_secret_key_2024")
JWT_ALGORITHM = "HS256"

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token for user."""
    payload = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "email": user_data["email"],
        "role": user_data["role"],
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = verify_jwt_token(credentials.credentials)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Error handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            timestamp=datetime.utcnow(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="ValidationError",
            message=f"Invalid request data: {exc.errors()}",
            timestamp=datetime.utcnow(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message="Internal server error",
            timestamp=datetime.utcnow(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Add request ID
    request_id = str(uuid.uuid4())
    
    # Log request
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Request {request_id} completed in {process_time:.3f}s with status {response.status_code}")
    
    return response

# Health check endpoints
@app.get("/health")
async def health_check():
    db_healthy = DatabaseManager.health_check()
    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "TradeSense API",
        "timestamp": datetime.utcnow(),
        "database": "healthy" if db_healthy else "unhealthy",
        "version": "2.0.0"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    db_stats = DatabaseManager.get_stats()
    return {
        "status": "healthy",
        "service": "TradeSense API",
        "timestamp": datetime.utcnow(),
        "database": db_stats,
        "system": {
            "python_version": sys.version,
            "platform": sys.platform
        }
    }

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    try:
        if AuthManager:
            auth_manager = AuthManager()
            result = auth_manager.login_user(request.username, request.password)
            if result["success"]:
                token = create_jwt_token(result["user"])
                return {
                    "success": True,
                    "token": token,
                    "user": result["user"]
                }
            raise HTTPException(status_code=401, detail=result["message"])
        else:
            # Mock authentication for development
            mock_user = {
                "id": "1",
                "username": request.username,
                "email": f"{request.username}@example.com",
                "role": "user"
            }
            token = create_jwt_token(mock_user)
            return {
                "success": True,
                "token": token,
                "user": mock_user
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    try:
        if AuthManager:
            auth_manager = AuthManager()
            result = auth_manager.register_user(request.username, request.email, request.password)
            if result["success"]:
                return {"success": True, "message": "Registration successful"}
            raise HTTPException(status_code=400, detail=result["message"])
        else:
            return {"success": True, "message": "Registration successful (mock)"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# Enhanced data upload endpoint
@app.post("/api/data/upload")
async def upload_trade_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    temp_path = None
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_ext = '.' + file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (10MB limit)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
        
        # Read uploaded file
        content = await file.read()
        
        # Save temporarily and process
        temp_path = f"temp_{current_user['user_id']}_{int(time.time())}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Load and validate data
        try:
            if file_ext == '.csv':
                df = pd.read_csv(temp_path)
            else:
                df = pd.read_excel(temp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
        # Validate data structure
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        required_columns = ['symbol', 'pnl']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Data validation
        if DataValidator:
            validator = DataValidator()
            validation_result = validator.validate_data(df)
            if not validation_result["valid"]:
                raise HTTPException(status_code=400, detail=validation_result["errors"])
        
        # Convert DataFrame to records for JSON response
        data_records = df.to_dict('records')
        
        logger.info(f"Successfully uploaded {len(df)} trades for user {current_user['user_id']}")
        
        return {
            "success": True,
            "rows": len(df),
            "columns": list(df.columns),
            "data": data_records,
            "message": "Data uploaded successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for user {current_user['user_id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

# Enhanced analytics endpoints
@app.post("/api/analytics/analyze")
async def analyze_data(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="No data provided for analysis")
        
        # Convert request data to DataFrame
        df = pd.DataFrame(request.data)
        
        # Ensure required columns exist
        required_columns = ['pnl']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Use the enhanced analytics service
        results = await analytics_service._calculate_comprehensive_analytics(df)
        
        logger.info(f"Analytics completed for user {current_user['user_id']}: {len(df)} trades analyzed")
        
        return {
            "success": True,
            "results": results,
            "metadata": {
                "analyzed_trades": len(df),
                "analysis_type": request.analysis_type,
                "timestamp": datetime.utcnow()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for user {current_user['user_id']}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/analytics/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Security: Users can only access their own data
        if current_user["user_id"] != user_id and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        
        analytics = await analytics_service.get_user_analytics(user_id, start_date, end_date)
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        return analytics
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard data: {str(e)}")

# Additional utility endpoints
@app.get("/api/analytics/symbols")
async def get_symbols(current_user: dict = Depends(get_current_user)):
    """Get list of traded symbols for the user."""
    # This would query the database for actual symbols
    return {
        "symbols": ["ES", "NQ", "YM", "RTY", "CL", "GC", "AAPL", "TSLA", "SPY"]
    }

@app.get("/api/analytics/metrics")
async def get_available_metrics(current_user: dict = Depends(get_current_user)):
    """Get list of available analytics metrics."""
    return {
        "metrics": [
            "total_pnl",
            "win_rate", 
            "profit_factor",
            "sharpe_ratio",
            "max_drawdown",
            "expectancy",
            "total_trades",
            "best_trade",
            "worst_trade",
            "max_consecutive_wins",
            "max_consecutive_losses"
        ]
    }

# Include the trades router
from backend.api.v1.trades import router as trades_router
app.include_router(trades_router, prefix="/api/v1", tags=["trades"])

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting TradeSense API server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        access_log=True
    )
