#!/bin/bash
# Automated Backup Configuration for Railway Production
# Sets up scheduled backups with S3 storage and monitoring

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔐 TradeSense Automated Backup Configuration${NC}"
echo "============================================"
echo ""

# Configuration
SERVICES=("auth" "trading" "analytics" "billing" "ai")
BACKUP_SCHEDULE="0 2 * * *"  # 2 AM daily
RETENTION_DAYS=30
S3_BUCKET="tradesense-backups-prod"
AWS_REGION="us-east-1"

# Function to create backup service
create_backup_service() {
    echo -e "${BLUE}Creating backup service configuration...${NC}"
    
    cat > services/backup/Dockerfile << 'EOF'
FROM postgres:15-alpine

# Install required tools
RUN apk add --no-cache \
    bash \
    curl \
    aws-cli \
    postgresql-client \
    tzdata

# Set timezone
ENV TZ=UTC

# Copy backup scripts
COPY scripts/backup.sh /usr/local/bin/backup.sh
COPY scripts/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/*.sh

# Create backup directory
RUN mkdir -p /backups

# Health check
HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/health-check.sh || exit 1

# Run backup script
CMD ["/usr/local/bin/backup.sh"]
EOF

    # Create backup script
    cat > services/backup/scripts/backup.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Load environment variables
source /etc/environment 2>/dev/null || true

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/backup_${TIMESTAMP}.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Send notification
notify() {
    local level=$1
    local message=$2
    
    # Send to monitoring endpoint
    if [[ -n "${MONITORING_WEBHOOK:-}" ]]; then
        curl -X POST "$MONITORING_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"level\":\"$level\",\"message\":\"$message\",\"service\":\"backup\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" \
            || log "Failed to send notification"
    fi
}

# Backup function
backup_database() {
    local service=$1
    local db_url=$2
    local backup_file="${BACKUP_DIR}/${service}_${TIMESTAMP}.sql.gz"
    
    log "Starting backup for $service..."
    
    # Parse database URL
    if [[ $db_url =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        local user="${BASH_REMATCH[1]}"
        local password="${BASH_REMATCH[2]}"
        local host="${BASH_REMATCH[3]}"
        local port="${BASH_REMATCH[4]}"
        local dbname="${BASH_REMATCH[5]}"
        
        # Perform backup with progress
        PGPASSWORD="$password" pg_dump \
            -h "$host" \
            -p "$port" \
            -U "$user" \
            -d "$dbname" \
            --no-owner \
            --no-acl \
            --clean \
            --if-exists \
            --verbose \
            --format=custom \
            --compress=9 \
            -f "$backup_file" 2>&1 | tee -a "$LOG_FILE"
        
        # Check backup size
        local size=$(du -h "$backup_file" | cut -f1)
        log "Backup complete: $backup_file ($size)"
        
        # Upload to S3
        if [[ -n "${S3_BUCKET:-}" ]]; then
            log "Uploading to S3..."
            aws s3 cp "$backup_file" "s3://${S3_BUCKET}/${service}/${TIMESTAMP}/" \
                --storage-class STANDARD_IA \
                --metadata "service=$service,timestamp=$TIMESTAMP" \
                || { log "S3 upload failed"; return 1; }
            
            # Remove local file after successful upload
            rm -f "$backup_file"
            log "S3 upload complete"
        fi
        
        return 0
    else
        log "ERROR: Invalid database URL format for $service"
        return 1
    fi
}

# Main backup process
main() {
    log "🔐 Starting automated backup process"
    notify "info" "Backup process started"
    
    local success_count=0
    local failed_count=0
    
    # Backup each service
    for service in auth trading analytics billing ai; do
        # Get database URL from environment
        db_url_var="DATABASE_URL_${service^^}"
        db_url="${!db_url_var:-}"
        
        if [[ -n "$db_url" ]]; then
            if backup_database "$service" "$db_url"; then
                ((success_count++))
            else
                ((failed_count++))
                notify "error" "Backup failed for $service"
            fi
        else
            log "WARNING: No database URL for $service"
            ((failed_count++))
        fi
    done
    
    # Clean old backups from S3
    if [[ -n "${S3_BUCKET:-}" ]] && [[ -n "${RETENTION_DAYS:-}" ]]; then
        log "Cleaning old backups (older than $RETENTION_DAYS days)..."
        
        cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        aws s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "" | \
        jq -r '.Contents[] | select(.LastModified < "'$cutoff_date'") | .Key' | \
        while read -r key; do
            aws s3 rm "s3://${S3_BUCKET}/${key}"
            log "Deleted old backup: $key"
        done
    fi
    
    # Summary
    log "✅ Backup process complete"
    log "Success: $success_count, Failed: $failed_count"
    
    if [[ $failed_count -eq 0 ]]; then
        notify "success" "All backups completed successfully"
    else
        notify "warning" "Backup completed with $failed_count failures"
    fi
    
    # Update metrics
    echo "backup_success_count $success_count" > /var/lib/node_exporter/textfile_collector/backup.prom
    echo "backup_failed_count $failed_count" >> /var/lib/node_exporter/textfile_collector/backup.prom
    echo "backup_last_run_timestamp $(date +%s)" >> /var/lib/node_exporter/textfile_collector/backup.prom
}

# Run based on schedule or immediately
if [[ "${1:-}" == "cron" ]]; then
    # Set up cron job
    echo "${BACKUP_SCHEDULE} /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" | crontab -
    log "Cron job configured: $BACKUP_SCHEDULE"
    
    # Keep container running
    crond -f
else
    # Run backup immediately
    main
fi
EOF

    # Create health check script
    cat > services/backup/scripts/health-check.sh << 'EOF'
#!/bin/sh
# Check if backup service is healthy

# Check if last backup was successful (within 25 hours)
LAST_BACKUP_FILE="/var/lib/node_exporter/textfile_collector/backup.prom"
if [ -f "$LAST_BACKUP_FILE" ]; then
    LAST_RUN=$(grep "backup_last_run_timestamp" "$LAST_BACKUP_FILE" | awk '{print $2}')
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - LAST_RUN))
    
    # If last backup was more than 25 hours ago, unhealthy
    if [ $TIME_DIFF -gt 90000 ]; then
        exit 1
    fi
else
    # No backup file yet, check if service just started
    UPTIME=$(awk '{print int($1)}' /proc/uptime)
    if [ $UPTIME -gt 3600 ]; then
        # Running for more than an hour without backup file
        exit 1
    fi
fi

exit 0
EOF

    # Create Railway configuration
    cat > services/backup/railway.toml << 'EOF'
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 60
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
cronSchedule = "0 2 * * *"

[env]
TZ = "UTC"
BACKUP_SCHEDULE = "0 2 * * *"
RETENTION_DAYS = "30"
EOF

    echo -e "${GREEN}✅ Backup service created${NC}"
}

# Function to configure S3 bucket
configure_s3_bucket() {
    echo -e "${BLUE}Configuring S3 bucket for backups...${NC}"
    
    # Create bucket policy
    cat > /tmp/bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedObjectUploads",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::${S3_BUCKET}/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        },
        {
            "Sid": "DenyInsecureConnections",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::${S3_BUCKET}",
                "arn:aws:s3:::${S3_BUCKET}/*"
            ],
            "Condition": {
                "Bool": {
                    "aws:SecureTransport": "false"
                }
            }
        }
    ]
}
EOF

    # Create lifecycle policy
    cat > /tmp/lifecycle-policy.json << EOF
{
    "Rules": [
        {
            "ID": "TransitionToIA",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 7,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 30,
                    "StorageClass": "GLACIER"
                }
            ]
        },
        {
            "ID": "DeleteOldBackups",
            "Status": "Enabled",
            "Expiration": {
                "Days": ${RETENTION_DAYS}
            }
        }
    ]
}
EOF

    echo -e "${GREEN}✅ S3 configuration files created${NC}"
    echo ""
    echo "To create the S3 bucket, run:"
    echo "  aws s3 mb s3://${S3_BUCKET} --region ${AWS_REGION}"
    echo "  aws s3api put-bucket-versioning --bucket ${S3_BUCKET} --versioning-configuration Status=Enabled"
    echo "  aws s3api put-bucket-encryption --bucket ${S3_BUCKET} --server-side-encryption-configuration '{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"AES256\"}}]}'"
    echo "  aws s3api put-bucket-policy --bucket ${S3_BUCKET} --policy file:///tmp/bucket-policy.json"
    echo "  aws s3api put-bucket-lifecycle-configuration --bucket ${S3_BUCKET} --lifecycle-configuration file:///tmp/lifecycle-policy.json"
}

# Function to create monitoring dashboard
create_monitoring_dashboard() {
    echo -e "${BLUE}Creating backup monitoring configuration...${NC}"
    
    cat > monitoring/backup-alerts.yml << 'EOF'
# Backup Monitoring Alerts

alerts:
  - name: BackupFailed
    condition: backup_failed_count > 0
    severity: critical
    message: "Database backup failed for {{ .Labels.service }}"
    channels:
      - slack
      - pagerduty
    
  - name: BackupDelayed
    condition: time() - backup_last_run_timestamp > 90000  # 25 hours
    severity: warning
    message: "Database backup has not run in over 24 hours"
    channels:
      - slack
    
  - name: BackupStorageHigh
    condition: backup_storage_used_gb > 1000
    severity: warning
    message: "Backup storage exceeds 1TB"
    channels:
      - email

dashboards:
  - name: "Database Backups"
    panels:
      - title: "Backup Success Rate"
        query: "rate(backup_success_count[24h])"
        type: graph
        
      - title: "Last Backup Time"
        query: "time() - backup_last_run_timestamp"
        type: stat
        unit: hours
        
      - title: "Storage Used"
        query: "backup_storage_used_gb"
        type: gauge
        max: 2000
        
      - title: "Backup Duration"
        query: "backup_duration_seconds"
        type: histogram
EOF

    echo -e "${GREEN}✅ Monitoring configuration created${NC}"
}

# Function to set up Railway environment variables
setup_railway_env() {
    echo -e "${BLUE}Setting up Railway environment variables...${NC}"
    
    # Create environment setup script
    cat > scripts/setup-backup-env.sh << 'EOF'
#!/bin/bash
# Set up backup service environment variables in Railway

# S3 Configuration
railway variables set S3_BUCKET="${S3_BUCKET}" --service backup
railway variables set AWS_REGION="${AWS_REGION}" --service backup
railway variables set AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" --service backup
railway variables set AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" --service backup

# Get database URLs from other services
for service in auth trading analytics billing ai; do
    DB_URL=$(railway variables get DATABASE_URL --service "tradesense-${service}")
    railway variables set "DATABASE_URL_${service^^}=${DB_URL}" --service backup
done

# Monitoring webhook
railway variables set MONITORING_WEBHOOK="${MONITORING_WEBHOOK}" --service backup

echo "✅ Backup service environment configured"
EOF

    chmod +x scripts/setup-backup-env.sh
    echo -e "${GREEN}✅ Environment setup script created${NC}"
}

# Function to create restore procedures
create_restore_procedures() {
    echo -e "${BLUE}Creating restore procedures...${NC}"
    
    cat > scripts/restore-from-backup.sh << 'EOF'
#!/bin/bash
# Restore database from backup

set -euo pipefail

# Usage
if [ $# -lt 2 ]; then
    echo "Usage: $0 <service> <backup-date> [target-env]"
    echo "Example: $0 auth 20240124 staging"
    exit 1
fi

SERVICE=$1
BACKUP_DATE=$2
TARGET_ENV=${3:-staging}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔄 Restoring $SERVICE from backup date: $BACKUP_DATE"
echo "Target environment: $TARGET_ENV"
echo ""

# Download backup from S3
echo "Downloading backup from S3..."
BACKUP_FILE="/tmp/${SERVICE}_${BACKUP_DATE}.sql.gz"
aws s3 cp "s3://${S3_BUCKET}/${SERVICE}/${BACKUP_DATE}/" "$BACKUP_FILE" --recursive

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found${NC}"
    exit 1
fi

# Get target database URL
if [ "$TARGET_ENV" == "production" ]; then
    read -p "⚠️  WARNING: Restoring to PRODUCTION. Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled"
        exit 1
    fi
fi

# Get database URL for target environment
DB_URL=$(railway variables get DATABASE_URL --service "tradesense-${SERVICE}" --environment "$TARGET_ENV")

# Parse database URL
if [[ $DB_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
    USER="${BASH_REMATCH[1]}"
    PASSWORD="${BASH_REMATCH[2]}"
    HOST="${BASH_REMATCH[3]}"
    PORT="${BASH_REMATCH[4]}"
    DBNAME="${BASH_REMATCH[5]}"
    
    # Create restore point
    echo "Creating restore point..."
    RESTORE_POINT="before_restore_$(date +%Y%m%d_%H%M%S)"
    PGPASSWORD="$PASSWORD" pg_dump -h "$HOST" -p "$PORT" -U "$USER" -d "$DBNAME" -f "/tmp/${RESTORE_POINT}.sql"
    
    # Perform restore
    echo "Restoring database..."
    PGPASSWORD="$PASSWORD" pg_restore \
        -h "$HOST" \
        -p "$PORT" \
        -U "$USER" \
        -d "$DBNAME" \
        --clean \
        --if-exists \
        --no-owner \
        --no-acl \
        --verbose \
        "$BACKUP_FILE"
    
    echo -e "${GREEN}✅ Restore complete${NC}"
    echo "Restore point saved at: /tmp/${RESTORE_POINT}.sql"
else
    echo -e "${RED}❌ Invalid database URL${NC}"
    exit 1
fi
EOF

    chmod +x scripts/restore-from-backup.sh
    echo -e "${GREEN}✅ Restore procedures created${NC}"
}

# Main execution
main() {
    echo "This script will configure automated backups for Railway"
    echo ""
    
    # Create directories
    mkdir -p services/backup/scripts
    mkdir -p monitoring
    mkdir -p scripts
    
    # Run setup functions
    create_backup_service
    configure_s3_bucket
    create_monitoring_dashboard
    setup_railway_env
    create_restore_procedures
    
    echo ""
    echo -e "${GREEN}✨ Automated backup configuration complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create S3 bucket using the AWS commands above"
    echo "2. Deploy backup service: cd services/backup && railway up"
    echo "3. Configure environment: ./scripts/setup-backup-env.sh"
    echo "4. Test backup: railway run ./backup.sh --service backup"
    echo "5. Monitor backups in your dashboard"
    echo ""
    echo "📝 Documentation generated:"
    echo "  - services/backup/ - Backup service"
    echo "  - scripts/restore-from-backup.sh - Restore procedure"
    echo "  - monitoring/backup-alerts.yml - Monitoring config"
}

# Run main function
main "$@"