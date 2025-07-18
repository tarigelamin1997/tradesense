# Railway Deployment Configuration

## Current Setup
- Railway auto-deploys on push to `backup-2025-01-14-day3` branch
- GitHub Actions workflow DISABLED to prevent duplicate deployments
- Use `railway up --detach` only for manual deployments when needed

## To Avoid Duplicate Deployments
1. **For normal updates**: Just push to GitHub, Railway will auto-deploy
2. **For manual deploy**: Use `railway up --detach` (only when auto-deploy is disabled)
3. **Never**: Push to GitHub AND run railway up at the same time

## Re-enable GitHub Actions
If you want to use GitHub Actions instead of Railway auto-deploy:
1. Disable auto-deploy in Railway dashboard
2. Rename `.github/workflows/railway-deploy.yml.disabled` back to `.github/workflows/railway-deploy.yml`