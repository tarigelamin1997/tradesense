#!/bin/bash

# Railway Emergency Toolkit
# Collection of emergency response scripts for disaster recovery

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SERVICES=(
    "gateway"
    "auth"
    "trading"
    "analytics"
    "market-data"
    "billing"
    "ai"
)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="emergency_response_${TIMESTAMP}.log"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Emergency backup function
emergency_backup() {
    log "🚨 Starting emergency backup of all databases..."
    
    local backup_dir="emergency_backups/${TIMESTAMP}"
    mkdir -p "$backup_dir"
    
    for service in "${SERVICES[@]}"; do
        if [[ "$service" == "gateway" ]] || [[ "$service" == "market-data" ]]; then
            continue  # Skip services without databases
        fi
        
        log "Backing up $service database..."
        
        # Get database URL
        db_url=$(railway variables get DATABASE_URL --service "tradesense-$service" 2>/dev/null || echo "")
        
        if [[ -n "$db_url" ]]; then
            # Extract connection details and perform backup
            if [[ $db_url =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
                PGPASSWORD="${BASH_REMATCH[2]}" pg_dump \
                    -h "${BASH_REMATCH[3]}" \
                    -p "${BASH_REMATCH[4]}" \
                    -U "${BASH_REMATCH[1]}" \
                    -d "${BASH_REMATCH[5]}" \
                    --no-owner \
                    --no-acl \
                    | gzip > "$backup_dir/${service}_emergency_${TIMESTAMP}.sql.gz"
                
                success "Backed up $service database"
            fi
        else
            warning "Could not get database URL for $service"
        fi
    done
    
    # Backup environment variables
    log "Backing up environment variables..."
    mkdir -p "$backup_dir/env"
    
    for service in "${SERVICES[@]}"; do
        railway variables export --service "tradesense-$service" > "$backup_dir/env/${service}.env" 2>/dev/null || warning "Failed to export env for $service"
    done
    
    success "Emergency backup completed in $backup_dir"
}

# Health check all services
health_check_all() {
    log "🏥 Checking health of all services..."
    
    local healthy=0
    local unhealthy=0
    
    declare -A SERVICE_URLS=(
        ["gateway"]="https://tradesense-gateway-production.up.railway.app"
        ["auth"]="https://tradesense-auth-production.up.railway.app"
        ["trading"]="https://tradesense-trading-production.up.railway.app"
        ["analytics"]="https://tradesense-analytics-production.up.railway.app"
        ["market-data"]="https://tradesense-market-data-production.up.railway.app"
        ["billing"]="https://tradesense-billing-production.up.railway.app"
        ["ai"]="https://tradesense-ai-production.up.railway.app"
    )
    
    for service in "${!SERVICE_URLS[@]}"; do
        url="${SERVICE_URLS[$service]}/health"
        
        if curl -sf --max-time 10 "$url" > /dev/null; then
            success "$service is healthy"
            ((healthy++))
        else
            error "$service is not responding"
            ((unhealthy++))
        fi
    done
    
    echo ""
    log "Health Check Summary: $healthy healthy, $unhealthy unhealthy"
    
    if [[ $unhealthy -gt 0 ]]; then
        return 1
    fi
    return 0
}

# Rotate all secrets
rotate_secrets() {
    log "🔐 Starting emergency secret rotation..."
    
    read -p "⚠️  This will rotate ALL secrets. Are you sure? (yes/no): " confirmation
    if [[ "$confirmation" != "yes" ]]; then
        log "Secret rotation cancelled"
        return
    fi
    
    # Backup current secrets first
    log "Backing up current secrets..."
    local secret_backup="secret_backup_${TIMESTAMP}"
    mkdir -p "$secret_backup"
    
    for service in "${SERVICES[@]}"; do
        railway variables export --service "tradesense-$service" > "$secret_backup/${service}_secrets.env" 2>/dev/null
    done
    
    # Generate new secrets
    log "Generating new secrets..."
    
    # JWT Secret (shared across services)
    NEW_JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
    
    # Inter-service secrets
    NEW_INTER_SERVICE_SECRET=$(openssl rand -base64 32)
    
    # Encryption keys
    NEW_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Update each service
    for service in "${SERVICES[@]}"; do
        log "Updating secrets for $service..."
        
        railway variables set JWT_SECRET_KEY="$NEW_JWT_SECRET" --service "tradesense-$service"
        railway variables set INTER_SERVICE_SECRET="$NEW_INTER_SERVICE_SECRET" --service "tradesense-$service"
        railway variables set ENCRYPTION_KEY="$NEW_ENCRYPTION_KEY" --service "tradesense-$service"
        
        # Service-specific secrets
        SERVICE_API_KEY=$(openssl rand -base64 32)
        railway variables set "SERVICE_API_KEY_${service^^}"="$SERVICE_API_KEY" --service "tradesense-$service"
    done
    
    # Save new secrets securely
    cat > "$secret_backup/new_secrets_${TIMESTAMP}.enc" << EOF
# New Secrets Generated at $TIMESTAMP
# STORE THIS FILE SECURELY!

JWT_SECRET_KEY=$NEW_JWT_SECRET
INTER_SERVICE_SECRET=$NEW_INTER_SERVICE_SECRET
ENCRYPTION_KEY=$NEW_ENCRYPTION_KEY

# Service API Keys
EOF
    
    success "Secret rotation completed. New secrets saved in $secret_backup/"
    warning "You must redeploy all services for the new secrets to take effect!"
}

# Restart all services
restart_all_services() {
    log "🔄 Restarting all services..."
    
    for service in "${SERVICES[@]}"; do
        log "Restarting $service..."
        railway restart --service "tradesense-$service" || error "Failed to restart $service"
        sleep 5  # Brief pause between restarts
    done
    
    success "All services restart initiated"
    
    # Wait and check health
    log "Waiting 30 seconds for services to stabilize..."
    sleep 30
    
    health_check_all
}

# Emergency shutdown
emergency_shutdown() {
    log "🛑 EMERGENCY SHUTDOWN INITIATED"
    
    read -p "⚠️  This will stop ALL services. Confirm by typing 'SHUTDOWN': " confirmation
    if [[ "$confirmation" != "SHUTDOWN" ]]; then
        log "Shutdown cancelled"
        return
    fi
    
    # Create emergency backup first
    emergency_backup
    
    # Shutdown services in reverse dependency order
    local shutdown_order=("ai" "billing" "market-data" "analytics" "trading" "auth" "gateway")
    
    for service in "${shutdown_order[@]}"; do
        log "Shutting down $service..."
        railway down --service "tradesense-$service" || error "Failed to stop $service"
    done
    
    warning "All services have been shut down"
    log "To restart, run: $0 --restore-all"
}

# Restore all services
restore_all_services() {
    log "🔧 Starting service restoration..."
    
    # Start services in dependency order
    local start_order=("auth" "gateway" "trading" "analytics" "market-data" "billing" "ai")
    
    for service in "${start_order[@]}"; do
        log "Starting $service..."
        cd "services/$service" 2>/dev/null || { error "Service directory not found for $service"; continue; }
        railway up --service "tradesense-$service" || error "Failed to start $service"
        cd - > /dev/null
        
        # Wait for service to be ready
        sleep 20
    done
    
    success "All services restoration initiated"
    
    # Check health
    sleep 30
    health_check_all
}

# DNS failover
dns_failover() {
    log "🌐 Initiating DNS failover..."
    
    warning "This requires Cloudflare API access"
    
    # This is a template - actual implementation depends on DNS provider
    cat > "dns_failover_${TIMESTAMP}.sh" << 'EOF'
#!/bin/bash
# DNS Failover Script
# Update DNS records to point to backup infrastructure

# Cloudflare API credentials
CF_API_TOKEN=${CLOUDFLARE_API_TOKEN}
CF_ZONE_ID=${CLOUDFLARE_ZONE_ID}

# Backup infrastructure IPs
BACKUP_GATEWAY_IP="xxx.xxx.xxx.xxx"

# Update A records
curl -X PUT "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/[record_id]" \
     -H "Authorization: Bearer ${CF_API_TOKEN}" \
     -H "Content-Type: application/json" \
     --data '{
       "type":"A",
       "name":"api.tradesense.com",
       "content":"'${BACKUP_GATEWAY_IP}'",
       "ttl":300,
       "proxied":true
     }'

echo "DNS failover completed"
EOF

    chmod +x "dns_failover_${TIMESTAMP}.sh"
    success "DNS failover script created: dns_failover_${TIMESTAMP}.sh"
    log "Edit the script with your actual DNS provider details before running"
}

# System diagnostics
run_diagnostics() {
    log "🔍 Running system diagnostics..."
    
    local diag_dir="diagnostics_${TIMESTAMP}"
    mkdir -p "$diag_dir"
    
    # Service logs
    log "Collecting service logs..."
    for service in "${SERVICES[@]}"; do
        railway logs --service "tradesense-$service" > "$diag_dir/${service}_logs.txt" 2>&1 &
    done
    wait
    
    # Service status
    log "Checking service status..."
    railway status > "$diag_dir/railway_status.txt" 2>&1
    
    # Environment verification
    log "Verifying environment variables..."
    for service in "${SERVICES[@]}"; do
        echo "=== $service ===" >> "$diag_dir/env_check.txt"
        railway variables --service "tradesense-$service" >> "$diag_dir/env_check.txt" 2>&1
        echo "" >> "$diag_dir/env_check.txt"
    done
    
    # Network connectivity
    log "Testing network connectivity..."
    for service in "${SERVICES[@]}"; do
        echo "=== $service ===" >> "$diag_dir/network_test.txt"
        curl -sv --max-time 5 "https://tradesense-${service}-production.up.railway.app/health" >> "$diag_dir/network_test.txt" 2>&1
        echo "" >> "$diag_dir/network_test.txt"
    done
    
    success "Diagnostics completed. Results in $diag_dir/"
}

# Show usage
usage() {
    cat << EOF
Railway Emergency Toolkit

Usage: $0 [OPTION]

Options:
    --health-check      Check health of all services
    --emergency-backup  Create emergency backup of all databases
    --rotate-secrets    Rotate all secrets (requires redeploy)
    --restart-all       Restart all services
    --shutdown          Emergency shutdown of all services
    --restore-all       Restore/start all services
    --dns-failover      Generate DNS failover script
    --diagnostics       Run full system diagnostics
    --help              Show this help message

Examples:
    $0 --health-check
    $0 --emergency-backup
    $0 --shutdown

Emergency Hotline Procedures:
1. Run health check first to assess situation
2. Create emergency backup before any major action
3. Use shutdown only in critical security incidents
4. Always document actions in incident log

EOF
}

# Main script logic
main() {
    case "${1:-}" in
        --health-check)
            health_check_all
            ;;
        --emergency-backup)
            emergency_backup
            ;;
        --rotate-secrets)
            rotate_secrets
            ;;
        --restart-all)
            restart_all_services
            ;;
        --shutdown)
            emergency_shutdown
            ;;
        --restore-all)
            restore_all_services
            ;;
        --dns-failover)
            dns_failover
            ;;
        --diagnostics)
            run_diagnostics
            ;;
        --help)
            usage
            ;;
        *)
            error "Unknown option: ${1:-}"
            usage
            exit 1
            ;;
    esac
}

# Create log directory
mkdir -p logs

# Run main function
main "$@"