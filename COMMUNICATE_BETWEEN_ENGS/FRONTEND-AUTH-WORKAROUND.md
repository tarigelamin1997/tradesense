# Frontend Authentication Workaround Instructions

**From**: Backend Engineer  
**To**: Frontend Team / DevOps  
**Date**: 2025-01-24  
**Priority**: URGENT - Immediate Fix Available

## Quick Fix: Direct Auth Service Connection

To immediately resolve the authentication issue, update your frontend environment configuration to connect directly to the auth service.

## Option 1: Environment Variable Update (Recommended)

### For Local Development
Create or update `.env` file in the frontend directory:
```bash
VITE_API_BASE_URL=https://tradesense-auth-production.up.railway.app
```

### For Vercel Deployment
1. Go to your Vercel project settings
2. Navigate to Environment Variables
3. Add: `VITE_API_BASE_URL` = `https://tradesense-auth-production.up.railway.app`
4. Redeploy your frontend

## Option 2: Code-Level Temporary Fix

If you need to hardcode temporarily, update `/frontend/src/lib/api/auth.ts`:

### Lines to Update:

**Line 60** - Login endpoint:
```javascript
// ORIGINAL:
const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/token`, {

// TEMPORARY FIX:
const response = await fetch(`https://tradesense-auth-production.up.railway.app/auth/token`, {
```

**Line 80** - Get user info:
```javascript
// ORIGINAL:
const userResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/me`, {

// TEMPORARY FIX:
const userResponse = await fetch(`https://tradesense-auth-production.up.railway.app/auth/me`, {
```

**Line 137** - Register endpoint:
```javascript
// ORIGINAL:
const registerResponse = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/register`, {

// TEMPORARY FIX:
const registerResponse = await fetch(`https://tradesense-auth-production.up.railway.app/auth/register`, {
```

**Line 184** - Logout endpoint:
```javascript
// ORIGINAL:
await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/logout`, {

// TEMPORARY FIX:
await fetch(`https://tradesense-auth-production.up.railway.app/auth/logout`, {
```

**Line 207** - Check auth status:
```javascript
// ORIGINAL:
const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/me`, {

// TEMPORARY FIX:
const response = await fetch(`https://tradesense-auth-production.up.railway.app/auth/me`, {
```

## Option 3: Create a Service URL Configuration

Create a new file `/frontend/src/lib/config/services.ts`:

```typescript
// Temporary service URLs until gateway is fixed
export const SERVICE_URLS = {
  auth: import.meta.env.VITE_AUTH_SERVICE_URL || 'https://tradesense-auth-production.up.railway.app',
  gateway: import.meta.env.VITE_GATEWAY_URL || 'https://tradesense-gateway-production.up.railway.app',
  // Add other services as needed
};

// Helper to get the appropriate base URL
export function getServiceUrl(service: keyof typeof SERVICE_URLS): string {
  return SERVICE_URLS[service];
}
```

Then update auth.ts to use:
```javascript
import { getServiceUrl } from '$lib/config/services';

// Replace all instances of:
`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/auth/...`

// With:
`${getServiceUrl('auth')}/auth/...`
```

## Testing After Implementation

1. Clear browser cache and cookies
2. Try to register a new account
3. Try to login with existing credentials
4. Verify the auth token is properly stored

## Important Notes

1. **CORS is already configured** - The auth service accepts requests from Vercel domains
2. **This is temporary** - Once the gateway is fixed, switch back to using the gateway URL
3. **Other services** - You may need similar workarounds for other services (trades, analytics, etc.)

## Long-term Solution

Once the gateway deployment issue is resolved:
1. Update `VITE_API_BASE_URL` back to `https://tradesense-gateway-production.up.railway.app`
2. Remove any hardcoded service URLs
3. All requests will properly route through the gateway

## Current Working Endpoints

Direct auth service endpoints that are confirmed working:
- POST `https://tradesense-auth-production.up.railway.app/auth/token` - Login
- POST `https://tradesense-auth-production.up.railway.app/auth/register` - Register
- GET `https://tradesense-auth-production.up.railway.app/auth/me` - Get current user
- POST `https://tradesense-auth-production.up.railway.app/auth/logout` - Logout

Choose the option that works best for your deployment process. Option 1 (environment variable) is recommended as it requires no code changes.