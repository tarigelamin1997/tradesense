# TradeSense Production Runbook

## Table of Contents
1. [Service Overview](#service-overview)
2. [Architecture](#architecture)
3. [Common Operations](#common-operations)
4. [Incident Response](#incident-response)
5. [Performance Issues](#performance-issues)
6. [Database Operations](#database-operations)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Emergency Procedures](#emergency-procedures)

## Service Overview

### Components
- **Backend API**: FastAPI application (Python 3.11)
- **Frontend**: SvelteKit application
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Queue**: Redis-based task queue
- **Search**: PostgreSQL full-text search

### Key URLs
- Production: https://tradesense.com
- API: https://api.tradesense.com
- Monitoring: https://monitoring.tradesense.com
- Status Page: https://status.tradesense.com

### SLOs (Service Level Objectives)
- Uptime: 99.9% (43.2 minutes downtime/month)
- API Response Time: p95 < 500ms
- Error Rate: < 0.1%
- Database Query Time: p95 < 100ms

## Architecture

### Request Flow
```
User → CloudFlare → Load Balancer → NGINX → Backend → Database/Cache
                                    ↓
                                Frontend ← Static Assets (CDN)
```

### Service Dependencies
```
Backend → PostgreSQL (primary data)
        → Redis (caching, sessions)
        → Stripe API (payments)
        → SendGrid (emails)
        → Sentry (error tracking)

Frontend → Backend API
         → Stripe.js
         → Google Analytics
```

## Common Operations

### 1. Health Checks

```bash
# Check all services
curl https://api.tradesense.com/api/v1/monitoring/health

# Detailed health check
curl https://api.tradesense.com/api/v1/monitoring/health/detailed

# Component checks
kubectl get pods -n tradesense
kubectl top pods -n tradesense
```

### 2. Scaling Operations

#### Horizontal Scaling
```bash
# Scale backend
kubectl scale deployment/backend --replicas=5 -n tradesense

# Scale frontend
kubectl scale deployment/frontend --replicas=3 -n tradesense

# Auto-scale based on CPU
kubectl autoscale deployment/backend --min=3 --max=10 --cpu-percent=70 -n tradesense
```

#### Vertical Scaling
```bash
# Update resource limits
kubectl set resources deployment/backend -n tradesense \
  --requests=memory=1Gi,cpu=1000m \
  --limits=memory=2Gi,cpu=2000m
```

### 3. Deployment Operations

#### Rolling Update
```bash
# Update backend image
kubectl set image deployment/backend backend=tradesense/backend:v2.0.1 -n tradesense

# Monitor rollout
kubectl rollout status deployment/backend -n tradesense

# Rollback if needed
kubectl rollout undo deployment/backend -n tradesense
```

#### Blue-Green Deployment
```bash
# Deploy green version
kubectl apply -f k8s/backend-green.yaml

# Test green version
curl https://api-green.tradesense.com/health

# Switch traffic
kubectl patch service backend-service -n tradesense \
  -p '{"spec":{"selector":{"version":"green"}}}'
```

### 4. Cache Operations

```bash
# Connect to Redis
kubectl exec -it deployment/redis -n tradesense -- redis-cli

# Clear all cache
> FLUSHALL

# Clear specific pattern
> EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "cache:analytics:*"

# Monitor cache hit rate
> INFO stats
```

### 5. Log Analysis

```bash
# View backend logs
kubectl logs -f deployment/backend -n tradesense

# View logs with timestamps
kubectl logs --timestamps deployment/backend -n tradesense

# Search for errors
kubectl logs deployment/backend -n tradesense | grep ERROR

# Export logs for analysis
kubectl logs deployment/backend -n tradesense > backend-logs-$(date +%Y%m%d).log
```

## Incident Response

### Severity Levels

| Level | Response Time | Example |
|-------|--------------|---------|
| P1 - Critical | 15 min | Site down, data loss |
| P2 - High | 1 hour | Payment failure, login issues |
| P3 - Medium | 4 hours | Slow performance, UI bugs |
| P4 - Low | 24 hours | Minor bugs, feature requests |

### P1 - Site Down

1. **Verify the issue**
   ```bash
   # Check external monitoring
   curl -I https://tradesense.com
   
   # Check from multiple locations
   for region in us-east eu-west asia; do
     curl -w "%{http_code} - %{time_total}s\n" -o /dev/null -s https://tradesense.com
   done
   ```

2. **Check infrastructure**
   ```bash
   # Kubernetes cluster
   kubectl get nodes
   kubectl get pods -n tradesense
   
   # Database
   kubectl exec -it deployment/postgres -n tradesense -- pg_isready
   ```

3. **Emergency restart**
   ```bash
   # Restart all services
   kubectl rollout restart deployment -n tradesense
   ```

4. **Failover (if needed)**
   ```bash
   # Switch to DR site
   kubectl config use-context tradesense-dr
   kubectl apply -f k8s/dr-activate.yaml
   ```

### P2 - Authentication Issues

1. **Check auth service**
   ```bash
   # Test login endpoint
   curl -X POST https://api.tradesense.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'
   
   # Check JWT signing key
   kubectl get secret tradesense-secrets -n tradesense -o yaml
   ```

2. **Check Redis sessions**
   ```bash
   kubectl exec -it deployment/redis -n tradesense -- redis-cli
   > KEYS "session:*"
   > TTL "session:user123"
   ```

3. **Reset user session**
   ```python
   # Connect to backend pod
   kubectl exec -it deployment/backend -n tradesense -- python
   
   from core.cache import redis_client
   redis_client.delete("session:user123")
   ```

### P3 - Performance Degradation

1. **Identify bottleneck**
   ```bash
   # Check response times
   curl -w "@curl-format.txt" -o /dev/null -s https://api.tradesense.com/api/v1/analytics/dashboard
   
   # Database slow queries
   kubectl exec -it deployment/postgres -n tradesense -- psql -U tradesense -c \
     "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
   ```

2. **Check resource usage**
   ```bash
   # Pod resources
   kubectl top pods -n tradesense
   
   # Node resources
   kubectl top nodes
   ```

3. **Quick fixes**
   ```bash
   # Increase replicas
   kubectl scale deployment/backend --replicas=10 -n tradesense
   
   # Clear cache
   kubectl exec -it deployment/redis -n tradesense -- redis-cli FLUSHALL
   ```

## Performance Issues

### High CPU Usage

1. **Identify the cause**
   ```bash
   # Check which pods
   kubectl top pods -n tradesense --sort-by=cpu
   
   # Profile the application
   kubectl exec -it deployment/backend -n tradesense -- py-spy top --pid 1
   ```

2. **Mitigation**
   ```bash
   # Scale horizontally
   kubectl scale deployment/backend --replicas=8 -n tradesense
   
   # Reduce worker threads
   kubectl set env deployment/backend WORKERS=2 -n tradesense
   ```

### High Memory Usage

1. **Check memory leaks**
   ```bash
   # Monitor memory growth
   kubectl exec -it deployment/backend -n tradesense -- ps aux
   
   # Check for large objects in Redis
   kubectl exec -it deployment/redis -n tradesense -- redis-cli --bigkeys
   ```

2. **Fix memory issues**
   ```bash
   # Restart pods with memory leaks
   kubectl delete pod -l app=backend -n tradesense
   
   # Adjust memory limits
   kubectl set resources deployment/backend -n tradesense --limits=memory=4Gi
   ```

### Slow Database Queries

1. **Identify slow queries**
   ```sql
   -- Connect to database
   kubectl exec -it deployment/postgres -n tradesense -- psql -U tradesense
   
   -- Enable query logging
   ALTER SYSTEM SET log_min_duration_statement = 100;
   SELECT pg_reload_conf();
   
   -- Check slow queries
   SELECT query, calls, mean_exec_time, total_exec_time
   FROM pg_stat_statements
   WHERE mean_exec_time > 100
   ORDER BY mean_exec_time DESC
   LIMIT 20;
   ```

2. **Optimize queries**
   ```sql
   -- Update statistics
   ANALYZE;
   
   -- Check missing indexes
   SELECT schemaname, tablename, attname, n_distinct, correlation
   FROM pg_stats
   WHERE schemaname = 'public'
   AND n_distinct > 100
   AND correlation < 0.1
   ORDER BY n_distinct DESC;
   
   -- Create index
   CREATE INDEX CONCURRENTLY idx_trades_user_date 
   ON trades(user_id, entry_date) 
   WHERE deleted_at IS NULL;
   ```

## Database Operations

### Backup Operations

```bash
# Manual backup
kubectl exec -it deployment/postgres -n tradesense -- \
  pg_dump -U tradesense -d tradesense | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Verify backup
gunzip -c backup_*.sql.gz | head -100

# List automated backups
kubectl get cronjobs -n tradesense
kubectl logs -l job-name=postgres-backup -n tradesense
```

### Restore Operations

```bash
# Stop application traffic
kubectl scale deployment/backend --replicas=0 -n tradesense

# Restore database
kubectl exec -i deployment/postgres -n tradesense -- \
  psql -U tradesense -d postgres -c "DROP DATABASE tradesense;"
  
kubectl exec -i deployment/postgres -n tradesense -- \
  psql -U tradesense -d postgres -c "CREATE DATABASE tradesense;"
  
gunzip -c backup_20240116_020000.sql.gz | kubectl exec -i deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense

# Restart application
kubectl scale deployment/backend --replicas=3 -n tradesense
```

### Maintenance Tasks

```bash
# Vacuum and analyze
kubectl exec -it deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense -c "VACUUM ANALYZE;"

# Reindex
kubectl exec -it deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense -c "REINDEX DATABASE tradesense;"

# Update statistics
kubectl exec -it deployment/postgres -n tradesense -- \
  psql -U tradesense -d tradesense -c "ANALYZE;"
```

## Monitoring & Alerts

### Key Metrics to Watch

1. **Application Metrics**
   - Request rate: `rate(tradesense_http_requests_total[5m])`
   - Error rate: `rate(tradesense_http_requests_total{status=~"5.."}[5m])`
   - Response time: `histogram_quantile(0.95, tradesense_http_request_duration_seconds)`

2. **Database Metrics**
   - Connection pool: `tradesense_db_connections_active`
   - Query time: `histogram_quantile(0.95, tradesense_db_query_duration_seconds)`
   - Replication lag: `pg_replication_lag_seconds`

3. **Cache Metrics**
   - Hit rate: `rate(tradesense_cache_hits_total[5m]) / rate(tradesense_cache_requests_total[5m])`
   - Memory usage: `redis_memory_used_bytes`
   - Evictions: `rate(redis_evicted_keys_total[5m])`

### Alert Response

| Alert | Action |
|-------|--------|
| High Error Rate | Check logs, rollback recent deployment |
| Database Connection Pool Exhausted | Scale backend, check for connection leaks |
| Cache Hit Rate Low | Check cache configuration, warm cache |
| Disk Space Low | Clean logs, increase volume size |
| Certificate Expiring | Renew SSL certificate |

## Emergency Procedures

### Complete Service Failure

1. **Activate incident response**
   ```bash
   # Page on-call engineer
   ./scripts/page-oncall.sh "P1: TradeSense Complete Outage"
   
   # Start incident channel
   ./scripts/create-incident.sh P1 "Complete Service Failure"
   ```

2. **Emergency restart sequence**
   ```bash
   # 1. Database
   kubectl delete pod -l app=postgres -n tradesense
   kubectl wait --for=condition=ready pod -l app=postgres -n tradesense
   
   # 2. Redis
   kubectl delete pod -l app=redis -n tradesense
   kubectl wait --for=condition=ready pod -l app=redis -n tradesense
   
   # 3. Backend
   kubectl rollout restart deployment/backend -n tradesense
   kubectl rollout status deployment/backend -n tradesense
   
   # 4. Frontend
   kubectl rollout restart deployment/frontend -n tradesense
   kubectl rollout status deployment/frontend -n tradesense
   ```

3. **Verify recovery**
   ```bash
   # Run smoke tests
   ./scripts/smoke-tests.sh production
   
   # Check all endpoints
   for endpoint in health trades analytics auth; do
     echo "Testing $endpoint..."
     curl -f https://api.tradesense.com/api/v1/$endpoint || echo "FAILED"
   done
   ```

### Data Corruption

1. **Stop writes immediately**
   ```bash
   # Set backend to read-only mode
   kubectl set env deployment/backend READ_ONLY=true -n tradesense
   ```

2. **Assess damage**
   ```sql
   -- Check data integrity
   SELECT COUNT(*) FROM trades WHERE created_at > NOW() - INTERVAL '1 hour';
   SELECT COUNT(*) FROM users WHERE updated_at > NOW() - INTERVAL '1 hour';
   ```

3. **Restore from backup**
   ```bash
   # Find clean backup
   ./scripts/find-clean-backup.sh
   
   # Restore
   ./scripts/restore-database.sh /backups/postgres_20240116_010000.sql.gz
   ```

### Security Breach

1. **Immediate actions**
   ```bash
   # Rotate all secrets
   ./scripts/rotate-secrets.sh --all
   
   # Force logout all users
   kubectl exec -it deployment/redis -n tradesense -- redis-cli FLUSHALL
   
   # Enable enhanced logging
   kubectl set env deployment/backend SECURITY_AUDIT=true -n tradesense
   ```

2. **Investigation**
   ```bash
   # Export logs
   ./scripts/export-security-logs.sh --last-24h
   
   # Check for suspicious activity
   grep -E "(auth|login|token)" backend-logs-*.log | grep -v 200
   ```

## Contacts

### Escalation Path
1. On-call Engineer: PagerDuty
2. Tech Lead: +1-XXX-XXX-XXXX
3. VP Engineering: +1-XXX-XXX-XXXX
4. CTO: +1-XXX-XXX-XXXX

### External Vendors
- **AWS Support**: [AWS Console](https://console.aws.amazon.com/support)
- **Stripe Support**: support@stripe.com
- **SendGrid Support**: [Support Portal](https://support.sendgrid.com)

### Communication Channels
- **Incident Channel**: #incidents (Slack)
- **Status Updates**: status@tradesense.com
- **Customer Communication**: support@tradesense.com