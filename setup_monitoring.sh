#!/bin/bash

# Monitoring Setup Script for TradeSense
# Sets up Prometheus, Grafana, and log aggregation

echo "🚀 Setting up TradeSense Monitoring Stack..."
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create monitoring directory
mkdir -p monitoring/{prometheus,grafana,loki}

# Step 1: Create Prometheus configuration
echo -e "\n${YELLOW}1. Creating Prometheus configuration...${NC}"
cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'tradesense-backend'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/api/v1/monitoring/metrics'
    bearer_token: 'YOUR_ADMIN_TOKEN_HERE'

  - job_name: 'tradesense-postgres'
    static_configs:
      - targets: ['tradesense-postgres:9187']

  - job_name: 'tradesense-redis'
    static_configs:
      - targets: ['tradesense-redis:9121']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

# Step 2: Create Grafana provisioning
echo -e "\n${YELLOW}2. Creating Grafana provisioning...${NC}"
mkdir -p monitoring/grafana/provisioning/{dashboards,datasources}

cat > monitoring/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Step 3: Create docker-compose for monitoring
echo -e "\n${YELLOW}3. Creating monitoring docker-compose...${NC}"
cat > docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: tradesense-prometheus
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    ports:
      - "9090:9090"
    networks:
      - tradesense-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: tradesense-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=tradesense123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - tradesense-network
    depends_on:
      - prometheus
    restart: unless-stopped

  loki:
    image: grafana/loki:latest
    container_name: tradesense-loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki-data:/loki
    networks:
      - tradesense-network
    restart: unless-stopped

  promtail:
    image: grafana/promtail:latest
    container_name: tradesense-promtail
    volumes:
      - /var/log:/var/log:ro
      - ./logs:/logs:ro
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - tradesense-network
    depends_on:
      - loki
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: tradesense-node-exporter
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    networks:
      - tradesense-network

  redis-exporter:
    image: oliver006/redis_exporter:latest
    container_name: tradesense-redis-exporter
    environment:
      REDIS_ADDR: redis://tradesense-redis:6379
    ports:
      - "9121:9121"
    networks:
      - tradesense-network
    depends_on:
      - redis

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: tradesense-postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://tradesense_user:2ca9bfcf1a40257caa7b4be903c7fe22@tradesense-postgres:5432/tradesense?sslmode=disable"
    ports:
      - "9187:9187"
    networks:
      - tradesense-network
    depends_on:
      - postgres

volumes:
  prometheus-data:
  grafana-data:
  loki-data:

networks:
  tradesense-network:
    external: true
EOF

# Step 4: Create Promtail configuration
echo -e "\n${YELLOW}4. Creating Promtail configuration...${NC}"
cat > monitoring/promtail-config.yml << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: tradesense
    static_configs:
      - targets:
          - localhost
        labels:
          job: tradesense
          __path__: /logs/*.log
EOF

# Step 5: Create TradeSense Dashboard
echo -e "\n${YELLOW}5. Creating Grafana dashboard...${NC}"
cat > monitoring/grafana/provisioning/dashboards/tradesense.json << 'EOF'
{
  "dashboard": {
    "title": "TradeSense Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(tradesense_http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(tradesense_http_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(tradesense_http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "rate(tradesense_cache_hits_total[5m]) / (rate(tradesense_cache_hits_total[5m]) + rate(tradesense_cache_misses_total[5m]))"
          }
        ]
      }
    ]
  }
}
EOF

# Step 6: Install Python monitoring dependencies
echo -e "\n${YELLOW}6. Installing Python monitoring dependencies...${NC}"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install prometheus-client python-json-logger sentry-sdk[fastapi] psutil
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found. Install manually:${NC}"
    echo "pip install prometheus-client python-json-logger sentry-sdk[fastapi] psutil"
fi

# Step 7: Create monitoring network
echo -e "\n${YELLOW}7. Creating Docker network...${NC}"
docker network create tradesense-network 2>/dev/null || echo "Network already exists"

# Step 8: Create systemd service (optional)
echo -e "\n${YELLOW}8. Creating systemd service template...${NC}"
cat > tradesense-monitoring.service << 'EOF'
[Unit]
Description=TradeSense Monitoring Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/tradesense
ExecStart=/usr/local/bin/docker-compose -f docker-compose.monitoring.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.monitoring.yml down
StandardOutput=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "\n${GREEN}✅ Monitoring setup complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Update monitoring/prometheus/prometheus.yml with your admin token"
echo "2. Start the monitoring stack:"
echo "   docker compose -f docker-compose.monitoring.yml up -d"
echo "3. Access services:"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/tradesense123)"
echo "   - Loki: http://localhost:3100"
echo "4. Configure alerts in Grafana"
echo "5. Set SENTRY_DSN environment variable for error tracking"
echo ""
echo "For production, consider:"
echo "- Using external monitoring services (Datadog, New Relic)"
echo "- Setting up PagerDuty integration"
echo "- Configuring log retention policies"
echo "- Implementing custom dashboards"