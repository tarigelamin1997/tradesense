# Section 3B: Integration & Infrastructure Design
*Extracted from ARCHITECTURE_STRATEGY.md*

---

## SECTION 3B: INTEGRATION & INFRASTRUCTURE DESIGN

### Executive Summary: Infrastructure Strategy

This section presents a pragmatic infrastructure strategy for TradeSense that embraces a **"Start Simple, Scale Smart"** philosophy. Rather than over-engineering for hypothetical future scale, the architecture is designed to **evolve naturally** as the business grows from **100 to 100,000+ concurrent users**.

The key strategic decisions include:
- **Modular Monolith Architecture** with clear evolutionary path to microservices
- **Shared Database Multi-Tenancy** with row-level security for operational simplicity
- **Event-Driven Integration** patterns for loose coupling between features
- **API-First Design** with RESTful APIs and future GraphQL consideration
- **Multi-Level Caching Strategy** for performance optimization
- **Container-Based Deployment** with Kubernetes readiness

---

### Microservices vs Modular Monolith Decision

#### Current State Assessment

**Team and Technical Context:**
- **Current Team Size**: 3-4 developers (vs. 8-12+ needed for effective microservices)
- **Technical Maturity**: Basic DevOps practices, no containerization, limited monitoring
- **Scaling Requirements**: 100 → 5,000 → 25,000 concurrent users over 24 months
- **Development Velocity Priority**: Need to deliver features quickly to capture market

#### Strategic Decision: Modular Monolith with Evolutionary Path

After comprehensive analysis using a weighted decision matrix, the architecture chooses a **Modular Monolith** approach:

**Decision Matrix Results:**
```
Modular Monolith: +19 total score
Microservices: +1 total score
Traditional Monolith: -8 total score
```

**Key Advantages of Modular Monolith:**
1. **Simplified Operations**: Single deployment artifact, unified logging, easier debugging
2. **Faster Development**: No network latency, shared database transactions, simpler testing
3. **Lower Costs**: 70% less infrastructure, reduced operational overhead
4. **Team Alignment**: Matches current team size and expertise
5. **Evolution Ready**: Clear boundaries enable future microservice extraction

#### Implementation Architecture

**Phase 1: Modular Monolith Structure (Months 1-12)**
```
backend/
├── src/
│   ├── features/              # Self-contained feature modules
│   │   ├── authentication/    # Complete auth capability
│   │   │   ├── domain/       # Business logic
│   │   │   ├── application/  # Use cases
│   │   │   ├── infrastructure/ # External integrations
│   │   │   └── presentation/ # API layer
│   │   ├── billing/          # Billing module
│   │   ├── trading/          # Trading module
│   │   └── analytics/        # Analytics module
│   ├── shared/               # Shared kernel
│   │   ├── domain/          # Common domain concepts
│   │   ├── infrastructure/  # Shared infrastructure
│   │   └── events/          # Event bus
│   └── api/                 # API composition
│       ├── v1/              # API version 1
│       └── middleware/      # Cross-cutting concerns
```

**Phase 2: Service Extraction Preparation (Months 6-18)**

**Extraction Criteria Framework:**
```python
class ServiceExtractionCriteria:
    """Criteria for determining when to extract a microservice"""
    
    def should_extract(self, module: FeatureModule) -> bool:
        return all([
            module.team_ownership_score > 0.8,      # Clear team ownership
            module.deployment_frequency > 5/week,    # High change rate
            module.scaling_difference > 3x,          # Different scaling needs
            module.data_independence > 0.9,          # Minimal shared data
            module.external_integrations > 3         # Multiple integrations
        ])
```

**Phase 3: Selective Service Extraction (Months 12-24)**

**Extraction Priority Order:**
1. **Authentication Service** - Stateless, high security requirements
2. **Notification Service** - Event-driven, independent scaling
3. **Billing Service** - External integrations, compliance requirements
4. **Analytics Engine** - CPU-intensive, different scaling profile
5. **Trading Core** - Remains monolithic longer due to transaction requirements

---

### Integration Patterns and Dependency Management

#### Event-Driven Architecture Implementation

**Core Event Infrastructure:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
import uuid

@dataclass
class DomainEvent:
    """Base class for all domain events"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = field(init=False)
    aggregate_id: str
    aggregate_type: str
    event_data: Dict[str, Any]
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    causation_id: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = self.__class__.__name__

class EventBus(ABC):
    """Abstract event bus interface"""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to bus"""
        pass
    
    @abstractmethod
    async def subscribe(
        self, 
        event_type: str, 
        handler: Callable[[DomainEvent], Awaitable[None]]
    ) -> None:
        """Subscribe to event type"""
        pass

class InProcessEventBus(EventBus):
    """In-process event bus for modular monolith"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all registered handlers"""
        handlers = self._handlers.get(event.event_type, [])
        
        # Execute handlers asynchronously
        await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True
        )
    
    async def subscribe(
        self, 
        event_type: str, 
        handler: Callable[[DomainEvent], Awaitable[None]]
    ) -> None:
        """Register event handler"""
        self._handlers[event_type].append(handler)
```

**Cross-Feature Event Communication:**
```python
# Trading module publishes event
@dataclass
class TradeExecutedEvent(DomainEvent):
    """Event raised when trade is executed"""
    trade_id: str
    symbol: str
    quantity: Decimal
    price: Decimal
    side: TradeSide
    portfolio_id: str

# Analytics module subscribes
class AnalyticsEventHandler:
    def __init__(self, analytics_service: AnalyticsService):
        self._analytics_service = analytics_service
    
    async def handle_trade_executed(self, event: TradeExecutedEvent) -> None:
        """Update analytics when trade executes"""
        await self._analytics_service.update_portfolio_metrics(
            portfolio_id=event.portfolio_id,
            trade_data={
                'symbol': event.symbol,
                'quantity': event.quantity,
                'price': event.price,
                'side': event.side
            }
        )

# Wire up in composition root
event_bus.subscribe(
    'TradeExecutedEvent',
    analytics_handler.handle_trade_executed
)
```

#### Dependency Injection Architecture

**DI Container Implementation:**
```python
class DIContainer:
    """Dependency injection container"""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._scopes: Dict[Type, ServiceScope] = {}
    
    def register_singleton(
        self, 
        interface: Type[T], 
        implementation: Union[T, Callable[[], T]]
    ) -> None:
        """Register singleton service"""
        if callable(implementation):
            instance = implementation()
        else:
            instance = implementation
        self._services[interface] = instance
        self._scopes[interface] = ServiceScope.SINGLETON
    
    def register_scoped(
        self, 
        interface: Type[T], 
        factory: Callable[[DIContainer], T]
    ) -> None:
        """Register scoped service"""
        self._factories[interface] = factory
        self._scopes[interface] = ServiceScope.SCOPED
    
    def register_transient(
        self, 
        interface: Type[T], 
        factory: Callable[[DIContainer], T]
    ) -> None:
        """Register transient service"""
        self._factories[interface] = factory
        self._scopes[interface] = ServiceScope.TRANSIENT
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve service instance"""
        scope = self._scopes.get(interface)
        
        if scope == ServiceScope.SINGLETON:
            return self._services[interface]
        elif scope in (ServiceScope.SCOPED, ServiceScope.TRANSIENT):
            factory = self._factories[interface]
            return factory(self)
        
        raise ServiceNotRegisteredError(f"{interface} not registered")

# Service registration
def configure_services(container: DIContainer) -> None:
    """Configure all services"""
    
    # Infrastructure services (singleton)
    container.register_singleton(DatabasePool, create_database_pool())
    container.register_singleton(RedisCache, create_redis_cache())
    container.register_singleton(EventBus, InProcessEventBus())
    
    # Domain services (scoped)
    container.register_scoped(UserRepository, 
        lambda c: PostgresUserRepository(c.resolve(DatabasePool))
    )
    container.register_scoped(AuthService,
        lambda c: AuthService(c.resolve(UserRepository))
    )
    
    # Application services (transient)
    container.register_transient(RegisterUserHandler,
        lambda c: RegisterUserHandler(
            c.resolve(AuthService),
            c.resolve(EventBus)
        )
    )
```

#### API Gateway Pattern

**Unified API Composition:**
```python
def create_api_gateway() -> FastAPI:
    """Create unified API gateway"""
    
    app = FastAPI(
        title="TradeSense API Gateway",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # Feature routers with versioning
    from features.authentication.presentation.api import router as auth_router
    from features.billing.presentation.api import router as billing_router
    from features.trading.presentation.api import router as trading_router
    from features.analytics.presentation.api import router as analytics_router
    
    # Mount feature APIs
    app.include_router(
        auth_router,
        prefix="/api/v1/auth",
        tags=["Authentication"]
    )
    app.include_router(
        billing_router,
        prefix="/api/v1/billing",
        tags=["Billing & Subscriptions"]
    )
    app.include_router(
        trading_router,
        prefix="/api/v1/trading",
        tags=["Trading Operations"]
    )
    app.include_router(
        analytics_router,
        prefix="/api/v1/analytics",
        tags=["Analytics & Reports"]
    )
    
    # Cross-cutting middleware
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://app.tradesense.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health checks
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.utcnow()}
    
    @app.get("/ready", tags=["Health"])
    async def readiness_check(db: Database = Depends(get_db)):
        # Check database connectivity
        await db.execute("SELECT 1")
        return {"status": "ready"}
    
    return app
```

---

### Database Architecture and Multi-Tenancy

#### Multi-Tenancy Strategy Decision

**Analysis of Three Patterns:**

1. **Separate Database per Tenant**
   - ❌ 100+ databases to manage
   - ❌ Complex cross-tenant analytics
   - ❌ High operational overhead
   
2. **Separate Schema per Tenant**
   - ❌ Schema proliferation
   - ❌ Migration complexity
   - ✅ Good isolation
   
3. **Shared Database with Row-Level Security** ✅ SELECTED
   - ✅ Operational simplicity
   - ✅ Cost efficiency (60-80% reduction)
   - ✅ Cross-tenant analytics
   - ✅ Single backup strategy

#### PostgreSQL Row-Level Security Implementation

**Database Schema Design:**
```sql
-- Create tenant management schema
CREATE SCHEMA IF NOT EXISTS tenant_management;

-- Tenant table
CREATE TABLE tenant_management.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    plan_type VARCHAR(50) NOT NULL DEFAULT 'starter',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Current tenant function
CREATE OR REPLACE FUNCTION tenant_management.current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        NULLIF(current_setting('app.current_tenant_id', true), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS on all tables
ALTER TABLE tradesense.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tradesense.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE tradesense.portfolios ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY tenant_isolation_policy ON tradesense.users
    FOR ALL TO application_user
    USING (tenant_id = tenant_management.current_tenant_id());

CREATE POLICY tenant_isolation_policy ON tradesense.trades
    FOR ALL TO application_user
    USING (tenant_id = tenant_management.current_tenant_id());

-- Automatic tenant_id insertion
CREATE OR REPLACE FUNCTION tenant_management.inject_tenant_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.tenant_id = tenant_management.current_tenant_id();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER inject_tenant_id_trigger
    BEFORE INSERT ON tradesense.users
    FOR EACH ROW
    EXECUTE FUNCTION tenant_management.inject_tenant_id();
```

**Application-Level Tenant Context:**
```python
class TenantContextMiddleware:
    """Middleware to set tenant context for each request"""
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            
            # Extract tenant from subdomain or header
            host = headers.get(b"host", b"").decode()
            tenant_id = self._extract_tenant_id(host, headers)
            
            # Store in context for request lifecycle
            tenant_context_var.set(tenant_id)
            
        await self.app(scope, receive, send)
    
    def _extract_tenant_id(self, host: str, headers: Dict[bytes, bytes]) -> str:
        """Extract tenant ID from request"""
        # Try subdomain first
        if ".tradesense.com" in host:
            subdomain = host.split(".")[0]
            tenant = self._get_tenant_by_subdomain(subdomain)
            if tenant:
                return str(tenant.id)
        
        # Fall back to header (for API clients)
        tenant_header = headers.get(b"x-tenant-id", b"").decode()
        if tenant_header:
            return tenant_header
        
        raise TenantNotFoundError("No tenant context")

class TenantAwareDatabase:
    """Database wrapper that sets tenant context"""
    
    def __init__(self, pool: AsyncConnectionPool):
        self._pool = pool
    
    @asynccontextmanager
    async def connection(self):
        """Get connection with tenant context set"""
        async with self._pool.acquire() as conn:
            tenant_id = tenant_context_var.get()
            
            # Set tenant context for this connection
            await conn.execute(
                "SELECT set_config('app.current_tenant_id', $1, false)",
                str(tenant_id)
            )
            
            yield conn
```

#### Performance Optimization Strategy

**Indexing Strategy:**
```sql
-- Composite indexes with tenant_id as leading column
CREATE INDEX idx_trades_tenant_date 
    ON tradesense.trades(tenant_id, entry_date DESC);

CREATE INDEX idx_portfolios_tenant_user 
    ON tradesense.portfolios(tenant_id, user_id);

-- Partial indexes for common queries
CREATE INDEX idx_active_trades 
    ON tradesense.trades(tenant_id, symbol) 
    WHERE status = 'active';

-- BRIN indexes for time-series data
CREATE INDEX idx_trades_created_brin 
    ON tradesense.trades USING BRIN(tenant_id, created_at);
```

**Connection Pool Configuration:**
```python
# Optimized connection pool settings
database_config = {
    "min_connections": 10,
    "max_connections": 50,
    "max_inactive_connection_lifetime": 300,
    "command_timeout": 60,
    
    # Performance settings
    "server_settings": {
        "jit": "off",  # Disable JIT for consistent performance
        "synchronous_commit": "off",  # Async commits for speed
        "wal_writer_delay": "200ms",
        "commit_delay": "10",
        "work_mem": "10MB",
        "maintenance_work_mem": "256MB"
    }
}
```

---

### Caching Strategy

#### Multi-Level Cache Architecture

**Cache Hierarchy:**
```
┌─────────────────┐
│  Browser Cache  │ 5 minutes for static assets
├─────────────────┤
│   CDN Cache     │ 24 hours for public content
├─────────────────┤
│ Application     │ In-memory cache for hot data
│ Memory Cache    │
├─────────────────┤
│  Redis Cache    │ Distributed cache for shared data
├─────────────────┤
│Database Cache   │ Query result cache
└─────────────────┘
```

**Redis Cache Implementation:**
```python
class CacheService:
    """Multi-level caching service"""
    
    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        self._local_cache = TTLCache(maxsize=1000, ttl=300)
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[T]],
        ttl: int = 3600,
        use_local: bool = True
    ) -> T:
        """Get from cache or compute and cache"""
        
        # Check local cache first
        if use_local and key in self._local_cache:
            return self._local_cache[key]
        
        # Check Redis
        cached = await self._redis.get(key)
        if cached:
            value = json.loads(cached)
            if use_local:
                self._local_cache[key] = value
            return value
        
        # Compute value
        value = await factory()
        
        # Cache in Redis
        await self._redis.setex(
            key,
            ttl,
            json.dumps(value, cls=CustomJSONEncoder)
        )
        
        # Cache locally
        if use_local:
            self._local_cache[key] = value
        
        return value
    
    def invalidate(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        # Clear local cache
        keys_to_remove = [k for k in self._local_cache if fnmatch(k, pattern)]
        for key in keys_to_remove:
            del self._local_cache[key]
        
        # Clear Redis cache
        for key in self._redis.scan_iter(match=pattern):
            self._redis.delete(key)
```

**Cache Key Strategy:**
```python
class CacheKeyBuilder:
    """Consistent cache key generation"""
    
    @staticmethod
    def user_profile(tenant_id: str, user_id: str) -> str:
        return f"tenant:{tenant_id}:user:{user_id}:profile"
    
    @staticmethod
    def portfolio_metrics(tenant_id: str, portfolio_id: str, date: date) -> str:
        return f"tenant:{tenant_id}:portfolio:{portfolio_id}:metrics:{date}"
    
    @staticmethod
    def trade_analytics(tenant_id: str, timeframe: str, filters: Dict) -> str:
        filter_hash = hashlib.md5(
            json.dumps(filters, sort_keys=True).encode()
        ).hexdigest()
        return f"tenant:{tenant_id}:analytics:{timeframe}:{filter_hash}"
```

---

### API Design and Versioning

#### RESTful API Standards

**API Design Principles:**
1. **Resource-Oriented**: URLs represent resources, not actions
2. **Stateless**: Each request contains all necessary information
3. **Consistent**: Predictable patterns across all endpoints
4. **Versioned**: Clear versioning strategy for evolution

**Standard Response Format:**
```python
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""
    success: bool
    data: Optional[T] = None
    error: Optional[APIError] = None
    metadata: Optional[ResponseMetadata] = None

class APIError(BaseModel):
    """Standard error format"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    field_errors: Optional[List[FieldError]] = None

class ResponseMetadata(BaseModel):
    """Response metadata"""
    request_id: str
    timestamp: datetime
    version: str
    pagination: Optional[PaginationInfo] = None

# Usage example
@router.get("/trades", response_model=APIResponse[List[Trade]])
async def get_trades(
    filters: TradeFilters = Depends(),
    pagination: PaginationParams = Depends(),
    service: TradeService = Depends(get_trade_service)
) -> APIResponse[List[Trade]]:
    """Get user trades with filters"""
    
    try:
        trades = await service.get_trades(filters, pagination)
        
        return APIResponse(
            success=True,
            data=trades,
            metadata=ResponseMetadata(
                request_id=get_request_id(),
                timestamp=datetime.utcnow(),
                version="1.0",
                pagination=pagination.to_info(len(trades))
            )
        )
    except ValidationError as e:
        return APIResponse(
            success=False,
            error=APIError(
                code="VALIDATION_ERROR",
                message="Invalid request parameters",
                field_errors=e.errors()
            )
        )
```

#### API Versioning Strategy

**URL Path Versioning:**
```python
# Version in URL path
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

# Version-specific implementations
class TradeServiceV1:
    """V1 trade service implementation"""
    async def get_trades(self, filters: TradeFiltersV1) -> List[TradeV1]:
        # V1 logic
        pass

class TradeServiceV2:
    """V2 trade service with enhanced features"""
    async def get_trades(self, filters: TradeFiltersV2) -> List[TradeV2]:
        # V2 logic with backward compatibility
        pass
```

---

### Message Queue Integration

#### RabbitMQ Architecture

**Exchange Configuration:**
```python
class MessageBusConfig:
    """RabbitMQ configuration"""
    
    # Exchanges
    EVENTS_EXCHANGE = "tradesense.events"  # Topic exchange for events
    COMMANDS_EXCHANGE = "tradesense.commands"  # Direct exchange for commands
    DLX_EXCHANGE = "tradesense.dlx"  # Dead letter exchange
    
    # Queues
    ANALYTICS_QUEUE = "analytics.events"
    NOTIFICATIONS_QUEUE = "notifications.events"
    BILLING_QUEUE = "billing.commands"
    
    # Routing patterns
    TRADE_EVENTS = "trade.*"
    USER_EVENTS = "user.*"
    BILLING_EVENTS = "billing.*"

async def setup_message_bus(connection: aio_pika.Connection):
    """Setup RabbitMQ topology"""
    
    channel = await connection.channel()
    
    # Declare exchanges
    events_exchange = await channel.declare_exchange(
        MessageBusConfig.EVENTS_EXCHANGE,
        type=ExchangeType.TOPIC,
        durable=True
    )
    
    commands_exchange = await channel.declare_exchange(
        MessageBusConfig.COMMANDS_EXCHANGE,
        type=ExchangeType.DIRECT,
        durable=True
    )
    
    # Declare queues with DLX
    analytics_queue = await channel.declare_queue(
        MessageBusConfig.ANALYTICS_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": MessageBusConfig.DLX_EXCHANGE,
            "x-message-ttl": 3600000  # 1 hour TTL
        }
    )
    
    # Bind queues to exchanges
    await analytics_queue.bind(
        events_exchange,
        routing_key=MessageBusConfig.TRADE_EVENTS
    )
```

---

### Security Architecture

#### Authentication and Authorization

**JWT-Based Authentication:**
```python
class JWTService:
    """JWT token management service"""
    
    def __init__(self, settings: SecuritySettings):
        self._private_key = settings.jwt_private_key
        self._public_key = settings.jwt_public_key
        self._algorithm = "RS256"
        self._access_token_ttl = timedelta(minutes=15)
        self._refresh_token_ttl = timedelta(days=30)
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        roles: List[str]
    ) -> str:
        """Create JWT access token"""
        
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "tenant": tenant_id,
            "roles": roles,
            "iat": now,
            "exp": now + self._access_token_ttl,
            "type": "access"
        }
        
        return jwt.encode(
            payload,
            self._private_key,
            algorithm=self._algorithm
        )
```

#### API Security Middleware

**Security Headers:**
```python
class SecurityHeadersMiddleware:
    """Add security headers to responses"""
    
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
```

---

### Monitoring and Observability

#### Comprehensive Monitoring Stack

**Metrics Collection:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
trades_created = Counter(
    'trades_created_total',
    'Total number of trades created',
    ['tenant_id', 'trade_type']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status']
)

active_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections',
    ['tenant_id']
)

# Decorator for automatic metrics
def track_metrics(endpoint: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            status = 500
            
            try:
                result = await func(*args, **kwargs)
                status = 200
                return result
            except HTTPException as e:
                status = e.status_code
                raise
            finally:
                duration = time.time() - start
                api_request_duration.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=status
                ).observe(duration)
        
        return wrapper
    return decorator
```

#### Distributed Tracing

**OpenTelemetry Integration:**
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Initialize tracing
tracer = trace.get_tracer(__name__)

# Instrument frameworks
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)

# Custom spans
@router.post("/trades")
async def create_trade(trade_data: CreateTradeRequest):
    with tracer.start_as_current_span("create_trade") as span:
        span.set_attribute("trade.symbol", trade_data.symbol)
        span.set_attribute("trade.quantity", trade_data.quantity)
        
        # Business logic with nested spans
        with tracer.start_as_current_span("validate_trade"):
            validation_result = await validate_trade(trade_data)
        
        with tracer.start_as_current_span("persist_trade"):
            trade = await trade_service.create(trade_data)
        
        return trade
```

---

### Deployment and DevOps

#### Container Strategy

**Multi-Stage Dockerfile:**
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Security: Non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

# Environment
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
          
      - name: Security scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'tradesense:${{ github.sha }}'
          
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api api=tradesense:${{ github.sha }}
          kubectl rollout status deployment/api
```

---

### Performance Optimization

#### Database Query Optimization

**Query Performance Patterns:**
```python
class OptimizedTradeRepository:
    """Repository with query optimizations"""
    
    async def get_portfolio_trades(
        self,
        portfolio_id: str,
        date_range: DateRange,
        limit: int = 100
    ) -> List[Trade]:
        """Get trades with optimized query"""
        
        # Use prepared statement
        query = """
            SELECT 
                t.*,
                -- Avoid N+1 by joining related data
                json_agg(
                    json_build_object(
                        'id', tn.id,
                        'content', tn.content,
                        'created_at', tn.created_at
                    )
                ) FILTER (WHERE tn.id IS NOT NULL) as notes
            FROM trades t
            LEFT JOIN trade_notes tn ON t.id = tn.trade_id
            WHERE 
                t.portfolio_id = $1
                AND t.entry_date BETWEEN $2 AND $3
                AND t.tenant_id = current_setting('app.current_tenant_id')::uuid
            GROUP BY t.id
            ORDER BY t.entry_date DESC
            LIMIT $4
        """
        
        rows = await self._db.fetch_all(
            query,
            portfolio_id,
            date_range.start,
            date_range.end,
            limit
        )
        
        return [self._row_to_trade(row) for row in rows]
```

#### Application Performance

**Async Processing:**
```python
class AsyncAnalyticsProcessor:
    """Asynchronous analytics processing"""
    
    def __init__(self, task_queue: Queue):
        self._queue = task_queue
        self._workers = []
    
    async def start_workers(self, count: int = 4):
        """Start async worker pool"""
        for i in range(count):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
    
    async def _worker(self, name: str):
        """Worker process loop"""
        while True:
            try:
                task = await self._queue.get()
                await self._process_task(task)
            except Exception as e:
                logger.error(f"Worker {name} error: {e}")
            finally:
                self._queue.task_done()
    
    async def _process_task(self, task: AnalyticsTask):
        """Process single analytics task"""
        async with self._semaphore:  # Limit concurrent processing
            result = await calculate_metrics(task.data)
            await self._store_result(task.id, result)
```

---

### Future Evolution Considerations

#### Microservice Extraction Roadmap

**Service Boundaries:**
```
Phase 1 (Months 12-15):
├── Authentication Service
│   ├── User management
│   ├── Token generation
│   └── Session management
│
Phase 2 (Months 15-18):
├── Notification Service
│   ├── Email notifications
│   ├── Push notifications
│   └── In-app notifications
│
Phase 3 (Months 18-21):
├── Analytics Engine
│   ├── Real-time calculations
│   ├── Report generation
│   └── Data aggregation
│
Phase 4 (Months 21-24):
├── Billing Service
│   ├── Subscription management
│   ├── Payment processing
│   └── Invoice generation
```

#### Technology Evolution

**Future Considerations:**
1. **GraphQL Gateway**: For flexible client queries
2. **gRPC**: For internal service communication
3. **Service Mesh**: For advanced traffic management
4. **Event Sourcing**: For audit and replay capabilities

This infrastructure design provides a solid foundation that can evolve with TradeSense's growth while maintaining simplicity and operational efficiency at each stage.