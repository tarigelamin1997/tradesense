# 🚀 TradeSense Rapid Deployment Guide

## Goal: Deploy in < 6 Hours

This guide will help you deploy TradeSense quickly to start gathering real user feedback.

## 📋 Pre-Deployment Checklist

- [ ] GitHub account
- [ ] Railway account (https://railway.app)
- [ ] Vercel account (https://vercel.com)
- [ ] Stripe account (at least test mode)
- [ ] Domain name (optional, can use Railway/Vercel subdomains)

## 🔧 Step 1: Prepare Your Repository (15 min)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "🚀 Ready for deployment with feedback system"
   git push origin main
   ```

2. **Create Environment Files**
   ```bash
   # Backend (.env.production)
   cp src/backend/.env.example src/backend/.env.production
   
   # Frontend (.env.production)
   echo "VITE_API_BASE_URL=https://your-backend.railway.app" > frontend/.env.production
   ```

## 🚂 Step 2: Deploy Backend to Railway (30 min)

### A. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Select the `main` branch

### B. Add PostgreSQL & Redis

1. In Railway dashboard, click "New"
2. Select "Database" → "Add PostgreSQL"
3. Click "New" again → "Database" → "Add Redis"
4. Note the connection strings (Railway provides these automatically)

### C. Configure Environment Variables

Click on your backend service and add these variables:

```env
# Auto-provided by Railway
DATABASE_URL=(auto-filled by Railway)
REDIS_URL=(auto-filled by Railway)

# Security (MUST CHANGE!)
JWT_SECRET_KEY=your-super-secret-key-at-least-32-chars
SECRET_KEY=another-secret-key-for-sessions

# CORS (update after Vercel deployment)
CORS_ORIGINS_STR=https://your-app.vercel.app,http://localhost:3000

# Email (optional for MVP)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
ADMIN_EMAIL=your-email@example.com

# Stripe (test keys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Environment
ENVIRONMENT=production
```

### D. Configure Start Command

In Railway settings, set the start command:
```bash
cd src/backend && pip install -r requirements.txt -r requirements-prod.txt && python -m alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### E. Deploy

Railway will automatically deploy. Wait for the build to complete (~5 min).

## 🎨 Step 3: Deploy Frontend to Vercel (20 min)

### A. Install Vercel CLI

```bash
npm i -g vercel
```

### B. Deploy Frontend

```bash
cd frontend

# Create production env file
echo "VITE_API_BASE_URL=https://your-backend.railway.app" > .env.production

# Deploy to Vercel
vercel --prod
```

Follow the prompts:
- Set up and deploy: Y
- Which scope: (your account)
- Link to existing project: N
- Project name: tradesense
- Directory: ./
- Override settings: N

### C. Update Backend CORS

Go back to Railway and update `CORS_ORIGINS_STR` with your Vercel URL:
```env
CORS_ORIGINS_STR=https://tradesense.vercel.app
```

## 🔍 Step 4: Quick Health Check (10 min)

1. **Backend Health**
   ```bash
   curl https://your-backend.railway.app/health
   ```

2. **Frontend Loading**
   - Visit https://tradesense.vercel.app
   - Check browser console for errors

3. **Test Registration**
   - Create a test account
   - Verify you can log in

4. **Test Feedback System**
   - Click feedback button
   - Submit test feedback
   - Check admin panel at /admin/feedback

## 📊 Step 5: Essential Monitoring (15 min)

### A. Add Sentry (Error Tracking)

1. Create account at https://sentry.io
2. Create new project (FastAPI + SvelteKit)
3. Add to backend:
   ```python
   # In main.py
   import sentry_sdk
   sentry_sdk.init(dsn="your-sentry-dsn")
   ```
4. Add to frontend:
   ```javascript
   // In app.html
   <script src="https://browser.sentry-cdn.com/..."></script>
   ```

### B. Add Basic Analytics

1. Create Google Analytics account
2. Add to frontend `app.html`:
   ```html
   <!-- Google Analytics -->
   <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
   ```

## 🎯 Step 6: Go Live Checklist (10 min)

- [ ] Test user registration flow
- [ ] Test CSV upload with sample data
- [ ] Test one analytics feature
- [ ] Submit feedback through the feedback system
- [ ] Check feedback appears in admin panel
- [ ] Test Stripe subscription (use test card: 4242 4242 4242 4242)

## 🌟 Post-Deployment (Ongoing)

### Immediate Actions

1. **Share with Beta Users**
   ```
   Subject: TradeSense Beta - Need Your Feedback!
   
   Hi [Name],
   
   I've just launched TradeSense beta and would love your feedback!
   
   Access: https://tradesense.vercel.app
   Use code BETA50 for 50% off any plan
   
   Please use the feedback button (bottom-right) to report any issues.
   
   Thanks!
   ```

2. **Monitor Feedback Daily**
   - Check /admin/feedback every morning
   - Respond to critical issues within 1 hour
   - Update users when issues are resolved

3. **Quick Iterations**
   ```bash
   # Frontend updates (auto-deploy)
   git push origin main
   
   # Backend updates
   git push origin main  # Railway auto-deploys
   ```

### Week 1 Goals

- [ ] Get 10+ beta users
- [ ] Collect 50+ feedback submissions  
- [ ] Fix top 5 critical issues
- [ ] Add most requested feature
- [ ] Gather testimonials

## 🚨 Common Issues & Fixes

### CORS Errors
```env
# Add more origins if needed
CORS_ORIGINS_STR=https://tradesense.vercel.app,https://www.tradesense.com
```

### Database Connection Issues
```bash
# In Railway, redeploy with:
python -m alembic upgrade head
```

### Slow Cold Starts
- Upgrade to Railway Pro ($20/mo) for always-on
- Or use webhook to ping every 10 min

### Feedback Not Working
1. Check browser console for errors
2. Verify API endpoint is correct
3. Check CORS configuration
4. Test with curl:
   ```bash
   curl -X POST https://your-backend.railway.app/api/v1/feedback/submit \
     -H "Content-Type: application/json" \
     -d '{"type":"bug","severity":"low","title":"Test","description":"Test"}'
   ```

## 💰 Costs

**Monthly estimate for MVP:**
- Railway Hobby: $5 (includes $5 credit)
- Vercel Free: $0
- PostgreSQL: Included in Railway
- Redis: Included in Railway
- **Total: ~$5-20/month**

**Scaling costs (100+ users):**
- Railway Pro: $20/mo
- Vercel Pro: $20/mo
- SendGrid: $15/mo
- **Total: ~$55/mo**

## 🎉 You're Live!

Congratulations! TradeSense is now deployed and ready for users. Focus on:

1. **Getting users**: Share in trading communities
2. **Gathering feedback**: The feedback system will guide improvements
3. **Iterating fast**: Deploy fixes daily based on feedback
4. **Building community**: Create Discord/Slack for users

Remember: Perfect is the enemy of shipped. You can improve everything based on real user feedback! 🚀

## 📞 Need Help?

- Railway Discord: https://discord.gg/railway
- Vercel Discord: https://vercel.com/discord
- Create issue: https://github.com/yourusername/tradesense/issues

Happy deploying! 🎊