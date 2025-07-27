# Manual Deployment Steps for Gateway CORS Update

The gateway is running but hasn't picked up the CORS configuration changes yet. Here's how to manually deploy the updated gateway:

## Option 1: Via Railway Dashboard (Recommended)

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Navigate to the `tradesense-gateway` service
3. Go to the "Deployments" tab
4. Click on "Redeploy" button
5. **Important**: Check "Clear build cache" option
6. Wait for deployment to complete (5-10 minutes)

## Option 2: Via Railway CLI

If you have Railway CLI installed:

```bash
cd services/gateway
railway up --service tradesense-gateway
```

## Option 3: Trigger via GitHub

1. Make a small change to force redeployment:
```bash
cd services/gateway
echo "# Force redeploy $(date)" >> README.md
git add README.md
git commit -m "chore: Force gateway redeployment for CORS update"
git push origin main
```

## Verification

After deployment, verify CORS is working:

```bash
curl -I https://tradesense-gateway-production.up.railway.app/auth/token \
  -H "Origin: https://frontend-bbfjkd8ow-tarig-ahmeds-projects.vercel.app" \
  -X OPTIONS
```

Look for this header in the response:
```
access-control-allow-origin: https://frontend-bbfjkd8ow-tarig-ahmeds-projects.vercel.app
```

## Current Status

- ✅ Gateway is running and healthy
- ✅ All backend services are accessible
- ✅ Authentication endpoints are working (returning 401 as expected)
- ❌ CORS configuration not yet updated (missing the new Vercel URL)

Once the gateway is redeployed with the latest code, the authentication will work properly from the frontend.