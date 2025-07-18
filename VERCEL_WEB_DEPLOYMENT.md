# 🌐 Deploy to Vercel via Web Interface

## Quick Deploy from GitHub (No CLI needed)

### 1. Import Project
1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Connect your GitHub account if not already connected
4. Search for `tradesense` repository
5. Select the repository

### 2. Configure Project
When importing, set these configurations:

**Framework Preset**: Vite
**Root Directory**: `frontend`
**Build Command**: `npm run build`
**Output Directory**: `dist`
**Install Command**: `npm install`

### 3. Environment Variables
Add these environment variables in Vercel dashboard:

```
VITE_API_BASE_URL=https://tradesense-production.up.railway.app
VITE_APP_URL=https://tradesense.vercel.app
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_public_key
```

### 4. Deploy
Click "Deploy" and wait for the build to complete.

## After Deployment

### Update CORS in Railway
Once you get your Vercel URL (e.g., `https://tradesense-abc123.vercel.app`):

```bash
cd /home/tarigelamin/Desktop/tradesense
./update-cors.sh https://tradesense-abc123.vercel.app
```

### Add Custom Domain
1. In Vercel Dashboard → Your Project → Settings → Domains
2. Add `tradesense.ai`
3. Configure DNS in GoDaddy:
   - Add CNAME record: `www` → `cname.vercel-dns.com`
   - Add A record: `@` → `76.76.21.21`

## Advantages of Web Deploy
- No CLI authentication issues
- Automatic deployments on git push
- Easy environment variable management
- Built-in analytics and logs