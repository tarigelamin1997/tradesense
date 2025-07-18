#!/bin/bash

# TradeSense Monitoring Setup Script
# Sets up Prometheus, Grafana, Loki, and Alertmanager

set -e

# Configuration
MONITORING_NAMESPACE="monitoring"
ENVIRONMENT=${1:-production}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if kubectl is installed (for Kubernetes deployments)
    if command -v kubectl &> /dev/null; then
        log "Kubernetes detected, will setup K8s monitoring"
        K8S_ENABLED=true
    else
        log "Kubernetes not detected, will setup Docker monitoring only"
        K8S_ENABLED=false
    fi
}

# Create monitoring directories
create_directories() {
    log "Creating monitoring directories..."
    
    mkdir -p monitoring/{prometheus,grafana,loki,alertmanager}/{data,config}
    mkdir -p monitoring/grafana/provisioning/{dashboards,datasources,notifiers}
    mkdir -p monitoring/prometheus/rules
    mkdir -p logs
    
    # Set permissions
    chmod -R 755 monitoring/
}

# Setup Prometheus
setup_prometheus() {
    log "Setting up Prometheus..."
    
    # Copy configuration
    cp monitoring/prometheus-${ENVIRONMENT}.yml monitoring/prometheus/config/prometheus.yml
    cp monitoring/prometheus/rules/*.yml monitoring/prometheus/rules/
    
    # Create Docker network if it doesn't exist
    docker network create monitoring || true
    
    # Start Prometheus
    docker run -d \
        --name prometheus \
        --network monitoring \
        -p 9090:9090 \
        -v $(pwd)/monitoring/prometheus/config:/etc/prometheus \
        -v $(pwd)/monitoring/prometheus/data:/prometheus \
        -v $(pwd)/monitoring/prometheus/rules:/etc/prometheus/rules \
        --restart unless-stopped \
        prom/prometheus:latest \
        --config.file=/etc/prometheus/prometheus.yml \
        --storage.tsdb.path=/prometheus \
        --web.console.libraries=/usr/share/prometheus/console_libraries \
        --web.console.templates=/usr/share/prometheus/consoles \
        --web.enable-lifecycle
    
    log "Prometheus started on http://localhost:9090"
}

# Setup Grafana
setup_grafana() {
    log "Setting up Grafana..."
    
    # Copy provisioning files
    cp -r monitoring/grafana/provisioning/* monitoring/grafana/provisioning/
    
    # Start Grafana
    docker run -d \
        --name grafana \
        --network monitoring \
        -p 3000:3000 \
        -v $(pwd)/monitoring/grafana/data:/var/lib/grafana \
        -v $(pwd)/monitoring/grafana/provisioning:/etc/grafana/provisioning \
        -e "GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}" \
        -e "GF_USERS_ALLOW_SIGN_UP=false" \
        -e "GF_SERVER_ROOT_URL=https://${GRAFANA_DOMAIN:-localhost}" \
        -e "GF_SMTP_ENABLED=true" \
        -e "GF_SMTP_HOST=${SMTP_HOST:-smtp.sendgrid.net:587}" \
        -e "GF_SMTP_USER=${SMTP_USER:-apikey}" \
        -e "GF_SMTP_PASSWORD=${SMTP_PASSWORD}" \
        -e "GF_SMTP_FROM_ADDRESS=${SMTP_FROM:-alerts@tradesense.com}" \
        --restart unless-stopped \
        grafana/grafana:latest
    
    log "Grafana started on http://localhost:3000 (admin/${GRAFANA_ADMIN_PASSWORD:-admin})"
}

# Setup Loki
setup_loki() {
    log "Setting up Loki..."
    
    # Copy configuration
    cp monitoring/loki-${ENVIRONMENT}.yml monitoring/loki/config/loki.yml
    
    # Start Loki
    docker run -d \
        --name loki \
        --network monitoring \
        -p 3100:3100 \
        -v $(pwd)/monitoring/loki/config:/etc/loki \
        -v $(pwd)/monitoring/loki/data:/loki \
        --restart unless-stopped \
        grafana/loki:latest \
        -config.file=/etc/loki/loki.yml
    
    log "Loki started on http://localhost:3100"
}

# Setup Promtail
setup_promtail() {
    log "Setting up Promtail..."
    
    # Copy configuration
    cp monitoring/promtail-${ENVIRONMENT}.yml monitoring/promtail/config/promtail.yml
    
    # Start Promtail
    docker run -d \
        --name promtail \
        --network monitoring \
        -v $(pwd)/monitoring/promtail/config:/etc/promtail \
        -v $(pwd)/logs:/var/log/tradesense:ro \
        -v /var/log:/var/log:ro \
        -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --restart unless-stopped \
        grafana/promtail:latest \
        -config.file=/etc/promtail/promtail.yml
    
    log "Promtail started"
}

# Setup Alertmanager
setup_alertmanager() {
    log "Setting up Alertmanager..."
    
    # Copy configuration
    cp monitoring/alertmanager.yml monitoring/alertmanager/config/alertmanager.yml
    
    # Start Alertmanager
    docker run -d \
        --name alertmanager \
        --network monitoring \
        -p 9093:9093 \
        -v $(pwd)/monitoring/alertmanager/config:/etc/alertmanager \
        -v $(pwd)/monitoring/alertmanager/data:/alertmanager \
        --restart unless-stopped \
        prom/alertmanager:latest \
        --config.file=/etc/alertmanager/alertmanager.yml \
        --storage.path=/alertmanager
    
    log "Alertmanager started on http://localhost:9093"
}

# Setup exporters
setup_exporters() {
    log "Setting up exporters..."
    
    # Node Exporter
    docker run -d \
        --name node-exporter \
        --network monitoring \
        -p 9100:9100 \
        --pid="host" \
        -v "/:/host:ro,rslave" \
        --restart unless-stopped \
        prom/node-exporter:latest \
        --path.rootfs=/host
    
    # PostgreSQL Exporter
    docker run -d \
        --name postgres-exporter \
        --network monitoring \
        -p 9187:9187 \
        -e DATA_SOURCE_NAME="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/tradesense_${ENVIRONMENT}?sslmode=disable" \
        --restart unless-stopped \
        prometheuscommunity/postgres-exporter:latest
    
    # Redis Exporter
    docker run -d \
        --name redis-exporter \
        --network monitoring \
        -p 9121:9121 \
        -e REDIS_ADDR="redis://redis:6379" \
        -e REDIS_PASSWORD="${REDIS_PASSWORD}" \
        --restart unless-stopped \
        oliver006/redis_exporter:latest
    
    # Blackbox Exporter
    docker run -d \
        --name blackbox-exporter \
        --network monitoring \
        -p 9115:9115 \
        --restart unless-stopped \
        prom/blackbox-exporter:latest
    
    log "Exporters started"
}

# Setup Kubernetes monitoring (if applicable)
setup_k8s_monitoring() {
    if [ "$K8S_ENABLED" = true ]; then
        log "Setting up Kubernetes monitoring..."
        
        # Create namespace
        kubectl create namespace $MONITORING_NAMESPACE || true
        
        # Install Prometheus Operator using Helm
        if command -v helm &> /dev/null; then
            helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
            helm repo update
            
            helm install prometheus prometheus-community/kube-prometheus-stack \
                --namespace $MONITORING_NAMESPACE \
                --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
                --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD:-admin}" \
                --wait
        else
            warning "Helm not installed, skipping Kubernetes monitoring setup"
        fi
    fi
}

# Verify setup
verify_setup() {
    log "Verifying monitoring setup..."
    
    sleep 10
    
    # Check if services are running
    services=("prometheus" "grafana" "loki" "promtail" "alertmanager" "node-exporter")
    
    for service in "${services[@]}"; do
        if docker ps | grep -q $service; then
            log "✓ $service is running"
        else
            warning "✗ $service is not running"
        fi
    done
    
    # Test endpoints
    endpoints=(
        "http://localhost:9090/-/healthy"
        "http://localhost:3000/api/health"
        "http://localhost:3100/ready"
        "http://localhost:9093/-/healthy"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -o /dev/null -w "%{http_code}" $endpoint | grep -q "200"; then
            log "✓ $endpoint is accessible"
        else
            warning "✗ $endpoint is not accessible"
        fi
    done
}

# Generate documentation
generate_docs() {
    log "Generating monitoring documentation..."
    
    cat > monitoring/README.md << EOF
# TradeSense Monitoring Setup

## Overview
This monitoring stack includes:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log shipping
- **Alertmanager**: Alert routing and notifications

## Access URLs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/${GRAFANA_ADMIN_PASSWORD:-admin})
- Alertmanager: http://localhost:9093
- Loki: http://localhost:3100

## Configuration
- Environment: ${ENVIRONMENT}
- Metrics retention: 30 days
- Logs retention: 30 days

## Common Tasks

### View Metrics
1. Open Prometheus at http://localhost:9090
2. Use the expression browser to query metrics

### View Dashboards
1. Open Grafana at http://localhost:3000
2. Navigate to Dashboards > TradeSense

### View Alerts
1. Open Alertmanager at http://localhost:9093
2. Check active alerts and silences

### Search Logs
1. Open Grafana at http://localhost:3000
2. Navigate to Explore
3. Select Loki as data source
4. Use LogQL to query logs

## Troubleshooting

### Check service logs
\`\`\`bash
docker logs prometheus
docker logs grafana
docker logs loki
docker logs alertmanager
\`\`\`

### Restart services
\`\`\`bash
docker restart prometheus grafana loki promtail alertmanager
\`\`\`

### Update configuration
1. Edit configuration files in monitoring/*/config/
2. Restart the affected service
3. Verify the changes took effect

## Backup
Important data to backup:
- monitoring/prometheus/data/
- monitoring/grafana/data/
- monitoring/loki/data/
- monitoring/alertmanager/data/
EOF
    
    log "Documentation generated at monitoring/README.md"
}

# Main execution
main() {
    log "Starting TradeSense monitoring setup for ${ENVIRONMENT} environment"
    
    check_prerequisites
    create_directories
    
    # Setup monitoring components
    setup_prometheus
    setup_grafana
    setup_loki
    setup_promtail
    setup_alertmanager
    setup_exporters
    setup_k8s_monitoring
    
    # Verify and document
    verify_setup
    generate_docs
    
    log "Monitoring setup completed!"
    log "Access Grafana at http://localhost:3000 (admin/${GRAFANA_ADMIN_PASSWORD:-admin})"
}

# Run main function
main "$@"