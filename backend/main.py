
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
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your existing modules
try:
    from auth import AuthManager
    from analytics import compute_basic_stats, performance_over_time, calculate_kpis
    from data_validation import DataValidator
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    AuthManager = None
    DataValidator = None

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
JWT_SECRET = "tradesense_jwt_secret_key_2024"
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

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TradeSense API", "timestamp": datetime.utcnow()}

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
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

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    if AuthManager:
        auth_manager = AuthManager()
        result = auth_manager.register_user(request.username, request.email, request.password)
        if result["success"]:
            return {"success": True, "message": "Registration successful"}
        raise HTTPException(status_code=400, detail=result["message"])
    else:
        return {"success": True, "message": "Registration successful (mock)"}

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
        # Read uploaded file
        content = await file.read()
        
        # Save temporarily and process
        temp_path = f"temp_{current_user['user_id']}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Load and validate data
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(temp_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")
        except Exception as e:
            os.remove(temp_path)
            raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
        # Data validation
        if DataValidator:
            validator = DataValidator()
            validation_result = validator.validate_data(df)
            if not validation_result["valid"]:
                os.remove(temp_path)
                raise HTTPException(status_code=400, detail=validation_result["errors"])
        
        # Convert DataFrame to records for JSON response
        data_records = df.to_dict('records')
        
        # Clean up
        os.remove(temp_path)
        
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
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
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
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No data provided for analysis")
        
        # Ensure required columns exist
        required_columns = ['pnl']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {missing_columns}"
            )
        
        # Run comprehensive analysis
        results = {}
        
        # Basic statistics
        if compute_basic_stats:
            basic_stats = compute_basic_stats(df)
            results.update(basic_stats)
        
        # Performance over time
        if performance_over_time and 'exit_time' in df.columns:
            try:
                perf_data = performance_over_time(df)
                results['performance_over_time'] = perf_data.to_dict('records') if not perf_data.empty else []
            except Exception as e:
                print(f"Performance over time analysis failed: {e}")
                results['performance_over_time'] = []
        
        # KPIs
        if calculate_kpis:
            try:
                kpis = calculate_kpis(df)
                results.update(kpis)
            except Exception as e:
                print(f"KPI calculation failed: {e}")
        
        # Additional calculated metrics
        if 'pnl' in df.columns:
            pnl_data = pd.to_numeric(df['pnl'], errors='coerce').dropna()
            
            if not pnl_data.empty:
                results.update({
                    'total_pnl': float(pnl_data.sum()),
                    'total_trades': len(pnl_data),
                    'winning_trades': len(pnl_data[pnl_data > 0]),
                    'losing_trades': len(pnl_data[pnl_data < 0]),
                    'best_trade': float(pnl_data.max()),
                    'worst_trade': float(pnl_data.min()),
                    'avg_trade': float(pnl_data.mean()),
                    'median_trade': float(pnl_data.median()),
                    'std_dev': float(pnl_data.std()),
                })
                
                # Win rate
                win_rate = (len(pnl_data[pnl_data > 0]) / len(pnl_data) * 100) if len(pnl_data) > 0 else 0
                results['win_rate'] = win_rate
                
                # Profit factor
                gross_profit = pnl_data[pnl_data > 0].sum() if len(pnl_data[pnl_data > 0]) > 0 else 0
                gross_loss = abs(pnl_data[pnl_data < 0].sum()) if len(pnl_data[pnl_data < 0]) > 0 else 0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                results['profit_factor'] = float(profit_factor) if profit_factor != float('inf') else 999
                
                # Expectancy
                results['expectancy'] = float(pnl_data.mean())
                
                # Sharpe ratio (simplified)
                if len(pnl_data) > 1:
                    sharpe_ratio = pnl_data.mean() / pnl_data.std() if pnl_data.std() > 0 else 0
                    results['sharpe_ratio'] = float(sharpe_ratio)
                
                # Max drawdown calculation
                cumulative_pnl = pnl_data.cumsum()
                running_max = cumulative_pnl.expanding().max()
                drawdown = running_max - cumulative_pnl
                results['max_drawdown'] = float(drawdown.max())
                
                # Equity curve
                results['equity_curve'] = cumulative_pnl.tolist()
                
                # Risk-reward ratio
                avg_win = pnl_data[pnl_data > 0].mean() if len(pnl_data[pnl_data > 0]) > 0 else 0
                avg_loss = abs(pnl_data[pnl_data < 0].mean()) if len(pnl_data[pnl_data < 0]) > 0 else 0
                results['reward_risk'] = float(avg_win / avg_loss) if avg_loss > 0 else 0
        
        # Ensure all numeric values are JSON serializable
        for key, value in results.items():
            if isinstance(value, (np.int64, np.int32)):
                results[key] = int(value)
            elif isinstance(value, (np.float64, np.float32)):
                results[key] = float(value)
            elif pd.isna(value):
                results[key] = None
        
        return {
            "success": True,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/analytics/dashboard/{user_id}")
async def get_dashboard_data(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Mock dashboard data for now
        # In production, this would fetch from database
        dashboard_data = {
            "total_trades": 1250,
            "win_rate": 68.5,
            "profit_factor": 1.85,
            "total_pnl": 125430.50,
            "best_day": 15420.30,
            "worst_day": -8945.20,
            "max_drawdown": -12500.00,
            "sharpe_ratio": 1.42,
            "avg_daily_pnl": 245.50,
            "risk_reward_ratio": 1.75,
            "equity_curve": [
                {"date": "Trade 1", "cumulativePnL": 150},
                {"date": "Trade 2", "cumulativePnL": 320},
                {"date": "Trade 3", "cumulativePnL": 180},
                {"date": "Trade 4", "cumulativePnL": 450},
                {"date": "Trade 5", "cumulativePnL": 820}
            ],
            "pnl_distribution": [
                {"range": "< -$1000", "count": 15},
                {"range": "-$1000 to -$500", "count": 45},
                {"range": "-$500 to -$100", "count": 120},
                {"range": "-$100 to $0", "count": 280},
                {"range": "$0 to $100", "count": 380},
                {"range": "$100 to $500", "count": 250},
                {"range": "$500 to $1000", "count": 85},
                {"range": "> $1000", "count": 75}
            ],
            "symbol_breakdown": [
                {"name": "ES", "trades": 450, "winRate": 72, "pnl": 85420},
                {"name": "NQ", "trades": 320, "winRate": 65, "pnl": 42180},
                {"name": "YM", "trades": 280, "winRate": 68, "pnl": -2170},
                {"name": "RTY", "trades": 200, "winRate": 58, "pnl": 0}
            ]
        }
        
        return dashboard_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional utility endpoints
@app.get("/api/analytics/symbols")
async def get_symbols(current_user: dict = Depends(get_current_user)):
    """Get list of traded symbols for the user."""
    # Mock data - replace with database query
    return {
        "symbols": ["ES", "NQ", "YM", "RTY", "CL", "GC"]
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
            "worst_trade"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
