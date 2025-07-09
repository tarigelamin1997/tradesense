import sys
import os

# Add backend to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(backend_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

print("🚀 Starting TradeSense Backend (Isolated)...")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI(title="TradeSense API", version="2.6.1")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check endpoints
@app.get("/ping")
async def ping():
    return {"pong": True}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.6.1"}

@app.get("/")
async def root():
    return {"message": "TradeSense API is running", "version": "2.6.1"}

# Import routers one by one to isolate issues
print("📦 Loading routers...")

try:
    from backend.api.v1.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    print("✅ Auth router loaded")
except Exception as e:
    print(f"❌ Auth router failed: {e}")

try:
    from backend.api.v1.trades.router import router as trades_router
    app.include_router(trades_router, prefix="/api/v1/trades", tags=["trades"])
    print("✅ Trades router loaded")
except Exception as e:
    print(f"❌ Trades router failed: {e}")

try:
    from backend.api.v1.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
    print("✅ Analytics router loaded")
except Exception as e:
    print(f"❌ Analytics router failed: {e}")

try:
    from backend.api.v1.uploads.router import router as uploads_router
    app.include_router(uploads_router, prefix="/api/v1/uploads", tags=["uploads"])
    print("✅ Uploads router loaded")
except Exception as e:
    print(f"❌ Uploads router failed: {e}")

try:
    from backend.api.v1.features.router import router as features_router
    app.include_router(features_router, prefix="/api/v1/features", tags=["features"])
    print("✅ Features router loaded")
except Exception as e:
    print(f"❌ Features router failed: {e}")

try:
    from backend.api.v1.intelligence.router import router as intelligence_router
    app.include_router(intelligence_router, prefix="/api/v1/intelligence", tags=["intelligence"])
    print("✅ Intelligence router loaded")
except Exception as e:
    print(f"❌ Intelligence router failed: {e}")

try:
    from backend.api.v1.market_data.router import router as market_data_router
    app.include_router(market_data_router, prefix="/api/v1/market-data", tags=["market-data"])
    print("✅ Market data router loaded")
except Exception as e:
    print(f"❌ Market data router failed: {e}")

try:
    from backend.api.v1.portfolio.router import router as portfolio_router
    app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["portfolio"])
    print("✅ Portfolio router loaded")
except Exception as e:
    print(f"❌ Portfolio router failed: {e}")

try:
    from backend.api.v1.leaderboard.router import router as leaderboard_router
    app.include_router(leaderboard_router, prefix="/api/v1/leaderboard", tags=["leaderboard"])
    print("✅ Leaderboard router loaded")
except Exception as e:
    print(f"❌ Leaderboard router failed: {e}")

try:
    from backend.api.v1.notes.router import router as notes_router
    app.include_router(notes_router, prefix="/api/v1/notes", tags=["notes"])
    print("✅ Notes router loaded")
except Exception as e:
    print(f"❌ Notes router failed: {e}")

try:
    from backend.api.v1.milestones.router import router as milestones_router
    app.include_router(milestones_router, prefix="/api/v1/milestones", tags=["milestones"])
    print("✅ Milestones router loaded")
except Exception as e:
    print(f"❌ Milestones router failed: {e}")

try:
    from backend.api.v1.patterns.router import router as patterns_router
    app.include_router(patterns_router, prefix="/api/v1/patterns", tags=["patterns"])
    print("✅ Patterns router loaded")
except Exception as e:
    print(f"❌ Patterns router failed: {e}")

try:
    from backend.api.v1.playbooks.router import router as playbooks_router
    app.include_router(playbooks_router, prefix="/api/v1/playbooks", tags=["playbooks"])
    print("✅ Playbooks router loaded")
except Exception as e:
    print(f"❌ Playbooks router failed: {e}")

try:
    from backend.api.v1.reviews.router import router as reviews_router
    app.include_router(reviews_router, prefix="/api/v1/reviews", tags=["reviews"])
    print("✅ Reviews router loaded")
except Exception as e:
    print(f"❌ Reviews router failed: {e}")

try:
    from backend.api.v1.strategies.router import router as strategies_router
    app.include_router(strategies_router, prefix="/api/v1/strategies", tags=["strategies"])
    print("✅ Strategies router loaded")
except Exception as e:
    print(f"❌ Strategies router failed: {e}")

try:
    from backend.api.v1.journal.router import router as journal_router
    app.include_router(journal_router, prefix="/api/v1/journal", tags=["journal"])
    print("✅ Journal router loaded")
except Exception as e:
    print(f"❌ Journal router failed: {e}")

try:
    from backend.api.v1.tags.router import router as tags_router
    app.include_router(tags_router, prefix="/api/v1/tags", tags=["tags"])
    print("✅ Tags router loaded")
except Exception as e:
    print(f"❌ Tags router failed: {e}")

try:
    from backend.api.v1.reflections.router import router as reflections_router
    app.include_router(reflections_router, prefix="/api/v1/reflections", tags=["reflections"])
    print("✅ Reflections router loaded")
except Exception as e:
    print(f"❌ Reflections router failed: {e}")

try:
    from backend.api.v1.critique.router import router as critique_router
    app.include_router(critique_router, prefix="/api/v1/critique", tags=["critique"])
    print("✅ Critique router loaded")
except Exception as e:
    print(f"❌ Critique router failed: {e}")

try:
    from backend.api.v1.strategy_lab.router import router as strategy_lab_router
    app.include_router(strategy_lab_router, prefix="/api/v1/strategy-lab", tags=["strategy-lab"])
    print("✅ Strategy lab router loaded")
except Exception as e:
    print(f"❌ Strategy lab router failed: {e}")

try:
    from backend.api.v1.mental_map.router import router as mental_map_router
    app.include_router(mental_map_router, prefix="/api/v1/mental-map", tags=["mental-map"])
    print("✅ Mental map router loaded")
except Exception as e:
    print(f"❌ Mental map router failed: {e}")

try:
    from backend.api.v1.emotions.router import router as emotions_router
    app.include_router(emotions_router, prefix="/api/v1/emotions", tags=["emotions"])
    print("✅ Emotions router loaded")
except Exception as e:
    print(f"❌ Emotions router failed: {e}")

try:
    from backend.api.v1.health.performance_router import router as performance_router
    app.include_router(performance_router, prefix="/api/v1/performance", tags=["performance"])
    print("✅ Performance router loaded")
except Exception as e:
    print(f"❌ Performance router failed: {e}")

try:
    from backend.api.v1.health.router import router as health_router
    app.include_router(health_router, tags=["health"])
    print("✅ Health router loaded")
except Exception as e:
    print(f"❌ Health router failed: {e}")

print("🎉 Router loading complete!")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 