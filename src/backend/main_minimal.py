"""
Minimal FastAPI app for Railway deployment
"""
import os
import sys

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create minimal app
app = FastAPI(
    title="TradeSense API",
    description="Minimal deployment for Railway",
    version="1.0.0"
)

# Configure CORS with cleaned origins
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
if cors_origins_raw != "*":
    # Clean up any formatting issues
    cors_origins_raw = cors_origins_raw.replace(";", ",").replace("\n", "").replace("\\n", "")
    cors_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
else:
    cors_origins = ["*"]

print(f"CORS Origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "tradesense-backend"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "TradeSense API - Minimal",
        "status": "operational",
        "version": "1.0.0"
    }

# Basic auth endpoints (placeholders)
@app.post("/api/v1/auth/login")
async def login():
    return {"message": "Login endpoint - minimal mode"}

@app.post("/api/v1/auth/register")
async def register():
    return {"message": "Register endpoint - minimal mode"}

@app.get("/api/v1/auth/me")
async def me():
    return {"message": "Me endpoint - minimal mode"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting minimal backend on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)