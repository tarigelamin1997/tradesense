# TradeSense Microservices Architecture

## Overview

Transform TradeSense from a monolithic application into a resilient microservices architecture where each service can fail independently without crashing the entire system.

## Architecture Design

```
┌─────────────────┐
│   Frontend      │
│   (Vercel)      │
└────────┬────────┘
         │
    HTTPS/REST
         │
┌────────▼────────┐
│  API Gateway    │ ← Entry point (Railway)
│  (Core Service) │
└────────┬────────┘
         │
    Internal Network
         │
┌────────┴────────────────────────────────────┐
│                                             │
▼                ▼              ▼             ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│  Auth   │  │ Trading │  │Analytics│  │ Market  │
│ Service │  │ Service │  │ Service │  │  Data   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
     │            │            │            │
     ▼            ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ Users   │  │ Trades  │  │Analytics│  │ Market  │
│   DB    │  │   DB    │  │   DB    │  │  Cache  │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
```

## Service Breakdown

### 1. API Gateway (Core Service)
**Purpose**: Route requests, handle CORS, rate limiting, health checks
**Endpoints**: 
- `/health` - Aggregated health status
- `/api/*` - Route to appropriate services
**Dependencies**: None (can run standalone)

### 2. Auth Service
**Purpose**: Authentication, JWT tokens, user management
**Endpoints**:
- `/auth/login`
- `/auth/register`
- `/auth/refresh`
- `/auth/users/*`
**Database**: PostgreSQL (users, sessions)
**Dependencies**: None

### 3. Trading Service
**Purpose**: Trade management, portfolio tracking
**Endpoints**:
- `/trades/*`
- `/portfolio/*`
- `/journal/*`
**Database**: PostgreSQL (trades, portfolios)
**Dependencies**: Auth Service (for user validation)

### 4. Analytics Service
**Purpose**: ML models, pattern recognition, performance metrics
**Endpoints**:
- `/analytics/*`
- `/patterns/*`
- `/performance/*`
**Database**: PostgreSQL (analytics data)
**Dependencies**: Trading Service (read-only)

### 5. Market Data Service
**Purpose**: Real-time market data, caching
**Endpoints**:
- `/market-data/*`
- `/quotes/*`
**Database**: Redis (cache)
**Dependencies**: External APIs

### 6. Billing Service
**Purpose**: Stripe integration, subscriptions
**Endpoints**:
- `/billing/*`
- `/subscriptions/*`
**Database**: PostgreSQL (billing)
**Dependencies**: Auth Service

### 7. AI Service
**Purpose**: OpenAI integration, trade intelligence
**Endpoints**:
- `/ai/*`
- `/intelligence/*`
**Database**: PostgreSQL (ai_cache)
**Dependencies**: Trading Service

## Communication Patterns

### Service Discovery
- **Development**: Hardcoded service URLs
- **Production**: Railway internal DNS (service.railway.internal)

### Inter-Service Communication
- **Synchronous**: REST over HTTP (internal network)
- **Asynchronous**: Redis Pub/Sub for events
- **Authentication**: Internal service tokens

### Example Request Flow
```
1. User requests /api/trades
2. API Gateway validates JWT
3. Gateway forwards to Trading Service
4. Trading Service validates user with Auth Service
5. Trading Service returns data
6. Gateway returns response to user
```

## Deployment Strategy

### Phase 1: Core Services (Week 1)
1. API Gateway - Basic routing and health checks
2. Auth Service - User management
3. Trading Service - Core functionality

### Phase 2: Enhanced Services (Week 2)
4. Analytics Service
5. Market Data Service

### Phase 3: Premium Services (Week 3)
6. Billing Service
7. AI Service

## Benefits

1. **Fault Isolation**: One service crash doesn't affect others
2. **Independent Scaling**: Scale only what needs scaling
3. **Faster Deployments**: Deploy single services
4. **Technology Flexibility**: Use different languages/frameworks
5. **Team Scalability**: Teams own services

## Railway Configuration

Each service gets:
- Own repository/directory
- Own Railway service
- Own database (if needed)
- Own environment variables
- Own scaling rules

## Implementation Plan

### Step 1: Create Service Structure
```
tradesense/
├── services/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── auth/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── trading/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── ...
└── shared/
    ├── models/
    ├── utils/
    └── config/
```

### Step 2: Extract Services
1. Copy relevant code to each service
2. Remove dependencies on other services
3. Define clear API contracts
4. Add health checks

### Step 3: Deploy Incrementally
1. Deploy Gateway first
2. Deploy Auth Service
3. Test Gateway → Auth communication
4. Continue with other services

## Monitoring & Observability

Each service should have:
- Health endpoint
- Metrics endpoint
- Structured logging
- Error tracking
- Performance monitoring

## Example Service Implementation

### Gateway Service (main.py)
```python
from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI(title="TradeSense Gateway")

# Service registry
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth:8000"),
    "trading": os.getenv("TRADING_SERVICE_URL", "http://trading:8000"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics:8000"),
}

@app.get("/health")
async def health():
    """Check health of all services"""
    health_status = {"gateway": "healthy", "services": {}}
    
    async with httpx.AsyncClient() as client:
        for service, url in SERVICES.items():
            try:
                resp = await client.get(f"{url}/health", timeout=2.0)
                health_status["services"][service] = "healthy" if resp.status_code == 200 else "unhealthy"
            except:
                health_status["services"][service] = "unreachable"
    
    return health_status

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    """Route requests to appropriate services"""
    # Determine target service based on path
    service = path.split("/")[0]
    if service not in SERVICES:
        return {"error": "Service not found"}, 404
    
    # Forward request
    target_url = f"{SERVICES[service]}/{path}"
    # ... proxy implementation
```

## Cost Considerations

- Each Railway service has own resource allocation
- Start with minimal resources (256MB RAM, 0.5 CPU)
- Scale based on actual usage
- Use Railway's built-in metrics

## Security Considerations

1. **Service-to-Service Auth**: Internal tokens
2. **Network Isolation**: Use Railway's private network
3. **Secrets Management**: Per-service env vars
4. **Rate Limiting**: At gateway level
5. **CORS**: Only at gateway

## Migration Path

1. Start with current monolith as "legacy service"
2. Gradually extract services
3. Route specific endpoints to new services
4. Deprecate monolith once all extracted

This architecture gives you the resilience and flexibility you're looking for while being practical to implement incrementally.