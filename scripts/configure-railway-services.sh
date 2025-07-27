#!/bin/bash
# Configure Railway Services with Production Environment Variables
# This script helps set up all the necessary environment variables for each service

set -e

echo "🚀 TradeSense Railway Configuration Script"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Generate secure keys
generate_key() {
    openssl rand -hex 32
}

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found!${NC}"
    echo "Please install: npm install -g @railway/cli"
    exit 1
fi

# Generate shared secrets
echo "🔐 Generating secure keys..."
JWT_SECRET_KEY=$(generate_key)
MASTER_ENCRYPTION_KEY=$(generate_key)
WEBHOOK_SECRET=$(generate_key)

echo -e "${GREEN}✅ Keys generated${NC}"
echo ""

# Save keys for reference
cat > .railway-secrets <<EOF
# Generated on $(date)
# KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT
JWT_SECRET_KEY=$JWT_SECRET_KEY
MASTER_ENCRYPTION_KEY=$MASTER_ENCRYPTION_KEY
WEBHOOK_SECRET=$WEBHOOK_SECRET
EOF

echo "📝 Configuring services..."
echo ""

# Gateway Service Configuration
echo "1️⃣ Configuring Gateway Service..."
cat > gateway-env.txt <<EOF
# Gateway Service Environment Variables
PORT=8000
ENVIRONMENT=production
LOG_LEVEL=INFO

# Service URLs (update with your actual Railway URLs)
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app
ANALYTICS_SERVICE_URL=https://tradesense-analytics-production.up.railway.app
BILLING_SERVICE_URL=https://tradesense-billing-production.up.railway.app
MARKET_DATA_SERVICE_URL=https://tradesense-market-data-production.up.railway.app
AI_SERVICE_URL=https://tradesense-ai-production.up.railway.app

# CORS Configuration
CORS_ORIGINS_STR=https://tradesense.vercel.app,https://tradesense.ai,https://www.tradesense.ai

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (if using Railway Redis)
# REDIS_URL=redis://default:password@host:port

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
EOF

echo -e "${GREEN}✅ Gateway configuration ready${NC}"
echo ""

# Auth Service Configuration
echo "2️⃣ Configuring Auth Service..."
cat > auth-env.txt <<EOF
# Auth Service Environment Variables
PORT=8001
ENVIRONMENT=production
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
MASTER_ENCRYPTION_KEY=$MASTER_ENCRYPTION_KEY
SECRET_KEY=$(generate_key)

# Database (Railway will auto-inject DATABASE_URL)
# DATABASE_URL will be automatically set by Railway PostgreSQL

# Email Service (SendGrid recommended)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
# SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@tradesense.ai

# MFA Settings
ENABLE_MFA=true
MFA_ISSUER=TradeSense

# OAuth (optional)
# GOOGLE_CLIENT_ID=your-google-client-id
# GOOGLE_CLIENT_SECRET=your-google-client-secret
EOF

echo -e "${GREEN}✅ Auth configuration ready${NC}"
echo ""

# Trading Service Configuration
echo "3️⃣ Configuring Trading Service..."
cat > trading-env.txt <<EOF
# Trading Service Environment Variables
PORT=8002
ENVIRONMENT=production
LOG_LEVEL=INFO

# Service Dependencies
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256

# Database (Railway will auto-inject DATABASE_URL)
# DATABASE_URL will be automatically set by Railway PostgreSQL

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_EXTENSIONS=.csv,.xlsx,.xls
UPLOAD_BATCH_SIZE=1000

# Performance
ENABLE_CACHING=true
CACHE_TTL=300
EOF

echo -e "${GREEN}✅ Trading configuration ready${NC}"
echo ""

# Analytics Service Configuration
echo "4️⃣ Configuring Analytics Service..."
cat > analytics-env.txt <<EOF
# Analytics Service Environment Variables
PORT=8003
ENVIRONMENT=production
LOG_LEVEL=INFO

# Service Dependencies
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256

# Database (Railway will auto-inject DATABASE_URL)
# DATABASE_URL will be automatically set by Railway PostgreSQL

# Analytics Settings
CALCULATION_TIMEOUT=30
ENABLE_ADVANCED_ANALYTICS=true
CACHE_ANALYTICS_RESULTS=true
ANALYTICS_CACHE_TTL=3600
EOF

echo -e "${GREEN}✅ Analytics configuration ready${NC}"
echo ""

# Billing Service Configuration
echo "5️⃣ Configuring Billing Service..."
cat > billing-env.txt <<EOF
# Billing Service Environment Variables
PORT=8004
ENVIRONMENT=production
LOG_LEVEL=INFO

# Service Dependencies
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
WEBHOOK_SECRET=$WEBHOOK_SECRET

# Stripe Configuration
# STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
# STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_SUCCESS_URL=https://tradesense.ai/payment-success
STRIPE_CANCEL_URL=https://tradesense.ai/pricing

# Pricing (create in Stripe Dashboard)
# STRIPE_PRICE_STARTER_MONTHLY=price_starter_monthly_id
# STRIPE_PRICE_PROFESSIONAL_MONTHLY=price_professional_monthly_id
# STRIPE_PRICE_TEAM_MONTHLY=price_team_monthly_id
EOF

echo -e "${GREEN}✅ Billing configuration ready${NC}"
echo ""

# Market Data Service Configuration
echo "6️⃣ Configuring Market Data Service..."
cat > market-data-env.txt <<EOF
# Market Data Service Environment Variables
PORT=8005
ENVIRONMENT=production
LOG_LEVEL=INFO

# Service Dependencies
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256

# Market Data APIs
ALPHA_VANTAGE_API_KEY=demo
MARKET_DATA_TIMEOUT=10
MARKET_DATA_CACHE_MINUTES=15

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
EOF

echo -e "${GREEN}✅ Market Data configuration ready${NC}"
echo ""

# AI Service Configuration
echo "7️⃣ Configuring AI Service..."
cat > ai-env.txt <<EOF
# AI Service Environment Variables
PORT=8006
ENVIRONMENT=production
LOG_LEVEL=INFO

# Service Dependencies
AUTH_SERVICE_URL=https://tradesense-auth-production.up.railway.app
TRADING_SERVICE_URL=https://tradesense-trading-production.up.railway.app

# Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256

# AI Configuration
# OPENAI_API_KEY=your-openai-api-key
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1000
ENABLE_AI_FEATURES=true
EOF

echo -e "${GREEN}✅ AI configuration ready${NC}"
echo ""

# Create deployment helper script
cat > deploy-configs.sh <<'DEPLOY_EOF'
#!/bin/bash
# Deploy configurations to Railway

echo "🚀 Deploying configurations to Railway..."
echo ""

# Function to set variables for a service
set_service_vars() {
    local service=$1
    local env_file=$2
    
    echo "Configuring $service..."
    
    # Read env file and set variables
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^#.*$ ]] || [[ -z $key ]] && continue
        
        # Remove quotes if present
        value="${value%\"}"
        value="${value#\"}"
        
        # Set the variable
        railway variables set "$key=$value" --service "$service"
    done < "$env_file"
    
    echo "✅ $service configured"
    echo ""
}

# Deploy each service configuration
set_service_vars "gateway" "gateway-env.txt"
set_service_vars "auth" "auth-env.txt"
set_service_vars "trading" "trading-env.txt"
set_service_vars "analytics" "analytics-env.txt"
set_service_vars "billing" "billing-env.txt"
set_service_vars "market-data" "market-data-env.txt"
set_service_vars "ai" "ai-env.txt"

echo "🎉 All services configured!"
DEPLOY_EOF

chmod +x deploy-configs.sh

echo ""
echo "=================================="
echo -e "${GREEN}✅ Configuration files created!${NC}"
echo "=================================="
echo ""
echo "📁 Files created:"
echo "  - gateway-env.txt"
echo "  - auth-env.txt"
echo "  - trading-env.txt"
echo "  - analytics-env.txt"
echo "  - billing-env.txt"
echo "  - market-data-env.txt"
echo "  - ai-env.txt"
echo "  - .railway-secrets (KEEP SECURE!)"
echo "  - deploy-configs.sh"
echo ""
echo "🚀 Next steps:"
echo "  1. Review and update the service URLs in each env file"
echo "  2. Add any missing API keys (Stripe, SendGrid, etc.)"
echo "  3. Run: ./deploy-configs.sh to apply configurations"
echo "  4. Add PostgreSQL to each service in Railway dashboard"
echo ""
echo "⚠️  IMPORTANT:"
echo "  - Keep .railway-secrets file secure"
echo "  - Update CORS origins if needed"
echo "  - Set production API keys before going live"
echo ""