import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(backend_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Initialize database first
try:
    print("🚀 Starting TradeSense Backend (Minimal)...")
    
    # Import all models first to register them with SQLAlchemy
    import backend.models  # This ensures all models are registered
    
    # Initialize database
    from backend.initialize_db import *

    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.middleware import setup_middleware
from backend.core.exceptions import setup_exception_handlers
from backend.api.v1.public import public_router
from backend.api.v1.auth.router import router as auth_router
from backend.api.v1.trades.router import router as trades_router
from backend.api.v1.analytics.router import router as analytics_router
from backend.api.v1.uploads.router import router as uploads_router
from backend.api.v1.features.router import router as features_router
from backend.api.v1.intelligence.router import router as intelligence_router
from backend.api.v1.market_data.router import router as market_data_router
from backend.api.v1.portfolio.router import router as portfolio_router
from backend.api.v1.leaderboard.router import router as leaderboard_router
from backend.api.v1.notes.router import router as notes_router
from backend.api.v1.milestones.router import router as milestones_router
from backend.api.v1.patterns.router import router as patterns_router
from backend.api.v1.playbooks.router import router as playbooks_router
from backend.api.v1.reviews.router import router as reviews_router
from backend.api.v1.strategies.router import router as strategies_router
from backend.api.v1.journal.router import router as journal_router
from backend.api.v1.tags.router import router as tags_router
from backend.api.v1.reflections.router import router as reflections_router
from backend.api.v1.critique.router import router as critique_router
from backend.api.v1.strategy_lab.router import router as strategy_lab_router
from backend.api.v1.mental_map.router import router as mental_map_router
from backend.api.v1.emotions.router import router as emotions_router

app = FastAPI()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup middleware and exception handlers
setup_middleware(app)
setup_exception_handlers(app)

app.include_router(public_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(trades_router, prefix="/api/v1/trades")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(features_router, prefix="/api/v1/features", tags=["features"])
app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(market_data_router, prefix="/api/v1/market-data", tags=["market-data"])
app.include_router(portfolio_router, prefix="/api/v1/portfolio")
app.include_router(leaderboard_router, prefix="/api/v1/leaderboard")
app.include_router(notes_router, prefix="/api/v1/notes")
app.include_router(milestones_router, prefix="/api/v1/milestones")
app.include_router(patterns_router, prefix="/api/v1/patterns")
app.include_router(playbooks_router, prefix="/api/v1/playbooks")
app.include_router(reviews_router, prefix="/api/v1/reviews")
app.include_router(strategies_router, prefix="/api/v1/strategies")
app.include_router(journal_router, prefix="/api/v1/journal")
app.include_router(tags_router, prefix="/api/v1/tags")
app.include_router(reflections_router, prefix="/api/v1/reflections")
app.include_router(critique_router, prefix="/api/v1/critique")
app.include_router(strategy_lab_router, prefix="/api/v1/strategy-lab")
app.include_router(mental_map_router, prefix="/api/v1/mental-map")
app.include_router(emotions_router, prefix="/api/v1/emotions") 