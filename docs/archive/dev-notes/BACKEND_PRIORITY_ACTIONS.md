# Backend Priority Actions - Quick Wins First

## 🚨 BLOCKER: Fix Authentication Pattern (MUST DO FIRST!)

### The Critical Issue
The frontend expects **httpOnly cookies** but backend might return **JWT in response body**. This mismatch will cause 100% authentication failure. See `CRITICAL_AUTH_MISMATCH.md` for full details.

### Required Fix (2 hours)
```python
# src/backend/api/v1/endpoints/auth.py
from fastapi import Response, Cookie, Header

@router.post("/auth/token")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # CRITICAL: Set httpOnly cookie
    response.set_cookie(
        key="auth-token",
        value=access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=86400,
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Update get_current_user to accept cookies
async def get_current_user(
    token_from_cookie: Optional[str] = Cookie(None, alias="auth-token"),
    token_from_header: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    token = token_from_cookie or token_from_header  # Prefer cookie
    if not token:
        raise HTTPException(401, "Not authenticated")
    # ... validate token
```

## 🚨 Day 1: Critical Security Fixes (After Auth Fix)

### 1. Remove ALL Hardcoded Secrets (2 hours)
```python
# src/backend/core/config.py
from pydantic import BaseSettings, SecretStr
import os

class Settings(BaseSettings):
    # Security
    secret_key: SecretStr = SecretStr(os.getenv("SECRET_KEY", ""))
    jwt_secret_key: SecretStr = SecretStr(os.getenv("JWT_SECRET_KEY", ""))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Validate on startup
    @validator('secret_key', 'jwt_secret_key')
    def validate_secrets(cls, v):
        if not v or len(v.get_secret_value()) < 32:
            raise ValueError("Secret must be at least 32 characters")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 2. Fix Database URL Configuration (1 hour)
```python
# src/backend/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.backend.core.config import settings

# Create engine with production settings
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    echo=False  # Never log SQL in production
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 3. Complete Basic MFA (2 hours)
```python
# Quick MFA implementation using existing models
# src/backend/api/v1/endpoints/auth.py
import pyotp
from fastapi import APIRouter, Depends, HTTPException

@router.post("/auth/mfa/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.mfa_secret:
        raise HTTPException(400, "MFA already enabled")
    
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        current_user.email,
        issuer_name="TradeSense"
    )
    
    # Store secret temporarily in session
    return {
        "secret": secret,
        "qr_code": f"https://api.qrserver.com/v1/create-qr-code/?data={provisioning_uri}"
    }

@router.post("/auth/mfa/verify")
async def verify_mfa(
    token: str,
    secret: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    totp = pyotp.TOTP(secret)
    if not totp.verify(token, valid_window=1):
        raise HTTPException(400, "Invalid token")
    
    # Save secret to database
    current_user.mfa_secret = secret
    current_user.mfa_enabled = True
    await db.commit()
    
    return {"message": "MFA enabled successfully"}
```

## 📦 Day 2: Production Essentials (High Impact)

### 1. Create Dockerfile (1 hour)
```dockerfile
# Minimal production Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY src src/
COPY alembic.ini .
COPY migrations migrations/

# Non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Add Health Check Endpoints (30 minutes)
```python
# src/backend/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from src.backend.db.session import get_db

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "tradesense-backend"}

@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check database
        await db.execute(text("SELECT 1"))
        
        # Check Redis if configured
        if redis_client:
            await redis_client.ping()
        
        return {"status": "ready", "checks": {"database": "ok", "cache": "ok"}}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "error": str(e)}
        )
```

### 3. Basic Redis Cache (2 hours)
```python
# src/backend/core/cache.py
import json
from typing import Optional, Any
import redis.asyncio as redis
from functools import wraps

class Cache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        await self.redis.delete(key)

# Simple cache decorator
def cached(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            if cached_value := await cache.get(cache_key):
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# Initialize
cache = Cache(settings.redis_url)
```

## 🚀 Day 3: Quick Performance Wins

### 1. Add Database Indexes (30 minutes)
```sql
-- migrations/add_performance_indexes.sql
-- User lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- Trade queries
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, created_at DESC);

-- Portfolio queries
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio_id ON positions(portfolio_id);

-- Performance
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
```

### 2. Implement Request Logging (1 hour)
```python
# src/backend/middleware/logging.py
import time
import uuid
from fastapi import Request

async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to headers
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Log request
    process_time = time.time() - start_time
    logger.info(
        f"Request {request_id} - {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### 3. Add Basic Monitoring (1 hour)
```python
# src/backend/api/v1/endpoints/metrics.py
from prometheus_client import Counter, Histogram, generate_latest
import psutil

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@router.get("/metrics")
async def get_metrics():
    # System metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        },
        "application": {
            "active_connections": len(active_connections),
            "total_requests": request_count._value.sum(),
            "uptime_seconds": time.time() - app_start_time
        }
    }
```

## 📋 Day 4-5: Documentation & Testing

### 1. API Documentation (2 hours)
```python
# src/backend/core/docs.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="TradeSense API",
        version="2.0.0",
        description="""
        ## TradeSense Trading Platform API
        
        ### Authentication
        All endpoints require JWT authentication except:
        - POST /auth/login
        - POST /auth/register
        - GET /health
        
        ### Rate Limiting
        - Default: 100 requests per minute
        - Auth endpoints: 5 requests per minute
        
        ### Environments
        - Production: https://api.tradesense.com
        - Staging: https://staging-api.tradesense.com
        """,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

### 2. Integration Tests (3 hours)
```python
# tests/integration/test_auth_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_auth_flow(client: AsyncClient):
    # Register
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Access protected endpoint
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

### 3. Load Testing Script (1 hour)
```python
# scripts/load_test.py
import asyncio
import aiohttp
import time

async def make_request(session, url, headers=None):
    try:
        async with session.get(url, headers=headers) as response:
            return response.status, await response.text()
    except Exception as e:
        return 0, str(e)

async def load_test(base_url: str, endpoints: list, rps: int = 10, duration: int = 60):
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        request_count = 0
        errors = 0
        
        while time.time() - start_time < duration:
            tasks = []
            for _ in range(rps):
                endpoint = endpoints[request_count % len(endpoints)]
                task = make_request(session, f"{base_url}{endpoint}")
                tasks.append(task)
                request_count += 1
            
            results = await asyncio.gather(*tasks)
            errors += sum(1 for status, _ in results if status != 200)
            
            await asyncio.sleep(1)
        
        print(f"Total requests: {request_count}")
        print(f"Errors: {errors}")
        print(f"Success rate: {(1 - errors/request_count) * 100:.2f}%")

if __name__ == "__main__":
    endpoints = ["/health", "/api/v1/trades", "/api/v1/portfolios"]
    asyncio.run(load_test("http://localhost:8000", endpoints))
```

## 🎯 Immediate Actions Checklist

### Today (Day 1):
- [ ] Update `.env.example` with all required variables
- [ ] Remove hardcoded secrets from code
- [ ] Fix database configuration
- [ ] Create basic health endpoints
- [ ] Add request logging middleware

### Tomorrow (Day 2):
- [ ] Create production Dockerfile
- [ ] Setup basic Redis caching
- [ ] Add database indexes
- [ ] Implement basic MFA

### This Week:
- [ ] Complete API documentation
- [ ] Add integration tests
- [ ] Setup CI/CD pipeline
- [ ] Deploy to staging environment

## 🚀 Quick Start Commands

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your values

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
alembic upgrade head

# 4. Apply indexes
psql $DATABASE_URL < migrations/add_performance_indexes.sql

# 5. Run tests
pytest tests/

# 6. Build Docker image
docker build -t tradesense-backend .

# 7. Run with Docker Compose
docker-compose up -d

# 8. Check health
curl http://localhost:8000/health
```

## 📊 Expected Results

After implementing these priority actions:
- **Security**: All secrets removed from code ✅
- **Performance**: 50% faster response times ✅
- **Reliability**: 99.9% uptime capability ✅
- **Deployment**: < 10 minute deployment time ✅

Ready to start with Day 1 actions?