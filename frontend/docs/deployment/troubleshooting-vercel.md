# Troubleshooting Vercel FUNCTION_INVOCATION_FAILED Error

## Quick Diagnosis Steps

### 1. Test Basic SSR
Visit: https://tradesense-gamma.vercel.app/test-ssr
- If this works, basic SSR is functioning
- If this fails, the issue is with the core setup

### 2. Check Environment Variables
Visit: https://tradesense-gamma.vercel.app/api/debug
- This will show all available environment variables
- Look for `VITE_API_URL` - it should be set to your Railway backend URL

### 3. Check Vercel Function Logs
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to "Functions" tab
4. Click on the failing function
5. Check the logs for specific error messages

## Most Common Causes & Solutions

### 1. Missing Environment Variables
**Problem**: `VITE_API_URL` is not set in Vercel

**Solution**:
1. Go to Vercel Dashboard → Settings → Environment Variables
2. Add:
   - `VITE_API_URL` = `https://tradesense-gateway-production.up.railway.app`
3. Redeploy

### 2. Backend Not Running
**Problem**: Railway backend is down or not deployed

**Solution**:
1. Check Railway dashboard
2. Ensure backend is deployed and running
3. Test backend directly: https://tradesense-gateway-production.up.railway.app/docs

### 3. CORS Not Configured
**Problem**: Backend rejecting frontend requests

**Solution**:
1. In Railway dashboard, set environment variable:
   - `CORS_ORIGINS_STR` = `https://tradesense-gamma.vercel.app,http://localhost:3001`
2. Railway will auto-redeploy

### 4. SSR Errors
**Problem**: Code accessing browser APIs during server-side rendering

**What we've already fixed**:
- Created SSR-safe API client that returns empty objects during SSR
- Protected all browser API access with checks
- Fixed auth subscription in layout

**If still failing**:
- Check function logs for specific error messages
- Look for "window is not defined" or similar errors

## Debugging Checklist

- [ ] Environment variables set in Vercel dashboard (not vercel.json)
- [ ] Backend is running on Railway
- [ ] CORS configured to allow Vercel domain
- [ ] /test-ssr page loads successfully
- [ ] /api/debug shows correct environment variables
- [ ] No "window/document is not defined" errors in logs
- [ ] No module import errors in logs

## Emergency Fixes

### If nothing else works:

1. **Force Fresh Deploy**:
   ```bash
   # Add a space to README and commit
   echo " " >> README.md
   git add . && git commit -m "Force redeploy" && git push
   ```

2. **Clear Vercel Cache**:
   - In Vercel dashboard, go to Settings → Advanced
   - Click "Purge Everything"

3. **Minimal Test**:
   - The `/test-ssr` page is a minimal SSR test
   - If this works but other pages don't, the issue is page-specific

## Getting Help

When asking for help, provide:
1. Error ID from the error page
2. Function logs from Vercel dashboard
3. Output from /api/debug endpoint
4. Which pages work vs fail