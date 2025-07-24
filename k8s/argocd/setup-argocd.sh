#!/bin/bash

# ArgoCD Setup Script for TradeSense
# This script installs and configures ArgoCD for GitOps

set -e

# Configuration
ARGOCD_VERSION="v2.9.3"
ARGOCD_NAMESPACE="argocd"
DOMAIN="argocd.tradesense.com"

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

# Install ArgoCD
install_argocd() {
    log "Installing ArgoCD ${ARGOCD_VERSION}..."
    
    # Create namespace
    kubectl apply -f namespace.yaml
    
    # Add Helm repository
    helm repo add argo https://argoproj.github.io/argo-helm
    helm repo update
    
    # Install ArgoCD using Helm
    helm upgrade --install argocd argo/argo-cd \
        --namespace ${ARGOCD_NAMESPACE} \
        --create-namespace \
        --version 5.51.6 \
        --values argocd-values.yaml \
        --wait \
        --timeout 10m
    
    success "ArgoCD installed"
}

# Configure ArgoCD
configure_argocd() {
    log "Configuring ArgoCD..."
    
    # Apply secrets (make sure to update with real values first)
    warning "Please update argocd-secrets.yaml with your actual secrets before applying!"
    read -p "Have you updated the secrets file? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl apply -f argocd-secrets.yaml
    else
        warning "Skipping secrets configuration. Please apply manually later."
    fi
    
    # Apply app project
    kubectl apply -f app-of-apps.yaml
    
    success "ArgoCD configured"
}

# Install ArgoCD CLI
install_argocd_cli() {
    log "Installing ArgoCD CLI..."
    
    # Download ArgoCD CLI
    curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-amd64
    
    # Install to /usr/local/bin
    sudo install -m 755 /tmp/argocd /usr/local/bin/argocd
    rm /tmp/argocd
    
    # Verify installation
    argocd version --client
    
    success "ArgoCD CLI installed"
}

# Configure ArgoCD access
configure_access() {
    log "Configuring ArgoCD access..."
    
    # Get initial admin password
    INITIAL_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")
    
    if [[ -n "$INITIAL_PASSWORD" ]]; then
        log "Initial admin password: ${INITIAL_PASSWORD}"
        warning "Please change this password immediately!"
    else
        log "Using password from argocd-secrets.yaml"
    fi
    
    # Port forward for initial access
    log "Setting up port forwarding for initial access..."
    log "Run this in a separate terminal:"
    echo "kubectl port-forward svc/argocd-server -n argocd 8080:443"
    echo ""
    log "Then access ArgoCD at: https://localhost:8080"
    log "Username: admin"
    log "Password: ${INITIAL_PASSWORD:-<from argocd-secrets.yaml>}"
    
    success "Access configuration complete"
}

# Create sample applications
create_applications() {
    log "Creating ArgoCD applications..."
    
    # Apply root application (app of apps)
    kubectl apply -f app-of-apps.yaml
    
    # Wait for applications to be created
    sleep 10
    
    # List applications
    kubectl get applications -n argocd
    
    success "Applications created"
}

# Setup GitHub webhook
setup_webhook() {
    log "GitHub webhook setup instructions:"
    
    cat << EOF

To enable automatic syncing on Git pushes:

1. Go to your GitHub repository settings
2. Navigate to Webhooks
3. Add a new webhook with:
   - Payload URL: https://${DOMAIN}/api/webhook
   - Content type: application/json
   - Secret: <from argocd-secrets.yaml webhook.github.secret>
   - Events: Just push events

4. Update the webhook secret in ArgoCD:
   kubectl edit secret argocd-secret -n argocd

EOF
    
    success "Webhook instructions displayed"
}

# Create documentation
create_documentation() {
    log "Creating ArgoCD documentation..."
    
    cat > ARGOCD_SETUP.md << 'EOF'
# ArgoCD GitOps Setup

## Overview
ArgoCD has been installed and configured for GitOps-based deployments.

## Access ArgoCD

### Web UI
- URL: https://argocd.tradesense.com
- Username: admin
- Password: Check argocd-secret or initial admin secret

### CLI Access
```bash
# Login
argocd login argocd.tradesense.com

# List applications
argocd app list

# Sync an application
argocd app sync <app-name>

# Get application details
argocd app get <app-name>
```

## Application Management

### Creating a New Application
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: tradesense
  source:
    repoURL: https://github.com/tarigelamin1997/tradesense.git
    targetRevision: HEAD
    path: k8s/my-app
  destination:
    server: https://kubernetes.default.svc
    namespace: my-namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Sync Strategies
- **Manual**: Applications sync only when manually triggered
- **Automated**: Applications sync automatically when Git changes
- **Self-heal**: Applications auto-sync when K8s resources drift

## Best Practices

### 1. Repository Structure
```
k8s/
├── argocd/
│   ├── applications/     # ArgoCD app definitions
│   └── projects/         # ArgoCD projects
├── base/                 # Base Kustomize configs
├── overlays/
│   ├── development/      # Dev environment
│   ├── staging/          # Staging environment
│   └── production/       # Production environment
└── components/           # Reusable components
```

### 2. Environment Promotion
1. Commit changes to development branch
2. Test in development environment
3. Create PR to staging branch
4. Test in staging environment
5. Create PR to main branch for production

### 3. Secret Management
- Use External Secrets Operator (already configured)
- Never commit secrets to Git
- Use Sealed Secrets for Git-stored secrets

## Monitoring

### Application Health
```bash
# Check application health
argocd app get <app-name> --refresh

# View application logs
argocd app logs <app-name>
```

### Metrics
- Prometheus metrics available at :8083/metrics
- Grafana dashboards for ArgoCD monitoring

## Troubleshooting

### Sync Issues
1. Check application status: `argocd app get <app-name>`
2. View sync details: `argocd app sync <app-name> --dry-run`
3. Check logs: `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server`

### Common Issues
- **OutOfSync**: Git state differs from cluster state
- **Degraded**: Application health checks failing
- **Missing**: Resources exist in Git but not in cluster
- **Unknown**: Unable to assess application health

## Security

### RBAC
- Projects limit what resources can be deployed
- AppProjects define source repos and destinations
- User roles control who can manage applications

### Best Practices
1. Use projects to isolate environments
2. Limit source repositories in projects
3. Use Git branch protection
4. Enable webhook signature verification
5. Rotate tokens regularly
EOF
    
    success "Documentation created: ARGOCD_SETUP.md"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up ArgoCD monitoring..."
    
    # Create ServiceMonitor for Prometheus
    cat > argocd-servicemonitor.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-metrics
  namespace: argocd
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-metrics
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-server-metrics
  namespace: argocd
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-server
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argocd-repo-server-metrics
  namespace: argocd
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: argocd-repo-server
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
    
    kubectl apply -f argocd-servicemonitor.yaml
    
    success "Monitoring configured"
}

# Main execution
main() {
    log "🚀 Starting ArgoCD setup for TradeSense..."
    
    check_prerequisites
    install_argocd
    configure_argocd
    install_argocd_cli
    configure_access
    create_applications
    setup_webhook
    setup_monitoring
    create_documentation
    
    success "✨ ArgoCD setup complete!"
    log ""
    log "Next steps:"
    log "1. Access ArgoCD UI at https://localhost:8080 (with port-forward)"
    log "2. Change the admin password"
    log "3. Configure GitHub webhook"
    log "4. Apply your applications"
    log "5. Set up external domain and ingress"
}

# Run main function
main "$@"