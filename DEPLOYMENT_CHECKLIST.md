# 🚀 TradeSense Deployment Checklist

Follow this checklist to deploy TradeSense to production. Expected time: 4-6 hours.

## 📋 Pre-Deployment (30 min)

### Accounts Setup
- [ ] GitHub account (code already there)
- [ ] Railway account - https://railway.app
- [ ] Vercel account - https://vercel.com  
- [ ] Stripe account - https://stripe.com (at least test mode)
- [ ] SendGrid account (optional) - https://sendgrid.com

### Local Preparation
- [ ] Generate secure secrets:
  ```bash
  ./scripts/generate-secrets.sh
  ```
- [ ] Save secrets in password manager
- [ ] Prepare environment variables list

## 🚂 Backend Deployment - Railway (45 min)

### 1. Create Railway Project
- [ ] Go to https://railway.app/new
- [ ] Click "Deploy from GitHub repo"
- [ ] Authorize Railway to access your GitHub
- [ ] Select your TradeSense repository
- [ ] Choose `main` branch

### 2. Add Databases
- [ ] Click "New" → "Database" → "Add PostgreSQL"
- [ ] Click "New" → "Database" → "Add Redis"
- [ ] Wait for provisioning (~2 min)

### 3. Configure Environment Variables
Click on your backend service → "Variables" → "RAW Editor" and paste:

```env
# These are auto-provided by Railway:
# DATABASE_URL=...
# REDIS_URL=...

# Security (from generate-secrets.sh)
JWT_SECRET_KEY=paste-your-generated-jwt-secret
SECRET_KEY=paste-your-generated-session-secret

# CORS (update after Vercel deployment)
CORS_ORIGINS_STR=http://localhost:3000

# Email (optional for MVP)
ADMIN_EMAIL=your-email@example.com

# Stripe Test Keys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Environment
ENVIRONMENT=production
PORT=8000
```

### 4. Deploy Backend
- [ ] Railway will auto-deploy after adding variables
- [ ] Check logs for "Uvicorn running on"
- [ ] Test health endpoint:
  ```bash
  curl https://your-app.railway.app/health
  ```
- [ ] Note your backend URL: `https://your-app.railway.app`

## 🎨 Frontend Deployment - Vercel (30 min)

### 1. Prepare Frontend Environment
- [ ] Create frontend/.env.production:
  ```bash
  echo "VITE_API_BASE_URL=https://your-backend.railway.app" > frontend/.env.production
  ```

### 2. Deploy to Vercel
```bash
cd frontend
npx vercel --prod
```

Follow prompts:
- [ ] Set up and deploy? **Y**
- [ ] Which scope? **(your account)**
- [ ] Link to existing project? **N**
- [ ] Project name? **tradesense**
- [ ] Directory? **./**
- [ ] Override settings? **N**

### 3. Update Backend CORS
- [ ] Go back to Railway
- [ ] Update CORS_ORIGINS_STR:
  ```env
  CORS_ORIGINS_STR=https://tradesense.vercel.app
  ```
- [ ] Railway will auto-redeploy

## 🔍 Verification (15 min)

### Backend Health Checks
- [ ] API Health: `https://your-backend.railway.app/health`
- [ ] API Docs: `https://your-backend.railway.app/api/docs`
- [ ] Database connection working
- [ ] Redis connection working

### Frontend Checks
- [ ] Homepage loads: `https://tradesense.vercel.app`
- [ ] No console errors
- [ ] Login/Register pages accessible
- [ ] API connection working (check Network tab)

### Feature Testing
- [ ] Create test account
- [ ] Log in successfully
- [ ] Test feedback button (bottom-right)
- [ ] Submit test feedback
- [ ] Check admin panel: `/admin/feedback`

## 📊 Monitoring Setup (15 min)

### Sentry (Error Tracking)
- [ ] Create account at https://sentry.io
- [ ] Create new project (FastAPI + SvelteKit)
- [ ] Add DSN to Railway env:
  ```env
  SENTRY_DSN=https://...@sentry.io/...
  ```
- [ ] Add to Vercel env:
  ```env
  VITE_SENTRY_DSN=https://...@sentry.io/...
  ```

### Google Analytics
- [ ] Create GA4 property
- [ ] Add to Vercel env:
  ```env
  VITE_GA_MEASUREMENT_ID=G-XXXXXXXXXX
  ```

## 🎯 Go-Live Tasks (10 min)

### Essential Tests
- [ ] User registration flow
- [ ] CSV upload with sample data
- [ ] View one analytics chart
- [ ] Submit feedback
- [ ] Stripe test payment (4242 4242 4242 4242)

### DNS Setup (Optional)
- [ ] Add custom domain in Vercel
- [ ] Update DNS records
- [ ] Add domain to CORS_ORIGINS_STR

### Final Checks
- [ ] Remove any test data
- [ ] Verify error handling works
- [ ] Test on mobile device
- [ ] Check loading speeds

## 📧 Launch Communications

### Beta Announcement Email
```
Subject: 🚀 TradeSense Beta is Live!

Hi [Name],

I'm excited to announce that TradeSense is now in beta!

🔗 Access: https://tradesense.vercel.app
🎁 Beta Offer: Use code BETA50 for 50% off any plan
📝 Feedback: Click the button in bottom-right corner

As a beta user, your feedback is invaluable. Please report any issues or suggestions using our in-app feedback system.

Thanks for being an early supporter!

[Your name]
```

### Social Media Post
```
🚀 Excited to launch TradeSense Beta!

A modern trading journal that helps you:
📊 Track performance
🧠 Identify patterns  
💡 Improve decisions

Beta users get 50% off with code BETA50

Try it: tradesense.vercel.app

#trading #fintech #startup
```

## 🔄 Post-Deployment (Ongoing)

### Daily Tasks
- [ ] Check feedback dashboard
- [ ] Monitor Sentry errors
- [ ] Review user signups
- [ ] Deploy fixes as needed

### Weekly Tasks
- [ ] Analyze feedback patterns
- [ ] Plan feature iterations
- [ ] Send update email to users
- [ ] Review performance metrics

## 🎉 Congratulations!

TradeSense is now live! Remember:
- Monitor feedback closely
- Iterate based on user input
- Deploy updates frequently
- Build in public

Need help? Check the [RAPID_DEPLOYMENT_GUIDE.md](./RAPID_DEPLOYMENT_GUIDE.md) for detailed instructions.

Happy launching! 🚀