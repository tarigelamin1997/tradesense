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
