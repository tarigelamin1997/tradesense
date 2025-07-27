import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="TradeSense API", version="2.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TradeSense API", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "tradesense-backend"}

@app.get("/api")
async def api_root():
    return {"message": "TradeSense API v2.0", "status": "operational"}

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "tradesense-backend"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)