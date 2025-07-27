# TradeSense API Endpoint Test Report
Generated: 2025-07-12T21:24:06.935250

## Summary
- **Total Endpoints**: 10
- **✅ Working**: 3 (30.0%)
- **🟡 Partial**: 0 (0.0%)
- **❌ Broken**: 4 (40.0%)
- **❓ Untested**: 3 (30.0%)

## Detailed Results

| Endpoint | Method | Status | Message | Response Time |
|----------|--------|--------|---------|---------------|
| /api/v1/analytics | ALL | ❓ Untested | No auth token available | 0.00s |
| /api/v1/trades | ALL | ❓ Untested | No auth token available | 0.00s |
| Other endpoints | ALL | ❓ Untested | No auth token available | 0.00s |
| /api/health | GET | ✅ Working | Health check active | 0.01s |
| /api/v1/health | GET | ❌ Broken | Unexpected status code: 405 | 0.00s |
| /api/v1/health/db | GET | ❌ Broken | Unexpected status code: 404 | 0.00s |
| /api/v1/performance/metrics | GET | ✅ Working | Health check active | 1.01s |
| /health | GET | ✅ Working | Health check active | 0.00s |
| /api/v1/auth/login | POST | ❌ Broken | Login failed | 0.00s |
| /api/v1/auth/register | POST | ❌ Broken | Unexpected status code: 201 | 0.31s |
