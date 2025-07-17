# TradeSense Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying TradeSense to production. Follow these steps carefully to ensure a smooth and successful deployment.

---

## Prerequisites

Before starting the deployment, ensure you have:

1. **Access Requirements**
   - SSH access to production servers
   - AWS console access
   - Database admin credentials
   - Docker registry credentials
   - Domain registrar access
   - SSL certificate management access

2. **Tools Installed**
   - Docker & Docker Compose
   - kubectl (if using Kubernetes)
   - AWS CLI configured
   - PostgreSQL client
   - Redis CLI
   - Git

3. **Configurations Ready**
   - Production environment variables
   - SSL certificates
   - Database connection strings
   - API keys for all services

---

## Step 1: Pre-Deployment Preparation

### 1.1 Run Launch Readiness Check

```bash
./scripts/launch-readiness.sh production
```

Address any failed checks before proceeding.

### 1.2 Backup Current State

```bash
# Backup database
pg_dump -h $PROD_DB_HOST -U $PROD_DB_USER -d tradesense_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup application files
tar -czf tradesense_backup_$(date +%Y%m%d_%H%M%S).tar.gz src/ frontend/

# Backup configurations
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz .env* nginx/ k8s/
```

### 1.3 Notify Team

Send deployment notification to team:
- Deployment window
- Expected duration
- Rollback plan
- Contact person

---

## Step 2: Infrastructure Setup

### 2.1 Database Setup

```bash
# Connect to production database
psql -h $PROD_DB_HOST -U $PROD_DB_USER -d postgres

# Create production database
CREATE DATABASE tradesense_production;

# Create user
CREATE USER tradesense_prod WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE tradesense_production TO tradesense_prod;

# Enable extensions
\c tradesense_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### 2.2 Redis Setup

```bash
# Test Redis connection
redis-cli -h $PROD_REDIS_HOST -a $PROD_REDIS_PASSWORD ping

# Set Redis configuration
redis-cli -h $PROD_REDIS_HOST -a $PROD_REDIS_PASSWORD CONFIG SET maxmemory 2gb
redis-cli -h $PROD_REDIS_HOST -a $PROD_REDIS_PASSWORD CONFIG SET maxmemory-policy allkeys-lru
```

### 2.3 S3 Bucket Setup

```bash
# Create S3 buckets
aws s3 mb s3://tradesense-production-uploads
aws s3 mb s3://tradesense-production-backups

# Set bucket policies
aws s3api put-bucket-versioning --bucket tradesense-production-uploads --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket tradesense-production-uploads --server-side-encryption-configuration file://s3-encryption.json
```

---

## Step 3: Application Deployment

### 3.1 Build and Push Docker Images

```bash
# Build backend image
cd src/backend
docker build -t tradesense-backend:latest -t tradesense-backend:v2.0.0 .
docker tag tradesense-backend:latest your-registry.com/tradesense-backend:latest
docker push your-registry.com/tradesense-backend:latest
docker push your-registry.com/tradesense-backend:v2.0.0

# Build frontend image
cd ../../frontend
docker build -t tradesense-frontend:latest -t tradesense-frontend:v2.0.0 \
  --build-arg VITE_API_BASE_URL=https://api.tradesense.com \
  --build-arg VITE_STRIPE_PUBLISHABLE_KEY=$STRIPE_PUB_KEY \
  --build-arg VITE_SENTRY_DSN=$SENTRY_DSN \
  --build-arg VITE_GA_TRACKING_ID=$GA_ID .
docker tag tradesense-frontend:latest your-registry.com/tradesense-frontend:latest
docker push your-registry.com/tradesense-frontend:latest
docker push your-registry.com/tradesense-frontend:v2.0.0
```

### 3.2 Deploy Backend

```bash
# Run database migrations
docker run --rm \
  -e DATABASE_URL=$PROD_DATABASE_URL \
  your-registry.com/tradesense-backend:v2.0.0 \
  alembic upgrade head

# Deploy backend service
docker-compose -f docker-compose.production.yml up -d backend worker scheduler

# Verify backend is running
curl https://api.tradesense.com/health
```

### 3.3 Deploy Frontend

```bash
# Deploy to S3 and CloudFront
aws s3 sync frontend/dist/ s3://tradesense-frontend-prod/ --delete
aws cloudfront create-invalidation --distribution-id $CF_DISTRIBUTION_ID --paths "/*"

# Or using Docker/Nginx
docker-compose -f docker-compose.production.yml up -d frontend nginx
```

---

## Step 4: Configuration & Verification

### 4.1 Configure DNS

```bash
# Add DNS records (example for Route53)
aws route53 change-resource-record-sets --hosted-zone-id $ZONE_ID --change-batch file://dns-records.json
```

DNS records needed:
- `tradesense.com` → CloudFront/Load Balancer
- `api.tradesense.com` → API Load Balancer
- `www.tradesense.com` → Redirect to apex domain

### 4.2 SSL Certificate Setup

```bash
# Using Let's Encrypt
certbot certonly --nginx -d tradesense.com -d www.tradesense.com -d api.tradesense.com

# Or using AWS Certificate Manager
aws acm request-certificate --domain-name tradesense.com --subject-alternative-names "*.tradesense.com" --validation-method DNS
```

### 4.3 Verify Services

```bash
# Run health checks
./scripts/health-check.sh production

# Test critical endpoints
curl https://api.tradesense.com/api/v1/health
curl https://api.tradesense.com/docs
curl https://tradesense.com

# Test authentication flow
curl -X POST https://api.tradesense.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'
```

---

## Step 5: Monitoring Setup

### 5.1 Deploy Monitoring Stack

```bash
# Deploy monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify monitoring
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
curl http://localhost:9093  # Alertmanager
```

### 5.2 Configure Alerts

```bash
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# Test alert routing
amtool alert add alertname=test severity=critical -a alertmanager:9093
```

---

## Step 6: Final Steps

### 6.1 Load Testing

```bash
# Run load test (using k6)
k6 run tests/load/production.js

# Monitor during load test
watch -n 1 'curl -s https://api.tradesense.com/metrics | grep http_requests'
```

### 6.2 Security Scan

```bash
# Run security scan
docker run --rm -v $(pwd):/zap/wrk/:rw \
  -t owasp/zap2docker-stable zap-baseline.py \
  -t https://tradesense.com -r security-report.html

# Check for vulnerabilities
trivy image your-registry.com/tradesense-backend:v2.0.0
trivy image your-registry.com/tradesense-frontend:v2.0.0
```

### 6.3 Enable Production Mode

```bash
# Set production flags
export NODE_ENV=production
export APP_ENV=production

# Restart services
docker-compose -f docker-compose.production.yml restart

# Verify production mode
curl https://api.tradesense.com/api/v1/config | jq .environment
```

---

## Step 7: Post-Deployment

### 7.1 Smoke Tests

Run the full test suite:

```bash
# API tests
pytest tests/integration/test_production.py -v

# Frontend tests
npm run test:e2e:production

# Payment flow test
./scripts/test-payment-flow.sh production
```

### 7.2 Monitor Metrics

Watch key metrics for the first hour:
- Response times
- Error rates
- Database connections
- Memory usage
- CPU usage
- Active users

### 7.3 Update Status Page

```bash
# Update status page
curl -X POST https://status.tradesense.com/api/v1/incidents \
  -H "Authorization: Bearer $STATUS_PAGE_TOKEN" \
  -d '{"name":"Deployment Complete","status":"resolved","message":"TradeSense v2.0.0 is now live!"}'
```

---

## Rollback Procedure

If issues arise, follow this rollback procedure:

### Immediate Rollback (< 5 minutes)

```bash
# Rollback containers to previous version
docker-compose -f docker-compose.production.yml up -d \
  --scale backend=0 \
  --scale frontend=0

docker run -d --name backend-rollback your-registry.com/tradesense-backend:v1.9.0
docker run -d --name frontend-rollback your-registry.com/tradesense-frontend:v1.9.0

# Rollback database if needed
psql $PROD_DATABASE_URL < backup_latest.sql
```

### Full Rollback

```bash
# Run rollback script
./scripts/rollback.sh production v1.9.0

# Verify rollback
./scripts/health-check.sh production

# Clear caches
redis-cli -h $PROD_REDIS_HOST FLUSHALL
aws cloudfront create-invalidation --distribution-id $CF_DISTRIBUTION_ID --paths "/*"
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check connectivity
   pg_isready -h $PROD_DB_HOST -p 5432
   
   # Check credentials
   psql -h $PROD_DB_HOST -U $PROD_DB_USER -d tradesense_production -c "SELECT 1"
   ```

2. **Redis Connection Failed**
   ```bash
   # Test connection
   redis-cli -h $PROD_REDIS_HOST -a $PROD_REDIS_PASSWORD ping
   
   # Check memory usage
   redis-cli -h $PROD_REDIS_HOST -a $PROD_REDIS_PASSWORD INFO memory
   ```

3. **High Error Rate**
   ```bash
   # Check logs
   docker logs tradesense-backend --tail 100
   
   # Check metrics
   curl https://api.tradesense.com/metrics | grep error_rate
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate
   echo | openssl s_client -connect api.tradesense.com:443 2>/dev/null | openssl x509 -noout -dates
   
   # Renew if needed
   certbot renew --nginx
   ```

---

## Contact Information

For deployment issues, contact:

- **Primary**: DevOps Lead - devops@tradesense.com
- **Secondary**: Tech Lead - tech@tradesense.com
- **Emergency**: On-call Engineer - +1-XXX-XXX-XXXX

---

## Deployment Checklist Summary

- [ ] Pre-deployment checks passed
- [ ] Backups completed
- [ ] Database migrations successful
- [ ] Docker images built and pushed
- [ ] Services deployed and healthy
- [ ] SSL certificates valid
- [ ] DNS configured correctly
- [ ] Monitoring active
- [ ] Smoke tests passed
- [ ] Team notified of completion

---

**Remember**: Take your time, double-check everything, and don't hesitate to rollback if something seems wrong. A successful deployment is better than a fast deployment!