#!/bin/bash
# SQLite Backup Script for TradeSense
# Creates timestamped backups with verification

set -e  # Exit on error

# Configuration
BACKUP_DIR="./backups/sqlite"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="tradesense.db"

echo "🔍 TradeSense SQLite Backup Tool"
echo "================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if SQLite database exists
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  No SQLite database found at $DB_PATH"
    echo "This might be a fresh installation or already using PostgreSQL."
    
    # Check for other possible locations
    echo ""
    echo "Searching for SQLite databases..."
    find . -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null | grep -v ".git" | head -10
    
    echo ""
    echo "If no databases found, you may already be using PostgreSQL. Proceeding..."
    exit 0
fi

echo "✅ Found SQLite database: $DB_PATH"

# Get database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo "📊 Database size: $DB_SIZE"

# Create backup
echo ""
echo "📦 Creating backup..."
BACKUP_FILE="$BACKUP_DIR/tradesense_${TIMESTAMP}.db"
cp "$DB_PATH" "$BACKUP_FILE"

# Create checksum
echo "🔐 Generating checksum..."
CHECKSUM=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
echo "$CHECKSUM" > "$BACKUP_FILE.sha256"

# Dump to SQL for analysis
echo "📝 Creating SQL dump..."
sqlite3 "$DB_PATH" .dump > "$BACKUP_DIR/tradesense_${TIMESTAMP}.sql"

# Compress SQL dump
gzip "$BACKUP_DIR/tradesense_${TIMESTAMP}.sql"

# Get table information
echo ""
echo "📊 Database Statistics:"
echo "======================"
sqlite3 "$DB_PATH" <<EOF
.headers on
.mode column
SELECT name as 'Table Name', 
       (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=m.name) as 'Indexes',
       (SELECT COUNT(*) FROM pragma_table_info(m.name)) as 'Columns'
FROM sqlite_master m 
WHERE type='table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;
EOF

echo ""
echo "📈 Row Counts:"
echo "============="
for table in $(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"); do
    count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table")
    printf "%-30s %10s rows\n" "$table" "$count"
done

# Create backup metadata
cat > "$BACKUP_DIR/tradesense_${TIMESTAMP}.metadata" <<EOF
Backup Timestamp: $(date)
Database Path: $DB_PATH
Database Size: $DB_SIZE
Checksum: $CHECKSUM
SQLite Version: $(sqlite3 --version | head -1)
Tables: $(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
Total Rows: $(sqlite3 "$DB_PATH" "SELECT SUM(cnt) FROM ($(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'" | awk '{print "SELECT COUNT(*) as cnt FROM " $1 " UNION ALL"}' | sed '$ s/ UNION ALL$//'))")
EOF

echo ""
echo "✅ Backup completed successfully!"
echo ""
echo "📁 Backup files created:"
echo "  - Binary backup: $BACKUP_FILE"
echo "  - Checksum: $BACKUP_FILE.sha256"
echo "  - SQL dump: $BACKUP_DIR/tradesense_${TIMESTAMP}.sql.gz"
echo "  - Metadata: $BACKUP_DIR/tradesense_${TIMESTAMP}.metadata"
echo ""
echo "💡 To restore from backup:"
echo "  cp $BACKUP_FILE ./tradesense.db"
echo ""
echo "🔒 Checksum for verification: $CHECKSUM"