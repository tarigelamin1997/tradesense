# Vercel Web Deployment Guide for TradeSense Frontend

## Prerequisites
1. Create a Vercel account at https://vercel.com/signup
2. Your Railway backend should be running at: https://tradesense-production.up.railway.app

## Step 1: Import Project to Vercel

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your GitHub repository: `tarigelamin1997/tradesense`
4. Click "Import"

## Step 2: Configure Build Settings

When prompted, use these settings:

- **Framework Preset**: Vite
- **Root Directory**: `frontend` (click "Edit" and change to `frontend`)
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`

## Step 3: Set Environment Variables

Click on "Environment Variables" and add:

```
VITE_API_BASE_URL = https://tradesense-production.up.railway.app
VITE_APP_URL = https://tradesense.vercel.app
VITE_APP_NAME = TradeSense
VITE_APP_VERSION = 2.0.0
```

## Step 4: Deploy

1. Click "Deploy"
2. Wait for the build to complete (usually 2-3 minutes)
3. Your app will be available at: https://tradesense-[your-username].vercel.app

## Step 5: Update Railway Backend CORS

Once deployed, you need to add your Vercel URL to Railway's CORS settings:

1. Go to Railway dashboard
2. Select your backend service
3. Go to Variables tab
4. Update `CORS_ORIGINS` to include your Vercel URL:
   ```
   CORS_ORIGINS=https://tradesense-[your-username].vercel.app,https://tradesense.vercel.app,http://localhost:3000,http://localhost:5173
   ```

## Step 6: Configure Custom Domain (Optional)

1. In Vercel dashboard, go to your project
2. Click "Settings" → "Domains"
3. Add your domain: `tradesense.ai`
4. Follow Vercel's instructions to update your DNS settings

## Step 7: Test Your Deployment

1. Visit your Vercel URL
2. Try to register a new account
3. Test the feedback feature
4. Check that API calls are working

## Troubleshooting

### If you see CORS errors:
- Make sure Railway backend has your Vercel URL in CORS_ORIGINS
- Restart the Railway service after updating environment variables

### If API calls fail:
- Check that Railway backend is running (visit https://tradesense-production.up.railway.app/health)
- Verify VITE_API_BASE_URL is set correctly in Vercel

### If build fails:
- Check the build logs in Vercel dashboard
- Make sure all dependencies are in package.json
- Try building locally first: `cd frontend && npm install && npm run build`

## Next Steps

After successful deployment:
1. Monitor the application for any errors
2. Set up error tracking (optional)
3. Configure analytics (optional)
4. Enable Vercel Analytics for performance monitoring