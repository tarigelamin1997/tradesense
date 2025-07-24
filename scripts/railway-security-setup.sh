#!/bin/bash

# Railway Security Setup Script
# This script implements security best practices for Railway deployments

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v gh >/dev/null 2>&1; then
        error "GitHub CLI (gh) is not installed"
        echo "Install with: brew install gh (macOS) or see https://cli.github.com"
        exit 1
    fi
    
    if ! gh auth status >/dev/null 2>&1; then
        error "Not authenticated with GitHub"
        echo "Run: gh auth login"
        exit 1
    fi
    
    if ! command -v railway >/dev/null 2>&1; then
        warning "Railway CLI not installed"
        echo "Install with: npm install -g @railway/cli"
    fi
    
    success "Prerequisites check passed"
}

# Apply GitHub branch protection
apply_branch_protection() {
    log "Applying branch protection rules..."
    
    REPO="tradesense/tradesense"  # Update with your repo
    
    # Main branch protection
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        /repos/${REPO}/branches/main/protection \
        --input - <<EOF
{
    "required_status_checks": {
        "strict": true,
        "contexts": ["test", "security-scan", "build"]
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews": true,
        "require_code_owner_reviews": true
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false,
    "required_conversation_resolution": true
}
EOF
    
    success "Branch protection enabled for main"
}

# Enable GitHub security features
enable_security_features() {
    log "Enabling GitHub security features..."
    
    REPO="tradesense/tradesense"
    
    # Enable Dependabot
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        /repos/${REPO}/vulnerability-alerts || warning "Dependabot may already be enabled"
    
    # Enable automated security fixes
    gh api \
        --method PUT \
        -H "Accept: application/vnd.github+json" \
        /repos/${REPO}/automated-security-fixes || warning "Automated fixes may already be enabled"
    
    success "Security features enabled"
}

# Generate secure secrets
generate_secrets() {
    log "Generating secure secrets..."
    
    # Generate JWT secret
    JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
    echo "JWT_SECRET_KEY=${JWT_SECRET}" > .env.railway.secrets
    
    # Generate API keys
    INTERNAL_API_KEY=$(openssl rand -hex 32)
    echo "INTERNAL_API_KEY=${INTERNAL_API_KEY}" >> .env.railway.secrets
    
    # Generate encryption key
    ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n')
    echo "ENCRYPTION_KEY=${ENCRYPTION_KEY}" >> .env.railway.secrets
    
    success "Secrets generated in .env.railway.secrets"
    warning "⚠️  IMPORTANT: Update these in Railway dashboard and delete this file!"
}

# Create security headers middleware
create_security_headers() {
    log "Creating security headers configuration..."
    
    cat > services/gateway/src/middleware/security-headers.ts << 'EOF'
import { FastifyReply, FastifyRequest } from 'fastify';

export const securityHeaders = async (
  request: FastifyRequest,
  reply: FastifyReply
) => {
  // Security headers
  reply.header('X-Content-Type-Options', 'nosniff');
  reply.header('X-Frame-Options', 'DENY');
  reply.header('X-XSS-Protection', '1; mode=block');
  reply.header('Referrer-Policy', 'strict-origin-when-cross-origin');
  reply.header('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  
  // HSTS (only in production)
  if (process.env.NODE_ENV === 'production') {
    reply.header(
      'Strict-Transport-Security',
      'max-age=31536000; includeSubDomains; preload'
    );
  }
  
  // CSP
  const cspDirectives = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' https://api.stripe.com wss://tradesense-gateway-production.up.railway.app",
    "frame-src https://js.stripe.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'"
  ].join('; ');
  
  reply.header('Content-Security-Policy', cspDirectives);
};

// Rate limiting configuration
export const rateLimitConfig = {
  global: {
    max: 100, // requests
    timeWindow: '1 minute'
  },
  auth: {
    max: 5,
    timeWindow: '15 minutes'
  },
  api: {
    max: 1000,
    timeWindow: '1 hour'
  }
};
EOF
    
    success "Security headers middleware created"
}

# Create Railway security audit script
create_audit_script() {
    log "Creating security audit script..."
    
    cat > scripts/railway-security-audit.sh << 'EOF'
#!/bin/bash

echo "🔐 Railway Security Audit"
echo "========================"

# Check for exposed secrets in environment
echo -e "\n📋 Checking for exposed secrets..."

SERVICES=(
    "gateway"
    "auth"
    "trading"
    "analytics"
    "market-data"
    "billing"
    "ai"
)

for service in "${SERVICES[@]}"; do
    echo -e "\nService: $service"
    
    # Check for common secret patterns
    if command -v railway >/dev/null 2>&1; then
        railway variables -s "$service" 2>/dev/null | grep -E "(SECRET|KEY|TOKEN|PASSWORD)" | \
        awk '{print $1}' | while read -r var; do
            echo "  - $var: [REDACTED]"
        done
    else
        echo "  - Railway CLI not installed"
    fi
done

echo -e "\n🔍 Security Recommendations:"
echo "1. Rotate all secrets quarterly"
echo "2. Use Railway's secret management"
echo "3. Enable 2FA for all team members"
echo "4. Regularly audit access logs"
echo "5. Implement API rate limiting"
echo "6. Use HTTPS everywhere"
echo "7. Implement CORS properly"
echo "8. Add security headers"
EOF
    
    chmod +x scripts/railway-security-audit.sh
    success "Security audit script created"
}

# Create CORS configuration
create_cors_config() {
    log "Creating CORS configuration..."
    
    cat > services/gateway/src/config/cors.ts << 'EOF'
export const corsConfig = {
  origin: (origin: string, callback: Function) => {
    const allowedOrigins = [
      'https://tradesense.vercel.app',
      'https://tradesense.ai',
      'https://www.tradesense.ai'
    ];
    
    // Allow requests with no origin (mobile apps, Postman)
    if (!origin) return callback(null, true);
    
    // Development
    if (process.env.NODE_ENV === 'development') {
      allowedOrigins.push('http://localhost:3000');
      allowedOrigins.push('http://localhost:5173');
    }
    
    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Request-ID',
    'X-API-Key'
  ],
  exposedHeaders: ['X-Request-ID'],
  maxAge: 86400 // 24 hours
};
EOF
    
    success "CORS configuration created"
}

# Create environment validator
create_env_validator() {
    log "Creating environment validator..."
    
    cat > services/gateway/src/config/validate-env.ts << 'EOF'
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']),
  PORT: z.string().transform(Number).default('8000'),
  
  // Service URLs
  AUTH_SERVICE_URL: z.string().url(),
  TRADING_SERVICE_URL: z.string().url(),
  ANALYTICS_SERVICE_URL: z.string().url(),
  MARKET_DATA_SERVICE_URL: z.string().url(),
  BILLING_SERVICE_URL: z.string().url(),
  AI_SERVICE_URL: z.string().url(),
  
  // Security
  JWT_SECRET_KEY: z.string().min(32),
  INTERNAL_API_KEY: z.string().min(32),
  
  // Optional
  SENTRY_DSN: z.string().url().optional(),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export type Env = z.infer<typeof envSchema>;

export function validateEnv(): Env {
  try {
    return envSchema.parse(process.env);
  } catch (error) {
    console.error('❌ Invalid environment variables:', error);
    process.exit(1);
  }
}
EOF
    
    success "Environment validator created"
}

# Create security checklist
create_security_checklist() {
    log "Creating security checklist..."
    
    cat > RAILWAY_SECURITY_CHECKLIST.md << 'EOF'
# Railway Security Checklist

## ✅ Authentication & Authorization
- [ ] JWT tokens expire after appropriate time
- [ ] Refresh tokens are rotated
- [ ] API keys are unique per service
- [ ] Role-based access control implemented
- [ ] Password complexity requirements enforced

## ✅ Data Protection
- [ ] All data encrypted in transit (HTTPS)
- [ ] Sensitive data encrypted at rest
- [ ] PII is properly handled
- [ ] Database connections use SSL
- [ ] Backups are encrypted

## ✅ API Security
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens for state-changing operations

## ✅ Infrastructure Security
- [ ] All secrets in Railway variables
- [ ] No hardcoded credentials
- [ ] Regular secret rotation
- [ ] Least privilege access
- [ ] Service-to-service authentication

## ✅ Monitoring & Logging
- [ ] Security events logged
- [ ] Anomaly detection configured
- [ ] Failed authentication attempts tracked
- [ ] Audit logs maintained
- [ ] Real-time alerts configured

## ✅ Compliance
- [ ] GDPR compliance (if applicable)
- [ ] PCI DSS compliance (for payments)
- [ ] Data retention policies
- [ ] Privacy policy updated
- [ ] Terms of service updated

## ✅ Incident Response
- [ ] Incident response plan documented
- [ ] Contact list maintained
- [ ] Rollback procedures tested
- [ ] Communication plan ready
- [ ] Post-mortem process defined
EOF
    
    success "Security checklist created"
}

# Main execution
main() {
    log "🔐 Starting Railway security setup..."
    
    check_prerequisites
    
    # GitHub security
    log "Configuring GitHub security..."
    apply_branch_protection
    enable_security_features
    
    # Generate secrets
    generate_secrets
    
    # Create security configurations
    log "Creating security configurations..."
    create_security_headers
    create_cors_config
    create_env_validator
    
    # Create helper scripts
    create_audit_script
    create_security_checklist
    
    success "✨ Security setup complete!"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Update secrets in Railway dashboard using .env.railway.secrets"
    echo "2. Delete .env.railway.secrets file"
    echo "3. Run security audit: ./scripts/railway-security-audit.sh"
    echo "4. Review RAILWAY_SECURITY_CHECKLIST.md"
    echo "5. Implement security headers in Gateway service"
    echo "6. Test CORS configuration"
    echo "7. Enable 2FA on Railway and GitHub"
    echo ""
    warning "Remember: Security is not a one-time setup, it's an ongoing process!"
}

# Run main function
main "$@"