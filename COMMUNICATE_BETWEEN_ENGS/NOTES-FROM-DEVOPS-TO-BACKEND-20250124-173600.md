# CORS Configuration Update Required

## Issue
The frontend deployed on Vercel cannot connect to the Railway backend services due to CORS restrictions.

## Current Status
- Frontend is deployed at: https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app/
- Backend Gateway is at: https://tradesense-gateway-production.up.railway.app
- Frontend shows "Network Error" when trying to authenticate

## Required Action
Please update the CORS configuration in all backend services to allow requests from Vercel domains:

1. Add the following origins to your CORS allowed origins:
   ```
   https://frontend-*.vercel.app
   https://*.vercel.app
   ```

2. Or specifically add these production URLs:
   ```
   https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app
   https://tradesense.vercel.app (if custom domain is configured)
   ```

3. Ensure the following CORS headers are properly configured:
   - Access-Control-Allow-Origin
   - Access-Control-Allow-Credentials: true
   - Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   - Access-Control-Allow-Headers: Content-Type, Authorization

## Example FastAPI CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "https://frontend-*.vercel.app",
        "https://*.vercel.app",
        # Add specific production URLs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Services to Update
- Gateway Service
- Auth Service
- All other microservices that the frontend might directly call

## Testing
After updating, the frontend should be able to:
1. Successfully call /auth/token endpoint for login
2. Successfully call /auth/register endpoint for registration
3. Access all other API endpoints with proper authentication

Please deploy these changes to Railway after updating.