#!/bin/bash
# PostgreSQL backup script

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/postgres"
mkdir -p "$BACKUP_DIR"

source .env.production

echo "Creating PostgreSQL backup..."
PGPASSWORD=$PG_PASSWORD pg_dump -h $PG_HOST -U $PG_USER -d $PG_DATABASE -Fc > "$BACKUP_DIR/tradesense_$TIMESTAMP.dump"

# Also create SQL format for portability
PGPASSWORD=$PG_PASSWORD pg_dump -h $PG_HOST -U $PG_USER -d $PG_DATABASE > "$BACKUP_DIR/tradesense_$TIMESTAMP.sql"
gzip "$BACKUP_DIR/tradesense_$TIMESTAMP.sql"

echo "Backup created: $BACKUP_DIR/tradesense_$TIMESTAMP.dump"
