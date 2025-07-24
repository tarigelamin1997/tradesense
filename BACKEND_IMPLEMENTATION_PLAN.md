# Backend Implementation Plan - Detailed Technical Guide

## Phase 1: Security Completion (Priority: CRITICAL)

### 1.1 Complete MFA Implementation

```python
# src/backend/services/mfa_service.py
import pyotp
import qrcode
import io
import base64
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

class MFAService:
    def __init__(self):
        self.issuer_name = "TradeSense"
    
    async def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    async def generate_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for authenticator app"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        
        return base64.b64encode(buf.getvalue()).decode()
    
    async def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    async def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        import secrets
        return [secrets.token_hex(4) for _ in range(count)]

# src/backend/api/v1/endpoints/mfa.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.backend.core.deps import get_current_user, get_db
from src.backend.services.mfa_service import MFAService
from src.backend.schemas.mfa import (
    MFAEnableRequest, MFAEnableResponse,
    MFAVerifyRequest, MFAVerifyResponse
)

router = APIRouter()
mfa_service = MFAService()

@router.post("/mfa/enable", response_model=MFAEnableResponse)
async def enable_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable MFA for user"""
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA already enabled"
        )
    
    secret = await mfa_service.generate_secret()
    qr_code = await mfa_service.generate_qr_code(current_user.email, secret)
    backup_codes = await mfa_service.generate_backup_codes()
    
    # Store temporarily until verified
    await redis_client.setex(
        f"mfa_setup:{current_user.id}",
        300,  # 5 minutes
        {
            "secret": secret,
            "backup_codes": backup_codes
        }
    )
    
    return MFAEnableResponse(
        qr_code=qr_code,
        backup_codes=backup_codes
    )
```

### 1.2 Secrets Management Integration

```python
# src/backend/core/secrets_manager.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import boto3
import hvac
from functools import lru_cache
import json

class SecretsProvider(ABC):
    @abstractmethod
    async def get_secret(self, secret_name: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def set_secret(self, secret_name: str, secret_value: str) -> bool:
        pass

class AWSSecretsProvider(SecretsProvider):
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client("secretsmanager", region_name=region_name)
    
    async def get_secret(self, secret_name: str) -> Optional[str]:
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response["SecretString"]
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {e}")
            return None
    
    async def set_secret(self, secret_name: str, secret_value: str) -> bool:
        try:
            self.client.put_secret_value(
                SecretId=secret_name,
                SecretString=secret_value
            )
            return True
        except Exception:
            return False

class VaultSecretsProvider(SecretsProvider):
    def __init__(self, vault_url: str, token: str):
        self.client = hvac.Client(url=vault_url, token=token)
    
    async def get_secret(self, secret_name: str) -> Optional[str]:
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_name
            )
            return response["data"]["data"].get("value")
        except Exception:
            return None

class SecretsManager:
    def __init__(self, provider: SecretsProvider):
        self.provider = provider
        self._cache = {}
    
    @lru_cache(maxsize=100)
    async def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret with caching"""
        if secret_name in self._cache:
            return self._cache[secret_name]
        
        value = await self.provider.get_secret(secret_name)
        if value:
            self._cache[secret_name] = value
            return value
        
        return default
    
    async def get_database_url(self) -> str:
        """Get database URL from secrets"""
        db_config = await self.get_secret("database/config")
        if db_config:
            config = json.loads(db_config)
            return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        
        # Fallback to environment variable
        return os.getenv("DATABASE_URL")

# Usage in config.py
from src.backend.core.secrets_manager import SecretsManager, AWSSecretsProvider

secrets_manager = SecretsManager(AWSSecretsProvider())

class Settings(BaseSettings):
    @property
    def database_url(self) -> str:
        return asyncio.run(secrets_manager.get_database_url())
    
    @property
    def jwt_secret(self) -> str:
        return asyncio.run(secrets_manager.get_secret("jwt/secret", "fallback-secret"))
```

### 1.3 Database Connection Pooling

```python
# src/backend/core/database_pool.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    def __init__(self, database_url: str, **kwargs):
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        
        # Pool configuration
        self.pool_size = kwargs.get("pool_size", 20)
        self.max_overflow = kwargs.get("max_overflow", 40)
        self.pool_timeout = kwargs.get("pool_timeout", 30)
        self.pool_recycle = kwargs.get("pool_recycle", 3600)
        
    async def connect(self):
        """Initialize database connection pool"""
        pool_class = QueuePool
        
        if "sqlite" in self.database_url:
            # SQLite doesn't support connection pooling
            pool_class = StaticPool
        
        self.engine = create_async_engine(
            self.database_url,
            poolclass=pool_class,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=False,
            pool_pre_ping=True,  # Verify connections before using
        )
        
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Test connection
        async with self.engine.begin() as conn:
            await conn.run_sync(lambda conn: conn.execute("SELECT 1"))
        
        logger.info("Database connection pool initialized")
    
    async def disconnect(self):
        """Close all database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get database session with automatic cleanup"""
        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.engine or not hasattr(self.engine.pool, "status"):
            return {}
        
        return {
            "size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "overflow": self.engine.pool.overflow(),
            "total": self.engine.pool.total()
        }

# Update database dependency
database_pool = DatabasePool(settings.database_url)

async def get_db() -> AsyncSession:
    async with database_pool.get_session() as session:
        yield session
```

## Phase 2: Infrastructure Implementation

### 2.1 Redis Caching Layer

```python
# src/backend/core/redis_client.py
import redis.asyncio as redis
from typing import Optional, Any, Union
import json
import pickle
from functools import wraps

class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        self.client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
            retry_on_timeout=True,
            retry_on_error=[redis.ConnectionError, redis.TimeoutError]
        )
        await self.client.ping()
        
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(self, key: str, value: Any, expire: int = None):
        """Set value in cache"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        if expire:
            await self.client.setex(key, expire, value)
        else:
            await self.client.set(key, value)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key)

# Cache decorator
def cache(expire: int = 300, prefix: str = "cache"):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.set(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator

# Usage example
@cache(expire=3600, prefix="user")
async def get_user_by_id(user_id: int, db: AsyncSession):
    return await db.get(User, user_id)
```

### 2.2 Celery Background Tasks

```python
# src/backend/core/celery_app.py
from celery import Celery
from kombu import Exchange, Queue
from src.backend.core.config import settings

celery_app = Celery(
    "tradesense",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.backend.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Configure task routing
celery_app.conf.task_routes = {
    "src.backend.tasks.email.*": {"queue": "email"},
    "src.backend.tasks.reports.*": {"queue": "reports"},
    "src.backend.tasks.maintenance.*": {"queue": "maintenance"},
}

# Define queues
celery_app.conf.task_queues = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("email", Exchange("email"), routing_key="email"),
    Queue("reports", Exchange("reports"), routing_key="reports"),
    Queue("maintenance", Exchange("maintenance"), routing_key="maintenance"),
)

# src/backend/tasks/email_tasks.py
from src.backend.core.celery_app import celery_app
from src.backend.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, to_email: str, subject: str, body: str, template: str = None):
    """Send email asynchronously"""
    try:
        email_service = EmailService()
        email_service.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            template=template
        )
        return {"status": "sent", "email": to_email}
    except Exception as exc:
        logger.error(f"Email sending failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

@celery_app.task
def send_bulk_emails(email_list: List[Dict[str, str]]):
    """Send bulk emails"""
    results = []
    for email_data in email_list:
        result = send_email_task.delay(
            to_email=email_data["email"],
            subject=email_data["subject"],
            body=email_data["body"]
        )
        results.append(result.id)
    return results
```

### 2.3 Structured Logging

```python
# src/backend/core/logging_config.py
import logging
import json
import sys
from datetime import datetime
from pythonjsonlogger import jsonlogger
from typing import Dict, Any

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id

def setup_logging(log_level: str = "INFO", log_format: str = "json"):
    """Configure structured logging"""
    handlers = []
    
    if log_format == "json":
        # JSON format for production
        json_handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter()
        json_handler.setFormatter(formatter)
        handlers.append(json_handler)
    else:
        # Human-readable format for development
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers
    )
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Logging middleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        
        # Add request ID to context
        request.state.request_id = request_id
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log response
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration
                },
                exc_info=True
            )
            raise
```

## Phase 3: Production Configuration

### 3.1 Docker Setup

```dockerfile
# Dockerfile
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Production image
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["gunicorn", "src.backend.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### 3.2 Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradesense-backend
  labels:
    app: tradesense-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tradesense-backend
  template:
    metadata:
      labels:
        app: tradesense-backend
    spec:
      containers:
      - name: backend
        image: tradesense/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: redis-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      - name: celery-worker
        image: tradesense/backend:latest
        command: ["celery", "-A", "src.backend.core.celery_app", "worker", "--loglevel=info"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: tradesense-backend
spec:
  selector:
    app: tradesense-backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tradesense-backend
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.tradesense.com
    secretName: tradesense-tls
  rules:
  - host: api.tradesense.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tradesense-backend
            port:
              number: 80
```

### 3.3 CI/CD Pipeline

```yaml
# .github/workflows/backend-ci.yml
name: Backend CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: tradesense_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost:5432/tradesense_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/ -v --cov=src/backend --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
  
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          tradesense/backend:latest
          tradesense/backend:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Kubernetes
      env:
        KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
      run: |
        echo "$KUBE_CONFIG" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
        kubectl set image deployment/tradesense-backend backend=tradesense/backend:${{ github.sha }}
        kubectl rollout status deployment/tradesense-backend
```

## Implementation Timeline

### Week 1 Daily Tasks:
- **Monday**: MFA implementation (8 hours)
- **Tuesday**: Secrets management (8 hours)
- **Wednesday**: Database pooling & optimization (8 hours)
- **Thursday**: OAuth integration (8 hours)
- **Friday**: Testing & documentation (8 hours)

### Week 2 Daily Tasks:
- **Monday**: Redis integration (8 hours)
- **Tuesday**: Celery setup (8 hours)
- **Wednesday**: Logging & monitoring (8 hours)
- **Thursday**: WebSocket implementation (8 hours)
- **Friday**: API documentation (8 hours)

### Week 3 Daily Tasks:
- **Monday**: Environment configuration (8 hours)
- **Tuesday**: Docker setup (8 hours)
- **Wednesday**: Kubernetes deployment (8 hours)
- **Thursday**: CI/CD pipeline (8 hours)
- **Friday**: Final testing & documentation (8 hours)

## Success Criteria
- All tests passing (>90% coverage)
- Performance benchmarks met
- Security scan passing
- Documentation complete
- Deployment automated