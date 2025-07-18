# 🚀 Vercel Frontend Deployment Guide

## Prerequisites Completed ✅
- Backend deployed to Railway: `https://tradesense-production.up.railway.app`
- Frontend configured with production environment variables
- Vercel CLI installed

## Step-by-Step Deployment

### 1. Login to Vercel
```bash
cd frontend
vercel login
```
Choose your preferred login method (GitHub recommended).

### 2. Deploy to Vercel
```bash
vercel --prod
```

When prompted:
- **Set up and deploy**: Yes
- **Which scope**: Choose your account
- **Link to existing project?**: No (create new)
- **Project name**: `tradesense` (or keep default)
- **Directory**: `./` (you're already in frontend)
- **Build settings**: Vercel will auto-detect Vite

### 3. Get Your Deployment URL
After deployment, you'll get a URL like:
- `https://tradesense-xxxxxxx.vercel.app`

### 4. Update Railway CORS Settings
```bash
# Go back to project root
cd ..

# Update CORS to allow your Vercel URL
railway variables set CORS_ORIGINS_STR="https://tradesense-xxxxxxx.vercel.app,https://tradesense.vercel.app"
```

### 5. Configure Custom Domain (tradesense.ai)
1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Domains
4. Add `tradesense.ai`
5. Follow DNS configuration instructions

### 6. Update CORS for Custom Domain
```bash
railway variables set CORS_ORIGINS_STR="https://tradesense.ai,https://www.tradesense.ai,https://tradesense.vercel.app"
```

## Environment Variables in Vercel

If you need to update environment variables:
1. Go to Vercel Dashboard → Project Settings → Environment Variables
2. Add/Update:
   - `VITE_API_BASE_URL`: `https://tradesense-production.up.railway.app`
   - `VITE_STRIPE_PUBLISHABLE_KEY`: Your Stripe public key
   - Any other VITE_ prefixed variables

## Verify Deployment

1. Visit your Vercel URL
2. Check browser console for any errors
3. Try logging in with test credentials
4. Test the feedback button functionality

## Troubleshooting

### CORS Errors
If you see CORS errors:
```bash
# Check current CORS settings
railway variables | grep CORS

# Update with all necessary origins
railway variables set CORS_ORIGINS_STR="https://tradesense.ai,https://www.tradesense.ai,https://tradesense.vercel.app,https://localhost:3000"
```

### API Connection Issues
1. Check backend health: `curl https://tradesense-production.up.railway.app/api/health`
2. Verify VITE_API_BASE_URL in Vercel environment settings
3. Check browser network tab for failed requests

## Next Steps

1. ✅ Frontend deployed to Vercel
2. ✅ CORS configured
3. 🔄 Configure custom domain
4. 🔄 Test feedback system
5. 🔄 Set up monitoring