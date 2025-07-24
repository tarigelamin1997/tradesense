#!/bin/bash

# External Secrets Operator Setup Script
# This script installs and configures the External Secrets Operator

set -e

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
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed!"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        error "helm is not installed!"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster!"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Install External Secrets Operator
install_external_secrets() {
    log "Installing External Secrets Operator..."
    
    # Add helm repository
    helm repo add external-secrets https://charts.external-secrets.io
    helm repo update
    
    # Create namespace
    kubectl apply -f namespace.yaml
    
    # Install using helm with custom values
    helm upgrade --install external-secrets \
        external-secrets/external-secrets \
        -n external-secrets \
        --create-namespace \
        --wait \
        --timeout 5m \
        --values <(kubectl get configmap external-secrets-operator-values -n external-secrets -o jsonpath='{.data.values\.yaml}' 2>/dev/null || echo "replicaCount: 2")
    
    success "External Secrets Operator installed"
}

# Configure AWS SecretStore
configure_aws_secretstore() {
    log "Configuring AWS SecretStore..."
    
    # Check if AWS credentials are configured
    if [[ -z "${AWS_ACCOUNT_ID}" ]]; then
        warning "AWS_ACCOUNT_ID not set. Please update the SecretStore configuration with your AWS account ID."
    else
        # Update the service account annotation with actual account ID
        sed -i "s/ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" aws-secret-store.yaml
    fi
    
    # Apply AWS SecretStore configuration
    kubectl apply -f aws-secret-store.yaml
    
    success "AWS SecretStore configured"
}

# Configure Vault SecretStore (optional)
configure_vault_secretstore() {
    log "Configuring Vault SecretStore (optional)..."
    
    read -p "Do you want to configure HashiCorp Vault integration? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Apply Vault SecretStore configuration
        kubectl apply -f vault-secret-store.yaml
        success "Vault SecretStore configured"
    else
        log "Skipping Vault configuration"
    fi
}

# Create External Secrets
create_external_secrets() {
    log "Creating External Secrets..."
    
    # Apply external secrets
    kubectl apply -f external-secrets.yaml
    
    # Wait for secrets to be created
    log "Waiting for secrets to sync..."
    sleep 10
    
    # Check secret status
    kubectl get externalsecrets -n tradesense
    
    success "External Secrets created"
}

# Update existing deployments
update_deployments() {
    log "Updating existing deployments to use External Secrets..."
    
    # Patch backend deployment to remove hardcoded secret refs
    kubectl patch deployment backend -n tradesense --type='json' -p='[
        {"op": "replace", "path": "/spec/template/spec/containers/0/env", "value": [
            {"name": "DATABASE_URL", "valueFrom": {"secretKeyRef": {"name": "tradesense-secrets", "key": "DATABASE_URL"}}},
            {"name": "REDIS_URL", "valueFrom": {"secretKeyRef": {"name": "tradesense-secrets", "key": "REDIS_URL"}}},
            {"name": "JWT_SECRET_KEY", "valueFrom": {"secretKeyRef": {"name": "tradesense-secrets", "key": "JWT_SECRET_KEY"}}},
            {"name": "STRIPE_API_KEY", "valueFrom": {"secretKeyRef": {"name": "tradesense-secrets", "key": "STRIPE_API_KEY"}}},
            {"name": "STRIPE_WEBHOOK_SECRET", "valueFrom": {"secretKeyRef": {"name": "tradesense-secrets", "key": "STRIPE_WEBHOOK_SECRET"}}},
            {"name": "SENTRY_DSN", "valueFrom": {"secretKeyRef": {"name": "tradesense-secrets", "key": "SENTRY_DSN"}}}
        ]}
    ]' 2>/dev/null || warning "Backend deployment update skipped (may not exist)"
    
    success "Deployments updated"
}

# Verify installation
verify_installation() {
    log "Verifying External Secrets installation..."
    
    # Check operator pods
    kubectl get pods -n external-secrets
    
    # Check CRDs
    kubectl get crd | grep external-secrets
    
    # Check external secrets status
    kubectl get externalsecrets -A
    
    success "Verification complete"
}

# Create documentation
create_documentation() {
    log "Creating documentation..."
    
    cat > EXTERNAL_SECRETS_SETUP.md << 'EOF'
# External Secrets Operator Setup

## Overview
External Secrets Operator has been installed to manage secrets from external systems like AWS Secrets Manager and HashiCorp Vault.

## Configuration

### AWS Secrets Manager
1. Create secrets in AWS Secrets Manager with the following structure:
   - `tradesense/production/database` - Database credentials
   - `tradesense/production/redis` - Redis credentials
   - `tradesense/production/app` - Application secrets
   - `tradesense/production/stripe` - Stripe API keys
   - `tradesense/production/monitoring` - Monitoring credentials

2. Configure IAM role for service account (IRSA):
   ```bash
   eksctl create iamserviceaccount \
     --name external-secrets-sa \
     --namespace tradesense \
     --cluster your-cluster-name \
     --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
     --approve
   ```

### HashiCorp Vault (Optional)
1. Enable Kubernetes auth in Vault
2. Create appropriate policies
3. Configure the Vault SecretStore

## Usage

### Creating a new External Secret
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-secret
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: my-k8s-secret
  data:
  - secretKey: password
    remoteRef:
      key: my-aws-secret
      property: password
```

### Monitoring
- Check operator logs: `kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets`
- View metrics: `kubectl port-forward -n external-secrets svc/external-secrets-metrics 8080:8080`

## Troubleshooting
- Check ExternalSecret status: `kubectl describe externalsecret <name> -n <namespace>`
- Verify SecretStore connection: `kubectl describe secretstore <name> -n <namespace>`
- Check operator logs for errors

## Security Best Practices
1. Use IRSA instead of static credentials
2. Enable secret rotation in AWS/Vault
3. Limit secret access with IAM policies
4. Monitor secret access with CloudTrail/Vault audit logs
5. Use separate SecretStores for different environments
EOF
    
    success "Documentation created: EXTERNAL_SECRETS_SETUP.md"
}

# Main execution
main() {
    log "🚀 Starting External Secrets Operator setup..."
    
    check_prerequisites
    install_external_secrets
    configure_aws_secretstore
    configure_vault_secretstore
    create_external_secrets
    update_deployments
    verify_installation
    create_documentation
    
    success "✨ External Secrets Operator setup complete!"
    log "Next steps:"
    log "1. Configure your AWS Secrets Manager or Vault with the required secrets"
    log "2. Update the IAM role ARN in aws-secret-store.yaml"
    log "3. Monitor the ExternalSecrets for successful sync"
}

# Run main function
main "$@"