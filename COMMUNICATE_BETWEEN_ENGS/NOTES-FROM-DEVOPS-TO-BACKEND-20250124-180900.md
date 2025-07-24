# Gateway Routing Issue - Auth Endpoints Not Found

## Error Description
Frontend is getting "Failed to fetch" error when trying to login/signup. Investigation shows the gateway is returning 404 for auth endpoints.

## Error Details
- **Error Message**: "Failed to fetch"
- **Location**: Login/Signup forms
- **Gateway Response**: 404 Not Found for `/auth/token`
- **Direct Auth Service**: Working correctly (returns 401 for invalid credentials)

## Technical Analysis

### 1. Gateway Health Check
```json
{
  "status": "healthy",
  "services": {
    "auth": {
      "status": "healthy"
    }
  }
}
```
✅ Gateway is healthy and sees the auth service

### 2. Gateway Request
```bash
POST https://tradesense-gateway-production.up.railway.app/auth/token
Response: 404 Not Found
```
❌ Gateway returns 404 for auth endpoints

### 3. Direct Auth Service Request
```bash
POST https://tradesense-auth-production.up.railway.app/auth/token
Response: 401 Unauthorized (expected for wrong credentials)
```
✅ Auth service endpoints are working correctly

## Root Cause
The gateway is not properly routing `/auth/*` requests to the auth service. The routing configuration in the gateway service needs to be fixed.

## Required Fix

### Check Gateway Routing Configuration
The gateway should be configured to route:
- `/auth/*` → Auth Service
- `/trading/*` → Trading Service
- `/analytics/*` → Analytics Service
- etc.

### Example FastAPI Gateway Route
```python
# In gateway main.py
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_auth(path: str, request: Request):
    # Proxy to auth service
    auth_url = f"{AUTH_SERVICE_URL}/{path}"
    # Forward the request
```

### Or Using Route Mounting
```python
# Mount auth service routes
app.mount("/auth", auth_proxy_app)
```

## Testing Steps
1. Fix the gateway routing configuration
2. Ensure `/auth/token`, `/auth/register`, `/auth/me` are properly proxied
3. Test with:
   ```bash
   curl -X POST https://tradesense-gateway-production.up.railway.app/auth/token
   ```
   Should return 401 (not 404)

## Impact
This is blocking all authentication functionality in the frontend. Users cannot login or register.

## Frontend Temporary Workaround
As a temporary measure, the frontend could be configured to call the auth service directly at `https://tradesense-auth-production.up.railway.app` instead of going through the gateway, but this is not recommended for production.

Please prioritize fixing the gateway routing configuration.