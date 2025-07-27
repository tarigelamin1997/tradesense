#!/bin/bash
# Set up backup service environment variables in Railway

# S3 Configuration
railway variables set S3_BUCKET="${S3_BUCKET}" --service backup
railway variables set AWS_REGION="${AWS_REGION}" --service backup
railway variables set AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" --service backup
railway variables set AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" --service backup

# Get database URLs from other services
for service in auth trading analytics billing ai; do
    DB_URL=$(railway variables get DATABASE_URL --service "tradesense-${service}")
    railway variables set "DATABASE_URL_${service^^}=${DB_URL}" --service backup
done

# Monitoring webhook
railway variables set MONITORING_WEBHOOK="${MONITORING_WEBHOOK}" --service backup

echo "✅ Backup service environment configured"
