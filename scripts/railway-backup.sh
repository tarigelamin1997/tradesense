#!/bin/bash

# Railway Database Backup Script
# Automated backup for all PostgreSQL databases on Railway

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKUP_DIR="./backups/railway"
RETENTION_DAYS=30
S3_BUCKET=${RAILWAY_BACKUP_BUCKET:-""}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Services with PostgreSQL databases
SERVICES=(
    "auth"
    "trading"
    "analytics"
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

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v railway >/dev/null 2>&1; then
        error "Railway CLI not installed"
        echo "Install with: npm install -g @railway/cli"
        exit 1
    fi
    
    if ! command -v pg_dump >/dev/null 2>&1; then
        error "PostgreSQL client not installed"
        echo "Install with: brew install postgresql (macOS)"
        exit 1
    fi
    
    # Check Railway login
    if ! railway whoami >/dev/null 2>&1; then
        error "Not logged in to Railway"
        echo "Run: railway login"
        exit 1
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    success "Prerequisites check passed"
}

# Get database URL for a service
get_database_url() {
    local service=$1
    log "Getting database URL for $service..."
    
    # Try to get DATABASE_URL from Railway
    local db_url=$(railway variables get DATABASE_URL --service "tradesense-$service" 2>/dev/null || echo "")
    
    if [[ -z "$db_url" ]]; then
        warning "Could not get DATABASE_URL for $service"
        return 1
    fi
    
    echo "$db_url"
}

# Backup a single database
backup_database() {
    local service=$1
    local db_url=$2
    local backup_file="${BACKUP_DIR}/${service}_${TIMESTAMP}.sql.gz"
    
    log "Backing up $service database..."
    
    # Extract connection details from URL
    if [[ $db_url =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        local user="${BASH_REMATCH[1]}"
        local password="${BASH_REMATCH[2]}"
        local host="${BASH_REMATCH[3]}"
        local port="${BASH_REMATCH[4]}"
        local dbname="${BASH_REMATCH[5]}"
        
        # Perform backup
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
            | gzip > "$backup_file"
        
        # Check backup size
        local size=$(du -h "$backup_file" | cut -f1)
        success "Backup complete: $backup_file ($size)"
        
        # Upload to S3 if configured
        if [[ -n "$S3_BUCKET" ]] && command -v aws >/dev/null 2>&1; then
            log "Uploading to S3..."
            aws s3 cp "$backup_file" "s3://${S3_BUCKET}/railway-backups/${service}/" || warning "S3 upload failed"
        fi
        
        return 0
    else
        error "Invalid database URL format for $service"
        return 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
    
    # Clean S3 if configured
    if [[ -n "$S3_BUCKET" ]] && command -v aws >/dev/null 2>&1; then
        aws s3 ls "s3://${S3_BUCKET}/railway-backups/" --recursive | \
        while read -r line; do
            createDate=$(echo $line | awk '{print $1" "$2}')
            createDate=$(date -d "$createDate" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$createDate" +%s)
            olderThan=$(date -d "$RETENTION_DAYS days ago" +%s 2>/dev/null || date -v-${RETENTION_DAYS}d +%s)
            
            if [[ $createDate -lt $olderThan ]]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BUCKET}/$fileName"
            fi
        done
    fi
    
    success "Cleanup complete"
}

# Create backup summary
create_summary() {
    local summary_file="${BACKUP_DIR}/backup_summary_${TIMESTAMP}.txt"
    
    cat > "$summary_file" << EOF
Railway Database Backup Summary
==============================
Date: $(date)
Timestamp: $TIMESTAMP

Backups Created:
EOF
    
    for service in "${SERVICES[@]}"; do
        local backup_file="${BACKUP_DIR}/${service}_${TIMESTAMP}.sql.gz"
        if [[ -f "$backup_file" ]]; then
            local size=$(du -h "$backup_file" | cut -f1)
            echo "- $service: $backup_file ($size)" >> "$summary_file"
        else
            echo "- $service: FAILED" >> "$summary_file"
        fi
    done
    
    echo "" >> "$summary_file"
    echo "Backup Location: $BACKUP_DIR" >> "$summary_file"
    
    if [[ -n "$S3_BUCKET" ]]; then
        echo "S3 Bucket: $S3_BUCKET" >> "$summary_file"
    fi
    
    cat "$summary_file"
}

# Create restore script
create_restore_script() {
    local restore_script="${BACKUP_DIR}/restore_${TIMESTAMP}.sh"
    
    cat > "$restore_script" << 'EOF'
#!/bin/bash
# Railway Database Restore Script
# Generated: $(date)

set -euo pipefail

# Usage: ./restore.sh <service> <backup_file>

SERVICE=$1
BACKUP_FILE=$2

if [[ -z "$SERVICE" ]] || [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <service> <backup_file>"
    echo "Services: auth, trading, analytics, billing, ai"
    exit 1
fi

# Get database URL
DB_URL=$(railway variables get DATABASE_URL --service "tradesense-$SERVICE")

if [[ -z "$DB_URL" ]]; then
    echo "Could not get DATABASE_URL for $SERVICE"
    exit 1
fi

# Extract connection details
if [[ $DB_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
    USER="${BASH_REMATCH[1]}"
    PASSWORD="${BASH_REMATCH[2]}"
    HOST="${BASH_REMATCH[3]}"
    PORT="${BASH_REMATCH[4]}"
    DBNAME="${BASH_REMATCH[5]}"
    
    echo "Restoring $SERVICE database from $BACKUP_FILE..."
    
    # Decompress and restore
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="$PASSWORD" psql \
        -h "$HOST" \
        -p "$PORT" \
        -U "$USER" \
        -d "$DBNAME" \
        -v ON_ERROR_STOP=1
    
    echo "Restore complete!"
else
    echo "Invalid database URL format"
    exit 1
fi
EOF
    
    chmod +x "$restore_script"
    success "Restore script created: $restore_script"
}

# Main backup process
main() {
    log "🔐 Starting Railway database backup..."
    
    check_prerequisites
    
    local success_count=0
    local failed_count=0
    
    # Backup each service
    for service in "${SERVICES[@]}"; do
        echo ""
        db_url=$(get_database_url "$service")
        
        if [[ -n "$db_url" ]]; then
            if backup_database "$service" "$db_url"; then
                ((success_count++))
            else
                ((failed_count++))
            fi
        else
            ((failed_count++))
        fi
    done
    
    echo ""
    cleanup_old_backups
    
    echo ""
    create_summary
    create_restore_script
    
    echo ""
    success "✨ Backup process complete!"
    log "Successfully backed up: $success_count services"
    
    if [[ $failed_count -gt 0 ]]; then
        warning "Failed backups: $failed_count services"
    fi
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Verify backup files in: $BACKUP_DIR"
    echo "2. Test restore procedure with a dev environment"
    echo "3. Set up automated backups with cron"
    echo "4. Configure S3 for offsite backups"
}

# Run main function
main "$@"