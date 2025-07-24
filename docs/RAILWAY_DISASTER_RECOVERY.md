# Railway Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for TradeSense services deployed on Railway. It covers backup strategies, recovery procedures, and business continuity planning.

## 🎯 Recovery Objectives

### RTO (Recovery Time Objective)
- **Critical Services** (Gateway, Auth, Trading): < 1 hour
- **Important Services** (Analytics, Billing): < 2 hours
- **Non-critical Services** (AI, Market Data cache): < 4 hours

### RPO (Recovery Point Objective)
- **Database**: < 15 minutes (with point-in-time recovery)
- **Configuration**: 0 minutes (stored in git)
- **User uploads**: < 1 hour

## 🔧 Backup Strategy

### 1. Database Backups

#### Automated Backups
```bash
# Run daily via cron
0 2 * * * /path/to/railway-backup.sh

# Weekly full backup with monthly retention
0 3 * * 0 /path/to/railway-backup.sh --full --retain 30
```

#### Manual Backup Before Major Changes
```bash
# Before deployments or migrations
./scripts/railway-backup.sh --tag pre-deployment-$(date +%Y%m%d)
```

### 2. Configuration Backups

#### Environment Variables
```bash
# Export all service configurations
for service in gateway auth trading analytics market-data billing ai; do
    railway variables export --service tradesense-$service > backups/env/$service.env
done
```

#### Railway Service Configuration
```bash
# Document service settings
railway status --json > backups/railway-config-$(date +%Y%m%d).json
```

### 3. Code and Infrastructure

- **Git Repository**: All code in GitHub with protected branches
- **Docker Images**: Automatically built and stored by Railway
- **Dependencies**: Locked versions in requirements.txt/package-lock.json

## 🚨 Disaster Scenarios

### Scenario 1: Service Failure

**Symptoms**: One or more services not responding

**Recovery Steps**:
1. Check Railway dashboard for service status
2. Review logs: `railway logs --service tradesense-[service]`
3. Restart service: `railway restart --service tradesense-[service]`
4. If persistent, redeploy: `railway up --service tradesense-[service]`

### Scenario 2: Database Corruption

**Symptoms**: Data inconsistencies, query failures

**Recovery Steps**:
1. Stop affected services to prevent further corruption
2. Identify last known good backup
3. Restore database:
   ```bash
   ./scripts/restore_[service]_[timestamp].sh
   ```
4. Verify data integrity
5. Restart services

### Scenario 3: Complete Railway Outage

**Symptoms**: All services unavailable, Railway platform down

**Recovery Steps**:
1. Check Railway status page
2. If extended outage (>2 hours), initiate failover:
   - Deploy to backup platform (Render/Fly.io)
   - Update DNS records
   - Restore from latest backups

### Scenario 4: Security Breach

**Symptoms**: Unauthorized access, data tampering

**Recovery Steps**:
1. **Immediate Actions**:
   ```bash
   # Rotate all secrets
   ./scripts/rotate-secrets.sh --emergency
   
   # Disable compromised services
   railway down --service tradesense-[affected-service]
   ```

2. **Investigation**:
   - Review access logs
   - Identify breach vector
   - Document timeline

3. **Recovery**:
   - Patch vulnerabilities
   - Restore from clean backup
   - Redeploy all services
   - Notify affected users

### Scenario 5: Data Loss

**Symptoms**: Missing records, accidental deletion

**Recovery Steps**:
1. Stop write operations to prevent overwriting
2. Identify extent of data loss
3. Restore from backup:
   ```bash
   # Point-in-time recovery
   ./scripts/restore-to-timestamp.sh --time "2024-01-23 14:30:00"
   ```
4. Verify recovered data
5. Resume operations

## 📋 Recovery Procedures

### 1. Service Recovery Checklist

- [ ] Identify failed service(s)
- [ ] Check service logs for errors
- [ ] Verify environment variables are set
- [ ] Check database connectivity
- [ ] Restart service
- [ ] Verify health endpoint
- [ ] Check dependent services
- [ ] Monitor for 15 minutes

### 2. Database Recovery Procedure

```bash
#!/bin/bash
# Database recovery script

SERVICE=$1
BACKUP_FILE=$2

# Stop service to prevent writes
railway down --service tradesense-$SERVICE

# Get database URL
DB_URL=$(railway variables get DATABASE_URL --service tradesense-$SERVICE)

# Restore database
gunzip -c $BACKUP_FILE | psql $DB_URL

# Verify restoration
railway run --service tradesense-$SERVICE python scripts/verify_db.py

# Restart service
railway up --service tradesense-$SERVICE
```

### 3. Full System Recovery

```bash
#!/bin/bash
# Full system recovery procedure

# 1. Restore databases
for service in auth trading analytics billing ai; do
    ./scripts/restore_${service}_latest.sh
done

# 2. Restore environment variables
for service in gateway auth trading analytics market-data billing ai; do
    railway variables set --service tradesense-$service < backups/env/$service.env
done

# 3. Deploy services in order
services=(auth gateway trading analytics market-data billing ai)
for service in "${services[@]}"; do
    cd services/$service
    railway up --service tradesense-$service
    sleep 30  # Wait for service to start
    
    # Verify health
    railway run --service tradesense-$service curl localhost:8000/health
done

# 4. Verify system health
./scripts/monitor-railway-health.sh --verify-all
```

## 🔄 Business Continuity

### 1. Communication Plan

**Internal Team**:
- Slack: #tradesense-incidents
- Email: ops@tradesense.com
- Phone tree for critical incidents

**External Communication**:
- Status page: status.tradesense.com
- Email notifications to affected users
- Support ticket auto-responses

### 2. Failover Strategy

**Primary**: Railway (us-west)
**Secondary**: Prepared configurations for:
- Render.com
- Fly.io
- DigitalOcean App Platform

**DNS Failover**:
- TTL set to 300 seconds for quick changes
- Cloudflare for DNS management
- Health checks every 30 seconds

### 3. Testing Schedule

**Monthly**:
- Service restart drills
- Backup restoration test (dev environment)

**Quarterly**:
- Full disaster recovery drill
- Failover to secondary platform
- Security incident simulation

**Annually**:
- Complete business continuity test
- Third-party security audit

## 📊 Monitoring and Alerts

### Critical Alerts

```yaml
# Datadog alerts for disaster scenarios
- Service Down:
    condition: service.health_check failing for 3 minutes
    action: Page on-call engineer
    
- Database Connection Lost:
    condition: database.connections = 0
    action: Immediate notification
    
- High Error Rate:
    condition: error_rate > 10% for 5 minutes
    action: Alert team
    
- Backup Failure:
    condition: backup job failed
    action: Email operations team
```

### Recovery Metrics

Track and report:
- Time to detect incident
- Time to respond
- Time to recover
- Data loss (if any)
- Affected users
- Root cause

## 🛠️ Tools and Scripts

### Essential Scripts

1. **health-check-all.sh**: Verify all services
2. **emergency-backup.sh**: Immediate backup of all databases
3. **restore-system.sh**: Automated full recovery
4. **rotate-secrets.sh**: Emergency secret rotation
5. **failover-dns.sh**: Update DNS for failover

### Recovery Toolkit

```bash
# Create DR toolkit
mkdir -p dr-toolkit
cd dr-toolkit

# Essential files
- railway-cli (latest version)
- backup scripts
- restoration scripts
- environment templates
- DNS update scripts
- communication templates
```

## 📱 On-Call Procedures

### Escalation Path

1. **Level 1** (0-15 min): On-call engineer
2. **Level 2** (15-30 min): Team lead
3. **Level 3** (30+ min): CTO/Head of Engineering

### On-Call Checklist

1. Acknowledge alert within 5 minutes
2. Assess severity and impact
3. Begin initial troubleshooting
4. Escalate if needed
5. Implement fix or workaround
6. Monitor for stability
7. Document incident
8. Conduct post-mortem

## 📝 Documentation

### Required Documentation

- [ ] System architecture diagram
- [ ] Service dependency map
- [ ] Database schemas
- [ ] API documentation
- [ ] Runbooks for common issues
- [ ] Contact information
- [ ] Vendor support contacts

### Post-Incident

1. **Incident Report** (within 24 hours)
2. **Post-Mortem** (within 3 days)
3. **Action Items** (within 1 week)
4. **Process Updates** (as needed)

## 🔐 Security Considerations

### During Recovery

- Verify identity of all personnel
- Use secure channels for communication
- Log all recovery actions
- Validate data integrity after restoration
- Change all passwords after security incident
- Review access logs

### Post-Recovery

- Security audit of recovered systems
- Update security policies
- Review and update access controls
- Implement additional monitoring

## 📞 Important Contacts

### Railway Support
- Email: support@railway.app
- Status: status.railway.app
- Documentation: docs.railway.app

### Internal Contacts
- On-call: [Phone/Slack]
- CTO: [Contact]
- Security Team: [Contact]

### External Services
- Datadog: [Support contact]
- Cloudflare: [Support contact]
- GitHub: [Support contact]

---

**Last Updated**: January 2025
**Next Review**: April 2025
**Owner**: DevOps Team