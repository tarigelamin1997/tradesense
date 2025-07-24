# TradeSense API Health Check Tests

This directory contains comprehensive health check tests for the TradeSense trading platform. The tests cover both the monolithic backend and microservices architecture, ensuring reliable health monitoring across the entire system.

## Test Structure

### 1. Monolithic Backend Tests (`src/backend/tests/api/test_health_comprehensive.py`)
Tests for the main backend API health endpoints:
- Basic health check (`/health`)
- Detailed health check (`/health/detailed`)
- Readiness probe (`/health/ready`)
- Version endpoints (`/version`, `/api/v1/version`)
- Failure scenarios (database down, cache failures)
- Authentication and CORS handling
- Concurrent request handling

### 2. Microservices Tests (`tests/services/test_microservices_health.py`)
Individual health checks for each microservice:
- **Auth Service**: Database connectivity, token validation
- **Trading Service**: Trade processor, message queue, database
- **Analytics Service**: Calculation engine, processing queue
- **Market Data Service**: Data sources, WebSocket connections
- **Billing Service**: Payment gateway, subscription processor
- **AI Service**: Model loading, GPU status, inference engine

### 3. API Gateway Tests (`tests/services/test_gateway_health.py`)
Tests for the gateway's health aggregation:
- Overall system health aggregation
- Service discovery and status tracking
- Circuit breaker implementation
- Health check caching
- Alert triggering logic
- Metrics collection

### 4. Edge Case Tests (`tests/integration/test_health_edge_cases.py`)
Comprehensive failure scenario testing:
- **Database Failures**: Connection loss, timeouts, pool exhaustion, locks
- **Cache Failures**: Redis disconnection, timeouts, memory full
- **Network Failures**: DNS resolution, unreachable services
- **Resource Exhaustion**: Low memory, high CPU, disk full
- **Concurrent Requests**: Load handling, rate limiting
- **Service Dependencies**: Cascading failures, recovery patterns

### 5. Performance Tests (`tests/performance/test_health_performance.py`)
Performance and scalability testing:
- Response time benchmarks (p50, p95, p99)
- Throughput testing (requests per second)
- Sustained load testing
- Scalability patterns
- Resource usage (CPU, memory)
- Caching effectiveness

### 6. Integration Tests (`tests/integration/test_health_monitoring.py`)
Monitoring and observability testing:
- Metrics collection (Prometheus format)
- Structured logging
- Alert management
- Dashboard data endpoints
- OpenTelemetry integration
- Kubernetes compliance

## Running the Tests

### Run All Health Check Tests
```bash
# From the project root
pytest tests/ -k "health" -v

# Run with coverage
pytest tests/ -k "health" --cov=src.backend.api.health --cov-report=html
```

### Run Specific Test Categories
```bash
# Monolithic backend tests only
pytest src/backend/tests/api/test_health_comprehensive.py -v

# Microservices tests only
pytest tests/services/test_microservices_health.py -v

# Performance tests
pytest tests/performance/test_health_performance.py -v

# Edge case tests
pytest tests/integration/test_health_edge_cases.py -v
```

### Run with Markers
```bash
# Fast tests only
pytest tests/ -k "health" -m "not slow" -v

# Integration tests
pytest tests/ -k "health" -m "integration" -v
```

## Performance Benchmarks

Expected performance targets for health endpoints:

| Endpoint | p50 (ms) | p95 (ms) | p99 (ms) |
|----------|----------|----------|----------|
| `/health` | < 30 | < 50 | < 100 |
| `/health/ready` | < 20 | < 30 | < 50 |
| `/health/detailed` | < 100 | < 200 | < 500 |
| `/api/v1/health` | < 30 | < 50 | < 100 |

## Load Testing

For load testing with Locust:
```bash
# Install Locust
pip install locust

# Run load test
locust -f tests/performance/test_health_performance.py --host=http://localhost:8000
```

## Monitoring Integration

The health check tests verify integration with:
- **Prometheus**: Metrics in Prometheus format
- **Grafana**: Dashboard data endpoints
- **Kubernetes**: Liveness/readiness probe compliance
- **OpenTelemetry**: Distributed tracing support

## Best Practices

1. **Health Check Design**:
   - Keep health checks lightweight
   - Implement proper timeouts
   - Use caching where appropriate
   - Separate liveness from readiness

2. **Testing Strategy**:
   - Test both success and failure scenarios
   - Verify graceful degradation
   - Test under concurrent load
   - Monitor resource usage

3. **Alert Configuration**:
   - Set appropriate thresholds
   - Implement rate limiting
   - Use escalation policies
   - Test alert delivery

## Troubleshooting

### Common Issues

1. **Tests Timing Out**:
   - Check if services are running
   - Verify network connectivity
   - Increase timeout values for slow environments

2. **Database Connection Errors**:
   - Ensure test database is running
   - Check connection string in test configuration
   - Verify database permissions

3. **Microservice Tests Failing**:
   - Start all microservices before running tests
   - Check service URLs and ports
   - Verify inter-service connectivity

## Future Enhancements

1. **Chaos Engineering**: Add fault injection tests
2. **Multi-Region Testing**: Test health checks across regions
3. **Custom Health Indicators**: Add business-specific health metrics
4. **SLA Monitoring**: Automated SLA compliance testing
5. **Synthetic Monitoring**: Continuous health check execution

## Contributing

When adding new health check tests:
1. Follow the existing test structure
2. Add appropriate test markers (`@pytest.mark.slow`, etc.)
3. Document expected behavior
4. Include performance benchmarks
5. Update this README with new test information