# Frontend Deployment to Vercel

## Prerequisites
- Vercel account (create at https://vercel.com)
- Git repository with the frontend code

## Deployment Steps

### 1. Prepare the Frontend

First, clean the build directory:
```bash
cd /home/tarigelamin/Desktop/tradesense/frontend
sudo rm -rf .svelte-kit
npm install
```

### 2. Deploy to Vercel (Web Interface)

1. Go to https://vercel.com
2. Click "Add New..." → "Project"
3. Import your Git repository
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

5. Add Environment Variables:
   ```
   VITE_API_URL=https://tradesense-gateway-production.up.railway.app
   ```

6. Click "Deploy"

### 3. Alternative: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd /home/tarigelamin/Desktop/tradesense/frontend
vercel

# Follow the prompts and add the environment variable when asked
```

## Post-Deployment Steps

### 1. Update CORS in Backend

Once deployed, you'll get a URL like `https://your-app.vercel.app`. Update the Gateway service CORS:

1. Go to Railway Gateway service
2. Add environment variable:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:5173
   ```
3. Redeploy Gateway service

### 2. Configure Custom Domain (Optional)

1. In Vercel project settings → Domains
2. Add `tradesense.ai`
3. Follow DNS configuration instructions

## Environment Variables Reference

- `VITE_API_URL`: The backend API URL (Gateway service)
- Future: `VITE_STRIPE_PUBLIC_KEY` for Stripe integration

## Troubleshooting

If you see CORS errors:
1. Check Gateway service logs
2. Ensure ALLOWED_ORIGINS is set correctly
3. Verify the frontend is sending proper headers

## Local Testing Before Deployment

```bash
# Test with production API
VITE_API_URL=https://tradesense-gateway-production.up.railway.app npm run dev
```

## Important Files

- `/frontend/vercel.json` - Vercel configuration
- `/frontend/.env` - Local environment variables (not committed)
- `/frontend/src/lib/api/client.ts` - API client configuration