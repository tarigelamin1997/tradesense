#!/bin/bash
# Production Database Migration Script
# Safely runs database migrations on all services with proper backups

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔄 TradeSense Production Migration Script"
echo "========================================"
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found!${NC}"
    echo "Please install: npm install -g @railway/cli"
    exit 1
fi

# Services that need migrations
SERVICES=("auth" "trading" "analytics" "billing")

# Function to backup database
backup_database() {
    local service=$1
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="./backups/$service"
    
    echo -e "${BLUE}📦 Creating backup for $service...${NC}"
    mkdir -p "$backup_dir"
    
    # Get database URL from Railway
    local db_url=$(railway variables get DATABASE_URL --service "$service" 2>/dev/null || echo "")
    
    if [ -z "$db_url" ]; then
        echo -e "${YELLOW}⚠️  No database found for $service, skipping backup${NC}"
        return 1
    fi
    
    # Create backup using Railway's database URL
    if railway run --service "$service" pg_dump "$db_url" > "$backup_dir/backup_$timestamp.sql"; then
        gzip "$backup_dir/backup_$timestamp.sql"
        echo -e "${GREEN}✅ Backup created: $backup_dir/backup_$timestamp.sql.gz${NC}"
        return 0
    else
        echo -e "${RED}❌ Backup failed for $service${NC}"
        return 1
    fi
}

# Function to run migrations
run_migrations() {
    local service=$1
    
    echo -e "${BLUE}🚀 Running migrations for $service...${NC}"
    
    # Create migration script
    cat > "migrate_$service.py" <<'EOF'
import os
import sys
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found!")
    sys.exit(1)

print(f"Connecting to database...")

# Test connection
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"Connected to: {result.scalar()}")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# Run Alembic migrations
try:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    
    # Check current revision
    from alembic.runtime.migration import MigrationContext
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        print(f"Current revision: {current_rev}")
    
    # Run migrations
    print("Running migrations...")
    command.upgrade(alembic_cfg, "head")
    
    # Verify new revision
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        new_rev = context.get_current_revision()
        print(f"New revision: {new_rev}")
    
    print("✅ Migrations completed successfully!")
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
EOF

    # Copy migration script to service and run
    if railway run --service "$service" python migrate_$service.py; then
        echo -e "${GREEN}✅ Migrations completed for $service${NC}"
        rm -f "migrate_$service.py"
        return 0
    else
        echo -e "${RED}❌ Migrations failed for $service${NC}"
        rm -f "migrate_$service.py"
        return 1
    fi
}

# Function to verify migrations
verify_migrations() {
    local service=$1
    
    echo -e "${BLUE}🔍 Verifying migrations for $service...${NC}"
    
    # Create verification script
    cat > "verify_$service.py" <<'EOF'
import os
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found!")
    exit(1)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

# Check tables
tables = inspector.get_table_names()
print(f"Tables found: {len(tables)}")
for table in sorted(tables):
    print(f"  - {table}")

# Check alembic version
with engine.connect() as conn:
    try:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"\nAlembic version: {version}")
    except:
        print("\nNo alembic_version table found!")

# Check critical tables
critical_tables = ['users', 'trades', 'portfolios']
missing = [t for t in critical_tables if t not in tables]
if missing:
    print(f"\n⚠️  Missing critical tables: {missing}")
else:
    print("\n✅ All critical tables present")
EOF

    railway run --service "$service" python verify_$service.py
    rm -f "verify_$service.py"
}

# Main migration process
echo "🚨 PRODUCTION MIGRATION WARNING"
echo "=============================="
echo "This will modify production databases!"
echo ""
read -p "Have you tested these migrations in staging? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting. Please test in staging first."
    exit 1
fi

echo ""
echo "📋 Migration Plan:"
echo "=================="
for service in "${SERVICES[@]}"; do
    echo "  • $service"
done
echo ""

read -p "Proceed with backups and migrations? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

# Track results
declare -A results
failed=0

# Process each service
for service in "${SERVICES[@]}"; do
    echo ""
    echo "Processing $service..."
    echo "-------------------"
    
    # Backup
    if backup_database "$service"; then
        # Run migrations
        if run_migrations "$service"; then
            # Verify
            verify_migrations "$service"
            results[$service]="✅ Success"
        else
            results[$service]="❌ Migration failed"
            ((failed++))
        fi
    else
        results[$service]="⚠️  Skipped (no database)"
    fi
    
    echo ""
done

# Summary
echo ""
echo "======================================"
echo "📊 Migration Summary"
echo "======================================"
for service in "${SERVICES[@]}"; do
    echo "$service: ${results[$service]}"
done
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ All migrations completed successfully!${NC}"
    
    # Create post-migration optimization script
    cat > optimize-after-migration.sql <<'SQL'
-- Post-migration optimizations
-- Run this after migrations to ensure optimal performance

-- Update statistics
ANALYZE;

-- Reindex tables for better performance
REINDEX DATABASE tradesense;

-- Create any missing indexes
DO $$
BEGIN
    -- Trades indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_trades_user_id') THEN
        CREATE INDEX idx_trades_user_id ON trades(user_id);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_trades_entry_time') THEN
        CREATE INDEX idx_trades_entry_time ON trades(entry_time);
    END IF;
    
    -- Add more indexes as needed
END $$;

-- Vacuum to reclaim space
VACUUM ANALYZE;
SQL
    
    echo ""
    echo "💡 Next steps:"
    echo "  1. Monitor application for any issues"
    echo "  2. Run optimization script: optimize-after-migration.sql"
    echo "  3. Verify all features are working"
    echo "  4. Keep backups for at least 7 days"
else
    echo -e "${RED}❌ Some migrations failed!${NC}"
    echo ""
    echo "⚠️  Rollback instructions:"
    echo "  1. Check logs for each failed service"
    echo "  2. Restore from backups if needed"
    echo "  3. Fix issues and retry"
fi

echo ""
echo "📁 Backups saved in: ./backups/"
echo ""