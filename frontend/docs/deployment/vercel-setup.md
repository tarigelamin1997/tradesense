# Vercel Deployment Setup

## Environment Variables

You must set the following environment variables in your Vercel project settings:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project (tradesense-gamma)
3. Go to "Settings" → "Environment Variables"
4. Add the following variables:

### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_API_URL` | `https://tradesense-gateway-production.up.railway.app` | Backend API URL from Railway |

### Optional Variables (if needed)

| Variable | Value | Description |
|----------|-------|-------------|
| `VITE_APP_URL` | `https://tradesense-gamma.vercel.app` | Frontend URL for CORS |

## Important Notes

1. **Environment variables must be set in Vercel Dashboard**, not in vercel.json
2. After adding environment variables, you need to **redeploy** for changes to take effect
3. You can trigger a redeployment by:
   - Pushing a new commit
   - Or clicking "Redeploy" in Vercel dashboard

## Troubleshooting

If you still see `FUNCTION_INVOCATION_FAILED` errors after setting environment variables:

1. Check Vercel function logs for specific error messages
2. Ensure the Railway backend is running and accessible
3. Verify CORS is configured correctly on the backend to allow requests from `tradesense-gamma.vercel.app`