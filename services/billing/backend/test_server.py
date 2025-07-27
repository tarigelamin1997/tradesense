#!/usr/bin/env python3
"""Minimal test server for TradeSense"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create app
app = FastAPI(title="TradeSense Test API", version="2.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "message": "TradeSense Test Server Running"}

# Test login endpoint
@app.post("/api/v1/auth/login")
async def login(email: str, password: str):
    if email == "test@example.com" and password == "testpass123":
        return {
            "access_token": "test-token-123",
            "token_type": "bearer",
            "user": {
                "id": "test-user-1",
                "email": email,
                "full_name": "Test User",
                "subscription_tier": "free"
            }
        }
    return {"error": "Invalid credentials"}

# Test trades endpoint
@app.get("/api/v1/trades")
async def get_trades():
    return {
        "trades": [
            {
                "id": "1",
                "symbol": "AAPL",
                "side": "long",
                "quantity": 100,
                "entry_price": 150.00,
                "exit_price": 155.00,
                "profit_loss": 500.00,
                "entry_time": "2024-01-15T09:30:00",
                "exit_time": "2024-01-15T15:30:00"
            },
            {
                "id": "2",
                "symbol": "GOOGL",
                "side": "short",
                "quantity": 50,
                "entry_price": 2800.00,
                "exit_price": 2750.00,
                "profit_loss": 2500.00,
                "entry_time": "2024-01-16T10:00:00",
                "exit_time": "2024-01-16T14:00:00"
            }
        ],
        "total": 2
    }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "TradeSense Test API", "docs": "/docs"}

if __name__ == "__main__":
    print("🚀 Starting TradeSense Test Server...")
    print("📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)