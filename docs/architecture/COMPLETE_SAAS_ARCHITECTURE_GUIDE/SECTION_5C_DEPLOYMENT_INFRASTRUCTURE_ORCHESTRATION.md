# Section 5C: Deployment & Infrastructure Orchestration
*Extracted from ARCHITECTURE_STRATEGY_PART4.md*

---

## **SECTION 5C: DEPLOYMENT & INFRASTRUCTURE ORCHESTRATION**

### **5C.1 CONTAINERIZATION AND ORCHESTRATION STRATEGY**

#### **5C.1.1 Container Architecture Design**

**Strategic Decision:** Implement a microservices-based containerization strategy using Docker and Kubernetes for maximum scalability, portability, and operational consistency across all environments.

**Container Strategy Overview:**
```
TradeSense Container Ecosystem
├── Frontend Containers
│   ├── tradesense-web (React/TypeScript)
│   ├── tradesense-mobile-web (PWA optimized)
│   └── tradesense-admin-dashboard
├── Backend API Containers
│   ├── tradesense-api-gateway (FastAPI)
│   ├── tradesense-trading-service
│   ├── tradesense-user-service
│   ├── tradesense-analytics-service
│   └── tradesense-notification-service
├── Infrastructure Containers
│   ├── tradesense-redis-cluster
│   ├── tradesense-postgres-primary
│   ├── tradesense-postgres-replica
│   └── tradesense-monitoring-stack
└── External Integrations
    ├── tradesense-broker-connectors
    ├── tradesense-market-data-ingestion
    └── tradesense-payment-processors
```

**Dockerfile Architecture - Frontend Container:**

```dockerfile
# File: /frontend/Dockerfile
# Multi-stage build for optimal production container
ARG NODE_VERSION=20.11.0
ARG NGINX_VERSION=1.25.4-alpine

# Build stage
FROM node:${NODE_VERSION}-alpine AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for node-gyp
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    git

# Copy package files
COPY package*.json ./
COPY yarn.lock ./

# Install dependencies with cache optimization
RUN yarn install --frozen-lockfile --network-timeout 100000

# Copy source code
COPY . .

# Build arguments for runtime configuration
ARG BUILD_ENV=production
ARG API_BASE_URL
ARG SENTRY_DSN
ARG ANALYTICS_TRACKING_ID

# Set build environment variables
ENV NODE_ENV=${BUILD_ENV}
ENV REACT_APP_API_BASE_URL=${API_BASE_URL}
ENV REACT_APP_SENTRY_DSN=${SENTRY_DSN}
ENV REACT_APP_ANALYTICS_TRACKING_ID=${ANALYTICS_TRACKING_ID}

# Build application
RUN yarn build

# Verify build output
RUN ls -la /app/dist && \
    echo "Build completed successfully"

# Production stage
FROM nginx:${NGINX_VERSION} AS production

# Install security updates
RUN apk upgrade --no-cache

# Create non-root user
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx nginx

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-security.conf /etc/nginx/conf.d/security.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Set proper permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Create startup script
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'echo "Starting TradeSense Frontend..."' >> /docker-entrypoint.sh && \
    echo 'echo "Environment: $NODE_ENV"' >> /docker-entrypoint.sh && \
    echo 'echo "API URL: $REACT_APP_API_BASE_URL"' >> /docker-entrypoint.sh && \
    echo 'exec "$@"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

# Metadata
LABEL \
    org.opencontainers.image.title="TradeSense Frontend" \
    org.opencontainers.image.description="React/TypeScript frontend for TradeSense trading platform" \
    org.opencontainers.image.vendor="TradeSense" \
    org.opencontainers.image.version="2.7.0" \
    org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    org.opencontainers.image.source="https://github.com/tradesense/frontend"
```

**Dockerfile Architecture - Backend API Container:**

```dockerfile
# File: /backend/Dockerfile
# Multi-stage build for Python FastAPI application
ARG PYTHON_VERSION=3.11.8
ARG ALPINE_VERSION=3.19

# Base stage with common dependencies
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    curl \
    && rm -rf /var/cache/apk/*

# Create application user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G appgroup appuser

# Set working directory
WORKDIR /app

# Dependencies stage
FROM base AS deps

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development stage
FROM deps AS development

# Install development dependencies
RUN pip install -r requirements-dev.txt

# Copy source code
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to application user
USER appuser

# Expose port
EXPOSE 8000

# Development command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM deps AS production

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp && \
    chown -R appuser:appgroup /app

# Switch to application user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production startup script
RUN echo '#!/bin/sh' > start.sh && \
    echo 'echo "Starting TradeSense API..."' >> start.sh && \
    echo 'echo "Environment: $ENVIRONMENT"' >> start.sh && \
    echo 'echo "Database URL: $DATABASE_URL"' >> start.sh && \
    echo '# Run database migrations' >> start.sh && \
    echo 'alembic upgrade head' >> start.sh && \
    echo '# Start application with optimized workers' >> start.sh && \
    echo 'exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker' >> start.sh && \
    chmod +x start.sh

# Default command
CMD ["./start.sh"]

# Metadata
LABEL \
    org.opencontainers.image.title="TradeSense API" \
    org.opencontainers.image.description="FastAPI backend for TradeSense trading platform" \
    org.opencontainers.image.vendor="TradeSense" \
    org.opencontainers.image.version="2.7.0" \
    org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    org.opencontainers.image.source="https://github.com/tradesense/backend"
```

#### **5C.1.2 Kubernetes Orchestration Framework**

**Namespace Organization Strategy:**

```yaml
# File: /k8s/namespaces/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-production
  labels:
    environment: production
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-staging
  labels:
    environment: staging
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-development
  labels:
    environment: development
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: tradesense-monitoring
  labels:
    environment: shared
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: monitoring
```

**Comprehensive Deployment Configuration - API Gateway:**

```yaml
# File: /k8s/deployments/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradesense-api-gateway
  namespace: tradesense-production
  labels:
    app: tradesense-api-gateway
    component: backend
    tier: api
    version: v2.7.0
spec:
  replicas: 3
  revisionHistoryLimit: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: tradesense-api-gateway
  template:
    metadata:
      labels:
        app: tradesense-api-gateway
        component: backend
        tier: api
        version: v2.7.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: tradesense-api-gateway
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
      - name: api-gateway
        image: tradesense/api-gateway:v2.7.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          protocol: TCP
          name: http
        - containerPort: 8080
          protocol: TCP
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-db-credentials
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: tradesense-redis-credentials
              key: REDIS_URL
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: tradesense-auth-secrets
              key: JWT_SECRET_KEY
        - name: SENTRY_DSN
          valueFrom:
            secretKeyRef:
              name: tradesense-monitoring-secrets
              key: SENTRY_DSN
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: app-logs
          mountPath: /app/logs
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: app-logs
        emptyDir: {}
      - name: tmp-volume
        emptyDir: {}
      nodeSelector:
        kubernetes.io/arch: amd64
      tolerations:
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      - key: "node.kubernetes.io/unreachable"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
---
apiVersion: v1
kind: Service
metadata:
  name: tradesense-api-gateway-service
  namespace: tradesense-production
  labels:
    app: tradesense-api-gateway
    component: backend
spec:
  selector:
    app: tradesense-api-gateway
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  - name: metrics
    port: 8080
    targetPort: 8080
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tradesense-api-gateway-ingress
  namespace: tradesense-production
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.tradesense.com
    secretName: tradesense-api-tls
  rules:
  - host: api.tradesense.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tradesense-api-gateway-service
            port:
              number: 80
```

**HorizontalPodAutoscaler Configuration:**

```yaml
# File: /k8s/autoscaling/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: tradesense-api-gateway-hpa
  namespace: tradesense-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: tradesense-api-gateway
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: custom_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

### **5C.2 ENVIRONMENT MANAGEMENT AND CONFIGURATION**

#### **5C.2.1 Environment-Specific Configuration Strategy**

**ConfigMap Management:**

```yaml
# File: /k8s/config/production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tradesense-config
  namespace: tradesense-production
data:
  # Application Configuration
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  
  # API Configuration
  API_VERSION: "v1"
  API_RATE_LIMIT: "1000"
  API_TIMEOUT: "30"
  
  # Database Configuration
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "10"
  DB_POOL_TIMEOUT: "30"
  DB_POOL_RECYCLE: "3600"
  
  # Redis Configuration
  REDIS_MAX_CONNECTIONS: "100"
  REDIS_RETRY_ON_TIMEOUT: "true"
  REDIS_SOCKET_KEEPALIVE: "true"
  
  # Trading Configuration
  MAX_ORDERS_PER_MINUTE: "60"
  POSITION_SIZE_LIMIT: "100000"
  RISK_CHECK_ENABLED: "true"
  
  # Monitoring Configuration
  METRICS_ENABLED: "true"
  TRACING_ENABLED: "true"
  PROMETHEUS_PORT: "8080"
  
  # External Services
  BROKER_TIMEOUT: "5"
  MARKET_DATA_REFRESH_INTERVAL: "1"
  NOTIFICATION_RETRY_ATTEMPTS: "3"
  
  # Security Configuration
  CORS_ORIGINS: "https://tradesense.com,https://app.tradesense.com"
  SESSION_TIMEOUT: "3600"
  MAX_LOGIN_ATTEMPTS: "5"
  
  # Performance Configuration
  WORKER_PROCESSES: "4"
  WORKER_CONNECTIONS: "1000"
  KEEPALIVE_TIMEOUT: "65"
```

**Secret Management:**

```yaml
# File: /k8s/secrets/production-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-db-credentials
  namespace: tradesense-production
type: Opaque
stringData:
  DATABASE_URL: "postgresql://tradesense_user:${DB_PASSWORD}@postgres-primary.tradesense-production.svc.cluster.local:5432/tradesense_production"
  DB_USERNAME: "tradesense_user"
  DB_PASSWORD: "${DB_PASSWORD}"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-redis-credentials
  namespace: tradesense-production
type: Opaque
stringData:
  REDIS_URL: "redis://:${REDIS_PASSWORD}@redis-cluster.tradesense-production.svc.cluster.local:6379/0"
  REDIS_PASSWORD: "${REDIS_PASSWORD}"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-auth-secrets
  namespace: tradesense-production
type: Opaque
stringData:
  JWT_SECRET_KEY: "${JWT_SECRET_KEY}"
  JWT_ALGORITHM: "HS256"
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  JWT_REFRESH_TOKEN_EXPIRE_DAYS: "30"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-external-api-keys
  namespace: tradesense-production
type: Opaque
stringData:
  ALPACA_API_KEY: "${ALPACA_API_KEY}"
  ALPACA_SECRET_KEY: "${ALPACA_SECRET_KEY}"
  POLYGON_API_KEY: "${POLYGON_API_KEY}"
  FINNHUB_API_KEY: "${FINNHUB_API_KEY}"
  SENDGRID_API_KEY: "${SENDGRID_API_KEY}"
  STRIPE_SECRET_KEY: "${STRIPE_SECRET_KEY}"
  STRIPE_WEBHOOK_SECRET: "${STRIPE_WEBHOOK_SECRET}"
---
apiVersion: v1
kind: Secret
metadata:
  name: tradesense-monitoring-secrets
  namespace: tradesense-production
type: Opaque
stringData:
  SENTRY_DSN: "${SENTRY_DSN}"
  DATADOG_API_KEY: "${DATADOG_API_KEY}"
  NEW_RELIC_LICENSE_KEY: "${NEW_RELIC_LICENSE_KEY}"
```

#### **5C.2.2 Service Account and RBAC Configuration**

**Service Account with Precise RBAC:**

```yaml
# File: /k8s/rbac/service-accounts.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tradesense-api-gateway
  namespace: tradesense-production
  labels:
    app.kubernetes.io/name: tradesense
    app.kubernetes.io/component: api-gateway
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tradesense-api-gateway-role
  namespace: tradesense-production
rules:
# ConfigMap access for runtime configuration
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
# Secret access for credentials
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
# Pod access for service discovery
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
# Service access for internal communication
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
# Events for debugging
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tradesense-api-gateway-binding
  namespace: tradesense-production
subjects:
- kind: ServiceAccount
  name: tradesense-api-gateway
  namespace: tradesense-production
roleRef:
  kind: Role
  name: tradesense-api-gateway-role
  apiGroup: rbac.authorization.k8s.io
```

### **5C.3 DEPLOYMENT STRATEGIES AND ROLLBACK MECHANISMS**

#### **5C.3.1 Advanced Deployment Patterns**

**Blue-Green Deployment Implementation:**

```yaml
# File: /k8s/deployments/blue-green-strategy.yaml
# Blue Environment (Current Production)
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: tradesense-api-gateway
  namespace: tradesense-production
spec:
  replicas: 5
  strategy:
    blueGreen:
      # Reference to service that the rollout modifies as the active service
      activeService: tradesense-api-gateway-active
      # Reference to service that the rollout modifies as the preview service
      previewService: tradesense-api-gateway-preview
      # Pre-promotion analysis
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: tradesense-api-gateway-preview.tradesense-production.svc.cluster.local
      # Post-promotion analysis
      postPromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: tradesense-api-gateway-active.tradesense-production.svc.cluster.local
      # Auto-promotion settings
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      previewReplicaCount: 1
  selector:
    matchLabels:
      app: tradesense-api-gateway
  template:
    metadata:
      labels:
        app: tradesense-api-gateway
    spec:
      containers:
      - name: api-gateway
        image: tradesense/api-gateway:v2.7.0
        ports:
        - containerPort: 8000
          name: http
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
---
# Active service (production traffic)
apiVersion: v1
kind: Service
metadata:
  name: tradesense-api-gateway-active
  namespace: tradesense-production
spec:
  selector:
    app: tradesense-api-gateway
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
---
# Preview service (testing traffic)
apiVersion: v1
kind: Service
metadata:
  name: tradesense-api-gateway-preview
  namespace: tradesense-production
spec:
  selector:
    app: tradesense-api-gateway
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
---
# Analysis template for deployment validation
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
  namespace: tradesense-production
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 2m
    count: 5
    # Success rate threshold must be > 95%
    successCondition: result[0] >= 0.95
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status!~"5.."}[2m])) / 
          sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
  - name: avg-response-time
    interval: 2m
    count: 5
    # Average response time must be < 500ms
    successCondition: result[0] < 0.5
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          histogram_quantile(0.50, 
          sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}"}[2m])) by (le))
```

**Canary Deployment Configuration:**

```yaml
# File: /k8s/deployments/canary-strategy.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: tradesense-trading-service
  namespace: tradesense-production
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      # Deploy canary with 10% traffic
      - setWeight: 10
      # Pause for manual verification
      - pause: 
          duration: 2m
      # Increase to 25% traffic
      - setWeight: 25
      # Run analysis for 5 minutes
      - analysis:
          templates:
          - templateName: canary-analysis
          args:
          - name: service-name
            value: tradesense-trading-service
          - name: canary-hash
            valueFrom:
              podTemplateHashValue: Latest
      # Increase to 50% traffic
      - setWeight: 50
      - pause: 
          duration: 5m
      # Increase to 75% traffic
      - setWeight: 75
      - pause: 
          duration: 5m
      # Full rollout
      - setWeight: 100
      # Traffic routing configuration
      trafficRouting:
        nginx:
          stableIngress: tradesense-trading-service-stable
          annotationPrefix: nginx.ingress.kubernetes.io
          additionalIngressAnnotations:
            canary-by-header: "x-canary"
            canary-by-header-value: "tradesense-canary"
  selector:
    matchLabels:
      app: tradesense-trading-service
  template:
    metadata:
      labels:
        app: tradesense-trading-service
    spec:
      containers:
      - name: trading-service
        image: tradesense/trading-service:latest
        env:
        - name: CANARY_DEPLOYMENT
          value: "true"
        - name: FEATURE_FLAGS_ENDPOINT
          value: "http://feature-flags.tradesense-production.svc.cluster.local:8080"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: canary-analysis
  namespace: tradesense-production
spec:
  args:
  - name: service-name
  - name: canary-hash
  metrics:
  # Error rate comparison between canary and stable
  - name: error-rate-comparison
    interval: 2m
    count: 10
    successCondition: result < 0.02  # Less than 2% error rate
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status=~"5..",revision="{{args.canary-hash}}"}[2m])) / 
          sum(rate(http_requests_total{service="{{args.service-name}}",revision="{{args.canary-hash}}"}[2m]))
  # Response time comparison
  - name: response-time-p99
    interval: 2m
    count: 10
    successCondition: result < 1.0  # Less than 1 second p99
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          histogram_quantile(0.99, 
          sum(rate(http_request_duration_seconds_bucket{service="{{args.service-name}}",revision="{{args.canary-hash}}"}[2m])) by (le))
  # Trading-specific metrics
  - name: order-success-rate
    interval: 1m
    count: 15
    successCondition: result > 0.98  # Greater than 98% success rate
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.tradesense-monitoring.svc.cluster.local:9090
        query: |
          sum(rate(trading_orders_total{status="success",revision="{{args.canary-hash}}"}[1m])) / 
          sum(rate(trading_orders_total{revision="{{args.canary-hash}}"}[1m]))
```

#### **5C.3.2 Automated Rollback Mechanisms**

**Rollback Automation Script:**

```python
# File: /scripts/deployment/automated_rollback.py
"""
Automated rollback system for TradeSense deployments

This script monitors deployment health and automatically triggers rollbacks
when critical thresholds are exceeded.

Key Features:
- Real-time metrics monitoring
- Multi-stage rollback validation
- Automated notification system
- Rollback impact assessment
- Recovery verification
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import kubernetes
from prometheus_client.parser import text_string_to_metric_families

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collect metrics from various sources for rollback decisions"""
    
    def __init__(self, prometheus_url: str, namespace: str):
        self.prometheus_url = prometheus_url
        self.namespace = namespace
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_error_rate(self, service_name: str, time_window: str = "5m") -> float:
        """Get error rate for a service"""
        query = f"""
        sum(rate(http_requests_total{{service="{service_name}",status=~"5.."}}[{time_window}])) / 
        sum(rate(http_requests_total{{service="{service_name}"}}[{time_window}]))
        """
        
        try:
            async with self.session.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            ) as response:
                data = await response.json()
                result = data.get("data", {}).get("result", [])
                
                if result:
                    return float(result[0]["value"][1])
                return 0.0
                
        except Exception as e:
            logger.error(f"Error fetching error rate: {e}")
            return 0.0
    
    async def get_response_time_p99(self, service_name: str, time_window: str = "5m") -> float:
        """Get 99th percentile response time"""
        query = f"""
        histogram_quantile(0.99, 
        sum(rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[{time_window}])) by (le))
        """
        
        try:
            async with self.session.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query}
            ) as response:
                data = await response.json()
                result = data.get("data", {}).get("result", [])
                
                if result:
                    return float(result[0]["value"][1])
                return 0.0
                
        except Exception as e:
            logger.error(f"Error fetching response time: {e}")
            return 0.0
    
    async def get_trading_metrics(self, service_name: str) -> Dict[str, float]:
        """Get trading-specific metrics"""
        metrics = {}
        
        # Order success rate
        order_success_query = f"""
        sum(rate(trading_orders_total{{status="success"}}[2m])) / 
        sum(rate(trading_orders_total[2m]))
        """
        
        # Position update latency
        position_latency_query = f"""
        histogram_quantile(0.95, 
        sum(rate(position_update_duration_seconds_bucket[2m])) by (le))
        """
        
        # Risk check failures
        risk_failures_query = f"""
        sum(rate(risk_check_failures_total[5m]))
        """
        
        queries = {
            "order_success_rate": order_success_query,
            "position_latency_p95": position_latency_query,
            "risk_failures_rate": risk_failures_query
        }
        
        for metric_name, query in queries.items():
            try:
                async with self.session.get(
                    f"{self.prometheus_url}/api/v1/query",
                    params={"query": query}
                ) as response:
                    data = await response.json()
                    result = data.get("data", {}).get("result", [])
                    
                    if result:
                        metrics[metric_name] = float(result[0]["value"][1])
                    else:
                        metrics[metric_name] = 0.0
                        
            except Exception as e:
                logger.error(f"Error fetching {metric_name}: {e}")
                metrics[metric_name] = 0.0
        
        return metrics

class KubernetesManager:
    """Manage Kubernetes resources for rollback operations"""
    
    def __init__(self, namespace: str):
        self.namespace = namespace
        kubernetes.config.load_incluster_config()
        self.apps_v1 = kubernetes.client.AppsV1Api()
        self.core_v1 = kubernetes.client.CoreV1Api()
        self.custom_objects = kubernetes.client.CustomObjectsApi()
    
    async def get_rollout_status(self, rollout_name: str) -> Dict:
        """Get Argo Rollout status"""
        try:
            rollout = self.custom_objects.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="rollouts",
                name=rollout_name
            )
            return rollout.get("status", {})
        except Exception as e:
            logger.error(f"Error getting rollout status: {e}")
            return {}
    
    async def trigger_rollback(self, rollout_name: str) -> bool:
        """Trigger rollback of a deployment"""
        try:
            # Patch the rollout to trigger rollback
            patch = {
                "spec": {
                    "restartAt": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            self.custom_objects.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="rollouts",
                name=rollout_name,
                body=patch
            )
            
            logger.info(f"Triggered rollback for {rollout_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error triggering rollback: {e}")
            return False
    
    async def abort_rollout(self, rollout_name: str) -> bool:
        """Abort current rollout"""
        try:
            # Set weight to 0 to stop traffic to canary
            patch = {
                "status": {
                    "abort": True
                }
            }
            
            self.custom_objects.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="rollouts",
                name=rollout_name,
                body=patch
            )
            
            logger.info(f"Aborted rollout for {rollout_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error aborting rollout: {e}")
            return False

class RollbackDecisionEngine:
    """Decision engine for automatic rollback triggers"""
    
    def __init__(self):
        self.thresholds = {
            "error_rate_critical": 0.05,      # 5% error rate
            "error_rate_warning": 0.02,       # 2% error rate
            "response_time_critical": 5.0,    # 5 seconds p99
            "response_time_warning": 2.0,     # 2 seconds p99
            "order_success_rate_min": 0.95,   # 95% minimum success rate
            "position_latency_max": 1.0,      # 1 second max latency
            "risk_failures_max": 10,          # Max 10 risk failures per minute
        }
        
        self.violation_counts = {}
        self.max_violations = 3  # Trigger rollback after 3 consecutive violations
    
    def should_rollback(self, metrics: Dict[str, float], service_name: str) -> Dict[str, any]:
        """Determine if rollback should be triggered"""
        violations = []
        current_time = datetime.utcnow()
        
        # Check error rate
        error_rate = metrics.get("error_rate", 0.0)
        if error_rate > self.thresholds["error_rate_critical"]:
            violations.append({
                "metric": "error_rate",
                "value": error_rate,
                "threshold": self.thresholds["error_rate_critical"],
                "severity": "critical"
            })
        
        # Check response time
        response_time = metrics.get("response_time_p99", 0.0)
        if response_time > self.thresholds["response_time_critical"]:
            violations.append({
                "metric": "response_time_p99",
                "value": response_time,
                "threshold": self.thresholds["response_time_critical"],
                "severity": "critical"
            })
        
        # Check trading metrics
        trading_metrics = metrics.get("trading_metrics", {})
        
        order_success_rate = trading_metrics.get("order_success_rate", 1.0)
        if order_success_rate < self.thresholds["order_success_rate_min"]:
            violations.append({
                "metric": "order_success_rate",
                "value": order_success_rate,
                "threshold": self.thresholds["order_success_rate_min"],
                "severity": "critical"
            })
        
        position_latency = trading_metrics.get("position_latency_p95", 0.0)
        if position_latency > self.thresholds["position_latency_max"]:
            violations.append({
                "metric": "position_latency_p95",
                "value": position_latency,
                "threshold": self.thresholds["position_latency_max"],
                "severity": "warning"
            })
        
        # Count violations
        if violations:
            violation_key = f"{service_name}:{current_time.strftime('%Y-%m-%d-%H-%M')}"
            self.violation_counts[violation_key] = self.violation_counts.get(violation_key, 0) + 1
            
            # Clean old violation counts (older than 10 minutes)
            cutoff_time = current_time - timedelta(minutes=10)
            cutoff_str = cutoff_time.strftime('%Y-%m-%d-%H-%M')
            self.violation_counts = {
                k: v for k, v in self.violation_counts.items()
                if k.split(':')[1] >= cutoff_str
            }
            
            # Check if we should trigger rollback
            consecutive_violations = self.violation_counts.get(violation_key, 0)
            should_rollback = consecutive_violations >= self.max_violations
            
            return {
                "should_rollback": should_rollback,
                "violations": violations,
                "consecutive_violations": consecutive_violations,
                "timestamp": current_time.isoformat()
            }
        
        return {
            "should_rollback": False,
            "violations": [],
            "consecutive_violations": 0,
            "timestamp": current_time.isoformat()
        }

class AutomatedRollbackSystem:
    """Main rollback automation system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.prometheus_url = config["prometheus_url"]
        self.namespace = config["namespace"]
        self.services = config["services"]
        
        self.k8s_manager = KubernetesManager(self.namespace)
        self.decision_engine = RollbackDecisionEngine()
        
        # Notification configuration
        self.notification_webhook = config.get("notification_webhook")
        self.slack_webhook = config.get("slack_webhook")
    
    async def monitor_deployments(self):
        """Main monitoring loop"""
        logger.info("Starting automated rollback monitoring...")
        
        async with MetricsCollector(self.prometheus_url, self.namespace) as collector:
            while True:
                try:
                    for service_config in self.services:
                        await self._monitor_service(collector, service_config)
                    
                    # Wait before next check
                    await asyncio.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
    
    async def _monitor_service(self, collector: MetricsCollector, service_config: Dict):
        """Monitor a specific service"""
        service_name = service_config["name"]
        rollout_name = service_config["rollout_name"]
        
        logger.info(f"Monitoring service: {service_name}")
        
        # Collect metrics
        metrics = {}
        metrics["error_rate"] = await collector.get_error_rate(service_name)
        metrics["response_time_p99"] = await collector.get_response_time_p99(service_name)
        
        # Collect trading-specific metrics if it's a trading service
        if service_config.get("is_trading_service", False):
            metrics["trading_metrics"] = await collector.get_trading_metrics(service_name)
        
        # Make rollback decision
        decision = self.decision_engine.should_rollback(metrics, service_name)
        
        if decision["should_rollback"]:
            logger.warning(f"Triggering rollback for {service_name} due to violations: {decision['violations']}")
            
            # Get rollout status
            rollout_status = await self.k8s_manager.get_rollout_status(rollout_name)
            
            # Execute rollback
            if rollout_status.get("currentPodHash") != rollout_status.get("stableRS"):
                # Canary is active, abort it
                success = await self.k8s_manager.abort_rollout(rollout_name)
            else:
                # Trigger full rollback
                success = await self.k8s_manager.trigger_rollback(rollout_name)
            
            if success:
                await self._send_rollback_notification(service_name, decision, metrics)
            else:
                logger.error(f"Failed to execute rollback for {service_name}")
                await self._send_error_notification(service_name, "Rollback execution failed")
        
        elif decision["violations"]:
            logger.warning(f"Violations detected for {service_name}: {decision['violations']}")
            await self._send_warning_notification(service_name, decision, metrics)
    
    async def _send_rollback_notification(self, service_name: str, decision: Dict, metrics: Dict):
        """Send rollback notification"""
        message = {
            "service": service_name,
            "action": "rollback_triggered",
            "violations": decision["violations"],
            "metrics": metrics,
            "timestamp": decision["timestamp"]
        }
        
        await self._send_notification("🚨 ROLLBACK TRIGGERED", message)
    
    async def _send_warning_notification(self, service_name: str, decision: Dict, metrics: Dict):
        """Send warning notification"""
        message = {
            "service": service_name,
            "action": "warning",
            "violations": decision["violations"],
            "consecutive_violations": decision["consecutive_violations"],
            "metrics": metrics,
            "timestamp": decision["timestamp"]
        }
        
        await self._send_notification("⚠️ DEPLOYMENT WARNING", message)
    
    async def _send_error_notification(self, service_name: str, error_message: str):
        """Send error notification"""
        message = {
            "service": service_name,
            "action": "error",
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_notification("❌ ROLLBACK ERROR", message)
    
    async def _send_notification(self, title: str, message: Dict):
        """Send notification to configured channels"""
        try:
            # Send to Slack if configured
            if self.slack_webhook:
                async with aiohttp.ClientSession() as session:
                    slack_payload = {
                        "text": title,
                        "attachments": [{
                            "color": "danger" if "ROLLBACK" in title else "warning",
                            "fields": [
                                {"title": "Service", "value": message["service"], "short": True},
                                {"title": "Action", "value": message["action"], "short": True},
                                {"title": "Timestamp", "value": message["timestamp"], "short": True}
                            ]
                        }]
                    }
                    
                    async with session.post(self.slack_webhook, json=slack_payload) as response:
                        if response.status == 200:
                            logger.info(f"Sent Slack notification: {title}")
                        else:
                            logger.error(f"Failed to send Slack notification: {response.status}")
            
            # Send to general webhook if configured
            if self.notification_webhook:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.notification_webhook, json=message) as response:
                        if response.status == 200:
                            logger.info(f"Sent webhook notification: {title}")
                        else:
                            logger.error(f"Failed to send webhook notification: {response.status}")
                            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

async def main():
    """Main function"""
    config = {
        "prometheus_url": "http://prometheus.tradesense-monitoring.svc.cluster.local:9090",
        "namespace": "tradesense-production",
        "notification_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
        "services": [
            {
                "name": "tradesense-api-gateway",
                "rollout_name": "tradesense-api-gateway",
                "is_trading_service": False
            },
            {
                "name": "tradesense-trading-service",
                "rollout_name": "tradesense-trading-service",
                "is_trading_service": True
            },
            {
                "name": "tradesense-user-service",
                "rollout_name": "tradesense-user-service",
                "is_trading_service": False
            }
        ]
    }
    
    rollback_system = AutomatedRollbackSystem(config)
    await rollback_system.monitor_deployments()

if __name__ == "__main__":
    asyncio.run(main())
```

<function_calls>
<invoke name="TodoWrite">
