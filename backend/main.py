
#!/usr/bin/env python3
"""
TradeSense Backend API Server
FastAPI-based REST API for TradeSense trading analytics
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import json
import logging
import os
import sys
import jwt
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing modules
from auth import AuthManager
from core.analysis_engine import run_analysis
from analytics import AnalyticsEngine
from data_validation import DataValidator

app = FastAPI(
    title="TradeSense API",
    description="Advanced Trading Analytics Platform API",
    version="1.0.0"
)

# CORS middleware for frontend
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
auth_manager = AuthManager()

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

# JWT configuration
JWT_SECRET = "tradesense_jwt_secret_key_2024"  # In production, use environment variable
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
        # Verify JWT token
        payload = verify_jwt_token(credentials.credentials)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TradeSense API"}

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    result = auth_manager.login_user(request.username, request.password)
    if result["success"]:
        # Create JWT token
        token = create_jwt_token(result["user"])
        return {
            "success": True,
            "token": token,
            "user": result["user"]
        }
    raise HTTPException(status_code=401, detail=result["message"])

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    result = auth_manager.register_user(request.username, request.email, request.password)
    if result["success"]:
        return {"success": True, "message": "Registration successful"}
    raise HTTPException(status_code=400, detail=result["message"])

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# Data upload endpoint
@app.post("/api/data/upload")
async def upload_trade_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Read uploaded CSV
        content = await file.read()
        
        # Save temporarily and process
        temp_path = f"temp_{current_user['user_id']}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Validate and process data
        df = pd.read_csv(temp_path)
        
        if DataValidator:
            validator = DataValidator()
            validation_result = validator.validate_data(df)
            if not validation_result["valid"]:
                os.remove(temp_path)
                raise HTTPException(status_code=400, detail=validation_result["errors"])
        
        # Store processed data (implement your storage logic)
        # For now, return basic info
        os.remove(temp_path)
        
        return {
            "success": True,
            "rows": len(df),
            "columns": list(df.columns),
            "message": "Data uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.post("/api/analytics/analyze")
async def analyze_data(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Convert request data to DataFrame
        df = pd.DataFrame(request.data)
        
        # Run analysis using your existing engine
        analytics_engine = AnalyticsEngine()
        results = analytics_engine.generate_comprehensive_report(df)
        
        return {
            "success": True,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Implement dashboard data retrieval
        # This would fetch user's trade data and generate dashboard metrics
        dashboard_data = {
            "total_trades": 1250,
            "win_rate": 68.5,
            "profit_factor": 1.85,
            "total_pnl": 125430.50,
            "best_day": 15420.30,
            "worst_day": -8945.20
        }
        
        return dashboard_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
