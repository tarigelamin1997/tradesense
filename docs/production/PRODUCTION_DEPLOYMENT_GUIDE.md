# TradeSense Production Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Deployment Process](#deployment-process)
5. [Configuration](#configuration)
6. [Security](#security)
7. [Monitoring](#monitoring)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)

## Overview

This guide provides comprehensive instructions for deploying TradeSense to production environments. TradeSense is a trading analytics SaaS platform built with:

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: SvelteKit
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Container Orchestration**: Kubernetes / Docker Swarm
- **CI/CD**: GitHub Actions

## Prerequisites

### Required Tools
- Docker 20.10+
- Kubernetes 1.28+ (or Docker Swarm)
- kubectl
- Helm 3+
- AWS CLI (for S3 backups)
- SSL certificates

### Access Requirements
- Container registry access
- Kubernetes cluster access
- Domain control for DNS
- SSL certificate authority
- Monitoring services (Prometheus, Grafana)

## Infrastructure Setup

### 1. Kubernetes Cluster

#### Option A: AWS EKS
```bash
# Create EKS cluster
eksctl create cluster \
  --name tradesense-prod \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

#### Option B: Digital Ocean Kubernetes
```bash
doctl kubernetes cluster create tradesense-prod \
  --region nyc1 \
  --size s-2vcpu-4gb \
  --count 3 \
  --auto-upgrade \
  --maintenance-window "saturday=02:00"
```

### 2. Install Required Components

```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install Prometheus and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack
```

### 3. Create Namespaces

```bash
kubectl create namespace tradesense
kubectl create namespace monitoring
kubectl create namespace cert-manager
```

## Deployment Process

### 1. Pre-deployment Checklist

- [ ] All tests passing in CI/CD
- [ ] Database migrations prepared
- [ ] Secrets configured in Kubernetes
- [ ] SSL certificates ready
- [ ] Backup of current production data
- [ ] Monitoring alerts configured
- [ ] Team notified of deployment window

### 2. Configure Secrets

```bash
# Create database credentials
kubectl create secret generic postgres-credentials \
  --from-literal=username=tradesense \
  --from-literal=password='<secure-password>' \
  -n tradesense

# Create application secrets
kubectl create secret generic tradesense-secrets \
  --from-literal=JWT_SECRET_KEY='<jwt-secret>' \
  --from-literal=STRIPE_API_KEY='<stripe-key>' \
  --from-literal=STRIPE_WEBHOOK_SECRET='<webhook-secret>' \
  --from-literal=SENTRY_DSN='<sentry-dsn>' \
  -n tradesense

# Create AWS credentials for backups
kubectl create secret generic aws-credentials \
  --from-literal=access-key-id='<aws-access-key>' \
  --from-literal=secret-access-key='<aws-secret-key>' \
  -n tradesense
```

### 3. Deploy Database

```bash
# Deploy PostgreSQL
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n tradesense --timeout=300s

# Run database migrations
kubectl exec -it deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense -f /migrations/init.sql
```

### 4. Deploy Redis

```bash
kubectl apply -f k8s/redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n tradesense --timeout=120s
```

### 5. Deploy Application

```bash
# Deploy backend
kubectl apply -f k8s/backend.yaml

# Deploy frontend
kubectl apply -f k8s/frontend.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml

# Apply autoscaling
kubectl apply -f k8s/hpa.yaml
```

### 6. Verify Deployment

```bash
# Check pod status
kubectl get pods -n tradesense

# Check services
kubectl get svc -n tradesense

# Check ingress
kubectl get ingress -n tradesense

# Test health endpoints
curl https://tradesense.com/api/v1/monitoring/health
curl https://tradesense.com/health
```

## Configuration

### Environment Variables

#### Backend Configuration
```yaml
DATABASE_URL: postgresql://user:pass@postgres:5432/tradesense
REDIS_URL: redis://redis:6379/0
JWT_SECRET_KEY: <32+ character secret>
ENVIRONMENT: production
LOG_LEVEL: INFO
CORS_ORIGINS: https://tradesense.com,https://www.tradesense.com
SENTRY_DSN: <sentry-dsn>
STRIPE_API_KEY: <stripe-key>
```

#### Frontend Configuration
```yaml
NODE_ENV: production
VITE_API_BASE_URL: https://api.tradesense.com
PUBLIC_STRIPE_KEY: <stripe-public-key>
```

### Resource Limits

```yaml
# Backend resources
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"

# Frontend resources
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Security

### 1. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-network-policy
  namespace: tradesense
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    - podSelector:
        matchLabels:
          app: nginx
    ports:
    - protocol: TCP
      port: 8000
```

### 2. SSL/TLS Configuration

```yaml
# Certificate configuration
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: tradesense-tls
  namespace: tradesense
spec:
  secretName: tradesense-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - tradesense.com
  - www.tradesense.com
  - api.tradesense.com
```

### 3. Security Headers

Configured in NGINX:
```nginx
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

## Monitoring

### 1. Health Checks

- **Liveness Probe**: `/api/v1/monitoring/health/live`
- **Readiness Probe**: `/api/v1/monitoring/health/ready`
- **Startup Probe**: `/api/v1/monitoring/health/startup`

### 2. Metrics Endpoints

- **Prometheus Metrics**: `/metrics`
- **Custom Metrics**: `/api/v1/monitoring/metrics`

### 3. Alerting Rules

```yaml
groups:
- name: tradesense
  rules:
  - alert: HighErrorRate
    expr: rate(tradesense_http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, tradesense_http_request_duration_seconds) > 0.5
    for: 5m
    annotations:
      summary: "95th percentile response time > 500ms"
```

### 4. Dashboards

Import Grafana dashboards from `/monitoring/grafana/dashboards/`:
- `tradesense-overview.json`
- `tradesense-performance.json`
- `tradesense-business-metrics.json`

## Maintenance

### 1. Automated Backups

Backups run via Kubernetes CronJobs:
- **PostgreSQL**: Daily at 2 AM
- **Redis**: Every 6 hours
- **File uploads**: Daily at 4 AM

### 2. Database Maintenance

```bash
# Vacuum and analyze
kubectl exec -it deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense -c "VACUUM ANALYZE;"

# Reindex
kubectl exec -it deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense -c "REINDEX DATABASE tradesense;"
```

### 3. Log Rotation

Logs are automatically rotated by Kubernetes. For custom logs:
```yaml
# In deployment spec
volumeMounts:
- name: logs
  mountPath: /app/logs
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 15"]
```

## Troubleshooting

### Common Issues

#### 1. Pod CrashLoopBackOff
```bash
# Check logs
kubectl logs -f pod/<pod-name> -n tradesense

# Describe pod
kubectl describe pod/<pod-name> -n tradesense

# Check events
kubectl get events -n tradesense --sort-by='.lastTimestamp'
```

#### 2. Database Connection Issues
```bash
# Test connection from backend pod
kubectl exec -it deployment/backend -n tradesense -- \
  python -c "from core.db.session import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 3. High Memory Usage
```bash
# Check resource usage
kubectl top pods -n tradesense

# Scale horizontally
kubectl scale deployment/backend --replicas=5 -n tradesense
```

### Debug Mode

Enable debug mode temporarily:
```bash
kubectl set env deployment/backend DEBUG=true LOG_LEVEL=DEBUG -n tradesense
```

## Rollback Procedures

### 1. Quick Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/backend -n tradesense
kubectl rollout undo deployment/frontend -n tradesense

# Check rollout status
kubectl rollout status deployment/backend -n tradesense
```

### 2. Database Rollback

```bash
# Restore from backup
kubectl exec -it deployment/postgres -n tradesense -- \
  pg_restore -U tradesense -d tradesense /backups/postgres_20240116_020000.sql.gz
```

### 3. Full Environment Rollback

```bash
# Apply previous configuration
kubectl apply -f k8s/releases/v1.0.0/

# Restore database
./scripts/restore-database.sh /backups/postgres_20240116_020000.sql.gz
```

## Post-Deployment

### 1. Smoke Tests

Run automated smoke tests:
```bash
./scripts/smoke-tests.sh production
```

### 2. Performance Verification

```bash
# Run basic load test
./scripts/run-performance-tests.sh load 5m 50 5
```

### 3. Monitor Key Metrics

- Response times < 200ms (p50)
- Error rate < 0.1%
- CPU usage < 70%
- Memory usage < 80%
- Cache hit rate > 80%

### 4. Update Status Page

Update public status page with deployment completion.

## Emergency Contacts

- **On-call Engineer**: +1-XXX-XXX-XXXX
- **DevOps Lead**: devops@tradesense.com
- **Escalation**: escalation@tradesense.com

## Additional Resources

- [Runbook](./RUNBOOK.md)
- [Disaster Recovery Plan](./DISASTER_RECOVERY.md)
- [Performance Tuning Guide](./PERFORMANCE_TUNING.md)
- [Security Hardening](./SECURITY_HARDENING.md)