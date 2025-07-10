# Section 4A: Multi-Tenancy & Authentication
*Extracted from ARCHITECTURE_STRATEGY.md*

---

## SECTION 4A: MULTI-TENANCY & AUTHENTICATION

### Strategic Infrastructure Philosophy

The multi-tenancy and authentication architecture for TradeSense v2.7.0 represents a **critical foundation** for scalable SaaS operations. This section details the comprehensive strategy for tenant isolation, authentication, authorization, and security that enables scaling from **startup to enterprise customers** while maintaining data security, compliance, and operational efficiency.

The architecture implements a **hybrid isolation strategy** with three tiers of tenant separation, comprehensive JWT-based authentication, enterprise SSO integration, and granular permission management—all designed to support **$10M+ ARR** with minimal operational overhead.

---

### Multi-Tenancy Strategy and Analysis

#### Tenant Isolation Requirements Analysis

**Business Context:**
- **Target Market**: B2B SaaS serving trading firms, hedge funds, and individual professional traders
- **Compliance Requirements**: SOC2, GDPR, financial industry regulations
- **Scale Requirements**: 10-10,000 tenants, 100-100,000 total users
- **Enterprise Needs**: Data sovereignty, custom domains, white-label options

#### Three-Tier Isolation Strategy

**1. Shared Database with Row-Level Security (90% of tenants)**
- **Target**: Small to medium businesses, individual traders
- **Isolation**: PostgreSQL RLS with automatic tenant filtering
- **Benefits**: Lowest operational cost, simplified management
- **Revenue**: $100-$2,000/month per tenant

**2. Separate Schema Isolation (9% of tenants)**
- **Target**: Enterprise customers with compliance requirements
- **Isolation**: Dedicated PostgreSQL schema per tenant
- **Benefits**: Enhanced performance isolation, easier compliance
- **Revenue**: $2,000-$10,000/month per tenant

**3. Separate Database Isolation (1% of tenants)**
- **Target**: Financial institutions, government contracts
- **Isolation**: Dedicated database instance
- **Benefits**: Complete data sovereignty, regional deployment
- **Revenue**: $10,000+/month per tenant

### Tenant Registry Architecture

#### Advanced Tenant Model

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class TenantStatus(Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class IsolationLevel(Enum):
    SHARED = "shared"
    SCHEMA = "schema"
    DATABASE = "database"

@dataclass
class Tenant:
    """Comprehensive tenant model with all metadata"""
    
    # Core identification
    id: UUID
    name: str
    subdomain: str
    custom_domain: Optional[str]
    
    # Business information
    company_name: str
    industry: str
    employee_count: int
    timezone: str
    locale: str
    currency: str
    
    # Subscription details
    plan_id: str
    subscription_status: str
    trial_end_date: Optional[datetime]
    billing_email: str
    payment_method_id: Optional[str]
    
    # Technical configuration
    isolation_level: IsolationLevel
    database_url: Optional[str]  # For dedicated DB
    schema_name: Optional[str]   # For schema isolation
    
    # Resource limits
    max_users: int
    max_portfolios: int
    max_trades_per_month: int
    storage_quota_gb: int
    api_rate_limit: int
    
    # Security settings
    allowed_ip_ranges: List[str]
    require_mfa: bool
    sso_enabled: bool
    sso_provider: Optional[str]
    data_retention_days: int
    
    # Features and customization
    enabled_features: List[str]
    white_label_config: Optional[Dict]
    webhook_endpoints: List[str]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    created_by: str
    status: TenantStatus
    
    # Compliance
    data_residency_region: str
    compliance_certifications: List[str]
    audit_log_retention_days: int
```

#### Tenant Context Management

```python
from contextvars import ContextVar
from typing import Optional
import asyncio

# Thread-safe tenant context
tenant_context_var: ContextVar[Optional[Tenant]] = ContextVar('tenant_context', default=None)

class TenantContextManager:
    """Manages tenant context throughout request lifecycle"""
    
    def __init__(self, tenant_service: TenantService):
        self._tenant_service = tenant_service
        self._cache = TTLCache(maxsize=1000, ttl=300)  # 5-minute cache
    
    async def set_tenant_context(self, tenant_identifier: str) -> Tenant:
        """Set tenant context from subdomain or ID"""
        
        # Check cache first
        if tenant_identifier in self._cache:
            tenant = self._cache[tenant_identifier]
        else:
            # Resolve tenant
            if is_uuid(tenant_identifier):
                tenant = await self._tenant_service.get_by_id(tenant_identifier)
            else:
                tenant = await self._tenant_service.get_by_subdomain(tenant_identifier)
            
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_identifier} not found")
            
            self._cache[tenant_identifier] = tenant
        
        # Validate tenant
        if tenant.status != TenantStatus.ACTIVE:
            raise TenantInactiveError(f"Tenant {tenant.name} is {tenant.status}")
        
        # Set context
        tenant_context_var.set(tenant)
        
        return tenant
    
    def get_current_tenant(self) -> Tenant:
        """Get current tenant from context"""
        tenant = tenant_context_var.get()
        if not tenant:
            raise NoTenantContextError("No tenant context set")
        return tenant
    
    def validate_resource_access(self, resource_type: str, resource_id: str) -> bool:
        """Validate tenant has access to resource"""
        tenant = self.get_current_tenant()
        
        # Implement resource validation logic
        # This prevents cross-tenant data access
        return True
```

### PostgreSQL Row-Level Security Implementation

#### Database Schema with RLS

```sql
-- Tenant management schema
CREATE SCHEMA IF NOT EXISTS tenant_management;

-- Comprehensive tenant table
CREATE TABLE tenant_management.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    custom_domain VARCHAR(255),
    
    -- Business info
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    employee_count INTEGER,
    timezone VARCHAR(50) DEFAULT 'UTC',
    locale VARCHAR(10) DEFAULT 'en-US',
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Subscription
    plan_id VARCHAR(50) NOT NULL,
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'trialing',
    trial_end_date TIMESTAMPTZ,
    billing_email VARCHAR(255) NOT NULL,
    
    -- Technical config
    isolation_level VARCHAR(20) NOT NULL DEFAULT 'shared',
    database_url TEXT,
    schema_name VARCHAR(100),
    
    -- Resource limits stored as JSONB for flexibility
    resource_limits JSONB NOT NULL DEFAULT '{
        "max_users": 10,
        "max_portfolios": 5,
        "max_trades_per_month": 1000,
        "storage_quota_gb": 10,
        "api_rate_limit": 1000
    }',
    
    -- Security settings
    security_config JSONB NOT NULL DEFAULT '{
        "allowed_ip_ranges": [],
        "require_mfa": false,
        "sso_enabled": false,
        "data_retention_days": 365
    }',
    
    -- Features and customization
    enabled_features TEXT[] DEFAULT ARRAY['basic_analytics', 'portfolio_management'],
    white_label_config JSONB,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    
    -- Compliance
    data_residency_region VARCHAR(20) DEFAULT 'us-east-1',
    compliance_certifications TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- RLS function for current tenant
CREATE OR REPLACE FUNCTION tenant_management.current_tenant_id()
RETURNS UUID AS $$
BEGIN
    -- Get tenant from session variable
    RETURN COALESCE(
        NULLIF(current_setting('app.current_tenant_id', true), ''),
        '00000000-0000-0000-0000-000000000000'  -- Default/system tenant
    )::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Apply RLS to all tenant-scoped tables
CREATE OR REPLACE FUNCTION tenant_management.enable_rls_on_table(
    schema_name TEXT,
    table_name TEXT
)
RETURNS VOID AS $$
BEGIN
    -- Enable RLS
    EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', schema_name, table_name);
    
    -- Create policy
    EXECUTE format('
        CREATE POLICY tenant_isolation_policy ON %I.%I
        FOR ALL
        TO application_user
        USING (tenant_id = tenant_management.current_tenant_id())
        WITH CHECK (tenant_id = tenant_management.current_tenant_id())
    ', schema_name, table_name);
    
    -- Create index for performance
    EXECUTE format('
        CREATE INDEX IF NOT EXISTS idx_%s_tenant_id 
        ON %I.%I(tenant_id)
    ', table_name, schema_name, table_name);
END;
$$ LANGUAGE plpgsql;

-- Apply RLS to all tables
DO $$
DECLARE
    t RECORD;
BEGIN
    FOR t IN 
        SELECT table_schema, table_name 
        FROM information_schema.columns 
        WHERE column_name = 'tenant_id' 
        AND table_schema NOT IN ('pg_catalog', 'information_schema', 'tenant_management')
    LOOP
        PERFORM tenant_management.enable_rls_on_table(t.table_schema, t.table_name);
    END LOOP;
END $$;
```

#### Automatic Tenant Context in Database Connections

```python
class TenantAwareDatabase:
    """Database connection manager with automatic tenant context"""
    
    def __init__(self, base_pool: asyncpg.Pool):
        self._base_pool = base_pool
    
    @asynccontextmanager
    async def connection(self) -> asyncpg.Connection:
        """Get connection with tenant context set"""
        
        # Get current tenant
        tenant = tenant_context_var.get()
        if not tenant:
            raise NoTenantContextError("Database operation requires tenant context")
        
        # Acquire connection
        async with self._base_pool.acquire() as conn:
            try:
                # Set tenant context for this connection
                await conn.execute(
                    "SELECT set_config('app.current_tenant_id', $1, false)",
                    str(tenant.id)
                )
                
                # For schema isolation, set search path
                if tenant.isolation_level == IsolationLevel.SCHEMA:
                    await conn.execute(
                        "SELECT set_config('search_path', $1, false)",
                        f"{tenant.schema_name},public"
                    )
                
                yield conn
                
            finally:
                # Reset context (optional, connection returned to pool)
                await conn.execute("RESET app.current_tenant_id")
                await conn.execute("RESET search_path")
    
    async def execute(self, query: str, *args) -> str:
        """Execute query with tenant context"""
        async with self.connection() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Record]:
        """Fetch records with tenant context"""
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
```

### Authentication Architecture

#### JWT Token Strategy

**Token Types and Lifecycle:**
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"

@dataclass
class TokenClaims:
    """JWT token claims structure"""
    
    # Standard claims
    sub: str  # User ID
    exp: datetime
    iat: datetime
    jti: str  # Token ID for revocation
    
    # Custom claims
    token_type: TokenType
    tenant_id: str
    tenant_subdomain: str
    
    # User context
    email: str
    roles: List[str]
    permissions: List[str]
    
    # Security context
    ip_address: str
    user_agent: str
    session_id: str
    
    # MFA status
    mfa_verified: bool
    mfa_required: bool
    
    # Resource limits
    rate_limit: int
    daily_api_calls: int

class JWTService:
    """Comprehensive JWT token management"""
    
    def __init__(self, config: SecurityConfig):
        # Load RSA keys for asymmetric signing
        self._private_key = serialization.load_pem_private_key(
            config.jwt_private_key.encode(),
            password=None
        )
        self._public_key = serialization.load_pem_public_key(
            config.jwt_public_key.encode()
        )
        
        # Token configuration
        self._access_token_ttl = timedelta(minutes=15)
        self._refresh_token_ttl = timedelta(days=7)
        self._algorithm = "RS256"
        
        # Security
        self._token_blacklist = RedisTokenBlacklist()
    
    async def create_token_pair(
        self,
        user: User,
        tenant: Tenant,
        device_info: DeviceInfo
    ) -> TokenPair:
        """Create access and refresh token pair"""
        
        # Common claims
        base_claims = {
            "tenant_id": str(tenant.id),
            "tenant_subdomain": tenant.subdomain,
            "email": user.email,
            "roles": [role.name for role in user.roles],
            "permissions": await self._get_computed_permissions(user, tenant),
            "ip_address": device_info.ip_address,
            "user_agent": device_info.user_agent,
            "mfa_verified": user.mfa_enabled and device_info.mfa_verified,
            "mfa_required": user.mfa_enabled,
            "rate_limit": tenant.api_rate_limit
        }
        
        # Create access token
        access_token = self._create_token(
            user_id=str(user.id),
            token_type=TokenType.ACCESS,
            ttl=self._access_token_ttl,
            additional_claims=base_claims
        )
        
        # Create refresh token with family tracking
        refresh_token = self._create_token(
            user_id=str(user.id),
            token_type=TokenType.REFRESH,
            ttl=self._refresh_token_ttl,
            additional_claims={
                **base_claims,
                "family_id": str(uuid.uuid4()),  # For refresh token rotation
                "parent_token_id": None
            }
        )
        
        # Store refresh token metadata
        await self._store_refresh_token_metadata(
            user_id=str(user.id),
            token_id=refresh_token.jti,
            family_id=refresh_token.family_id,
            device_info=device_info
        )
        
        return TokenPair(
            access_token=access_token.encoded,
            refresh_token=refresh_token.encoded,
            expires_in=self._access_token_ttl.total_seconds()
        )
    
    async def refresh_tokens(
        self,
        refresh_token: str,
        device_info: DeviceInfo
    ) -> TokenPair:
        """Refresh token pair with rotation"""
        
        try:
            # Decode and validate refresh token
            claims = self._decode_token(refresh_token)
            
            # Verify token type
            if claims.get("token_type") != TokenType.REFRESH.value:
                raise InvalidTokenError("Not a refresh token")
            
            # Check if token is blacklisted
            if await self._token_blacklist.is_blacklisted(claims["jti"]):
                raise TokenRevokedError("Refresh token has been revoked")
            
            # Validate token family (detect token reuse)
            family_valid = await self._validate_token_family(
                claims["jti"],
                claims["family_id"]
            )
            if not family_valid:
                # Potential token theft - revoke entire family
                await self._revoke_token_family(claims["family_id"])
                raise TokenTheftDetectedError("Refresh token reuse detected")
            
            # Get user and tenant
            user = await self._user_service.get_by_id(claims["sub"])
            tenant = await self._tenant_service.get_by_id(claims["tenant_id"])
            
            # Create new token pair
            new_tokens = await self.create_token_pair(user, tenant, device_info)
            
            # Revoke old refresh token
            await self._token_blacklist.blacklist_token(
                claims["jti"],
                expires_at=datetime.fromtimestamp(claims["exp"])
            )
            
            return new_tokens
            
        except JWTError as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
    
    def _create_token(
        self,
        user_id: str,
        token_type: TokenType,
        ttl: timedelta,
        additional_claims: Dict[str, Any]
    ) -> Token:
        """Create individual JWT token"""
        
        now = datetime.utcnow()
        jti = str(uuid.uuid4())
        
        claims = {
            "sub": user_id,
            "exp": now + ttl,
            "iat": now,
            "jti": jti,
            "token_type": token_type.value,
            **additional_claims
        }
        
        encoded = jwt.encode(
            claims,
            self._private_key,
            algorithm=self._algorithm
        )
        
        return Token(
            encoded=encoded,
            jti=jti,
            expires_at=claims["exp"]
        )
```

#### Session Management

```python
class SessionManager:
    """Manages user sessions with Redis backend"""
    
    def __init__(self, redis_client: Redis, config: SessionConfig):
        self._redis = redis_client
        self._session_ttl = config.session_ttl
        self._max_sessions_per_user = config.max_sessions_per_user
    
    async def create_session(
        self,
        user_id: str,
        tenant_id: str,
        device_info: DeviceInfo,
        token_jti: str
    ) -> Session:
        """Create new user session"""
        
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            token_jti=token_jti,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            device_info=device_info,
            ip_address=device_info.ip_address,
            user_agent=device_info.user_agent
        )
        
        # Store session
        session_key = f"session:{session.id}"
        await self._redis.setex(
            session_key,
            self._session_ttl,
            session.json()
        )
        
        # Add to user's session list
        user_sessions_key = f"user_sessions:{user_id}"
        await self._redis.zadd(
            user_sessions_key,
            {session.id: time.time()}
        )
        
        # Enforce session limit
        await self._enforce_session_limit(user_id)
        
        return session
    
    async def validate_session(self, session_id: str) -> Optional[Session]:
        """Validate and refresh session"""
        
        session_key = f"session:{session_id}"
        session_data = await self._redis.get(session_key)
        
        if not session_data:
            return None
        
        session = Session.parse_raw(session_data)
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        await self._redis.setex(
            session_key,
            self._session_ttl,
            session.json()
        )
        
        return session
    
    async def revoke_session(self, session_id: str) -> None:
        """Revoke specific session"""
        
        session_key = f"session:{session_id}"
        session_data = await self._redis.get(session_key)
        
        if session_data:
            session = Session.parse_raw(session_data)
            
            # Remove session
            await self._redis.delete(session_key)
            
            # Remove from user's session list
            user_sessions_key = f"user_sessions:{session.user_id}"
            await self._redis.zrem(user_sessions_key, session_id)
            
            # Blacklist associated token
            await self._token_blacklist.blacklist_token(
                session.token_jti,
                ttl=self._session_ttl
            )
    
    async def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = await self._redis.zrange(user_sessions_key, 0, -1)
        
        count = 0
        for session_id in session_ids:
            await self.revoke_session(session_id.decode())
            count += 1
        
        return count
```

### Authorization Framework

#### Role-Based Access Control (RBAC)

```python
@dataclass
class Permission:
    """Granular permission definition"""
    
    id: str
    name: str
    category: str  # trading, analytics, billing, admin
    resource: str  # trades, portfolios, users, etc.
    action: str    # create, read, update, delete, execute
    description: str
    
    # Conditional constraints
    conditions: Optional[Dict[str, Any]] = None
    
    def allows(self, context: PermissionContext) -> bool:
        """Check if permission allows action in context"""
        
        if not self.conditions:
            return True
        
        # Evaluate conditions
        for condition_type, condition_value in self.conditions.items():
            if condition_type == "own_resource":
                if context.resource_owner_id != context.user_id:
                    return False
            
            elif condition_type == "time_range":
                current_time = datetime.now().time()
                start_time = time.fromisoformat(condition_value["start"])
                end_time = time.fromisoformat(condition_value["end"])
                if not (start_time <= current_time <= end_time):
                    return False
            
            elif condition_type == "max_amount":
                if context.amount and context.amount > condition_value:
                    return False
            
            elif condition_type == "ip_whitelist":
                if context.ip_address not in condition_value:
                    return False
        
        return True

@dataclass
class Role:
    """Role with hierarchical permissions"""
    
    id: str
    name: str
    description: str
    permissions: List[Permission]
    parent_role_id: Optional[str] = None
    
    # Role constraints
    max_users: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class RBACService:
    """Comprehensive RBAC implementation"""
    
    def __init__(self, cache_service: CacheService):
        self._cache = cache_service
        self._permission_evaluator = PermissionEvaluator()
    
    async def get_user_permissions(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[Permission]:
        """Get all permissions for user including inherited"""
        
        cache_key = f"user_permissions:{tenant_id}:{user_id}"
        
        return await self._cache.get_or_set(
            cache_key,
            lambda: self._compute_user_permissions(user_id, tenant_id),
            ttl=300  # 5 minute cache
        )
    
    async def _compute_user_permissions(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[Permission]:
        """Compute effective permissions for user"""
        
        # Get user roles
        user_roles = await self._get_user_roles(user_id, tenant_id)
        
        # Collect permissions from all roles
        permissions = set()
        
        for role in user_roles:
            # Add role permissions
            permissions.update(role.permissions)
            
            # Add inherited permissions
            if role.parent_role_id:
                parent_permissions = await self._get_role_permissions(
                    role.parent_role_id
                )
                permissions.update(parent_permissions)
        
        return list(permissions)
    
    async def check_permission(
        self,
        user_id: str,
        tenant_id: str,
        required_permission: str,
        context: Optional[PermissionContext] = None
    ) -> bool:
        """Check if user has specific permission"""
        
        # Get user permissions
        permissions = await self.get_user_permissions(user_id, tenant_id)
        
        # Find matching permission
        for permission in permissions:
            if permission.id == required_permission:
                # Check conditional constraints
                if context and not permission.allows(context):
                    return False
                return True
        
        return False
    
    def require_permission(self, permission: str):
        """Decorator for permission-based access control"""
        
        def decorator(func):
            @wraps(func)
            async def wrapper(
                *args,
                user: User = Depends(get_current_user),
                tenant: Tenant = Depends(get_current_tenant),
                **kwargs
            ):
                # Build context from request
                context = PermissionContext(
                    user_id=str(user.id),
                    tenant_id=str(tenant.id),
                    ip_address=request.client.host,
                    resource_owner_id=kwargs.get("resource_owner_id")
                )
                
                # Check permission
                allowed = await rbac_service.check_permission(
                    user_id=str(user.id),
                    tenant_id=str(tenant.id),
                    required_permission=permission,
                    context=context
                )
                
                if not allowed:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission {permission} required"
                    )
                
                return await func(*args, user=user, tenant=tenant, **kwargs)
            
            return wrapper
        return decorator
```

#### System Roles and Permissions

```python
# Define system roles hierarchy
SYSTEM_ROLES = {
    "super_admin": Role(
        id="super_admin",
        name="Super Administrator",
        description="Full system access across all tenants",
        permissions=[ALL_PERMISSIONS],  # Every possible permission
        parent_role_id=None
    ),
    
    "tenant_admin": Role(
        id="tenant_admin", 
        name="Tenant Administrator",
        description="Full access within tenant",
        permissions=[
            Permission("manage_users", "admin", "users", "*"),
            Permission("manage_roles", "admin", "roles", "*"),
            Permission("manage_billing", "billing", "*", "*"),
            Permission("view_analytics", "analytics", "*", "read"),
            Permission("manage_settings", "admin", "settings", "*")
        ],
        parent_role_id=None
    ),
    
    "manager": Role(
        id="manager",
        name="Trading Manager", 
        description="Manage traders and view all portfolios",
        permissions=[
            Permission("view_all_portfolios", "trading", "portfolios", "read"),
            Permission("view_all_trades", "trading", "trades", "read"),
            Permission("manage_traders", "admin", "users", "update", {
                "role_constraint": ["trader", "analyst"]
            }),
            Permission("export_reports", "analytics", "reports", "create")
        ],
        parent_role_id="trader"
    ),
    
    "trader": Role(
        id="trader",
        name="Trader",
        description="Execute trades and manage own portfolios",
        permissions=[
            Permission("create_trade", "trading", "trades", "create", {
                "max_amount": 1000000,
                "time_range": {"start": "09:00", "end": "16:00"}
            }),
            Permission("view_own_trades", "trading", "trades", "read", {
                "own_resource": True
            }),
            Permission("manage_portfolios", "trading", "portfolios", "*", {
                "own_resource": True
            })
        ],
        parent_role_id="analyst"
    ),
    
    "analyst": Role(
        id="analyst",
        name="Analyst",
        description="View and analyze trading data",
        permissions=[
            Permission("view_analytics", "analytics", "*", "read"),
            Permission("create_reports", "analytics", "reports", "create"),
            Permission("view_market_data", "trading", "market_data", "read")
        ],
        parent_role_id="viewer"
    ),
    
    "viewer": Role(
        id="viewer",
        name="Viewer",
        description="Read-only access",
        permissions=[
            Permission("view_dashboard", "analytics", "dashboard", "read"),
            Permission("view_public_data", "trading", "public", "read")
        ],
        parent_role_id=None
    )
}
```

### OAuth 2.0 and SSO Integration

#### OAuth Provider Integration

```python
class OAuthProvider(Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    LINKEDIN = "linkedin"
    GITHUB = "github"

@dataclass
class OAuthConfig:
    """OAuth provider configuration"""
    provider: OAuthProvider
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str]
    
    # Provider-specific settings
    tenant_id: Optional[str] = None  # For Microsoft
    hosted_domain: Optional[str] = None  # For Google

class OAuthService:
    """Comprehensive OAuth integration service"""
    
    def __init__(self, config: Dict[OAuthProvider, OAuthConfig]):
        self._providers = config
        self._state_store = RedisStateStore()  # CSRF protection
    
    async def create_authorization_url(
        self,
        provider: OAuthProvider,
        tenant_id: str,
        redirect_uri: str
    ) -> AuthorizationUrl:
        """Create OAuth authorization URL"""
        
        config = self._providers.get(provider)
        if not config:
            raise OAuthProviderNotConfiguredError(f"{provider} not configured")
        
        # Generate state for CSRF protection
        state = OAuthState(
            id=str(uuid.uuid4()),
            provider=provider,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri,
            created_at=datetime.utcnow()
        )
        
        # Store state with TTL
        await self._state_store.save_state(state, ttl=600)  # 10 minutes
        
        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(config.scopes),
            "state": state.id,
            "response_type": "code",
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"
        }
        
        # Provider-specific parameters
        if provider == OAuthProvider.GOOGLE and config.hosted_domain:
            params["hd"] = config.hosted_domain
        elif provider == OAuthProvider.MICROSOFT and config.tenant_id:
            params["tenant"] = config.tenant_id
        
        auth_url = f"{config.authorize_url}?{urlencode(params)}"
        
        return AuthorizationUrl(url=auth_url, state=state.id)
    
    async def handle_callback(
        self,
        provider: OAuthProvider,
        code: str,
        state: str
    ) -> OAuthUser:
        """Handle OAuth callback and exchange code for user info"""
        
        # Validate state
        oauth_state = await self._state_store.validate_state(state)
        if not oauth_state or oauth_state.provider != provider:
            raise OAuthStateValidationError("Invalid OAuth state")
        
        config = self._providers[provider]
        
        # Exchange code for tokens
        token_data = await self._exchange_code_for_token(
            config,
            code,
            oauth_state.redirect_uri
        )
        
        # Get user info
        user_info = await self._get_user_info(
            config,
            token_data["access_token"]
        )
        
        # Normalize user data across providers
        oauth_user = self._normalize_user_info(provider, user_info)
        
        # Store OAuth tokens for future use
        await self._store_oauth_tokens(
            oauth_user.id,
            oauth_state.tenant_id,
            provider,
            token_data
        )
        
        return oauth_user
    
    def _normalize_user_info(
        self,
        provider: OAuthProvider,
        user_info: Dict[str, Any]
    ) -> OAuthUser:
        """Normalize user info across different providers"""
        
        if provider == OAuthProvider.GOOGLE:
            return OAuthUser(
                id=user_info["sub"],
                email=user_info["email"],
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                email_verified=user_info.get("email_verified", False)
            )
        
        elif provider == OAuthProvider.MICROSOFT:
            return OAuthUser(
                id=user_info["id"],
                email=user_info.get("mail") or user_info.get("userPrincipalName"),
                name=user_info.get("displayName"),
                picture=None,  # Need Graph API for photo
                email_verified=True  # Microsoft verifies emails
            )
        
        elif provider == OAuthProvider.LINKEDIN:
            return OAuthUser(
                id=user_info["id"],
                email=user_info.get("email"),
                name=f"{user_info.get('firstName')} {user_info.get('lastName')}",
                picture=user_info.get("profilePicture", {}).get("displayImage"),
                email_verified=True
            )
        
        # Add other providers...
```

#### SAML 2.0 Integration

```python
class SAML2Service:
    """SAML 2.0 SSO implementation"""
    
    def __init__(self, config: SAML2Config):
        self._config = config
        self._metadata_cache = TTLCache(maxsize=100, ttl=3600)
    
    async def create_saml_request(
        self,
        tenant: Tenant,
        relay_state: Optional[str] = None
    ) -> SAMLRequest:
        """Create SAML authentication request"""
        
        # Get tenant's SAML configuration
        saml_config = await self._get_tenant_saml_config(tenant.id)
        if not saml_config:
            raise SAMLNotConfiguredError(f"SAML not configured for tenant {tenant.name}")
        
        # Create SAML request
        request_id = f"id-{uuid.uuid4()}"
        issue_instant = datetime.utcnow().isoformat() + "Z"
        
        saml_request = f"""
        <samlp:AuthnRequest
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{issue_instant}"
            Destination="{saml_config.idp_sso_url}"
            AssertionConsumerServiceURL="{saml_config.sp_acs_url}"
            ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
            
            <saml:Issuer>{saml_config.sp_entity_id}</saml:Issuer>
            
            <samlp:NameIDPolicy
                Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                AllowCreate="true"/>
                
            <samlp:RequestedAuthnContext Comparison="minimum">
                <saml:AuthnContextClassRef>
                    urn:oasis:names:tc:SAML:2.0:ac:classes:Password
                </saml:AuthnContextClassRef>
            </samlp:RequestedAuthnContext>
        </samlp:AuthnRequest>
        """
        
        # Sign request if required
        if saml_config.sign_requests:
            saml_request = self._sign_saml_request(saml_request, saml_config)
        
        # Encode and deflate
        encoded_request = base64.b64encode(
            zlib.compress(saml_request.encode())
        ).decode()
        
        # Build redirect URL
        params = {"SAMLRequest": encoded_request}
        if relay_state:
            params["RelayState"] = relay_state
        
        redirect_url = f"{saml_config.idp_sso_url}?{urlencode(params)}"
        
        return SAMLRequest(
            url=redirect_url,
            request_id=request_id
        )
    
    async def handle_saml_response(
        self,
        saml_response: str,
        relay_state: Optional[str] = None
    ) -> SAMLUser:
        """Process SAML response and extract user info"""
        
        # Decode response
        decoded_response = base64.b64decode(saml_response)
        
        # Parse XML
        root = etree.fromstring(decoded_response)
        
        # Extract tenant from response
        issuer = root.find(".//{urn:oasis:names:tc:SAML:2.0:assertion}Issuer").text
        tenant = await self._get_tenant_by_idp_entity_id(issuer)
        
        # Get SAML config
        saml_config = await self._get_tenant_saml_config(tenant.id)
        
        # Validate response signature
        if not self._validate_saml_signature(root, saml_config):
            raise SAMLSignatureValidationError("Invalid SAML response signature")
        
        # Validate response conditions
        self._validate_saml_conditions(root)
        
        # Extract user attributes
        attributes = self._extract_saml_attributes(root, saml_config.attribute_mapping)
        
        # Create user object
        return SAMLUser(
            name_id=attributes.get("nameID"),
            email=attributes.get("email"),
            first_name=attributes.get("firstName"),
            last_name=attributes.get("lastName"),
            groups=attributes.get("groups", []),
            attributes=attributes
        )
```

### API Key Management

```python
class APIKeyService:
    """Secure API key management service"""
    
    def __init__(self, config: APIKeyConfig):
        self._hasher = hashlib.sha256
        self._prefix_length = 8
        self._key_length = 32
    
    async def create_api_key(
        self,
        tenant_id: str,
        name: str,
        permissions: List[str],
        expires_at: Optional[datetime] = None,
        rate_limit: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None
    ) -> APIKeyCreated:
        """Create new API key with permissions"""
        
        # Generate secure random key
        raw_key = secrets.token_urlsafe(self._key_length)
        
        # Create key format: ts_[prefix]_[suffix]
        prefix = raw_key[:self._prefix_length]
        key_string = f"ts_{prefix}_{raw_key}"
        
        # Hash for storage
        key_hash = self._hasher(key_string.encode()).hexdigest()
        
        # Create key record
        api_key = APIKey(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            permissions=permissions,
            expires_at=expires_at,
            rate_limit=rate_limit or 1000,
            ip_whitelist=ip_whitelist or [],
            created_at=datetime.utcnow(),
            last_used_at=None,
            usage_count=0
        )
        
        # Store key
        await self._api_key_repository.create(api_key)
        
        # Return key only once
        return APIKeyCreated(
            id=api_key.id,
            key=key_string,  # Only time full key is shown
            prefix=prefix,
            name=name,
            expires_at=expires_at
        )
    
    async def validate_api_key(
        self,
        key_string: str,
        ip_address: str
    ) -> Optional[APIKeyContext]:
        """Validate API key and return context"""
        
        # Extract prefix
        if not key_string.startswith("ts_"):
            return None
        
        parts = key_string.split("_")
        if len(parts) != 3:
            return None
        
        prefix = parts[1]
        
        # Find key by prefix
        api_key = await self._api_key_repository.find_by_prefix(prefix)
        if not api_key:
            return None
        
        # Verify hash
        key_hash = self._hasher(key_string.encode()).hexdigest()
        if key_hash != api_key.key_hash:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Check IP whitelist
        if api_key.ip_whitelist and ip_address not in api_key.ip_whitelist:
            return None
        
        # Update usage
        await self._api_key_repository.increment_usage(api_key.id)
        
        # Return context
        return APIKeyContext(
            api_key_id=api_key.id,
            tenant_id=api_key.tenant_id,
            permissions=api_key.permissions,
            rate_limit=api_key.rate_limit
        )
```

### Enterprise Features

#### White-Label Support

```python
class WhiteLabelService:
    """White-label customization service"""
    
    async def get_tenant_branding(self, tenant: Tenant) -> TenantBranding:
        """Get tenant-specific branding configuration"""
        
        if not tenant.white_label_config:
            return self._get_default_branding()
        
        config = tenant.white_label_config
        
        return TenantBranding(
            # Visual customization
            logo_url=config.get("logo_url", "/static/default-logo.png"),
            favicon_url=config.get("favicon_url", "/static/favicon.ico"),
            
            # Colors
            primary_color=config.get("primary_color", "#1976d2"),
            secondary_color=config.get("secondary_color", "#dc004e"),
            background_color=config.get("background_color", "#ffffff"),
            text_color=config.get("text_color", "#333333"),
            
            # Typography
            font_family=config.get("font_family", "Roboto, sans-serif"),
            
            # Content
            company_name=config.get("company_name", tenant.company_name),
            support_email=config.get("support_email", "support@tradesense.com"),
            support_url=config.get("support_url"),
            
            # Features
            hide_tradesense_branding=config.get("hide_branding", False),
            custom_css=config.get("custom_css"),
            custom_js=config.get("custom_js"),
            
            # Email templates
            email_templates=config.get("email_templates", {})
        )
```

#### Data Residency and Compliance

```python
class DataResidencyService:
    """Manage data residency requirements"""
    
    def __init__(self, regions: Dict[str, RegionConfig]):
        self._regions = regions
    
    async def get_tenant_database_url(self, tenant: Tenant) -> str:
        """Get region-specific database URL for tenant"""
        
        region = tenant.data_residency_region
        region_config = self._regions.get(region)
        
        if not region_config:
            raise InvalidRegionError(f"Region {region} not configured")
        
        if tenant.isolation_level == IsolationLevel.DATABASE:
            # Dedicated database in specific region
            return await self._provision_regional_database(
                tenant,
                region_config
            )
        else:
            # Shared database in region
            return region_config.shared_database_url
    
    async def validate_data_access(
        self,
        tenant: Tenant,
        access_region: str
    ) -> bool:
        """Validate data access complies with residency requirements"""
        
        # Check if access is from allowed region
        if tenant.data_residency_region == "eu":
            # GDPR compliance - data must stay in EU
            return access_region.startswith("eu-")
        
        return True
```

### Performance Optimization

#### Caching Strategy

```python
class AuthCacheService:
    """High-performance caching for auth operations"""
    
    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        self._local_cache = TTLCache(maxsize=10000, ttl=60)  # 1-minute local cache
    
    async def cache_user_permissions(
        self,
        user_id: str,
        tenant_id: str,
        permissions: List[str],
        ttl: int = 300
    ) -> None:
        """Cache computed user permissions"""
        
        cache_key = f"perms:{tenant_id}:{user_id}"
        
        # Cache in Redis
        await self._redis.setex(
            cache_key,
            ttl,
            json.dumps(permissions)
        )
        
        # Cache locally for hot path
        self._local_cache[cache_key] = permissions
    
    async def get_cached_permissions(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[List[str]]:
        """Get cached permissions with local cache fallback"""
        
        cache_key = f"perms:{tenant_id}:{user_id}"
        
        # Check local cache first
        if cache_key in self._local_cache:
            return self._local_cache[cache_key]
        
        # Check Redis
        cached = await self._redis.get(cache_key)
        if cached:
            permissions = json.loads(cached)
            self._local_cache[cache_key] = permissions
            return permissions
        
        return None
```

### Section 4A Summary: Infrastructure Benefits and Implementation Strategy

**Comprehensive Multi-Tenancy & Authentication Achievement:**

- **Secure Tenant Isolation**: Implemented three-tier isolation strategy (shared DB, separate schemas, separate databases) with PostgreSQL RLS
- **Enterprise Authentication**: Complete JWT implementation with RS256 signing, refresh token rotation, and session management
- **Granular Authorization**: Hierarchical RBAC system with conditional permissions, resource constraints, and usage limits  
- **Enterprise SSO**: SAML 2.0 and OAuth 2.0/OIDC integration for seamless organizational authentication
- **Developer APIs**: Secure API key management with rate limiting, permission scoping, and comprehensive audit trails

**Security & Compliance Benefits:**
- **Data Segregation**: Complete tenant data isolation with multiple migration paths
- **Audit Compliance**: Comprehensive logging for SOC2, GDPR, and financial industry requirements
- **Security Monitoring**: Real-time threat detection and automated security response
- **Enterprise Readiness**: SSO, MFA, and advanced security features for enterprise customers

This infrastructure foundation enables TradeSense v2.7.0 to scale from startup to enterprise customers while maintaining security, compliance, and operational excellence.