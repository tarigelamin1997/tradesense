#!/usr/bin/env python3
"""
Comprehensive import checker for TradeSense
Simulates the startup process to catch all import errors
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

print("🔍 Checking all imports in TradeSense backend...")
print("=" * 50)

errors = []

# Set minimal environment variables to prevent config errors
os.environ['JWT_SECRET_KEY'] = 'test-key-for-import-check'
os.environ['DATABASE_URL'] = 'postgresql://test@localhost/test'

try:
    print("\n1️⃣ Checking core modules...")
    from core import config, db, cache, security
    print("✅ Core modules OK")
except Exception as e:
    errors.append(f"Core modules: {e}")
    print(f"❌ Core modules: {e}")

try:
    print("\n2️⃣ Checking models...")
    import models
    print("✅ Models OK")
except Exception as e:
    errors.append(f"Models: {e}")
    print(f"❌ Models: {e}")

try:
    print("\n3️⃣ Checking services...")
    from services import (
        trade_intelligence_engine,
        critique_engine,
        behavioral_analytics,
        edge_strength,
        pattern_detection,
        emotional_analytics,
        market_context,
        feature_flag_service
    )
    print("✅ Services OK")
except Exception as e:
    errors.append(f"Services: {e}")
    print(f"❌ Services: {e}")

try:
    print("\n4️⃣ Checking API routers...")
    from api.v1.auth.router import router as auth_router
    from api.v1.trades.router import router as trades_router
    from api.v1.analytics.router import router as analytics_router
    from api.v1.uploads.router import router as uploads_router
    from api.v1.features.router import router as features_router
    from api.v1.portfolio.router import router as portfolio_router
    from api.v1.intelligence.router import router as intelligence_router
    from api.v1.market_data.router import router as market_data_router
    from api.v1.leaderboard.router import router as leaderboard_router
    from api.v1.notes.router import router as notes_router
    from api.v1.milestones.router import router as milestones_router
    from api.v1.patterns.router import router as patterns_router
    from api.v1.playbooks.router import router as playbooks_router
    from api.v1.reviews.router import router as reviews_router
    from api.v1.strategies.router import router as strategies_router
    from api.v1.journal.router import router as journal_router
    from api.v1.tags.router import router as tags_router
    from api.v1.reflections.router import router as reflections_router
    from api.v1.critique.router import router as critique_router
    from api.v1.strategy_lab.router import router as strategy_lab_router
    from api.v1.mental_map.router import router as mental_map_router
    from api.v1.emotions.router import router as emotions_router
    from api.v1.health.performance_router import router as performance_router
    from api.v1.health.router import router as health_router
    from api.v1.billing.router import router as billing_router
    from api.v1.websocket.router import router as websocket_router
    from api.v1.ai.router import router as ai_router
    from api.v1.feedback.router import router as feedback_router
    print("✅ API v1 routers OK")
except Exception as e:
    errors.append(f"API v1 routers: {e}")
    print(f"❌ API v1 routers: {e}")

try:
    print("\n5️⃣ Checking additional API routers...")
    from api.admin import router as admin_router
    from api.subscription import router as subscription_router
    from api.support import router as support_router
    from api.feature_flags import router as feature_flags_router
    from api.reporting import router as reporting_router
    from api.experiments import router as experiments_router
    from api.backup import router as backup_router
    from api.mfa import router as mfa_router
    from api.alerts import router as alerts_router
    from api.mobile import mobile_router
    from api.collaboration import router as collaboration_router
    print("✅ Additional API routers OK")
except Exception as e:
    errors.append(f"Additional API routers: {e}")
    print(f"❌ Additional API routers: {e}")

try:
    print("\n6️⃣ Checking main app creation...")
    from main import create_app
    app = create_app()
    print("✅ Main app creation OK")
except Exception as e:
    errors.append(f"Main app: {e}")
    print(f"❌ Main app: {e}")

print("\n" + "=" * 50)
print(f"\n📊 Summary:")
print(f"   Total errors: {len(errors)}")

if errors:
    print(f"\n❌ Import errors found:\n")
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")
    print("\nFix these errors before deployment!")
    sys.exit(1)
else:
    print("\n✅ All imports successful! Ready for deployment.")
    sys.exit(0)