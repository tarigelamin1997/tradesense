#!/bin/bash

# Istio and Flagger Setup Script
# This script installs Istio service mesh and Flagger for progressive delivery

set -e

# Configuration
ISTIO_VERSION="1.20.1"
FLAGGER_VERSION="1.35.0"
ISTIO_NAMESPACE="istio-system"
FLAGGER_NAMESPACE="flagger"

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
    
    # Check for existing Istio installation
    if kubectl get namespace ${ISTIO_NAMESPACE} &> /dev/null; then
        warning "Istio namespace already exists. Will upgrade existing installation."
    fi
    
    success "Prerequisites check passed"
}

# Download and install istioctl
install_istioctl() {
    log "Installing istioctl version ${ISTIO_VERSION}..."
    
    if command -v istioctl &> /dev/null; then
        CURRENT_VERSION=$(istioctl version --remote=false 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        if [[ "$CURRENT_VERSION" == "$ISTIO_VERSION" ]]; then
            success "istioctl ${ISTIO_VERSION} already installed"
            return
        fi
    fi
    
    # Download istioctl
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
    
    # Move to PATH
    sudo mv istio-${ISTIO_VERSION}/bin/istioctl /usr/local/bin/
    rm -rf istio-${ISTIO_VERSION}
    
    success "istioctl installed"
}

# Install Istio
install_istio() {
    log "Installing Istio..."
    
    # Create namespace
    kubectl apply -f namespace.yaml
    
    # Install Istio using istioctl with custom configuration
    istioctl install -y -f istio-values.yaml \
        --set values.pilot.env.PILOT_ENABLE_ANALYSIS=true \
        --set values.global.proxy.resources.requests.cpu=100m \
        --set values.global.proxy.resources.requests.memory=128Mi
    
    # Wait for Istio to be ready
    log "Waiting for Istio components to be ready..."
    kubectl wait --for=condition=ready pod -l app=istiod -n ${ISTIO_NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app=istio-ingressgateway -n ${ISTIO_NAMESPACE} --timeout=300s
    
    success "Istio installed"
}

# Install Istio addons
install_istio_addons() {
    log "Installing Istio addons..."
    
    # Install Kiali (optional)
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%.*}/samples/addons/kiali.yaml || warning "Kiali installation skipped"
    
    # Install Istio dashboards for Grafana
    kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-${ISTIO_VERSION%.*}/samples/addons/grafana.yaml || warning "Grafana dashboards skipped"
    
    success "Istio addons installed"
}

# Install cert-manager for automatic TLS
install_cert_manager() {
    log "Installing cert-manager..."
    
    # Check if already installed
    if kubectl get namespace cert-manager &> /dev/null; then
        warning "cert-manager already installed"
        return
    fi
    
    # Install cert-manager
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s
    
    # Create ClusterIssuer for Let's Encrypt
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@tradesense.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: istio
EOF
    
    success "cert-manager installed"
}

# Install Flagger
install_flagger() {
    log "Installing Flagger..."
    
    # Create namespace
    kubectl create namespace ${FLAGGER_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Add Flagger Helm repository
    helm repo add flagger https://flagger.app
    helm repo update
    
    # Install Flagger
    helm upgrade --install flagger flagger/flagger \
        --namespace ${FLAGGER_NAMESPACE} \
        --version ${FLAGGER_VERSION} \
        --values flagger-values.yaml \
        --wait
    
    # Install Flagger Grafana dashboards
    helm upgrade --install flagger-grafana flagger/grafana \
        --namespace ${FLAGGER_NAMESPACE} \
        --set url=http://prometheus-server.monitoring:80 \
        --set user=admin \
        --set password=admin || warning "Flagger Grafana dashboards skipped"
    
    success "Flagger installed"
}

# Configure Istio for TradeSense
configure_tradesense() {
    log "Configuring Istio for TradeSense..."
    
    # Label namespace for automatic sidecar injection
    kubectl label namespace tradesense istio-injection=enabled --overwrite
    
    # Apply Gateway and VirtualServices
    kubectl apply -f gateway.yaml
    
    # Apply Canary configurations
    kubectl apply -f canary.yaml
    
    # Restart deployments to inject sidecars
    log "Restarting deployments to inject Istio sidecars..."
    kubectl rollout restart deployment -n tradesense
    
    success "TradeSense configuration applied"
}

# Verify installation
verify_installation() {
    log "Verifying Istio installation..."
    
    # Check Istio
    istioctl verify-install || warning "Istio verification failed"
    
    # Check proxy injection
    TOTAL_PODS=$(kubectl get pods -n tradesense -o json | jq '.items | length')
    INJECTED_PODS=$(kubectl get pods -n tradesense -o json | jq '.items[].spec.containers[].name' | grep -c istio-proxy || true)
    
    log "Sidecar injection status: ${INJECTED_PODS}/${TOTAL_PODS} pods have sidecars"
    
    # Get ingress gateway IP
    INGRESS_IP=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
    INGRESS_HOSTNAME=$(kubectl get svc istio-ingressgateway -n istio-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
    
    log "Ingress Gateway endpoint: ${INGRESS_IP:-$INGRESS_HOSTNAME}"
    
    # Test with curl (if endpoint is available)
    if [[ "$INGRESS_IP" != "pending" ]] && [[ -n "$INGRESS_IP" ]]; then
        log "Testing gateway connectivity..."
        curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://${INGRESS_IP} || warning "Gateway test failed"
    fi
    
    success "Verification completed"
}

# Create documentation
create_documentation() {
    log "Creating Istio documentation..."
    
    cat > SERVICE_MESH_GUIDE.md << 'EOF'
# Service Mesh Implementation Guide

## Overview
This guide covers the Istio service mesh and Flagger progressive delivery setup for TradeSense.

## Architecture

### Istio Components
1. **Control Plane (istiod)**
   - Service discovery
   - Configuration management
   - Certificate management

2. **Data Plane (Envoy proxies)**
   - Traffic management
   - Security (mTLS)
   - Observability

3. **Ingress Gateway**
   - External traffic entry point
   - TLS termination
   - Load balancing

### Flagger Components
1. **Flagger Controller**
   - Monitors deployments
   - Manages canary releases
   - Analyzes metrics

2. **Load Tester**
   - Generates synthetic traffic
   - Runs acceptance tests

## Traffic Management

### Virtual Services
```yaml
# Example: Route 10% traffic to canary
spec:
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: backend
        subset: canary
      weight: 100
  - route:
    - destination:
        host: backend
        subset: stable
      weight: 90
    - destination:
        host: backend
        subset: canary
      weight: 10
```

### Circuit Breaking
```yaml
# Configured in DestinationRules
outlierDetection:
  consecutiveErrors: 5
  interval: 30s
  baseEjectionTime: 30s
```

### Retry Logic
```yaml
# Configured in VirtualServices
retries:
  attempts: 3
  perTryTimeout: 2s
  retryOn: gateway-error,connect-failure,refused-stream
```

## Security

### mTLS Configuration
- Automatic mTLS between services
- STRICT mode enforced in production
- Certificate rotation every 24 hours

### Authorization Policies
```bash
# Check current policies
kubectl get authorizationpolicies -n tradesense

# Test authorization
kubectl exec deploy/frontend -- curl -s backend:8000/api/v1/test
```

### JWT Authentication
- Configured for external API access
- JWKS endpoint for key validation
- Token forwarding enabled

## Progressive Delivery

### Canary Deployment Process
1. **New version deployed**
   - Creates backend-canary deployment
   - 0% traffic initially

2. **Analysis phase**
   - Gradually increase traffic (10% → 20% → 50%)
   - Monitor success rate, latency, errors
   - Run automated tests

3. **Promotion or rollback**
   - Promote if metrics pass thresholds
   - Automatic rollback on failures

### Deployment Commands
```bash
# Trigger canary deployment
kubectl set image deployment/backend backend=tradesense/backend:v2 -n tradesense

# Check canary status
kubectl get canary backend -n tradesense

# Manual promotion
kubectl patch canary backend -n tradesense --type merge -p '{"spec":{"skipAnalysis":true}}'

# Manual rollback
kubectl delete canary backend -n tradesense
```

## Observability

### Distributed Tracing
- Automatic trace collection
- Integration with Tempo
- 10% sampling rate

### Metrics
```bash
# Key metrics to monitor
- istio_request_total
- istio_request_duration_milliseconds
- istio_tcp_connections_opened_total
- istio_tcp_connections_closed_total
```

### Dashboards
1. **Istio Dashboard**
   - Service mesh overview
   - Traffic flow
   - Error rates

2. **Flagger Dashboard**
   - Canary deployments
   - Promotion history
   - Metric analysis

## Troubleshooting

### Common Issues

1. **Sidecar not injected**
```bash
# Check namespace label
kubectl get ns tradesense -o yaml | grep istio-injection

# Manually inject
kubectl label namespace tradesense istio-injection=enabled
kubectl rollout restart deployment -n tradesense
```

2. **503 errors**
```bash
# Check destination rules
kubectl get destinationrules -n tradesense

# Check service endpoints
istioctl proxy-config endpoints deploy/backend -n tradesense
```

3. **mTLS issues**
```bash
# Check mTLS status
istioctl authn tls-check deploy/backend.tradesense

# View certificates
istioctl proxy-config secret deploy/backend -n tradesense
```

4. **Canary stuck**
```bash
# Check Flagger logs
kubectl logs -n flagger deploy/flagger

# Check metrics
kubectl logs -n tradesense deploy/flagger-loadtester
```

### Debugging Commands
```bash
# Enable debug logging
kubectl exec deploy/backend -c istio-proxy -- curl -X POST "localhost:15000/logging?level=debug"

# View Envoy configuration
istioctl proxy-config all deploy/backend -n tradesense

# Analyze mesh configuration
istioctl analyze -n tradesense

# Check proxy sync status
istioctl proxy-status
```

## Best Practices

### Traffic Management
1. Always use VirtualServices for routing
2. Configure circuit breakers
3. Set appropriate timeouts
4. Use retry policies sparingly

### Security
1. Enable STRICT mTLS
2. Use authorization policies
3. Rotate certificates regularly
4. Audit access logs

### Performance
1. Tune connection pools
2. Monitor proxy memory usage
3. Use locality load balancing
4. Configure outlier detection

### Canary Deployments
1. Start with small traffic percentages
2. Define clear success criteria
3. Automate testing
4. Monitor business metrics

## Integration Examples

### Frontend to Backend
```javascript
// Automatic retry and circuit breaking
const response = await fetch('http://backend:8000/api/v1/data', {
  headers: {
    'x-request-id': generateRequestId(),
    'authorization': `Bearer ${token}`
  }
});
```

### External Services
```python
# Stripe API with circuit breaker
import stripe
stripe.api_base = "https://api.stripe.com"
# Istio handles retry and circuit breaking
```

## Maintenance

### Upgrade Istio
```bash
# Download new version
istioctl x precheck
istioctl upgrade

# Restart workloads
kubectl rollout restart deployment -n tradesense
```

### Certificate Rotation
- Automatic via Istio
- Manual rotation: `kubectl rollout restart deployment/istiod -n istio-system`

### Policy Updates
1. Edit YAML files
2. Apply changes: `kubectl apply -f gateway.yaml`
3. Verify: `istioctl analyze`

## Links
- [Istio Documentation](https://istio.io/latest/docs/)
- [Flagger Documentation](https://docs.flagger.app/)
- [Envoy Documentation](https://www.envoyproxy.io/docs/envoy/latest/)
EOF
    
    success "Documentation created: SERVICE_MESH_GUIDE.md"
}

# Create example configurations
create_examples() {
    log "Creating example configurations..."
    
    cat > examples/traffic-shifting.yaml << 'EOF'
# Example: A/B Testing with Header-based Routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-ab-test
  namespace: tradesense
spec:
  hosts:
  - backend
  http:
  - match:
    - headers:
        x-version:
          exact: v2
    route:
    - destination:
        host: backend
        subset: v2
  - route:
    - destination:
        host: backend
        subset: v1
      weight: 80
    - destination:
        host: backend
        subset: v2
      weight: 20
EOF

    cat > examples/fault-injection.yaml << 'EOF'
# Example: Fault Injection for Testing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-fault-injection
  namespace: tradesense
spec:
  hosts:
  - backend
  http:
  - fault:
      delay:
        percentage:
          value: 10.0
        fixedDelay: 5s
      abort:
        percentage:
          value: 5.0
        httpStatus: 503
    route:
    - destination:
        host: backend
EOF

    cat > examples/rate-limiting.yaml << 'EOF'
# Example: Rate Limiting Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: ratelimit-config
  namespace: istio-system
data:
  config.yaml: |
    domain: production
    descriptors:
      - key: PATH
        value: "/api/v1/orders"
        rate_limit:
          unit: minute
          requests_per_unit: 100
      - key: PATH
        value: "/api/v1/trades"
        rate_limit:
          unit: second
          requests_per_unit: 10
---
apiVersion: networking.istio.io/v1beta1
kind: EnvoyFilter
metadata:
  name: ratelimit-filter
  namespace: tradesense
spec:
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: SIDECAR_INBOUND
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.ratelimit
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.http.ratelimit.v3.RateLimit
          domain: production
          rate_limit_service:
            grpc_service:
              envoy_grpc:
                cluster_name: rate_limit_service
              timeout: 0.25s
EOF
    
    success "Example configurations created"
}

# Main execution
main() {
    log "🚀 Starting Istio and Flagger setup..."
    
    check_prerequisites
    
    # Create examples directory
    mkdir -p examples
    
    # Install istioctl
    install_istioctl
    
    # Install cert-manager
    install_cert_manager
    
    # Install Istio
    install_istio
    install_istio_addons
    
    # Install Flagger
    install_flagger
    
    # Configure for TradeSense
    configure_tradesense
    
    # Verify installation
    verify_installation
    
    # Create documentation and examples
    create_documentation
    create_examples
    
    success "✨ Service mesh setup complete!"
    log ""
    log "Next steps:"
    log "1. Configure DNS to point to Istio ingress gateway"
    log "2. Update application deployments with proper labels"
    log "3. Configure Slack webhook for Flagger notifications"
    log "4. Test canary deployments with sample application"
    log "5. Configure external service entries as needed"
    log ""
    log "Access Kiali dashboard:"
    log "kubectl port-forward svc/kiali -n istio-system 20001:20001"
    log ""
    log "View Flagger metrics:"
    log "kubectl port-forward svc/flagger-grafana -n flagger 3000:80"
}

# Run main function
main "$@"