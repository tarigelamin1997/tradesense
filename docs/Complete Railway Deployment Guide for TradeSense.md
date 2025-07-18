# **Complete Railway Deployment Guide for TradeSense**

## **Table of Contents**

1. [Executive Summary](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#executive-summary)  
2. [Railway Fundamentals](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#railway-fundamentals)  
3. [Pre-Deployment Checklist](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#pre-deployment-checklist)  
4. [Database Setup (PostgreSQL)](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#database-setup-postgresql)  
5. [Redis Configuration](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#redis-configuration)  
6. [Backend Deployment](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#backend-deployment)  
7. [Environment Variables Management](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#environment-variables-management)  
8. [Common Railway Issues & Solutions](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#common-railway-issues-solutions)  
9. [Production Configuration](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#production-configuration)  
10. [Monitoring & Debugging](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#monitoring-debugging)  
11. [Continuous Deployment](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#continuous-deployment)  
12. [Scaling Strategies](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#scaling-strategies)  
13. [Cost Optimization](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#cost-optimization)  
14. [Feature Deployment Workflow](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#feature-deployment-workflow)  
15. [Emergency Procedures](https://claude.ai/chat/95685fe6-7e6d-4539-84cd-5aee1d8672d0#emergency-procedures)

---

## **1\. Executive Summary**

### **Railway Key Concepts**

* **Projects**: Container for all your services  
* **Services**: Individual deployments (backend, database, redis)  
* **Environments**: Separate configs (production, staging)  
* **Deployments**: Each code push creates a new deployment  
* **Volumes**: Persistent storage for databases

### **Why Railway for TradeSense**

* **Zero DevOps**: No Kubernetes, Docker knowledge needed  
* **Instant PostgreSQL/Redis**: One-click provisioning  
* **Automatic HTTPS**: SSL certificates handled  
* **Built-in CI/CD**: GitHub integration  
* **Predictable Pricing**: $20 for starter, scales linearly

---

## **2\. Railway Fundamentals**

### **Service Architecture for TradeSense**

Railway Project: tradesense-production  
├── Services:  
│   ├── tradesense-backend (FastAPI)  
│   ├── postgres (Database)  
│   └── redis (Cache)  
├── Environments:  
│   ├── production  
│   └── staging (optional)  
└── Volumes:  
    └── postgres-data

### **Railway's Build Process**

1. **Detect**: Railway auto-detects Python via requirements.txt  
2. **Build**: Installs dependencies, builds app  
3. **Deploy**: Starts your app with detected start command  
4. **Route**: Assigns subdomain, configures networking

### **Critical Railway Behaviors**

\# Railway defaults you MUST know:  
PORT: Dynamically assigned (use $PORT)  
Build: Nixpacks by default  
Start: Gunicorn auto-detected for Python  
Health: No health checks by default  
Restart: Automatic on crash  
Logs: Retained for 7 days

---

## **3\. Pre-Deployment Checklist**

### **Backend Code Requirements**

\# ✅ CORRECT: Use Railway's PORT  
import os  
import uvicorn

if \_\_name\_\_ \== "\_\_main\_\_":  
    port \= int(os.environ.get("PORT", 8000))  
    uvicorn.run("main:app", host="0.0.0.0", port=port)

\# ❌ WRONG: Hardcoded port  
uvicorn.run("main:app", host="localhost", port=8000)

### **File Structure Check**

src/backend/  
├── requirements.txt      \# REQUIRED: Dependencies  
├── railway.json         \# OPTIONAL: Custom config  
├── Procfile            \# OPTIONAL: Custom start command  
├── runtime.txt         \# OPTIONAL: Python version  
├── .env.example        \# REQUIRED: Document env vars  
└── main.py            \# REQUIRED: Entry point

### **Requirements.txt Optimization**

\# ✅ GOOD: Pinned versions  
fastapi==0.104.1  
uvicorn\[standard\]==0.24.0  
sqlalchemy==2.0.23  
alembic==1.12.1  
redis==5.0.1  
psycopg2-binary==2.9.9

\# ❌ BAD: Unpinned versions  
fastapi  
uvicorn  
sqlalchemy

### **Railway.json (Optional but Recommended)**

{  
  "$schema": "https://railway.app/railway.schema.json",  
  "build": {  
    "builder": "NIXPACKS",  
    "buildCommand": "cd src/backend && pip install \-r requirements.txt"  
  },  
  "deploy": {  
    "startCommand": "cd src/backend && python main.py",  
    "healthcheckPath": "/health",  
    "healthcheckTimeout": 300,  
    "restartPolicyType": "ON\_FAILURE",  
    "restartPolicyMaxRetries": 10  
  }  
}

---

## **4\. Database Setup (PostgreSQL)**

### **One-Click PostgreSQL Setup**

1. **Add Service**: Click "New" → "Database" → "PostgreSQL"  
2. **Wait**: 30 seconds for provisioning  
3. **Connection**: Railway provides DATABASE\_URL automatically

### **PostgreSQL Configuration**

\# core/database.py  
import os  
from sqlalchemy import create\_engine  
from sqlalchemy.pool import QueuePool

\# Railway provides DATABASE\_URL  
DATABASE\_URL \= os.environ.get("DATABASE\_URL")

\# Fix for SQLAlchemy (Railway uses postgresql://, SQLAlchemy wants postgresql+psycopg2://)  
if DATABASE\_URL and DATABASE\_URL.startswith("postgres://"):  
    DATABASE\_URL \= DATABASE\_URL.replace("postgres://", "postgresql://", 1\)

\# Production-ready engine  
engine \= create\_engine(  
    DATABASE\_URL,  
    poolclass=QueuePool,  
    pool\_size=20,  
    max\_overflow=40,  
    pool\_pre\_ping=True,  \# Verify connections  
    pool\_recycle=300,    \# Recycle after 5 min  
    echo=False,          \# Set True for debugging  
    connect\_args={  
        "sslmode": "require",  \# Railway requires SSL  
        "connect\_timeout": 10,  
        "options": "-c statement\_timeout=30000"  \# 30s timeout  
    }  
)

### **Database Migrations**

\# 1\. Local: Generate migration  
alembic revision \--autogenerate \-m "initial migration"

\# 2\. Commit and push  
git add alembic/versions/  
git commit \-m "Add database migration"  
git push

\# 3\. Railway: Run migration (one-time command)  
railway run python \-m alembic upgrade head

\# OR: Auto-run on deploy (add to start command)  
\# railway.json  
{  
  "deploy": {  
    "startCommand": "alembic upgrade head && python main.py"  
  }  
}

### **Database Backup Strategy**

\# Manual backup  
railway run pg\_dump $DATABASE\_URL \> backup\_$(date \+%Y%m%d).sql

\# Automated daily backups (add to your app)  
\# services/backup\_service.py  
import os  
import subprocess  
from datetime import datetime  
import boto3  \# Upload to S3

async def backup\_database():  
    """Daily database backup"""  
    date \= datetime.now().strftime("%Y%m%d\_%H%M%S")  
    filename \= f"tradesense\_backup\_{date}.sql"  
      
    \# Dump database  
    subprocess.run(\[  
        "pg\_dump",  
        os.environ\["DATABASE\_URL"\],  
        "-f", filename  
    \])  
      
    \# Upload to S3  
    s3 \= boto3.client('s3')  
    s3.upload\_file(filename, 'tradesense-backups', filename)  
      
    \# Clean local file  
    os.remove(filename)

---

## **5\. Redis Configuration**

### **Redis Setup**

1. **Add Service**: "New" → "Database" → "Redis"  
2. **Connection**: REDIS\_URL provided automatically

### **Redis Connection Handler**

\# core/cache.py  
import os  
import redis  
from typing import Optional, Any  
import json  
import logging

logger \= logging.getLogger(\_\_name\_\_)

class RedisCache:  
    def \_\_init\_\_(self):  
        self.redis\_url \= os.environ.get("REDIS\_URL")  
        self.\_client \= None  
          
    @property  
    def client(self):  
        """Lazy connection to Redis"""  
        if not self.\_client and self.redis\_url:  
            try:  
                self.\_client \= redis.from\_url(  
                    self.redis\_url,  
                    decode\_responses=True,  
                    socket\_timeout=5,  
                    socket\_connect\_timeout=5,  
                    socket\_keepalive=True,  
                    socket\_keepalive\_options={},  
                    health\_check\_interval=30,  
                    retry\_on\_timeout=True,  
                    retry\_on\_error=\[redis.ConnectionError, redis.TimeoutError\]  
                )  
                \# Test connection  
                self.\_client.ping()  
                logger.info("Redis connected successfully")  
            except Exception as e:  
                logger.error(f"Redis connection failed: {e}")  
                self.\_client \= None  
        return self.\_client  
      
    async def get(self, key: str) \-\> Optional\[Any\]:  
        """Get value with fallback"""  
        if not self.client:  
            return None  
              
        try:  
            value \= self.client.get(key)  
            return json.loads(value) if value else None  
        except Exception as e:  
            logger.error(f"Redis get error: {e}")  
            return None  
      
    async def set(self, key: str, value: Any, ttl: int \= 300\) \-\> bool:  
        """Set value with error handling"""  
        if not self.client:  
            return False  
              
        try:  
            self.client.setex(key, ttl, json.dumps(value))  
            return True  
        except Exception as e:  
            logger.error(f"Redis set error: {e}")  
            return False

\# Global instance  
cache \= RedisCache()

### **Redis Best Practices**

\# 1\. Use key prefixes  
def make\_key(prefix: str, \*parts) \-\> str:  
    """Create consistent Redis keys"""  
    return f"tradesense:{prefix}:{':'.join(map(str, parts))}"

\# Usage  
user\_key \= make\_key("user", user\_id)  
trade\_key \= make\_key("trade", user\_id, trade\_id)

\# 2\. Implement cache-aside pattern  
async def get\_user\_stats(user\_id: str):  
    \# Try cache first  
    key \= make\_key("stats", user\_id)  
    cached \= await cache.get(key)  
    if cached:  
        return cached  
      
    \# Calculate if not cached  
    stats \= calculate\_expensive\_stats(user\_id)  
      
    \# Cache for 5 minutes  
    await cache.set(key, stats, ttl=300)  
      
    return stats

\# 3\. Handle Redis downtime gracefully  
def cache\_optional(func):  
    """Decorator: Continue if Redis is down"""  
    async def wrapper(\*args, \*\*kwargs):  
        try:  
            return await func(\*args, \*\*kwargs)  
        except redis.RedisError:  
            logger.warning(f"Redis error in {func.\_\_name\_\_}, continuing without cache")  
            \# Call original function without cache  
            return await calculate\_without\_cache(\*args, \*\*kwargs)  
    return wrapper

---

## **6\. Backend Deployment**

### **Step-by-Step Deployment**

\# 1\. Install Railway CLI  
npm install \-g @railway/cli

\# 2\. Login  
railway login

\# 3\. Link to project (first time)  
railway link

\# 4\. Deploy  
railway up

\# 5\. Check logs  
railway logs

\# 6\. Open in browser  
railway open

### **Deployment Configuration**

\# main.py \- Production-ready FastAPI setup  
import os  
import logging  
from contextlib import asynccontextmanager  
from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.middleware.gzip import GZipMiddleware  
from prometheus\_fastapi\_instrumentator import Instrumentator

\# Configure logging  
logging.basicConfig(  
    level=logging.INFO,  
    format='%(asctime)s \- %(name)s \- %(levelname)s \- %(message)s'  
)  
logger \= logging.getLogger(\_\_name\_\_)

@asynccontextmanager  
async def lifespan(app: FastAPI):  
    """Startup and shutdown events"""  
    \# Startup  
    logger.info("Starting TradeSense backend...")  
      
    \# Initialize database  
    from core.database import init\_db  
    await init\_db()  
      
    \# Warm up cache  
    from core.cache import cache  
    if cache.client:  
        await cache.client.ping()  
      
    yield  
      
    \# Shutdown  
    logger.info("Shutting down TradeSense backend...")  
      
    \# Close database connections  
    from core.database import engine  
    engine.dispose()

\# Create app with lifespan  
app \= FastAPI(  
    title="TradeSense API",  
    version="2.0.0",  
    lifespan=lifespan  
)

\# Middleware  
app.add\_middleware(  
    CORSMiddleware,  
    allow\_origins=os.environ.get("CORS\_ORIGINS", "").split(","),  
    allow\_credentials=True,  
    allow\_methods=\["\*"\],  
    allow\_headers=\["\*"\],  
)

app.add\_middleware(GZipMiddleware, minimum\_size=1000)

\# Prometheus metrics  
Instrumentator().instrument(app).expose(app)

\# Health check  
@app.get("/health")  
async def health\_check():  
    """Railway health check endpoint"""  
    checks \= {  
        "status": "healthy",  
        "database": "unknown",  
        "redis": "unknown"  
    }  
      
    \# Check database  
    try:  
        from core.database import engine  
        with engine.connect() as conn:  
            conn.execute("SELECT 1")  
        checks\["database"\] \= "healthy"  
    except Exception as e:  
        checks\["database"\] \= f"unhealthy: {str(e)}"  
        checks\["status"\] \= "unhealthy"  
      
    \# Check Redis  
    try:  
        from core.cache import cache  
        if cache.client:  
            cache.client.ping()  
            checks\["redis"\] \= "healthy"  
        else:  
            checks\["redis"\] \= "not configured"  
    except Exception as e:  
        checks\["redis"\] \= f"unhealthy: {str(e)}"  
      
    return checks

\# Include routers  
from api.v1 import auth, trades, analytics  
app.include\_router(auth.router, prefix="/api/v1/auth", tags=\["auth"\])  
app.include\_router(trades.router, prefix="/api/v1/trades", tags=\["trades"\])  
app.include\_router(analytics.router, prefix="/api/v1/analytics", tags=\["analytics"\])

if \_\_name\_\_ \== "\_\_main\_\_":  
    import uvicorn  
      
    port \= int(os.environ.get("PORT", 8000))  
    workers \= int(os.environ.get("WEB\_CONCURRENCY", 1))  
      
    logger.info(f"Starting server on port {port} with {workers} workers")  
      
    if workers \> 1:  
        \# Multi-worker setup for production  
        uvicorn.run(  
            "main:app",  
            host="0.0.0.0",  
            port=port,  
            workers=workers,  
            loop="uvloop",  
            access\_log=False  \# Use structured logging instead  
        )  
    else:  
        \# Single worker for development  
        uvicorn.run(  
            "main:app",  
            host="0.0.0.0",  
            port=port,  
            reload=os.environ.get("ENVIRONMENT") \== "development"  
        )

### **Procfile (Optional for Custom Commands)**

web: cd src/backend && python main.py  
release: cd src/backend && alembic upgrade head  
worker: cd src/backend && python worker.py

---

## **7\. Environment Variables Management**

### **Railway Environment Variables**

\# Set via CLI  
railway variables set KEY=value

\# Set multiple  
railway variables set KEY1=value1 KEY2=value2

\# Set from .env file  
railway variables set $(cat .env)

\# List all  
railway variables

\# Delete  
railway variables delete KEY

### **Environment Configuration**

\# core/config.py  
import os  
from typing import List, Optional  
from pydantic import BaseSettings, validator  
import secrets

class Settings(BaseSettings):  
    """Production-ready settings with validation"""  
      
    \# Environment  
    ENVIRONMENT: str \= "production"  
    DEBUG: bool \= False  
      
    \# Security  
    SECRET\_KEY: str \= secrets.token\_urlsafe(32)  
    JWT\_SECRET\_KEY: str \= secrets.token\_urlsafe(32)  
    JWT\_ALGORITHM: str \= "HS256"  
    ACCESS\_TOKEN\_EXPIRE\_MINUTES: int \= 30  
      
    \# Database  
    DATABASE\_URL: str  
      
    @validator("DATABASE\_URL", pre=True)  
    def fix\_postgres\_url(cls, v: str) \-\> str:  
        """Fix Railway's postgres:// to postgresql://"""  
        if v and v.startswith("postgres://"):  
            return v.replace("postgres://", "postgresql://", 1\)  
        return v  
      
    \# Redis  
    REDIS\_URL: Optional\[str\] \= None  
      
    \# CORS  
    CORS\_ORIGINS\_STR: str \= ""  
      
    @property  
    def CORS\_ORIGINS(self) \-\> List\[str\]:  
        return \[origin.strip() for origin in self.CORS\_ORIGINS\_STR.split(",") if origin.strip()\]  
      
    \# Stripe  
    STRIPE\_SECRET\_KEY: Optional\[str\] \= None  
    STRIPE\_WEBHOOK\_SECRET: Optional\[str\] \= None  
    STRIPE\_PRICE\_ID\_PRO: Optional\[str\] \= None  
    STRIPE\_PRICE\_ID\_TEAM: Optional\[str\] \= None  
      
    \# Email  
    SMTP\_HOST: Optional\[str\] \= None  
    SMTP\_PORT: int \= 587  
    SMTP\_USER: Optional\[str\] \= None  
    SMTP\_PASSWORD: Optional\[str\] \= None  
    FROM\_EMAIL: str \= "noreply@tradesense.ai"  
      
    \# Monitoring  
    SENTRY\_DSN: Optional\[str\] \= None  
      
    \# Railway specific  
    RAILWAY\_ENVIRONMENT: Optional\[str\] \= None  
    RAILWAY\_PROJECT\_ID: Optional\[str\] \= None  
    RAILWAY\_SERVICE\_ID: Optional\[str\] \= None  
      
    class Config:  
        case\_sensitive \= True  
        env\_file \= ".env"

\# Create global instance  
settings \= Settings()

\# Validate critical settings on startup  
def validate\_settings():  
    """Ensure critical settings are configured"""  
    errors \= \[\]  
      
    if settings.ENVIRONMENT \== "production":  
        if not settings.DATABASE\_URL:  
            errors.append("DATABASE\_URL not set")  
          
        if settings.SECRET\_KEY \== settings.JWT\_SECRET\_KEY:  
            errors.append("SECRET\_KEY and JWT\_SECRET\_KEY must be different")  
          
        if not settings.CORS\_ORIGINS:  
            errors.append("CORS\_ORIGINS\_STR not set")  
          
        if not settings.STRIPE\_SECRET\_KEY:  
            errors.append("STRIPE\_SECRET\_KEY not set for production")  
      
    if errors:  
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

\# Run validation  
if settings.ENVIRONMENT \== "production":  
    validate\_settings()

### **Environment Variables Template**

\# .env.railway.example

\# Core Settings  
ENVIRONMENT=production  
DEBUG=false

\# Security (generate with: openssl rand \-hex 32\)  
SECRET\_KEY=your-secret-key-here  
JWT\_SECRET\_KEY=your-jwt-secret-here

\# Database (provided by Railway)  
DATABASE\_URL=${{Postgres.DATABASE\_URL}}

\# Redis (provided by Railway)  
REDIS\_URL=${{Redis.REDIS\_URL}}

\# CORS  
CORS\_ORIGINS\_STR=https://tradesense.ai,https://www.tradesense.ai

\# Stripe  
STRIPE\_SECRET\_KEY=sk\_live\_...  
STRIPE\_WEBHOOK\_SECRET=whsec\_...  
STRIPE\_PRICE\_ID\_PRO=price\_...  
STRIPE\_PRICE\_ID\_TEAM=price\_...

\# Email (SendGrid)  
SMTP\_HOST=smtp.sendgrid.net  
SMTP\_PORT=587  
SMTP\_USER=apikey  
SMTP\_PASSWORD=SG.xxx  
FROM\_EMAIL=hello@tradesense.ai

\# Monitoring  
SENTRY\_DSN=https://xxx@sentry.io/xxx

\# Performance  
WEB\_CONCURRENCY=2

---

## **8\. Common Railway Issues & Solutions**

### **Issue 1: Build Failures**

**Problem**: "No start command found"

\# Solution 1: Add explicit start command in railway.json  
{  
  "deploy": {  
    "startCommand": "python main.py"  
  }  
}

\# Solution 2: Add Procfile  
web: python main.py

\# Solution 3: Ensure main.py has if \_\_name\_\_ \== "\_\_main\_\_":

**Problem**: "Module not found"

\# Solution: Fix Python path  
\# In main.py or any entry point:  
import sys  
import os  
sys.path.insert(0, os.path.dirname(os.path.abspath(\_\_file\_\_)))

### **Issue 2: Database Connection Errors**

**Problem**: "SSL required"

\# Solution: Add SSL to connection  
connect\_args={"sslmode": "require"}

**Problem**: "Too many connections"

\# Solution: Implement connection pooling  
engine \= create\_engine(  
    DATABASE\_URL,  
    pool\_size=5,  \# Reduce for Railway  
    max\_overflow=10  
)

### **Issue 3: Port Binding**

**Problem**: "Address already in use"

\# Railway assigns PORT dynamically  
\# NEVER hardcode port  
port \= int(os.environ.get("PORT", 8000))  
\# ALWAYS bind to 0.0.0.0, not localhost  
host \= "0.0.0.0"

### **Issue 4: Memory Issues**

**Problem**: "Container killed (OOM)"

\# Solution 1: Optimize memory usage  
\# Limit connection pools  
pool\_size=5  \# Instead of 20

\# Solution 2: Use streaming for large responses  
from fastapi.responses import StreamingResponse

@app.get("/large-export")  
async def large\_export():  
    def generate():  
        \# Yield data in chunks  
        for chunk in get\_data\_chunks():  
            yield chunk  
      
    return StreamingResponse(generate(), media\_type="text/csv")

\# Solution 3: Upgrade Railway plan

### **Issue 5: Deployment Stuck**

**Problem**: "Deployment pending for 10+ minutes"

\# Solution 1: Check logs  
railway logs

\# Solution 2: Cancel and retry  
railway down  
railway up

\# Solution 3: Check Railway status  
\# status.railway.app

\# Solution 4: Simplify build  
\# Remove unnecessary dependencies

### **Issue 6: Environment Variable Issues**

**Problem**: "Environment variable not found"

\# Solution: Use defaults and validate  
DATABASE\_URL \= os.environ.get("DATABASE\_URL")  
if not DATABASE\_URL:  
    if os.environ.get("RAILWAY\_ENVIRONMENT"):  
        raise ValueError("DATABASE\_URL not set in Railway")  
    else:  
        \# Local development fallback  
        DATABASE\_URL \= "postgresql://localhost/tradesense"

---

## **9\. Production Configuration**

### **Security Hardening**

\# middleware/security.py  
from fastapi import Request  
from fastapi.responses import Response  
import hashlib  
import hmac

async def security\_headers\_middleware(request: Request, call\_next):  
    response \= await call\_next(request)  
      
    \# Security headers  
    response.headers\["X-Content-Type-Options"\] \= "nosniff"  
    response.headers\["X-Frame-Options"\] \= "DENY"  
    response.headers\["X-XSS-Protection"\] \= "1; mode=block"  
    response.headers\["Strict-Transport-Security"\] \= "max-age=31536000; includeSubDomains"  
    response.headers\["Referrer-Policy"\] \= "strict-origin-when-cross-origin"  
    response.headers\["Permissions-Policy"\] \= "geolocation=(), microphone=(), camera=()"  
      
    \# Remove server header  
    response.headers.pop("Server", None)  
      
    return response

\# Webhook signature verification  
def verify\_webhook\_signature(payload: bytes, signature: str, secret: str) \-\> bool:  
    """Verify webhook signatures (Stripe, etc)"""  
    expected \= hmac.new(  
        secret.encode(),  
        payload,  
        hashlib.sha256  
    ).hexdigest()  
      
    return hmac.compare\_digest(expected, signature)

### **Rate Limiting**

\# middleware/rate\_limit.py  
from fastapi import Request, HTTPException  
import time  
from collections import defaultdict  
import asyncio

class RateLimiter:  
    def \_\_init\_\_(self, calls: int \= 100, period: int \= 60):  
        self.calls \= calls  
        self.period \= period  
        self.clients \= defaultdict(list)  
        self.cleanup\_task \= None  
      
    async def \_\_call\_\_(self, request: Request):  
        \# Get client IP  
        client\_ip \= request.client.host  
        now \= time.time()  
          
        \# Clean old entries  
        self.clients\[client\_ip\] \= \[  
            timestamp for timestamp in self.clients\[client\_ip\]  
            if timestamp \> now \- self.period  
        \]  
          
        \# Check rate limit  
        if len(self.clients\[client\_ip\]) \>= self.calls:  
            raise HTTPException(  
                status\_code=429,  
                detail=f"Rate limit exceeded: {self.calls} calls per {self.period} seconds"  
            )  
          
        \# Record call  
        self.clients\[client\_ip\].append(now)  
      
    async def cleanup(self):  
        """Periodic cleanup of old entries"""  
        while True:  
            await asyncio.sleep(300)  \# Every 5 minutes  
            now \= time.time()  
              
            \# Clean up old entries  
            for client\_ip in list(self.clients.keys()):  
                self.clients\[client\_ip\] \= \[  
                    t for t in self.clients\[client\_ip\]  
                    if t \> now \- self.period  
                \]  
                  
                \# Remove empty entries  
                if not self.clients\[client\_ip\]:  
                    del self.clients\[client\_ip\]

\# Apply rate limiting  
rate\_limiter \= RateLimiter(calls=100, period=60)

@app.middleware("http")  
async def rate\_limit\_middleware(request: Request, call\_next):  
    \# Skip rate limiting for health checks  
    if request.url.path \!= "/health":  
        await rate\_limiter(request)  
      
    return await call\_next(request)

### **Logging Configuration**

\# core/logging.py  
import logging  
import json  
import sys  
from datetime import datetime  
import traceback

class JSONFormatter(logging.Formatter):  
    """Format logs as JSON for better parsing"""  
      
    def format(self, record):  
        log\_obj \= {  
            "timestamp": datetime.utcnow().isoformat(),  
            "level": record.levelname,  
            "logger": record.name,  
            "message": record.getMessage(),  
            "module": record.module,  
            "function": record.funcName,  
            "line": record.lineno  
        }  
          
        \# Add exception info if present  
        if record.exc\_info:  
            log\_obj\["exception"\] \= traceback.format\_exception(\*record.exc\_info)  
          
        \# Add extra fields  
        for key, value in record.\_\_dict\_\_.items():  
            if key not in \["name", "msg", "args", "created", "filename", "funcName",   
                          "levelname", "levelno", "lineno", "module", "msecs",   
                          "pathname", "process", "processName", "relativeCreated",   
                          "thread", "threadName", "exc\_info", "exc\_text", "getMessage"\]:  
                log\_obj\[key\] \= value  
          
        return json.dumps(log\_obj)

def setup\_logging():  
    """Configure production logging"""  
    \# Remove default handlers  
    logging.getLogger().handlers \= \[\]  
      
    \# Create console handler with JSON formatter  
    console\_handler \= logging.StreamHandler(sys.stdout)  
    console\_handler.setFormatter(JSONFormatter())  
      
    \# Configure root logger  
    logging.basicConfig(  
        level=logging.INFO,  
        handlers=\[console\_handler\]  
    )  
      
    \# Reduce noise from libraries  
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  
    logging.getLogger("urllib3").setLevel(logging.WARNING)  
    logging.getLogger("asyncio").setLevel(logging.WARNING)

\# Call in main.py  
setup\_logging()

---

## **10\. Monitoring & Debugging**

### **Railway Logs**

\# View logs  
railway logs

\# Follow logs  
railway logs \-f

\# Filter logs  
railway logs | grep ERROR  
railway logs | jq '.message'

\# Save logs  
railway logs \> deployment\_$(date \+%Y%m%d).log

### **Application Metrics**

\# metrics/app\_metrics.py  
from prometheus\_client import Counter, Histogram, Gauge, generate\_latest  
from fastapi import Response  
import psutil  
import time

\# Define metrics  
request\_count \= Counter(  
    'http\_requests\_total',  
    'Total HTTP requests',  
    \['method', 'endpoint', 'status'\]  
)

request\_duration \= Histogram(  
    'http\_request\_duration\_seconds',  
    'HTTP request duration',  
    \['method', 'endpoint'\]  
)

active\_users \= Gauge(  
    'active\_users\_total',  
    'Number of active users'  
)

db\_connections \= Gauge(  
    'database\_connections\_active',  
    'Active database connections'  
)

\# System metrics  
cpu\_usage \= Gauge('cpu\_usage\_percent', 'CPU usage percentage')  
memory\_usage \= Gauge('memory\_usage\_percent', 'Memory usage percentage')

\# Update system metrics periodically  
async def update\_system\_metrics():  
    while True:  
        cpu\_usage.set(psutil.cpu\_percent(interval=1))  
        memory\_usage.set(psutil.virtual\_memory().percent)  
        await asyncio.sleep(30)

\# Metrics endpoint  
@app.get("/metrics")  
async def get\_metrics():  
    return Response(content=generate\_latest(), media\_type="text/plain")

\# Track requests  
@app.middleware("http")  
async def track\_metrics(request: Request, call\_next):  
    start\_time \= time.time()  
      
    response \= await call\_next(request)  
      
    duration \= time.time() \- start\_time  
      
    \# Record metrics  
    request\_count.labels(  
        method=request.method,  
        endpoint=request.url.path,  
        status=response.status\_code  
    ).inc()  
      
    request\_duration.labels(  
        method=request.method,  
        endpoint=request.url.path  
    ).observe(duration)  
      
    return response

### **Error Tracking with Sentry**

\# monitoring/sentry\_config.py  
import sentry\_sdk  
from sentry\_sdk.integrations.fastapi import FastApiIntegration  
from sentry\_sdk.integrations.sqlalchemy import SqlalchemyIntegration  
import os

def setup\_sentry():  
    """Initialize Sentry error tracking"""  
    if sentry\_dsn := os.environ.get("SENTRY\_DSN"):  
        sentry\_sdk.init(  
            dsn=sentry\_dsn,  
            environment=os.environ.get("RAILWAY\_ENVIRONMENT", "production"),  
            integrations=\[  
                FastApiIntegration(transaction\_style="endpoint"),  
                SqlalchemyIntegration(),  
            \],  
            traces\_sample\_rate=0.1,  \# 10% of transactions  
            profiles\_sample\_rate=0.1,  \# 10% profiling  
            attach\_stacktrace=True,  
            send\_default\_pii=False,  \# Don't send personal info  
            before\_send=before\_send\_filter,  
            release=os.environ.get("RAILWAY\_DEPLOYMENT\_ID", "unknown")  
        )

def before\_send\_filter(event, hint):  
    """Filter sensitive data before sending to Sentry"""  
    \# Remove sensitive headers  
    if "request" in event and "headers" in event\["request"\]:  
        event\["request"\]\["headers"\] \= {  
            k: v for k, v in event\["request"\]\["headers"\].items()  
            if k.lower() not in \["authorization", "cookie", "x-api-key"\]  
        }  
      
    \# Remove sensitive data from errors  
    if "extra" in event:  
        event\["extra"\] \= {  
            k: "\[FILTERED\]" if any(s in k.lower() for s in \["password", "token", "secret"\]) else v  
            for k, v in event\["extra"\].items()  
        }  
      
    return event

### **Custom Monitoring Dashboard**

\# monitoring/dashboard.py  
from fastapi import APIRouter, Request  
from fastapi.responses import HTMLResponse

router \= APIRouter()

@router.get("/admin/dashboard", response\_class=HTMLResponse)  
async def monitoring\_dashboard(request: Request):  
    """Simple monitoring dashboard"""  
      
    \# Collect metrics  
    from core.database import engine  
    from core.cache import cache  
      
    \# Database stats  
    db\_stats \= {}  
    try:  
        with engine.connect() as conn:  
            result \= conn.execute("""  
                SELECT   
                    count(\*) as total\_connections,  
                    count(\*) filter (where state \= 'active') as active\_connections  
                FROM pg\_stat\_activity  
                WHERE datname \= current\_database()  
            """).fetchone()  
            db\_stats \= dict(result)  
    except:  
        db\_stats \= {"error": "Could not fetch database stats"}  
      
    \# Redis stats  
    redis\_stats \= {}  
    try:  
        if cache.client:  
            info \= cache.client.info()  
            redis\_stats \= {  
                "connected\_clients": info.get("connected\_clients"),  
                "used\_memory\_human": info.get("used\_memory\_human"),  
                "total\_commands\_processed": info.get("total\_commands\_processed")  
            }  
    except:  
        redis\_stats \= {"error": "Could not fetch Redis stats"}  
      
    \# Application stats  
    app\_stats \= {  
        "uptime": time.time() \- app.state.start\_time,  
        "total\_requests": sum(request\_count.\_value.values()),  
        "active\_users": active\_users.\_value.get()  
    }  
      
    html \= f"""  
    \<\!DOCTYPE html\>  
    \<html\>  
    \<head\>  
        \<title\>TradeSense Monitoring\</title\>  
        \<style\>  
            body {{ font-family: Arial, sans-serif; margin: 20px; }}  
            .metric {{ background: \#f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }}  
            .metric h3 {{ margin: 0 0 10px 0; }}  
            .error {{ color: red; }}  
        \</style\>  
    \</head\>  
    \<body\>  
        \<h1\>TradeSense Monitoring Dashboard\</h1\>  
          
        \<div class="metric"\>  
            \<h3\>Application\</h3\>  
            \<p\>Uptime: {app\_stats\['uptime'\]:.0f} seconds\</p\>  
            \<p\>Total Requests: {app\_stats\['total\_requests'\]}\</p\>  
            \<p\>Active Users: {app\_stats\['active\_users'\]}\</p\>  
        \</div\>  
          
        \<div class="metric"\>  
            \<h3\>Database\</h3\>  
            {json.dumps(db\_stats, indent=2)}  
        \</div\>  
          
        \<div class="metric"\>  
            \<h3\>Redis\</h3\>  
            {json.dumps(redis\_stats, indent=2)}  
        \</div\>  
          
        \<div class="metric"\>  
            \<h3\>Quick Actions\</h3\>  
            \<a href="/metrics"\>Prometheus Metrics\</a\> |  
            \<a href="/docs"\>API Documentation\</a\> |  
            \<a href="/health"\>Health Check\</a\>  
        \</div\>  
    \</body\>  
    \</html\>  
    """  
      
    return html

---

## **11\. Continuous Deployment**

### **GitHub Integration**

\# .github/workflows/railway-deploy.yml  
name: Deploy to Railway

on:  
  push:  
    branches: \[main\]  
  pull\_request:  
    types: \[opened, synchronize\]

jobs:  
  test:  
    runs-on: ubuntu-latest  
    steps:  
      \- uses: actions/checkout@v3  
        
      \- name: Set up Python  
        uses: actions/setup-python@v4  
        with:  
          python-version: '3.11'  
        
      \- name: Install dependencies  
        run: |  
          pip install \-r src/backend/requirements.txt  
          pip install pytest pytest-asyncio  
        
      \- name: Run tests  
        run: |  
          cd src/backend  
          pytest tests/ \-v  
        
      \- name: Check code quality  
        run: |  
          pip install black flake8  
          black \--check src/backend  
          flake8 src/backend \--max-line-length=88

  deploy:  
    needs: test  
    runs-on: ubuntu-latest  
    if: github.ref \== 'refs/heads/main'  
      
    steps:  
      \- uses: actions/checkout@v3  
        
      \- name: Install Railway  
        run: npm i \-g @railway/cli  
        
      \- name: Deploy to Railway  
        env:  
          RAILWAY\_TOKEN: ${{ secrets.RAILWAY\_TOKEN }}  
        run: |  
          railway up \--service tradesense-backend

### **Railway Environments**

\# Create staging environment  
railway environment create staging

\# Switch to staging  
railway environment staging

\# Deploy to staging  
railway up

\# Promote to production  
railway environment production  
railway up

\# Environment-specific variables  
railway variables set ENVIRONMENT=staging \--environment staging  
railway variables set ENVIRONMENT=production \--environment production

### **Blue-Green Deployment**

\# deployment/blue\_green.py  
"""  
Blue-green deployment strategy for Railway  
"""  
import subprocess  
import time  
import requests

def health\_check(url: str, timeout: int \= 300\) \-\> bool:  
    """Check if service is healthy"""  
    start\_time \= time.time()  
      
    while time.time() \- start\_time \< timeout:  
        try:  
            response \= requests.get(f"{url}/health")  
            if response.status\_code \== 200:  
                data \= response.json()  
                if data.get("status") \== "healthy":  
                    return True  
        except:  
            pass  
          
        time.sleep(5)  
      
    return False

def deploy\_blue\_green():  
    """Deploy with blue-green strategy"""  
      
    \# 1\. Deploy to staging (green)  
    print("Deploying to staging environment...")  
    subprocess.run(\["railway", "environment", "staging"\])  
    subprocess.run(\["railway", "up"\])  
      
    \# 2\. Get staging URL  
    result \= subprocess.run(  
        \["railway", "status", "--json"\],  
        capture\_output=True,  
        text=True  
    )  
    staging\_url \= json.loads(result.stdout)\["url"\]  
      
    \# 3\. Health check staging  
    print("Running health checks...")  
    if not health\_check(staging\_url):  
        print("Staging deployment failed health check\!")  
        return False  
      
    \# 4\. Run smoke tests  
    print("Running smoke tests...")  
    if not run\_smoke\_tests(staging\_url):  
        print("Smoke tests failed\!")  
        return False  
      
    \# 5\. Promote to production  
    print("Promoting to production...")  
    subprocess.run(\["railway", "environment", "production"\])  
    subprocess.run(\["railway", "up"\])  
      
    \# 6\. Verify production  
    print("Verifying production deployment...")  
    production\_url \= "https://tradesense.ai"  
    if not health\_check(production\_url):  
        print("Production deployment failed\!")  
        \# Rollback would go here  
        return False  
      
    print("Deployment successful\!")  
    return True

if \_\_name\_\_ \== "\_\_main\_\_":  
    deploy\_blue\_green()

---

## **12\. Scaling Strategies**

### **Horizontal Scaling**

\# Railway automatically handles horizontal scaling  
\# Configure with environment variables:

\# Number of workers (processes)  
WEB\_CONCURRENCY=4  \# Based on CPU cores

\# Thread pool size  
THREAD\_POOL\_SIZE=10

\# Gunicorn configuration  
\# gunicorn\_config.py  
import os

bind \= f"0.0.0.0:{os.environ.get('PORT', 8000)}"  
workers \= int(os.environ.get("WEB\_CONCURRENCY", 2))  
worker\_class \= "uvicorn.workers.UvicornWorker"  
worker\_connections \= 1000  
keepalive \= 120  
timeout \= 30  
graceful\_timeout \= 30  
max\_requests \= 1000  
max\_requests\_jitter \= 50

\# Logging  
accesslog \= "-"  
errorlog \= "-"  
loglevel \= "info"

\# Process naming  
proc\_name \= "tradesense"

### **Vertical Scaling**

\# Upgrade Railway plan for more resources  
\# Via dashboard: Settings \-\> Plan \-\> Upgrade

\# Monitor resource usage  
railway logs | grep "Memory:"

### **Database Scaling**

\# 1\. Read replicas (manual setup)  
\# core/database.py  
import random

class DatabaseManager:  
    def \_\_init\_\_(self):  
        self.write\_engine \= create\_engine(os.environ\["DATABASE\_URL"\])  
          
        \# Read replicas  
        read\_urls \= \[  
            url for key, url in os.environ.items()  
            if key.startswith("DATABASE\_READ\_URL\_")  
        \]  
          
        self.read\_engines \= \[  
            create\_engine(url) for url in read\_urls  
        \] if read\_urls else \[self.write\_engine\]  
      
    def get\_read\_engine(self):  
        """Get random read replica for load balancing"""  
        return random.choice(self.read\_engines)  
      
    def get\_write\_engine(self):  
        """Get write engine"""  
        return self.write\_engine

\# 2\. Connection pooling optimization  
engine \= create\_engine(  
    DATABASE\_URL,  
    pool\_size=20,  \# Increase for high traffic  
    max\_overflow=40,  
    pool\_pre\_ping=True,  
    pool\_recycle=300  
)

\# 3\. Query optimization  
\# Add indexes  
CREATE INDEX CONCURRENTLY idx\_trades\_user\_id\_created\_at   
ON trades(user\_id, created\_at DESC);

CREATE INDEX CONCURRENTLY idx\_trades\_symbol\_user\_id   
ON trades(symbol, user\_id);

\# 4\. Materialized views for analytics  
CREATE MATERIALIZED VIEW user\_stats AS  
SELECT   
    user\_id,  
    COUNT(\*) as total\_trades,  
    SUM(CASE WHEN pnl \> 0 THEN 1 ELSE 0 END) as winning\_trades,  
    SUM(pnl) as total\_pnl,  
    AVG(pnl) as avg\_pnl,  
    MAX(created\_at) as last\_trade\_date  
FROM trades  
GROUP BY user\_id;

\-- Refresh periodically  
REFRESH MATERIALIZED VIEW CONCURRENTLY user\_stats;

### **Caching Strategy**

\# caching/strategies.py  
from functools import wraps  
import hashlib  
import json

def cache\_key(\*args, \*\*kwargs):  
    """Generate cache key from arguments"""  
    key\_data \= {  
        "args": args,  
        "kwargs": kwargs  
    }  
    key\_string \= json.dumps(key\_data, sort\_keys=True)  
    return hashlib.md5(key\_string.encode()).hexdigest()

def cached(ttl: int \= 300, prefix: str \= ""):  
    """Cache decorator with TTL"""  
    def decorator(func):  
        @wraps(func)  
        async def wrapper(\*args, \*\*kwargs):  
            \# Generate cache key  
            key \= f"{prefix}:{func.\_\_name\_\_}:{cache\_key(\*args, \*\*kwargs)}"  
              
            \# Try cache  
            cached\_value \= await cache.get(key)  
            if cached\_value is not None:  
                return cached\_value  
              
            \# Calculate result  
            result \= await func(\*args, \*\*kwargs)  
              
            \# Cache result  
            await cache.set(key, result, ttl=ttl)  
              
            return result  
        return wrapper  
    return decorator

\# Usage  
@cached(ttl=600, prefix="analytics")  
async def get\_user\_analytics(user\_id: str):  
    \# Expensive calculation  
    return calculate\_analytics(user\_id)

\# Cache invalidation  
async def invalidate\_user\_cache(user\_id: str):  
    """Invalidate all user-related cache"""  
    pattern \= f"\*:\*:{user\_id}\*"  
      
    if cache.client:  
        for key in cache.client.scan\_iter(match=pattern):  
            cache.client.delete(key)

---

## **13\. Cost Optimization**

### **Railway Pricing**

\# Railway pricing (as of 2024\)  
\- $20/month credit included  
\- $0.000463/vCPU/minute  
\- $0.000231/GB RAM/minute  
\- $0.25/GB storage/month  
\- $0.10/GB network egress

### **Cost Monitoring**

\# monitoring/cost\_tracker.py  
import os  
import requests  
from datetime import datetime, timedelta

def get\_railway\_usage():  
    """Get current month's Railway usage"""  
      
    headers \= {  
        "Authorization": f"Bearer {os.environ\['RAILWAY\_API\_TOKEN'\]}"  
    }  
      
    \# Get current usage  
    response \= requests.get(  
        "https://api.railway.app/v1/usage",  
        headers=headers  
    )  
      
    usage \= response.json()  
      
    return {  
        "cpu\_hours": usage\["cpu\_hours"\],  
        "memory\_gb\_hours": usage\["memory\_gb\_hours"\],  
        "network\_gb": usage\["network\_gb"\],  
        "estimated\_cost": usage\["estimated\_cost"\]  
    }

\# Add to monitoring dashboard  
@app.get("/admin/costs")  
async def cost\_dashboard():  
    usage \= get\_railway\_usage()  
      
    return {  
        "current\_month\_usage": usage,  
        "cost\_breakdown": {  
            "cpu": usage\["cpu\_hours"\] \* 0.000463 \* 60,  
            "memory": usage\["memory\_gb\_hours"\] \* 0.000231 \* 60,  
            "network": usage\["network\_gb"\] \* 0.10  
        },  
        "recommendations": get\_cost\_recommendations(usage)  
    }

def get\_cost\_recommendations(usage):  
    """Provide cost optimization recommendations"""  
    recommendations \= \[\]  
      
    \# High CPU usage  
    if usage\["cpu\_hours"\] \> 1000:  
        recommendations.append({  
            "issue": "High CPU usage",  
            "suggestion": "Optimize queries, add caching, or scale horizontally"  
        })  
      
    \# High memory usage  
    if usage\["memory\_gb\_hours"\] \> 500:  
        recommendations.append({  
            "issue": "High memory usage",  
            "suggestion": "Check for memory leaks, reduce connection pools"  
        })  
      
    \# High network usage  
    if usage\["network\_gb"\] \> 100:  
        recommendations.append({  
            "issue": "High network usage",  
            "suggestion": "Enable compression, use CDN for static assets"  
        })  
      
    return recommendations

### **Optimization Techniques**

\# 1\. Reduce idle resources  
\# Stop development services when not in use  
railway down \--service tradesense-staging

\# 2\. Optimize database queries  
\# Use query profiling  
EXPLAIN ANALYZE  
SELECT \* FROM trades WHERE user\_id \= '123' ORDER BY created\_at DESC LIMIT 10;

\# 3\. Implement request caching  
@app.get("/api/v1/analytics/summary/{user\_id}")  
@cached(ttl=3600)  \# Cache for 1 hour  
async def get\_user\_summary(user\_id: str):  
    return expensive\_calculation(user\_id)

\# 4\. Use CDN for static assets  
\# Serve static files from Cloudflare or similar

\# 5\. Compress responses  
app.add\_middleware(GZipMiddleware, minimum\_size=1000)

\# 6\. Optimize Docker images  
\# Multi-stage builds to reduce size  
FROM python:3.11-slim as builder  
\# Build dependencies  
RUN pip install \--user \-r requirements.txt

FROM python:3.11-slim  
\# Copy only necessary files  
COPY \--from=builder /root/.local /root/.local

---

## **14\. Feature Deployment Workflow**

### **Feature Branch Workflow**

\# 1\. Create feature branch  
git checkout \-b feature/advanced-analytics

\# 2\. Develop locally  
\# Make changes, test locally

\# 3\. Deploy to preview  
railway up \--environment preview-advanced-analytics

\# 4\. Test in preview  
\# Share preview URL with team

\# 5\. Merge to main  
git checkout main  
git merge feature/advanced-analytics  
git push

\# 6\. Auto-deploy to production  
\# GitHub Action triggers Railway deployment

### **Feature Flags Implementation**

\# feature\_flags/manager.py  
import os  
from typing import Dict, Any  
from datetime import datetime

class FeatureFlag:  
    def \_\_init\_\_(self, name: str, enabled: bool \= False, rollout\_percentage: int \= 0):  
        self.name \= name  
        self.enabled \= enabled  
        self.rollout\_percentage \= rollout\_percentage  
        self.created\_at \= datetime.utcnow()

class FeatureFlagManager:  
    def \_\_init\_\_(self):  
        self.flags \= self.\_load\_flags()  
      
    def \_load\_flags(self) \-\> Dict\[str, FeatureFlag\]:  
        """Load flags from environment or database"""  
        flags \= {}  
          
        \# Load from environment  
        for key, value in os.environ.items():  
            if key.startswith("FEATURE\_"):  
                flag\_name \= key\[8:\].lower()  
                flags\[flag\_name\] \= FeatureFlag(  
                    name=flag\_name,  
                    enabled=value.lower() \== "true"  
                )  
          
        \# Default flags  
        default\_flags \= {  
            "advanced\_analytics": FeatureFlag("advanced\_analytics", False, 10),  
            "ai\_insights": FeatureFlag("ai\_insights", False, 0),  
            "real\_time\_sync": FeatureFlag("real\_time\_sync", True, 100),  
        }  
          
        \# Merge with defaults  
        for name, flag in default\_flags.items():  
            if name not in flags:  
                flags\[name\] \= flag  
          
        return flags  
      
    def is\_enabled(self, flag\_name: str, user\_id: str \= None) \-\> bool:  
        """Check if feature is enabled for user"""  
        flag \= self.flags.get(flag\_name)  
          
        if not flag:  
            return False  
          
        if flag.enabled:  
            return True  
          
        if user\_id and flag.rollout\_percentage \> 0:  
            \# Consistent hashing for gradual rollout  
            user\_hash \= int(hashlib.md5(  
                f"{flag\_name}:{user\_id}".encode()  
            ).hexdigest(), 16\)  
              
            return (user\_hash % 100\) \< flag.rollout\_percentage  
          
        return False  
      
    def enable\_flag(self, flag\_name: str, rollout\_percentage: int \= 100):  
        """Enable a feature flag"""  
        if flag\_name in self.flags:  
            self.flags\[flag\_name\].enabled \= True  
            self.flags\[flag\_name\].rollout\_percentage \= rollout\_percentage  
        else:  
            self.flags\[flag\_name\] \= FeatureFlag(  
                flag\_name,   
                True,   
                rollout\_percentage  
            )  
      
    def disable\_flag(self, flag\_name: str):  
        """Disable a feature flag"""  
        if flag\_name in self.flags:  
            self.flags\[flag\_name\].enabled \= False  
            self.flags\[flag\_name\].rollout\_percentage \= 0

\# Global instance  
feature\_flags \= FeatureFlagManager()

\# Usage in API  
@app.get("/api/v1/analytics/advanced")  
async def get\_advanced\_analytics(  
    current\_user: User \= Depends(get\_current\_user)  
):  
    if not feature\_flags.is\_enabled("advanced\_analytics", str(current\_user.id)):  
        raise HTTPException(  
            status\_code=404,  
            detail="Feature not available"  
        )  
      
    return await calculate\_advanced\_analytics(current\_user.id)

### **Safe Rollout Process**

\# deployment/safe\_rollout.py  
"""  
Safe feature rollout process  
"""

async def rollout\_feature(feature\_name: str):  
    """Gradually roll out a feature"""  
      
    rollout\_stages \= \[  
        (1, "1% canary"),  
        (5, "5% early adopters"),  
        (10, "10% beta"),  
        (25, "25% expansion"),  
        (50, "50% half rollout"),  
        (100, "100% full rollout")  
    \]  
      
    for percentage, stage\_name in rollout\_stages:  
        print(f"\\n🚀 Rolling out {feature\_name} \- {stage\_name}")  
          
        \# Enable feature for percentage  
        feature\_flags.enable\_flag(feature\_name, percentage)  
          
        \# Monitor for issues  
        print("⏱️  Monitoring for 30 minutes...")  
        issues \= await monitor\_rollout(feature\_name, duration=1800)  
          
        if issues:  
            print(f"❌ Issues detected: {issues}")  
            print("🔄 Rolling back...")  
            feature\_flags.disable\_flag(feature\_name)  
            return False  
          
        print(f"✅ {stage\_name} successful")  
          
        \# Wait before next stage (except for 100%)  
        if percentage \< 100:  
            print("⏸️  Waiting 1 hour before next stage...")  
            await asyncio.sleep(3600)  
      
    print(f"🎉 {feature\_name} fully rolled out\!")  
    return True

async def monitor\_rollout(feature\_name: str, duration: int) \-\> list:  
    """Monitor feature rollout for issues"""  
    start\_time \= time.time()  
    issues \= \[\]  
      
    while time.time() \- start\_time \< duration:  
        \# Check error rates  
        error\_rate \= await get\_feature\_error\_rate(feature\_name)  
        if error\_rate \> 0.05:  \# 5% threshold  
            issues.append(f"High error rate: {error\_rate:.2%}")  
          
        \# Check performance  
        latency \= await get\_feature\_latency(feature\_name)  
        if latency \> 1000:  \# 1 second threshold  
            issues.append(f"High latency: {latency}ms")  
          
        \# Check user feedback  
        negative\_feedback \= await get\_negative\_feedback(feature\_name)  
        if negative\_feedback \> 10:  
            issues.append(f"Negative feedback: {negative\_feedback} reports")  
          
        if issues:  
            break  
          
        await asyncio.sleep(60)  \# Check every minute  
      
    return issues

---

## **15\. Emergency Procedures**

### **Incident Response**

\# emergency/incident\_response.py  
"""  
Emergency procedures for production incidents  
"""

class IncidentResponse:  
    def \_\_init\_\_(self):  
        self.incident\_log \= \[\]  
      
    async def handle\_incident(self, incident\_type: str):  
        """Main incident response handler"""  
          
        self.log(f"🚨 INCIDENT DETECTED: {incident\_type}")  
          
        \# Incident type handlers  
        handlers \= {  
            "database\_down": self.handle\_database\_down,  
            "high\_error\_rate": self.handle\_high\_error\_rate,  
            "memory\_leak": self.handle\_memory\_leak,  
            "ddos\_attack": self.handle\_ddos\_attack,  
            "data\_breach": self.handle\_data\_breach  
        }  
          
        handler \= handlers.get(incident\_type, self.handle\_unknown)  
        await handler()  
      
    async def handle\_database\_down(self):  
        """Database outage response"""  
          
        self.log("Checking database connection...")  
          
        \# 1\. Verify database is actually down  
        if not await self.check\_database():  
            \# 2\. Enable read-only mode  
            await self.enable\_read\_only\_mode()  
              
            \# 3\. Notify users  
            await self.notify\_users("We're experiencing database issues. Read-only mode enabled.")  
              
            \# 4\. Check Railway status  
            railway\_status \= await self.check\_railway\_status()  
            self.log(f"Railway status: {railway\_status}")  
              
            \# 5\. Attempt restart  
            if railway\_status \== "service\_crashed":  
                await self.restart\_service("postgres")  
              
            \# 6\. Escalate if not resolved  
            if not await self.check\_database():  
                await self.escalate\_to\_oncall()  
        else:  
            self.log("False alarm \- database is responding")  
      
    async def handle\_high\_error\_rate(self):  
        """High error rate response"""  
          
        \# 1\. Get error details  
        errors \= await self.get\_recent\_errors()  
        self.log(f"Recent errors: {len(errors)}")  
          
        \# 2\. Identify pattern  
        error\_pattern \= self.analyze\_errors(errors)  
          
        \# 3\. Take action based on pattern  
        if error\_pattern \== "timeout":  
            \# Scale up  
            await self.scale\_service("tradesense-backend", instances=4)  
        elif error\_pattern \== "database":  
            \# Check database  
            await self.handle\_database\_down()  
        elif error\_pattern \== "external\_api":  
            \# Enable circuit breaker  
            await self.enable\_circuit\_breaker("external\_api")  
          
        \# 4\. Monitor recovery  
        await self.monitor\_recovery()  
      
    async def rollback\_deployment(self):  
        """Emergency rollback procedure"""  
          
        self.log("🔄 INITIATING EMERGENCY ROLLBACK")  
          
        \# 1\. Get previous deployment  
        previous \= await self.get\_previous\_deployment()  
          
        \# 2\. Rollback via Railway  
        subprocess.run(\[  
            "railway", "deployments", "rollback", previous\["id"\]  
        \])  
          
        \# 3\. Verify rollback  
        await asyncio.sleep(30)  
        if await self.health\_check():  
            self.log("✅ Rollback successful")  
        else:  
            self.log("❌ Rollback failed \- escalating")  
            await self.escalate\_to\_oncall()

\# Quick commands for emergencies  
"""  
\# 1\. View recent logs  
railway logs \--lines 1000 | grep ERROR

\# 2\. Restart service  
railway restart

\# 3\. Scale up  
railway scale \--replicas 4

\# 4\. Emergency environment variable  
railway variables set EMERGENCY\_MODE=true

\# 5\. Rollback deployment  
railway deployments list  
railway deployments rollback \<deployment-id\>  
"""

### **Disaster Recovery**

\#\!/bin/bash  
\# disaster\_recovery.sh

echo "🚨 DISASTER RECOVERY PROCEDURE 🚨"

\# 1\. Check all services  
echo "Checking service health..."  
railway status

\# 2\. Backup current data  
echo "Creating emergency backup..."  
railway run pg\_dump $DATABASE\_URL \> emergency\_backup\_$(date \+%Y%m%d\_%H%M%S).sql

\# 3\. Check Railway status page  
echo "Railway status: https://status.railway.app"

\# 4\. Switch to backup region (if configured)  
if \[ "$1" \== "--switch-region" \]; then  
    echo "Switching to backup region..."  
    railway environment disaster-recovery  
    railway up  
fi

\# 5\. Notify team  
echo "Sending notifications..."  
curl \-X POST $SLACK\_WEBHOOK\_URL \\  
  \-H 'Content-type: application/json' \\  
  \-d '{"text":"🚨 Disaster recovery initiated for TradeSense"}'

\# 6\. Monitor recovery  
echo "Monitoring recovery..."  
while true; do  
    if curl \-s https://tradesense.ai/health | grep \-q "healthy"; then  
        echo "✅ Service recovered\!"  
        break  
    fi  
    echo "Still recovering..."  
    sleep 30  
done

### **Post-Incident Review**

\# emergency/post\_incident.py  
"""  
Post-incident review template  
"""

def generate\_post\_incident\_report(incident\_data: dict) \-\> str:  
    """Generate post-incident report"""  
      
    template \= """  
\# Post-Incident Report: {title}

\#\# Summary  
\- \*\*Date\*\*: {date}  
\- \*\*Duration\*\*: {duration}  
\- \*\*Severity\*\*: {severity}  
\- \*\*Impact\*\*: {impact}

\#\# Timeline  
{timeline}

\#\# Root Cause  
{root\_cause}

\#\# Resolution  
{resolution}

\#\# Action Items  
{action\_items}

\#\# Lessons Learned  
{lessons\_learned}

\#\# Metrics  
\- \*\*Time to Detection\*\*: {ttd}  
\- \*\*Time to Resolution\*\*: {ttr}  
\- \*\*Users Affected\*\*: {users\_affected}  
\- \*\*Revenue Impact\*\*: ${revenue\_impact}  
    """  
      
    return template.format(\*\*incident\_data)

\# Usage  
incident \= {  
    "title": "Database Connection Pool Exhaustion",  
    "date": "2024-01-20",  
    "duration": "45 minutes",  
    "severity": "P1",  
    "impact": "30% of users unable to access analytics",  
    "timeline": """  
\- 14:00 \- Error rate spike detected  
\- 14:05 \- Automated alert triggered  
\- 14:10 \- Engineer acknowledged  
\- 14:15 \- Root cause identified  
\- 14:30 \- Fix deployed  
\- 14:45 \- Service fully recovered  
    """,  
    "root\_cause": "Connection pool size too small for peak traffic",  
    "resolution": "Increased pool size from 20 to 50 connections",  
    "action\_items": """  
1\. \[ \] Implement connection pool monitoring  
2\. \[ \] Add auto-scaling for connection pool  
3\. \[ \] Create runbook for connection issues  
    """,  
    "lessons\_learned": """  
\- Need better visibility into connection pool metrics  
\- Should have load tested with realistic traffic patterns  
\- Alerting thresholds were too high  
    """,  
    "ttd": "5 minutes",  
    "ttr": "45 minutes",  
    "users\_affected": "\~3,000",  
    "revenue\_impact": "0"  
}

report \= generate\_post\_incident\_report(incident)

---

## **Summary**

This comprehensive guide covers everything you need to successfully deploy and manage TradeSense on Railway. Key takeaways:

1. **Pre-deployment**: Fix hardcoded values, use environment variables, bind to 0.0.0.0:$PORT  
2. **Database**: Handle PostgreSQL URL format, implement connection pooling, run migrations  
3. **Monitoring**: Use structured logging, implement health checks, track metrics  
4. **Deployment**: Use GitHub integration, implement feature flags, gradual rollouts  
5. **Incidents**: Have clear procedures, implement circuit breakers, maintain runbooks

Remember: Railway abstracts away infrastructure complexity, but you still need to follow production best practices for a reliable service.

For immediate deployment success:

* Start with the minimal configuration  
* Add monitoring from day one  
* Implement gradual rollouts  
* Keep deployment simple  
* Scale based on actual usage

Good luck with your deployment\! 🚀

