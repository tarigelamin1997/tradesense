#!/bin/bash

# Railway Cost Analysis Script
# Generates cost reports and optimization recommendations

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REPORT_DIR="./reports/railway"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/cost_report_${TIMESTAMP}.md"

# Railway pricing (as of 2024)
HOBBY_BASE_COST=5  # $5/month base
MEMORY_COST_PER_GB=10  # $10/GB/month
VCPU_COST=20  # $20/vCPU/month
POSTGRES_COST=5  # $5/month per database
REDIS_COST=5  # $5/month

# Services
SERVICES=(
    "gateway"
    "auth"
    "trading"
    "analytics"
    "market-data"
    "billing"
    "ai"
)

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Initialize report
init_report() {
    mkdir -p "$REPORT_DIR"
    
    cat > "$REPORT_FILE" << EOF
# Railway Cost Report
Generated: $(date)

## Executive Summary

This report analyzes the costs of running TradeSense on Railway and provides optimization recommendations.

## Current Infrastructure

### Services
- **Microservices**: 7 (Gateway, Auth, Trading, Analytics, Market Data, Billing, AI)
- **Databases**: 5 PostgreSQL + 1 Redis
- **Environment**: Production

## Cost Breakdown

### Base Costs
EOF
}

# Calculate base costs
calculate_base_costs() {
    log "Calculating base costs..."
    
    local service_count=${#SERVICES[@]}
    local postgres_count=5
    local redis_count=1
    
    local base_cost=$((HOBBY_BASE_COST))
    local db_cost=$((postgres_count * POSTGRES_COST + redis_count * REDIS_COST))
    local total_base=$((base_cost + db_cost))
    
    cat >> "$REPORT_FILE" << EOF

| Component | Quantity | Unit Cost | Total Cost |
|-----------|----------|-----------|------------|
| Hobby Plan | 1 | \$$HOBBY_BASE_COST/month | \$$base_cost/month |
| PostgreSQL | $postgres_count | \$$POSTGRES_COST/month | \$$((postgres_count * POSTGRES_COST))/month |
| Redis | $redis_count | \$$REDIS_COST/month | \$$REDIS_COST/month |
| **Total Base** | | | **\$$total_base/month** |

### Resource Usage Costs (Estimated)
EOF
    
    echo "$total_base"
}

# Estimate resource usage
estimate_resource_usage() {
    log "Estimating resource usage..."
    
    # Default estimates per service
    declare -A MEMORY_USAGE=(
        ["gateway"]="512MB"
        ["auth"]="512MB"
        ["trading"]="1GB"
        ["analytics"]="1GB"
        ["market-data"]="512MB"
        ["billing"]="512MB"
        ["ai"]="2GB"
    )
    
    declare -A CPU_USAGE=(
        ["gateway"]="0.5"
        ["auth"]="0.5"
        ["trading"]="1.0"
        ["analytics"]="1.0"
        ["market-data"]="0.5"
        ["billing"]="0.5"
        ["ai"]="2.0"
    )
    
    cat >> "$REPORT_FILE" << EOF

| Service | Memory | vCPU | Est. Memory Cost | Est. CPU Cost |
|---------|--------|------|------------------|---------------|
EOF
    
    local total_memory_cost=0
    local total_cpu_cost=0
    
    for service in "${SERVICES[@]}"; do
        local mem=${MEMORY_USAGE[$service]}
        local cpu=${CPU_USAGE[$service]}
        
        # Convert memory to GB
        local mem_gb=0
        if [[ $mem == *"GB"* ]]; then
            mem_gb=${mem%GB}
        else
            mem_gb=$(echo "scale=2; ${mem%MB} / 1024" | bc)
        fi
        
        local mem_cost=$(echo "scale=2; $mem_gb * $MEMORY_COST_PER_GB" | bc)
        local cpu_cost=$(echo "scale=2; $cpu * $VCPU_COST" | bc)
        
        total_memory_cost=$(echo "scale=2; $total_memory_cost + $mem_cost" | bc)
        total_cpu_cost=$(echo "scale=2; $total_cpu_cost + $cpu_cost" | bc)
        
        echo "| $service | $mem | $cpu | \$$mem_cost | \$$cpu_cost |" >> "$REPORT_FILE"
    done
    
    cat >> "$REPORT_FILE" << EOF
| **Total** | | | **\$$total_memory_cost** | **\$$total_cpu_cost** |

**Note**: Resource costs are usage-based and vary with actual consumption.
EOF
    
    echo "$total_memory_cost $total_cpu_cost"
}

# Generate cost optimization recommendations
generate_recommendations() {
    log "Generating optimization recommendations..."
    
    cat >> "$REPORT_FILE" << EOF

## Cost Optimization Recommendations

### 1. Resource Right-Sizing
- **Monitor actual usage**: Use Railway's metrics to identify over-provisioned services
- **Reduce memory allocation** for services using <50% of allocated memory
- **Implement auto-scaling** to handle variable loads efficiently

### 2. Service Consolidation
Consider consolidating low-traffic services:
- Merge Analytics into Trading service (save ~\$15-20/month)
- Combine Billing and Auth services (save ~\$10-15/month)

### 3. Database Optimization
- **Connection pooling**: Reduce database connections
- **Query optimization**: Improve slow queries to reduce CPU usage
- **Archive old data**: Move historical data to cheaper storage

### 4. Caching Strategy
- **Implement Redis caching** aggressively to reduce database load
- **Use CDN** for static assets (Vercel handles this for frontend)
- **API response caching** for frequently accessed data

### 5. Development Environment
- **Use sleep settings**: Configure dev environments to sleep after inactivity
- **Share databases** in development to reduce costs
- **Use local development** when possible

## Estimated Savings

| Optimization | Potential Monthly Savings |
|--------------|--------------------------|
| Resource right-sizing | \$20-30 |
| Service consolidation | \$25-35 |
| Database optimization | \$10-15 |
| Development environment | \$15-20 |
| **Total Potential Savings** | **\$70-100** |

## Implementation Priority

1. **Week 1**: Resource monitoring and right-sizing
2. **Week 2**: Implement aggressive caching
3. **Week 3**: Optimize database queries
4. **Month 2**: Consider service consolidation

EOF
}

# Create monitoring dashboard
create_monitoring_setup() {
    log "Creating monitoring setup..."
    
    cat >> "$REPORT_FILE" << EOF

## Monitoring Setup

### Key Metrics to Track
1. **Memory Usage**: Aim for 70-80% utilization
2. **CPU Usage**: Target 60-70% average
3. **Response Times**: Monitor p95 latency
4. **Error Rates**: Track failed requests
5. **Database Connections**: Monitor pool usage

### Alerting Thresholds
- Memory usage >90% for 5 minutes
- CPU usage >85% for 10 minutes
- Response time >1s p95
- Error rate >1%
- Database connections >80% of pool

### Cost Tracking Script
\`\`\`bash
# Add to crontab for weekly reports
0 9 * * 1 /path/to/railway-cost-report.sh
\`\`\`

EOF
}

# Generate cost projection
generate_projection() {
    log "Generating cost projection..."
    
    cat >> "$REPORT_FILE" << EOF

## Cost Projections

### Current State (Estimated)
- **Monthly Cost**: \$50-100
- **Annual Cost**: \$600-1,200

### With Optimizations
- **Monthly Cost**: \$30-50
- **Annual Cost**: \$360-600
- **Annual Savings**: \$240-600

### Growth Scenarios

| Users | Current Cost | Optimized Cost | Savings |
|-------|--------------|----------------|---------|
| 1K | \$50-100 | \$30-50 | 40% |
| 10K | \$200-300 | \$120-180 | 40% |
| 100K | \$800-1,200 | \$500-750 | 37% |

EOF
}

# Create action items
create_action_items() {
    log "Creating action items..."
    
    cat >> "$REPORT_FILE" << EOF

## Action Items

### Immediate (This Week)
- [ ] Set up resource monitoring dashboard
- [ ] Configure memory limits for all services
- [ ] Implement basic caching for hot paths
- [ ] Review and optimize database indexes

### Short Term (This Month)
- [ ] Implement connection pooling
- [ ] Set up automated cost alerts
- [ ] Configure development environment sleep
- [ ] Optimize Docker images for size

### Long Term (Quarter)
- [ ] Evaluate service consolidation
- [ ] Implement horizontal scaling
- [ ] Consider Railway Teams plan if needed
- [ ] Explore volume discounts

## Monitoring Commands

\`\`\`bash
# Check service metrics
railway logs --service tradesense-gateway

# Monitor resource usage
railway status

# View current usage
railway usage
\`\`\`

## Useful Links
- [Railway Pricing](https://railway.app/pricing)
- [Railway Docs](https://docs.railway.app)
- [Cost Optimization Guide](https://blog.railway.app/p/optimize-costs)

---
*Report generated by railway-cost-report.sh*
EOF
}

# Main function
main() {
    log "📊 Generating Railway cost report..."
    
    init_report
    
    # Calculate costs
    base_cost=$(calculate_base_costs)
    read mem_cost cpu_cost <<< $(estimate_resource_usage)
    
    # Total estimated cost
    total_cost=$(echo "scale=2; $base_cost + $mem_cost + $cpu_cost" | bc)
    
    echo "" >> "$REPORT_FILE"
    echo "### Total Estimated Monthly Cost: \$$total_cost" >> "$REPORT_FILE"
    
    # Generate sections
    generate_recommendations
    create_monitoring_setup
    generate_projection
    create_action_items
    
    success "✨ Cost report generated: $REPORT_FILE"
    
    # Display summary
    echo ""
    echo -e "${CYAN}Cost Summary:${NC}"
    echo "- Base costs: \$$base_cost/month"
    echo "- Estimated resource costs: \$$(echo "scale=2; $mem_cost + $cpu_cost" | bc)/month"
    echo "- Total estimated: \$$total_cost/month"
    echo "- Potential savings: \$70-100/month (with optimizations)"
    
    echo ""
    echo "📄 Full report: $REPORT_FILE"
}

# Run main function
main "$@"