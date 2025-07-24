#!/bin/bash

# Security Setup Script for Falco and OPA
# This script installs runtime security monitoring and policy enforcement

set -e

# Configuration
FALCO_NAMESPACE="falco"
OPA_NAMESPACE="opa"
FALCO_VERSION="4.0.0"
OPA_VERSION="0.59.0"

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
    
    # Check kernel version for Falco
    KERNEL_VERSION=$(uname -r)
    log "Kernel version: $KERNEL_VERSION"
    
    success "Prerequisites check passed"
}

# Create TLS certificates for OPA
create_opa_certs() {
    log "Creating TLS certificates for OPA..."
    
    # Create temporary directory
    CERT_DIR=$(mktemp -d)
    
    # Create CA key and certificate
    openssl genrsa -out ${CERT_DIR}/ca.key 2048
    openssl req -x509 -new -nodes -key ${CERT_DIR}/ca.key -days 365 -out ${CERT_DIR}/ca.crt -subj "/CN=opa-ca"
    
    # Create OPA key and certificate request
    openssl genrsa -out ${CERT_DIR}/opa.key 2048
    
    # Create certificate configuration
    cat > ${CERT_DIR}/opa.conf <<EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = opa
DNS.2 = opa.opa
DNS.3 = opa.opa.svc
DNS.4 = opa.opa.svc.cluster.local
EOF
    
    # Create certificate request
    openssl req -new -key ${CERT_DIR}/opa.key -out ${CERT_DIR}/opa.csr -subj "/CN=opa.opa.svc" -config ${CERT_DIR}/opa.conf
    
    # Sign the certificate
    openssl x509 -req -in ${CERT_DIR}/opa.csr -CA ${CERT_DIR}/ca.crt -CAkey ${CERT_DIR}/ca.key -CAcreateserial -out ${CERT_DIR}/opa.crt -days 365 -extensions v3_req -extfile ${CERT_DIR}/opa.conf
    
    # Create secret
    kubectl create secret tls opa-tls \
        --cert=${CERT_DIR}/opa.crt \
        --key=${CERT_DIR}/opa.key \
        -n ${OPA_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Update webhook CA bundle
    CA_BUNDLE=$(cat ${CERT_DIR}/ca.crt | base64 | tr -d '\n')
    
    # Clean up
    rm -rf ${CERT_DIR}
    
    success "TLS certificates created"
    echo "CA Bundle: $CA_BUNDLE"
}

# Install Falco
install_falco() {
    log "Installing Falco..."
    
    # Create namespace
    kubectl apply -f falco/namespace.yaml
    
    # Add Falco Helm repository
    helm repo add falcosecurity https://falcosecurity.github.io/charts
    helm repo update
    
    # Install Falco
    helm upgrade --install falco falcosecurity/falco \
        --namespace ${FALCO_NAMESPACE} \
        --version ${FALCO_VERSION} \
        --values falco/falco-values.yaml \
        --wait \
        --timeout 10m
    
    success "Falco installed"
}

# Install OPA
install_opa() {
    log "Installing OPA..."
    
    # Create namespace
    kubectl apply -f opa/namespace.yaml
    
    # Create certificates
    create_opa_certs
    
    # Apply policies
    kubectl apply -f opa/policies.yaml
    
    # Deploy OPA
    kubectl apply -f opa/opa-deployment.yaml
    
    # Wait for OPA to be ready
    log "Waiting for OPA to be ready..."
    kubectl wait --for=condition=ready pod -l app=opa -n ${OPA_NAMESPACE} --timeout=300s
    
    success "OPA installed"
}

# Configure webhook
configure_webhook() {
    log "Configuring admission webhooks..."
    
    # Get CA bundle from secret
    CA_BUNDLE=$(kubectl get secret opa-tls -n ${OPA_NAMESPACE} -o jsonpath='{.data.ca\.crt}' | base64 -d | base64 | tr -d '\n')
    
    # Update webhook configurations with CA bundle
    kubectl patch validatingwebhookconfiguration opa-validating-webhook \
        --type='json' -p='[{"op": "replace", "path": "/webhooks/0/clientConfig/caBundle", "value":"'${CA_BUNDLE}'"}]'
    
    kubectl patch mutatingwebhookconfiguration opa-mutating-webhook \
        --type='json' -p='[{"op": "replace", "path": "/webhooks/0/clientConfig/caBundle", "value":"'${CA_BUNDLE}'"}]'
    
    success "Webhooks configured"
}

# Test Falco
test_falco() {
    log "Testing Falco..."
    
    # Create test pod that should trigger Falco rules
    cat > test-falco.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: falco-test
  namespace: default
spec:
  containers:
  - name: test
    image: alpine
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'test'; sleep 60; done"]
EOF
    
    kubectl apply -f test-falco.yaml
    
    # Wait a moment
    sleep 5
    
    # Execute suspicious command
    kubectl exec falco-test -- sh -c "cat /etc/shadow" || true
    
    # Check Falco logs
    log "Checking Falco logs for alerts..."
    kubectl logs -n ${FALCO_NAMESPACE} -l app.kubernetes.io/name=falco --tail=50 | grep -i "warning\|error" || true
    
    # Clean up
    kubectl delete -f test-falco.yaml
    rm test-falco.yaml
    
    success "Falco test completed"
}

# Test OPA
test_opa() {
    log "Testing OPA policies..."
    
    # Test 1: Try to create a privileged pod (should be denied)
    cat > test-opa-deny.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: opa-test-deny
  namespace: default
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      privileged: true
EOF
    
    log "Test 1: Creating privileged pod (should be denied)..."
    kubectl apply -f test-opa-deny.yaml 2>&1 | grep -E "denied|Error" || error "OPA should have denied this pod"
    
    # Test 2: Create a compliant pod (should be allowed)
    cat > test-opa-allow.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: opa-test-allow
  namespace: default
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: test
    image: tradesense/backend:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
EOF
    
    log "Test 2: Creating compliant pod (should be allowed)..."
    kubectl apply -f test-opa-allow.yaml || warning "Make sure the image exists"
    
    # Clean up
    kubectl delete -f test-opa-allow.yaml --ignore-not-found
    rm -f test-opa-deny.yaml test-opa-allow.yaml
    
    success "OPA test completed"
}

# Create dashboards
create_dashboards() {
    log "Creating security dashboards..."
    
    # Falco dashboard for Grafana
    cat > falco-dashboard.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-falco-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  falco-dashboard.json: |
    {
      "dashboard": {
        "title": "Falco Security Events",
        "panels": [
          {
            "title": "Security Events by Priority",
            "targets": [
              {
                "expr": "rate(falco_events_total[5m])",
                "legendFormat": "{{priority}}"
              }
            ]
          },
          {
            "title": "Top Security Rules Triggered",
            "targets": [
              {
                "expr": "topk(10, sum by (rule) (rate(falco_events_total[5m])))"
              }
            ]
          }
        ]
      }
    }
EOF
    
    kubectl apply -f falco-dashboard.yaml || warning "Grafana ConfigMap not found"
    rm falco-dashboard.yaml
    
    success "Dashboards created"
}

# Create documentation
create_documentation() {
    log "Creating security documentation..."
    
    cat > SECURITY_SETUP.md << 'EOF'
# Container Security Setup Guide

## Overview
This setup provides runtime security monitoring (Falco) and policy enforcement (OPA) for the TradeSense platform.

## Falco - Runtime Security Monitoring

### What Falco Monitors
- Suspicious process execution
- File system changes
- Network connections
- System calls
- Container escapes
- Privilege escalations

### Viewing Falco Alerts
```bash
# View Falco logs
kubectl logs -n falco -l app.kubernetes.io/name=falco -f

# Check Falcosidekick for formatted alerts
kubectl logs -n falco -l app.kubernetes.io/name=falcosidekick
```

### Custom Rules
Edit `falco/falco-values.yaml` to add custom rules specific to your applications.

### Slack Integration
1. Set your Slack webhook URL in `falco-values.yaml`
2. Restart Falcosidekick: `kubectl rollout restart deployment falcosidekick -n falco`

## OPA - Policy Enforcement

### Enforced Policies
1. **Container Security**:
   - No privileged containers
   - No root users (UID 0)
   - Required security contexts
   - Read-only root filesystem

2. **Resource Management**:
   - CPU and memory limits required
   - Liveness and readiness probes required

3. **Network Security**:
   - TLS required for Ingress
   - NodePort services restricted
   - LoadBalancer annotations required

4. **Image Security**:
   - Only allowed registries
   - TradeSense images preferred

### Testing Policies
```bash
# Test if a resource would be allowed
kubectl auth can-i create pod --as=system:serviceaccount:default:test

# Dry run to test policies
kubectl apply --dry-run=server -f your-manifest.yaml
```

### Exemptions
To exempt a namespace from OPA:
```bash
kubectl label namespace <namespace-name> openpolicyagent.org/webhook=ignore
```

## Security Best Practices

### 1. Container Images
- Scan images for vulnerabilities
- Use minimal base images (distroless)
- Sign images with cosign
- Regular updates

### 2. RBAC
- Least privilege principle
- Service account per application
- Regular permission audits

### 3. Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### 4. Secrets Management
- Use External Secrets Operator
- Rotate secrets regularly
- Encrypt at rest

## Monitoring & Alerting

### Prometheus Metrics
- `falco_events_total` - Total Falco events
- `opa_decisions_total` - OPA policy decisions
- `opa_decision_duration_seconds` - Decision latency

### Alert Examples
```yaml
- alert: HighSecurityEvents
  expr: rate(falco_events_total{priority="Critical"}[5m]) > 0
  annotations:
    summary: "Critical security event detected"
    
- alert: OPAPolicyViolations
  expr: rate(opa_decisions_total{decision="deny"}[5m]) > 10
  annotations:
    summary: "High rate of policy violations"
```

## Troubleshooting

### Falco Issues
1. **No events appearing**:
   - Check kernel module: `lsmod | grep falco`
   - Verify eBPF probe: `kubectl logs -n falco <falco-pod>`

2. **High CPU usage**:
   - Reduce rules complexity
   - Adjust output rate limiting

### OPA Issues
1. **Webhooks timing out**:
   - Check OPA pod resources
   - Review policy complexity

2. **Policies not enforcing**:
   - Verify webhook configuration
   - Check namespace labels

## Compliance

### CIS Kubernetes Benchmark
- Pod Security Standards enforced
- RBAC properly configured
- Network policies in place

### PCI DSS
- Access logging enabled
- Security monitoring active
- Encryption enforced

### SOC 2
- Change tracking via OPA
- Incident detection via Falco
- Audit trails maintained

## Links
- [Falco Documentation](https://falco.org/docs/)
- [OPA Documentation](https://www.openpolicyagent.org/docs/latest/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
EOF
    
    success "Documentation created: SECURITY_SETUP.md"
}

# Main execution
main() {
    log "🚀 Starting security setup with Falco and OPA..."
    
    check_prerequisites
    
    # Install Falco
    log "Installing Falco for runtime security monitoring..."
    install_falco
    
    # Install OPA
    log "Installing OPA for policy enforcement..."
    install_opa
    configure_webhook
    
    # Run tests
    log "Running security tests..."
    test_falco
    test_opa
    
    # Create dashboards and documentation
    create_dashboards
    create_documentation
    
    success "✨ Security setup complete!"
    log ""
    log "Next steps:"
    log "1. Configure Slack webhook for Falco alerts"
    log "2. Review and customize OPA policies"
    log "3. Set up Prometheus alerts"
    log "4. Train team on security policies"
    log "5. Regular security audits"
}

# Run main function
main "$@"