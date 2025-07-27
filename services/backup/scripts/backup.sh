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
