# TradeSense Production Authentication Debugging Guide

## Overview

This guide helps diagnose and fix authentication issues in the TradeSense production environment.

## Architecture

```
Frontend (Vercel) → Gateway (Render) → Auth Service (Render) → PostgreSQL
```

## Current Production URLs

- **Frontend**: https://frontend-self-nu-47.vercel.app
- **Gateway**: https://tradesense-gateway.onrender.com
- **Auth Service**: https://tradesense-auth.onrender.com

## Authentication Flow

1. **Registration**: 
   - Frontend POSTs to `{GATEWAY_URL}/auth/register` with JSON body
   - Gateway forwards to Auth service
   - Auth service creates user and returns user data

2. **Login**:
   - Frontend POSTs to `{GATEWAY_URL}/auth/token` with form-encoded data
   - Format: `username={email_or_username}&password={password}`
   - Auth service returns JWT token

3. **Protected Routes**:
   - Frontend includes token in Authorization header: `Bearer {token}`
   - Gateway forwards authenticated requests to appropriate services

## Testing Production Endpoints

### 1. Run the Bash Test Script
```bash
./test-production-endpoints.sh
```

### 2. Run the Python Test Script
```bash
python3 test_production_auth.py
```

### 3. Manual Testing with curl

#### Test Gateway Health
```bash
curl https://tradesense-gateway.onrender.com/health
```

#### Test CORS Preflight
```bash
curl -X OPTIONS https://tradesense-gateway.onrender.com/auth/token \
  -H "Origin: https://frontend-self-nu-47.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -i
```

#### Test Login
```bash
curl -X POST https://tradesense-gateway.onrender.com/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Origin: https://frontend-self-nu-47.vercel.app" \
  -d "username=test@example.com&password=testpassword"
```

## Common Issues and Solutions

### 1. CORS Errors

**Symptoms**: 
- Browser console shows CORS policy errors
- Preflight OPTIONS requests fail

**Solutions**:
- Ensure frontend URL is in CORS origins list in both gateway and auth service
- Check that CORS middleware is properly configured
- Verify OPTIONS requests return proper headers

### 2. 502/503 Gateway Errors

**Symptoms**:
- Gateway returns 502 Bad Gateway or 503 Service Unavailable
- Auth endpoints unreachable

**Solutions**:
- Check if auth service is running: `curl https://tradesense-auth.onrender.com/health`
- Review Render deployment logs for auth service
- Verify service URLs in gateway configuration
- Check if services have started successfully

### 3. 404 Not Found

**Symptoms**:
- Auth endpoints return 404
- Routes not found

**Solutions**:
- Verify routing configuration in gateway
- Check that auth routes are properly mapped
- Ensure endpoints match between frontend and backend

### 4. Connection Refused

**Symptoms**:
- Unable to connect to services
- Timeout errors

**Solutions**:
- Verify services are deployed and running
- Check Render service logs
- Ensure environment variables are set correctly
- Verify database connections

### 5. Authentication Failures

**Symptoms**:
- Login returns 401 Unauthorized
- Token validation fails

**Solutions**:
- Verify JWT_SECRET_KEY is same across services
- Check user exists in database
- Ensure password hashing is consistent
- Verify token format and expiration

## Frontend Configuration

### Environment Variables
Set in Vercel dashboard:
```
VITE_API_BASE_URL=https://tradesense-gateway.onrender.com
```

### Update API Client
Ensure `frontend/src/lib/api/auth.ts` uses the correct endpoints:
- Login: `/auth/token` (NOT `/api/auth/token`)
- Register: `/auth/register`
- Get user: `/auth/me`

## Backend Configuration

### Gateway Environment Variables
```
AUTH_SERVICE_URL=http://auth:8000  # Internal Docker network
# OR
AUTH_SERVICE_URL=https://tradesense-auth.onrender.com  # External URL
```

### Auth Service Environment Variables
```
DATABASE_URL=postgresql://user:pass@host/db
JWT_SECRET_KEY=your-secret-key
```

### CORS Origins
Ensure these are included in both gateway and auth service:
```python
cors_origins = [
    "https://frontend-self-nu-47.vercel.app",
    "https://tradesense.vercel.app",
    "https://tradesense-gamma.vercel.app",
    # Add your specific Vercel deployment URLs
]
```

## Debugging Steps

1. **Check Service Health**
   - Gateway: `https://tradesense-gateway.onrender.com/health`
   - Auth: `https://tradesense-auth.onrender.com/health`

2. **Verify CORS Configuration**
   - Test OPTIONS requests from frontend domain
   - Check Access-Control headers in response

3. **Test Auth Flow**
   - Register a test user
   - Login with credentials
   - Access protected endpoint with token

4. **Review Logs**
   - Check Render deployment logs
   - Look for startup errors
   - Monitor request/response logs

5. **Database Connection**
   - Verify PostgreSQL is accessible
   - Check connection string format
   - Ensure migrations have run

## Quick Fixes

### Frontend Not Connecting
```javascript
// In frontend/.env or Vercel settings
VITE_API_BASE_URL=https://tradesense-gateway.onrender.com
```

### CORS Issues
Add frontend URL to allowed origins in gateway and auth service.

### Auth Service Down
1. Check Render dashboard
2. Restart service if needed
3. Review deployment logs

### Database Issues
1. Verify DATABASE_URL format
2. Check PostgreSQL is running
3. Run migrations if needed

## Contact Support

If issues persist after following this guide:
1. Collect logs from all services
2. Document exact error messages
3. Note which endpoints are failing
4. Include browser console errors