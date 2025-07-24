# Frontend Network Error - CORS Configuration Required

## Error Description
Frontend users are experiencing "Network Error" when attempting to login or sign up. The frontend is unable to communicate with the backend services.

## Error Details
- **Error Message**: "Network Error" 
- **Location**: Login/Signup page
- **Frontend URL**: https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app/
- **Backend Gateway URL**: https://tradesense-gateway-production.up.railway.app
- **Error Type**: CORS (Cross-Origin Resource Sharing) blocking

## Technical Analysis
When the frontend (deployed on Vercel) tries to make API calls to the backend (deployed on Railway), the browser blocks the requests due to CORS policy. The backend is not configured to accept requests from the Vercel domain.

## Browser Console Error (Expected)
```
Access to fetch at 'https://tradesense-gateway-production.up.railway.app/auth/token' from origin 'https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app' has been blocked by CORS policy
```

## Required Fix
Update CORS middleware configuration in ALL backend services to include Vercel domains:

### 1. Gateway Service
Update the CORS middleware to include:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001", 
    "https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app",
    "https://frontend-*.vercel.app",
    "https://*.vercel.app"
]
```

### 2. Auth Service
Same CORS configuration update needed.

### 3. All Other Microservices
Apply the same CORS configuration to ensure consistency.

## Complete CORS Configuration Example
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://frontend-og3gd5s4j-tarig-ahmeds-projects.vercel.app",
        "https://frontend-*.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

## Important Notes
1. **allow_credentials=True** is crucial for authentication cookies to work
2. Include OPTIONS method for preflight requests
3. The wildcard patterns will allow all Vercel preview deployments to work

## Deployment Steps
1. Update CORS configuration in all services
2. Test locally to ensure no regression
3. Deploy to Railway
4. The frontend should immediately start working once deployed

## Verification
After deployment, test:
1. Login functionality
2. Registration functionality  
3. API calls with authentication tokens

Please prioritize this fix as it's blocking all frontend functionality in production.