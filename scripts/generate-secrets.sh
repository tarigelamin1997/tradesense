#!/bin/bash

# Generate secure secrets for production deployment

echo "🔐 Generating secure secrets for TradeSense production deployment..."
echo ""

# Generate JWT Secret
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT_SECRET_KEY=$JWT_SECRET"
echo ""

# Generate Session Secret
SESSION_SECRET=$(openssl rand -hex 32)
echo "SECRET_KEY=$SESSION_SECRET"
echo ""

echo "✅ Secrets generated successfully!"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Copy these secrets to your Railway environment variables"
echo "2. Never commit these to git"
echo "3. Store them securely in a password manager"
echo "4. Use different secrets for each environment (dev, staging, prod)"