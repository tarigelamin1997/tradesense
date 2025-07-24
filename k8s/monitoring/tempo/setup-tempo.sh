#!/bin/bash

# Tempo Setup Script for Distributed Tracing
# This script installs Grafana Tempo and OpenTelemetry Collector

set -e

# Configuration
NAMESPACE="monitoring"
TEMPO_VERSION="2.3.1"
OTEL_VERSION="0.91.0"

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
    
    # Check if Prometheus is installed
    if ! kubectl get deployment -n monitoring prometheus-server &> /dev/null; then
        warning "Prometheus not found. Tempo metrics may not be visible in Grafana."
    fi
    
    success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log "Creating monitoring namespace..."
    
    kubectl apply -f namespace.yaml || kubectl create namespace ${NAMESPACE} || true
    
    success "Namespace created"
}

# Install Tempo using Helm
install_tempo_helm() {
    log "Installing Tempo using Helm..."
    
    # Add Grafana Helm repository
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    
    # Install Tempo
    helm upgrade --install tempo grafana/tempo-distributed \
        --namespace ${NAMESPACE} \
        --values tempo-values.yaml \
        --wait \
        --timeout 10m
    
    success "Tempo installed via Helm"
}

# Install Tempo distributed manually
install_tempo_distributed() {
    log "Installing Tempo distributed components..."
    
    # Apply Tempo distributed configuration
    kubectl apply -f tempo-distributed.yaml
    
    # Wait for components to be ready
    log "Waiting for Tempo components to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=tempo -n ${NAMESPACE} --timeout=300s || true
    
    success "Tempo distributed components installed"
}

# Install OpenTelemetry Collector
install_otel_collector() {
    log "Installing OpenTelemetry Collector..."
    
    # Apply OpenTelemetry Collector configuration
    kubectl apply -f otel-collector.yaml
    
    # Wait for collector to be ready
    log "Waiting for OpenTelemetry Collector to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=otel-collector -n ${NAMESPACE} --timeout=300s || true
    
    success "OpenTelemetry Collector installed"
}

# Configure Grafana data source
configure_grafana() {
    log "Configuring Grafana data source for Tempo..."
    
    # Create Tempo data source configuration
    cat > tempo-datasource.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-tempo-datasource
  namespace: ${NAMESPACE}
  labels:
    grafana_datasource: "1"
data:
  tempo-datasource.yaml: |
    apiVersion: 1
    datasources:
      - name: Tempo
        type: tempo
        access: proxy
        url: http://tempo-query-frontend:3100
        uid: tempo
        jsonData:
          httpMethod: GET
          serviceMap:
            datasourceUid: prometheus
          tracesToLogs:
            datasourceUid: loki
            tags: ['job', 'pod', 'namespace']
            mappedTags: [{ key: 'service.name', value: 'service' }]
            mapTagNamesEnabled: true
            spanStartTimeShift: '1h'
            spanEndTimeShift: '1h'
            filterByTraceID: true
            filterBySpanID: false
          tracesToMetrics:
            datasourceUid: prometheus
            tags: [{ key: 'service.name', value: 'service' }]
            queries:
              - name: 'Request Rate'
                query: 'sum(rate(traces_spanmetrics_calls_total{service="$${__tags.service.name}"}[5m]))'
              - name: 'Error Rate'
                query: 'sum(rate(traces_spanmetrics_calls_total{service="$${__tags.service.name}",status_code="STATUS_CODE_ERROR"}[5m]))'
              - name: 'Latency P95'
                query: 'histogram_quantile(0.95, sum(rate(traces_spanmetrics_latency_bucket{service="$${__tags.service.name}"}[5m])) by (le))'
          nodeGraph:
            enabled: true
          search:
            hide: false
          lokiSearch:
            datasourceUid: loki
          traceQuery:
            timeShiftEnabled: true
            spanStartTimeShift: '1h'
            spanEndTimeShift: '1h'
          spanBar:
            type: 'Tag'
            tag: 'http.status_code'
EOF
    
    kubectl apply -f tempo-datasource.yaml
    
    # Apply Tempo dashboards
    kubectl apply -f ../grafana/tempo-dashboards.yaml
    
    success "Grafana configured for Tempo"
}

# Update application deployments
update_deployments() {
    log "Updating application deployments for tracing..."
    
    # Patch backend deployment to add OTLP endpoint
    kubectl patch deployment backend -n tradesense --type='json' -p='[
        {"op": "add", "path": "/spec/template/spec/containers/0/env/-", "value": {
            "name": "OTLP_ENDPOINT",
            "value": "otel-collector.monitoring:4317"
        }},
        {"op": "add", "path": "/spec/template/spec/containers/0/env/-", "value": {
            "name": "OTEL_EXPORTER_OTLP_ENDPOINT",
            "value": "http://otel-collector.monitoring:4317"
        }},
        {"op": "add", "path": "/spec/template/spec/containers/0/env/-", "value": {
            "name": "OTEL_SERVICE_NAME",
            "value": "tradesense-backend"
        }},
        {"op": "add", "path": "/spec/template/spec/containers/0/env/-", "value": {
            "name": "OTEL_TRACES_EXPORTER",
            "value": "otlp"
        }},
        {"op": "add", "path": "/spec/template/spec/containers/0/env/-", "value": {
            "name": "OTEL_METRICS_EXPORTER",
            "value": "prometheus"
        }}
    ]' 2>/dev/null || warning "Backend deployment patch skipped (may not exist)"
    
    success "Deployments updated"
}

# Create example trace
create_example_trace() {
    log "Creating example trace..."
    
    cat > example-trace.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: trace-generator
  namespace: ${NAMESPACE}
data:
  generate-trace.py: |
    import time
    import random
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    
    # Set up tracing
    resource = Resource.create({SERVICE_NAME: "trace-generator"})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector.monitoring:4317", insecure=True))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)
    
    # Generate traces
    for i in range(10):
        with tracer.start_as_current_span("example-operation") as span:
            span.set_attribute("iteration", i)
            span.set_attribute("user.id", f"user-{random.randint(1, 100)}")
            
            # Simulate some work
            time.sleep(random.uniform(0.1, 0.5))
            
            # Create child span
            with tracer.start_as_current_span("database-query") as child_span:
                child_span.set_attribute("db.statement", "SELECT * FROM users")
                time.sleep(random.uniform(0.01, 0.1))
        
        print(f"Generated trace {i+1}")
        time.sleep(1)
    
    print("Trace generation complete!")
---
apiVersion: batch/v1
kind: Job
metadata:
  name: trace-generator
  namespace: ${NAMESPACE}
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: generator
        image: python:3.9-slim
        command: ["/bin/bash", "-c"]
        args:
          - |
            pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
            python /scripts/generate-trace.py
        volumeMounts:
        - name: script
          mountPath: /scripts
      volumes:
      - name: script
        configMap:
          name: trace-generator
EOF
    
    kubectl apply -f example-trace.yaml
    
    success "Example trace generator created"
}

# Verify installation
verify_installation() {
    log "Verifying Tempo installation..."
    
    # Check Tempo components
    echo ""
    log "Tempo Components:"
    kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=tempo
    
    # Check OpenTelemetry Collector
    echo ""
    log "OpenTelemetry Collector:"
    kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=otel-collector
    
    # Check services
    echo ""
    log "Services:"
    kubectl get svc -n ${NAMESPACE} | grep -E "(tempo|otel)"
    
    # Port forward to access Tempo
    echo ""
    log "To access Tempo Query UI:"
    echo "kubectl port-forward -n ${NAMESPACE} svc/tempo-query-frontend 3100:3100"
    echo "Then visit: http://localhost:3100"
    
    echo ""
    log "To access traces in Grafana:"
    echo "1. Port forward Grafana: kubectl port-forward -n ${NAMESPACE} svc/grafana 3000:80"
    echo "2. Visit http://localhost:3000"
    echo "3. Go to Explore and select Tempo data source"
    
    success "Verification complete"
}

# Create documentation
create_documentation() {
    log "Creating Tempo documentation..."
    
    cat > TEMPO_SETUP.md << 'EOF'
# Grafana Tempo Setup Guide

## Overview
Grafana Tempo has been installed for distributed tracing across the TradeSense platform.

## Architecture
- **Tempo Distributor**: Receives traces from applications
- **Tempo Ingester**: Processes and stores traces temporarily
- **Tempo Querier**: Queries traces from storage
- **Tempo Compactor**: Compacts and manages long-term storage
- **OpenTelemetry Collector**: Collects and forwards traces

## Instrumenting Applications

### Python (FastAPI)
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Set up tracing
resource = Resource.create({SERVICE_NAME: "my-service"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="otel-collector.monitoring:4317", insecure=True)
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

### Environment Variables
```bash
OTEL_SERVICE_NAME=my-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.monitoring:4317
OTEL_TRACES_EXPORTER=otlp
```

## Querying Traces

### Using Grafana
1. Open Grafana Explore
2. Select Tempo data source
3. Search by:
   - Trace ID
   - Service name
   - Tags (e.g., `http.status_code=500`)
   - Time range

### Using Tempo API
```bash
# Search traces
curl -G -s http://tempo-query-frontend:3100/api/search \
  --data-urlencode 'tags=service.name="tradesense-backend"' \
  --data-urlencode 'limit=20'

# Get trace by ID
curl http://tempo-query-frontend:3100/api/traces/{trace_id}
```

## Retention and Storage

- Traces are retained for 30 days
- Stored in S3 bucket: `tradesense-tempo-traces`
- Local cache for recent traces

## Monitoring Tempo

### Metrics
Tempo exposes Prometheus metrics:
- `tempo_distributor_spans_received_total`
- `tempo_ingester_traces_created_total`
- `tempo_compactor_blocks_total`

### Dashboards
- **Tempo Operational**: Overall health and performance
- **Tempo Service Graph**: Service dependencies and latencies

## Troubleshooting

### No traces appearing
1. Check OTLP endpoint connectivity
2. Verify instrumentation is active
3. Check OpenTelemetry Collector logs

### High memory usage
1. Adjust batch processor settings
2. Increase resource limits
3. Check trace volume

### S3 connectivity issues
1. Verify IAM permissions
2. Check S3 bucket policy
3. Validate endpoint configuration

## Best Practices

1. **Sampling**: Use head-based or tail-based sampling for high-volume services
2. **Context Propagation**: Ensure trace context is propagated across service boundaries
3. **Span Attributes**: Add meaningful attributes but avoid sensitive data
4. **Error Tracking**: Always record exceptions in spans
5. **Performance**: Keep span creation lightweight

## Links
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Distributed Tracing Best Practices](https://www.w3.org/TR/trace-context/)
EOF
    
    success "Documentation created: TEMPO_SETUP.md"
}

# Main execution
main() {
    log "🚀 Starting Tempo setup for distributed tracing..."
    
    check_prerequisites
    create_namespace
    
    # Choose installation method
    read -p "Install Tempo using Helm? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_tempo_helm
    else
        install_tempo_distributed
    fi
    
    install_otel_collector
    configure_grafana
    update_deployments
    create_example_trace
    verify_installation
    create_documentation
    
    success "✨ Tempo setup complete!"
    log ""
    log "Next steps:"
    log "1. Instrument your applications with OpenTelemetry"
    log "2. Configure sampling strategies"
    log "3. Set up trace-based alerts"
    log "4. Explore traces in Grafana"
}

# Run main function
main "$@"