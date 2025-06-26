from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import os

# Import routers
from backend.api.v1.analytics.router import router as analytics_router
from backend.api.v1.auth.router import router as auth_router
from backend.api.v1.users.router import router as users_router
from backend.api.v1.trades.router import router as trades_router
from backend.api.v1.uploads.router import router as uploads_router
from backend.api.v1.tags.router import router as tags_router
from backend.api.v1.strategies.router import router as strategies_router
from backend.api.v1.notes.router import router as notes_router
from backend.api.v1.reflections.router import router as reflections_router
from backend.api.v1.critique.router import router as critique_router
from backend.api.v1.analytics.streaks import router as streaks_router
from backend.api.v1.analytics.heatmap import router as heatmap_router
from backend.api.v1.analytics.edge_strength import router as edge_strength_router
from backend.api.v1.trades.search import router as trade_search_router
from backend.api.v1.milestones.router import router as milestones_router
# Assuming these routers exist based on the user story.
from backend.api.v1.accounts.router import router as accounts_router
from backend.api.v1.leaderboard.router import router as leaderboard_router
from backend.api.v1.mental_map import router as mental_map_router
from backend.api.v1.patterns.router import router as patterns_router
from backend.api.v1.playbooks.router import router as playbooks_router
from backend.api.v1.reviews.router import router as reviews_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend/logs/tradesense.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TradeSense API",
    description="Professional Trading Analytics Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Global exception handler
@app.exception_handler(Request, Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check
@app.get("/")
async def root():
    return {"message": "TradeSense API is running", "status": "healthy"}

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(trades_router)
app.include_router(notes_router)  # Journal entries
app.include_router(tags_router)
app.include_router(strategies_router)
app.include_router(uploads_router)
app.include_router(users_router)
app.include_router(analytics_router, prefix="/api/v1/analytics")
app.include_router(edge_strength_router, prefix="/api/v1/analytics")
app.include_router(heatmap_router, prefix="/api/v1/analytics", tags=["heatmap"])
app.include_router(streaks_router, prefix="/api/v1/analytics", tags=["streaks"])
app.include_router(critique_router, prefix="/api/v1/critique")
app.include_router(reflections_router, prefix="/api/v1/reflections")
app.include_router(milestones_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")
app.include_router(leaderboard_router, prefix="/api/v1")
app.include_router(mental_map_router, prefix="/api/v1/mental-map", tags=["mental-map"])
app.include_router(patterns_router, prefix="/api/v1/patterns", tags=["patterns"])
app.include_router(playbooks_router, prefix="/api/v1/playbooks", tags=["playbooks"])
app.include_router(reviews_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )