# TradeSense Monitoring Guide

## Overview

TradeSense implements comprehensive monitoring and alerting to ensure system reliability and performance. This guide covers the monitoring stack, key metrics, alert configurations, and troubleshooting procedures.

## Monitoring Stack

### Components

1. **Prometheus** - Metrics collection and storage
2. **Grafana** - Visualization and dashboards
3. **AlertManager** - Alert routing and notifications
4. **Custom Metrics** - Application-specific metrics
5. **Health Checks** - Component health monitoring

### Architecture

```
Application → Metrics Endpoint → Prometheus → Grafana
                ↓                    ↓
          Health Checks         AlertManager → PagerDuty/Slack/Email
```

## Key Metrics

### Application Metrics

#### HTTP Metrics
- `tradesense_http_requests_total` - Total HTTP requests by status, method, endpoint
- `tradesense_http_request_duration_seconds` - Request latency histogram
- `tradesense_http_requests_in_flight` - Currently processing requests

#### Business Metrics
- `tradesense_trades_created_total` - Trades created by type and user tier
- `tradesense_trades_value_dollars` - Trade values histogram
- `tradesense_active_users` - Active users by period and tier
- `tradesense_subscription_revenue_total` - Revenue by plan

#### Performance Metrics
- `tradesense_db_query_duration_seconds` - Database query performance
- `tradesense_cache_operations_total` - Cache hits/misses
- `tradesense_background_task_duration_seconds` - Background job performance

### System Metrics

- CPU usage
- Memory usage
- Disk space
- Network I/O
- Database connections
- Redis memory usage

## Health Checks

### Endpoints

- `/api/v1/monitoring/health` - Basic health check
- `/api/v1/monitoring/health/detailed` - Detailed component status
- `/api/v1/monitoring/health/live` - Kubernetes liveness probe
- `/api/v1/monitoring/health/ready` - Kubernetes readiness probe

### Component Checks

1. **Database Health**
   - Connectivity
   - Connection pool status
   - Query performance
   - Replication lag

2. **Redis Health**
   - Connectivity
   - Memory usage
   - Hit rate
   - Evictions

3. **External APIs**
   - Stripe API
   - SendGrid API
   - Third-party integrations

4. **System Resources**
   - Disk space
   - Memory usage
   - SSL certificates

## Alerting

### Alert Severity Levels

- **Critical** - Immediate action required (PagerDuty)
- **High** - Urgent, needs attention soon
- **Medium** - Should be investigated
- **Low** - Informational
- **Info** - FYI only

### Key Alerts

#### Critical Alerts
1. **API Down** - Backend service unreachable
2. **Database Connection Pool Exhausted** - No available connections
3. **Payment System Failure** - Stripe API errors

#### High Priority Alerts
1. **High Error Rate** - >5% of requests failing
2. **SSL Certificate Expiry** - <30 days remaining
3. **Disk Space Low** - <15% free space
4. **User Activity Drop** - >30% decrease

#### Medium Priority Alerts
1. **Slow Response Times** - p95 >500ms
2. **Low Cache Hit Rate** - <80%
3. **Background Task Failures** - >10 per hour
4. **High Memory Usage** - >85%

### Alert Configuration

Alerts are configured in `/monitoring/prometheus/alerts.yml`:

```yaml
- alert: TradesenseHighErrorRate
  expr: |
    (
      sum(rate(tradesense_http_requests_total{status=~"5.."}[5m]))
      /
      sum(rate(tradesense_http_requests_total[5m]))
    ) > 0.05
  for: 5m
  labels:
    severity: high
    team: backend
  annotations:
    summary: "High API error rate"
    description: "API error rate is {{ $value | humanizePercentage }}"
```

## Dashboards

### Main Dashboard

Access at: https://grafana.tradesense.com/d/tradesense-monitoring

Key panels:
- Health Status
- Active Users
- Error Rate
- Response Time (p95)
- Request Rate by Status
- Database Performance
- Cache Hit Rate
- Business Metrics

### Custom Dashboards

1. **Business Metrics Dashboard**
   - Trade volume
   - Revenue tracking
   - User activity
   - Feature usage

2. **Performance Dashboard**
   - Response time percentiles
   - Slow endpoints
   - Database query performance
   - Cache efficiency

3. **Infrastructure Dashboard**
   - CPU/Memory usage
   - Disk I/O
   - Network traffic
   - Container metrics

## Monitoring Best Practices

### 1. Metric Naming

Follow Prometheus naming conventions:
- Use lowercase with underscores
- Include unit suffix (`_seconds`, `_bytes`, `_total`)
- Be descriptive but concise

### 2. Label Usage

- Keep cardinality low
- Use consistent label names
- Avoid user IDs or high-cardinality values

### 3. Alert Tuning

- Set appropriate thresholds
- Use time windows to reduce noise
- Include runbook links
- Test alerts regularly

### 4. Dashboard Design

- Group related metrics
- Use appropriate visualizations
- Set meaningful time ranges
- Include documentation

## Troubleshooting

### High Error Rate

1. Check recent deployments
2. Review error logs
3. Check external dependencies
4. Verify database health
5. Consider rollback if needed

### Slow Response Times

1. Check database query performance
2. Review cache hit rates
3. Check CPU/memory usage
4. Look for N+1 queries
5. Profile slow endpoints

### Memory Issues

1. Check for memory leaks
2. Review background job queues
3. Check cache size
4. Look for large objects
5. Consider scaling

### Database Issues

1. Check connection pool
2. Review slow queries
3. Check replication lag
4. Verify indexes
5. Consider connection limits

## Metric Collection

### Adding Custom Metrics

```python
from prometheus_client import Counter, Histogram

# Define metric
feature_usage = Counter(
    'tradesense_feature_usage_total',
    'Feature usage tracking',
    ['feature', 'user_tier']
)

# Use in code
@track_feature_usage("advanced_analytics")
async def get_advanced_analytics(user: User):
    feature_usage.labels(
        feature="advanced_analytics",
        user_tier=user.subscription_tier
    ).inc()
    # ... rest of function
```

### Metric Guidelines

1. **What to measure**
   - User actions
   - Business events
   - Performance metrics
   - Error conditions

2. **What not to measure**
   - Personal information
   - High-cardinality data
   - Temporary values
   - Debug information

## Integration

### Slack Integration

Alerts are sent to:
- `#alerts` - All alerts
- `#alerts-critical` - Critical only
- `#engineering` - Engineering team

### PagerDuty Integration

Critical alerts trigger PagerDuty:
- On-call rotation
- Escalation policies
- Incident management

### Email Notifications

High-priority alerts sent to:
- Engineering team
- DevOps team
- On-call engineer

## Maintenance

### Regular Tasks

1. **Daily**
   - Review overnight alerts
   - Check dashboard anomalies
   - Verify backup success

2. **Weekly**
   - Review alert noise
   - Update thresholds
   - Clean up old alerts

3. **Monthly**
   - Review metric cardinality
   - Update dashboards
   - Test alert paths
   - Update runbooks

### Metric Retention

- Raw metrics: 15 days
- 5-minute aggregations: 90 days
- Hourly aggregations: 2 years

## Emergency Procedures

### Complete Monitoring Failure

1. Check Prometheus health
2. Verify network connectivity
3. Check disk space
4. Restart services if needed
5. Use backup monitoring

### Alert Storm

1. Acknowledge alerts
2. Identify root cause
3. Silence non-critical alerts
4. Focus on critical issues
5. Post-mortem after resolution

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [TradeSense Runbook](./RUNBOOK.md)