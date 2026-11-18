# TradeSense Deployment Instructions

## Production Deployment Steps

### Prerequisites
- Railway CLI installed and logged in
- Vercel CLI installed and logged in  
- Node.js 20+ installed
- Git repository up to date

### 1. Deploy Backend Services to Railway

First, link each service to Railway:

```bash
# For each service, run:
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

### 2. Set Environment Variables in Railway

For each service, set these variables in Railway dashboard:

```bash
# Security
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true
JWT_SECRET_KEY=<generate-secure-key>
MASTER_ENCRYPTION_KEY=<generate-secure-key>

# Service-specific
SERVICE_NAME=<service-name>
NODE_ENV=production
```

### 3. Deploy Frontend to Vercel

```bash
cd frontend

# Install dependencies
npm install

# Build
npm run build

# Deploy manually via Vercel dashboard:
1. Go to https://vercel.com/new
2. Import the tradesense repository
3. Set the root directory to "frontend"
4. Set Framework Preset to "SvelteKit"
5. Add environment variables:
   - PUBLIC_API_URL=https://tradesense-gateway-production.up.railway.app
   - PUBLIC_WS_URL=wss://tradesense-gateway-production.up.railway.app
6. Deploy
```

### 4. Configure Domain & SSL

#### Railway:
- Each service gets a unique URL: https://tradesense-<service>-production.up.railway.app
- SSL is automatically configured

#### Vercel:
- Frontend URL: https://your-app.vercel.app
- Add custom domain in Vercel dashboard
- SSL is automatically configured

### 5. Post-Deployment Verification

```bash
# Check all services health
./scripts/monitor-railway-health.sh

# Test authentication
curl https://tradesense-gateway-production.up.railway.app/health

# Test frontend
curl https://your-app.vercel.app
```

### 6. Database Migrations

Run migrations for each service:

```bash
# Gateway service
railway run --service gateway "alembic upgrade head"

# Auth service  
railway run --service auth "alembic upgrade head"

# Trading service
railway run --service trading "alembic upgrade head"

# Analytics service
railway run --service analytics "alembic upgrade head"

# Billing service
railway run --service billing "alembic upgrade head"
```

### 7. Enable Monitoring (Optional)

If using Datadog:
```bash
# Set for each service
railway variables --set DD_API_KEY=<your-api-key> --service <service-name>
```

### 8. Setup Backups

```bash
# Run backup script
./scripts/automated-backup-config.sh
```

## Troubleshooting

### Railway Issues
- Check logs: `railway logs --service <service-name>`
- Restart service: `railway restart --service <service-name>`
- Check environment variables: `railway variables --service <service-name>`

### Vercel Issues
- Check build logs in Vercel dashboard
- Ensure all environment variables are set
- Verify framework preset is SvelteKit
- Check that root directory is set to "frontend"

### CORS Issues
- Verify gateway CORS configuration includes your frontend URL
- Check that API_URL in frontend points to correct gateway URL

## Rollback Procedure

If issues occur:
```bash
# Railway
railway rollback --service <service-name>

# Vercel
# Use Vercel dashboard to rollback to previous deployment
```

## Security Checklist

- [ ] All services have unique JWT secrets
- [ ] Master encryption keys are set
- [ ] Security headers enabled
- [ ] Rate limiting active  
- [ ] Audit logging configured
- [ ] Database passwords are strong
- [ ] HTTPS enforced on all endpoints
- [ ] CORS properly configured

## Support

For issues:
1. Check service logs
2. Verify environment variables
3. Test health endpoints
4. Review deployment summaries in deployments/ directory