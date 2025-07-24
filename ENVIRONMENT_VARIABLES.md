# Environment Variables Guide

## 🔒 Security First

**NEVER commit actual values of environment variables to the repository!**

This document describes the environment variables used by TradeSense. Copy `.env.example` to `.env` and fill in your actual values.

## Backend Environment Variables

### Core Configuration
```bash
# Application
ENVIRONMENT=development  # development, staging, production
DEBUG=true              # Set to false in production
SECRET_KEY=             # Generate with: openssl rand -hex 32
APP_NAME=TradeSense
APP_VERSION=1.0.0

# Database
DATABASE_URL=           # postgresql://user:password@host:port/dbname
DB_POOL_SIZE=20
DB_POOL_MAX_OVERFLOW=40

# Redis
REDIS_URL=              # redis://localhost:6379/0

# Security
MASTER_ENCRYPTION_KEY=  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=         # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### External Services
```bash
# AWS (if using)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=

# Email Service
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=noreply@tradesense.com

# Stripe (if using)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# OpenAI (if using AI features)
OPENAI_API_KEY=

# Sentry (error tracking)
SENTRY_DSN=
```

### Broker APIs
```bash
# Alpaca
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=

# Interactive Brokers
IB_ACCOUNT_ID=
IB_USERNAME=
IB_PASSWORD=

# TD Ameritrade
TD_API_KEY=
TD_REFRESH_TOKEN=
```

## Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000

# Application
VITE_APP_NAME=TradeSense
VITE_APP_VERSION=1.0.0
VITE_APP_URL=http://localhost:5173

# Analytics (optional)
VITE_GA_TRACKING_ID=
VITE_MIXPANEL_TOKEN=
VITE_SENTRY_DSN=

# Stripe (public key)
VITE_STRIPE_PUBLISHABLE_KEY=

# Feature Flags
VITE_FEATURE_AI_INSIGHTS=false
VITE_FEATURE_SOCIAL_TRADING=false
VITE_FEATURE_PAPER_TRADING=true
```

## Docker Environment Variables

Create a `.env.docker` file:

```bash
# Container Configuration
COMPOSE_PROJECT_NAME=tradesense
DOCKER_REGISTRY=
IMAGE_TAG=latest

# Volumes
DATA_PATH=./data
LOGS_PATH=./logs
```

## 🛡️ Best Practices

### 1. **Generate Strong Secrets**
```bash
# Generate secure random strings
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using openssl
openssl rand -hex 32
```

### 2. **Use Different Values Per Environment**
- Never use production secrets in development
- Rotate secrets regularly
- Use secret management services in production

### 3. **Secret Management Services**

#### AWS Secrets Manager
```python
import boto3

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='prod/tradesense/api-keys')
```

#### HashiCorp Vault
```python
import hvac

client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.v2.read_secret_version(path='tradesense/prod')
```

#### Azure Key Vault
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

client = SecretClient(vault_url="https://vault.vault.azure.net/", credential=DefaultAzureCredential())
secret = client.get_secret("api-key")
```

### 4. **Environment-Specific Files**
```
.env                # Default/development
.env.local          # Local overrides (gitignored)
.env.test           # Test environment
.env.staging        # Staging environment
.env.production     # Production (NEVER commit)
```

### 5. **Validation on Startup**
```python
# src/backend/core/config.py
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    
    @validator('SECRET_KEY')
    def secret_key_strength(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v
    
    class Config:
        env_file = ".env"
```

## 🚨 Security Checklist

- [ ] All `.env*` files are in `.gitignore`
- [ ] No secrets in code comments
- [ ] No default passwords in code
- [ ] Secrets are loaded from environment only
- [ ] Production secrets are in secure vault
- [ ] Secrets are rotated regularly
- [ ] Different secrets for each environment
- [ ] Audit log for secret access
- [ ] Encrypted secrets at rest
- [ ] Secure secret transmission

## 📚 Additional Resources

- [12 Factor App - Config](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)