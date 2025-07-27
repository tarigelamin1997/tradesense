# CORS Configuration Fix Steps

## The Issue
Your frontend is deployed but showing a CORS configuration issue because the backend services aren't deployed yet on Railway.

## Quick Solutions:

### 1. Wait for Backend Update (5-10 minutes)
The backend services are being updated to accept the Vercel URL. Wait for the update to complete.

### 2. Use the Main URL
Visit: https://tradesense.vercel.app instead

### 3. Run Locally with npm run dev
```bash
cd frontend
npm run dev
```
Then visit http://localhost:3001

### 4. Browser Extension (Temporary)
Install a CORS unblock extension temporarily for testing.

## Permanent Fix Steps:

### Step 1: Deploy Backend Services to Railway

1. **For each service directory:**
```bash
cd services/gateway
railway link
railway up

cd ../auth  
railway link
railway up

cd ../trading
railway link
railway up

cd ../analytics
railway link
railway up

cd ../billing
railway link
railway up

cd ../market-data
railway link
railway up

cd ../ai
railway link
railway up
```

### Step 2: Configure Railway Environment Variables

For each service in Railway dashboard, add:

```
CORS_ORIGINS=https://frontend-self-nu-47.vercel.app,https://tradesense.vercel.app,https://frontend-7uz3djyzl-tarig-ahmeds-projects.vercel.app
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true
JWT_SECRET_KEY=<generate-secure-key>
MASTER_ENCRYPTION_KEY=<generate-secure-key>
```

### Step 3: Update Frontend Environment

In Vercel dashboard, ensure these are set:
- `PUBLIC_API_URL=https://tradesense-gateway-production.up.railway.app`
- `PUBLIC_WS_URL=wss://tradesense-gateway-production.up.railway.app`

### Step 4: Redeploy Frontend

```bash
cd frontend
git add .
git commit -m "Fix CORS configuration"
git push
```

This will trigger a new deployment with the updated configuration.

## Testing the Fix

1. Clear your browser cache
2. Visit your Vercel URL
3. Open browser developer tools (F12)
4. Check the Network tab for API calls
5. Verify they're going to the Railway backend

## Alternative: Use Railway's Built-in Frontend Hosting

Instead of Vercel, you can deploy the frontend to Railway too:

```bash
cd frontend
railway link
railway up
```

This keeps everything in one platform and simplifies CORS.