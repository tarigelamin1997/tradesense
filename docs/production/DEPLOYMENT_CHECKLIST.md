# TradeSense Production Deployment Checklist

## Pre-Deployment (Day Before)

### Infrastructure Preparation
- [ ] Verify Kubernetes cluster health
- [ ] Check node capacity (CPU, Memory, Disk)
- [ ] Ensure backup storage has sufficient space
- [ ] Verify SSL certificates are valid for > 30 days
- [ ] Test disaster recovery procedures
- [ ] Review and update security groups/firewall rules

### Code Preparation
- [ ] All tests passing in CI/CD pipeline
- [ ] Security scan completed (no critical vulnerabilities)
- [ ] Code reviewed and approved by team lead
- [ ] Release notes prepared
- [ ] Database migration scripts tested in staging
- [ ] Performance benchmarks meet requirements

### Communication
- [ ] Deployment window scheduled and communicated
- [ ] On-call engineer notified
- [ ] Status page prepared for updates
- [ ] Customer communication drafted (if needed)
- [ ] Rollback plan reviewed with team

## Deployment Day

### Pre-Deployment (1 Hour Before)
- [ ] Create full production backup
  ```bash
  ./scripts/backup-system.sh full
  ```
- [ ] Verify backup integrity
- [ ] Scale down non-critical services to free resources
- [ ] Clear CDN cache
- [ ] Enable maintenance mode (if required)
- [ ] Start recording deployment metrics

### Database Migration (30 Minutes Before)
- [ ] Take database snapshot
- [ ] Run migration in dry-run mode
  ```bash
  kubectl exec deployment/backend -- alembic upgrade head --sql
  ```
- [ ] Review migration SQL
- [ ] Execute migration
  ```bash
  kubectl exec deployment/backend -- alembic upgrade head
  ```
- [ ] Verify migration success
- [ ] Test critical queries

### Deployment Phase

#### 1. Deploy Backend (15 Minutes)
- [ ] Build and push Docker images
  ```bash
  docker build -f src/backend/Dockerfile.production -t tradesense/backend:v2.0.0 .
  docker push tradesense/backend:v2.0.0
  ```
- [ ] Update Kubernetes deployment
  ```bash
  kubectl set image deployment/backend backend=tradesense/backend:v2.0.0 -n tradesense
  ```
- [ ] Monitor rollout
  ```bash
  kubectl rollout status deployment/backend -n tradesense
  ```
- [ ] Verify health checks pass
- [ ] Check error logs
- [ ] Test API endpoints

#### 2. Deploy Frontend (10 Minutes)
- [ ] Build and push frontend image
  ```bash
  docker build -f frontend/Dockerfile.production -t tradesense/frontend:v2.0.0 .
  docker push tradesense/frontend:v2.0.0
  ```
- [ ] Update frontend deployment
  ```bash
  kubectl set image deployment/frontend frontend=tradesense/frontend:v2.0.0 -n tradesense
  ```
- [ ] Monitor rollout
- [ ] Clear browser cache requirements
- [ ] Verify static assets loading
- [ ] Test critical user flows

#### 3. Update Supporting Services (5 Minutes)
- [ ] Update cron jobs
- [ ] Update worker deployments
- [ ] Refresh configuration maps
- [ ] Update ingress rules (if needed)

### Post-Deployment Verification (30 Minutes)

#### Automated Verification
- [ ] Run deployment verification script
  ```bash
  ./scripts/verify-deployment.sh production
  ```
- [ ] All tests must pass before proceeding

#### Manual Verification
- [ ] Login flow works correctly
- [ ] Dashboard loads with data
- [ ] Trade creation/update works
- [ ] Analytics calculations correct
- [ ] Payment processing functional
- [ ] Email notifications sending
- [ ] File uploads working
- [ ] API rate limiting active

#### Performance Verification
- [ ] Response times < 200ms (p50)
- [ ] Error rate < 0.1%
- [ ] Database query times normal
- [ ] Cache hit rate > 80%
- [ ] No memory leaks detected

#### Monitoring Verification
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards updating
- [ ] Alerts configured and firing correctly
- [ ] Logs aggregating properly
- [ ] APM traces visible

### Final Steps (15 Minutes)
- [ ] Update status page - deployment complete
- [ ] Send deployment success notification
- [ ] Document any issues or deviations
- [ ] Update runbook with new findings
- [ ] Schedule post-deployment review

## Post-Deployment Monitoring (24 Hours)

### First Hour
- [ ] Monitor error rates closely
- [ ] Check for any performance degradation
- [ ] Review user feedback channels
- [ ] Verify backup jobs running

### First Day
- [ ] Review overnight performance
- [ ] Check for any delayed issues
- [ ] Analyze user behavior changes
- [ ] Review security alerts
- [ ] Validate business metrics

## Rollback Procedure

If critical issues detected:

### Immediate Rollback (< 5 Minutes)
```bash
# Rollback deployments
kubectl rollout undo deployment/backend -n tradesense
kubectl rollout undo deployment/frontend -n tradesense

# Verify rollback
kubectl rollout status deployment/backend -n tradesense
kubectl rollout status deployment/frontend -n tradesense
```

### Database Rollback (If Needed)
```bash
# Stop application
kubectl scale deployment/backend --replicas=0 -n tradesense

# Restore database
./scripts/restore-database.sh /backups/pre-deployment-backup.sql.gz

# Restart application
kubectl scale deployment/backend --replicas=3 -n tradesense
```

### Communication
- [ ] Update status page
- [ ] Notify stakeholders
- [ ] Document rollback reason
- [ ] Schedule incident review

## Success Criteria

Deployment is considered successful when:
- ✓ All automated tests pass
- ✓ Zero critical errors in first hour
- ✓ Performance metrics within SLA
- ✓ No customer-reported issues
- ✓ All monitoring systems green

## Sign-Off

| Role | Name | Signature | Date/Time |
|------|------|-----------|-----------|
| DevOps Lead | | | |
| Backend Lead | | | |
| Frontend Lead | | | |
| QA Lead | | | |
| Product Manager | | | |

## Notes

_Use this section to document any deployment-specific notes, issues encountered, or deviations from the standard process._

---

**Deployment Log**: `/var/log/deployments/tradesense-YYYYMMDD-HHMMSS.log`