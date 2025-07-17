#!/bin/bash
# PostgreSQL Setup Script for TradeSense Production
# Sets up PostgreSQL with proper configuration for production use

set -e  # Exit on error

echo "🐘 TradeSense PostgreSQL Setup"
echo "=============================="
echo ""

# Configuration
DB_NAME="tradesense"
DB_USER="tradesense_user"
DB_PASSWORD=${DB_PASSWORD:-$(openssl rand -hex 16)}
PG_VERSION="15"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if command_exists docker; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    USE_DOCKER=true
elif command_exists psql; then
    echo -e "${GREEN}✓${NC} PostgreSQL client is installed"
    USE_DOCKER=false
else
    echo -e "${RED}✗${NC} Neither Docker nor PostgreSQL found!"
    echo "Please install either Docker or PostgreSQL first."
    exit 1
fi

# Option 1: Docker-based PostgreSQL (Recommended for development)
if [ "$USE_DOCKER" = true ]; then
    echo ""
    echo "🐳 Setting up PostgreSQL with Docker..."
    
    # Check if container already exists
    if docker ps -a | grep -q "tradesense-postgres"; then
        echo -e "${YELLOW}⚠${NC} Container 'tradesense-postgres' already exists"
        read -p "Remove existing container and create new one? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker stop tradesense-postgres 2>/dev/null || true
            docker rm tradesense-postgres 2>/dev/null || true
        else
            echo "Using existing container..."
            docker start tradesense-postgres 2>/dev/null || true
        fi
    fi
    
    # Create Docker volume for persistence
    docker volume create tradesense-pgdata 2>/dev/null || true
    
    # Run PostgreSQL container
    docker run -d \
        --name tradesense-postgres \
        -e POSTGRES_DB=$DB_NAME \
        -e POSTGRES_USER=$DB_USER \
        -e POSTGRES_PASSWORD=$DB_PASSWORD \
        -p 5433:5432 \
        -v tradesense-pgdata:/var/lib/postgresql/data \
        --restart unless-stopped \
        postgres:$PG_VERSION-alpine \
        postgres \
        -c max_connections=200 \
        -c shared_buffers=256MB \
        -c effective_cache_size=1GB \
        -c maintenance_work_mem=64MB \
        -c checkpoint_completion_target=0.9 \
        -c wal_buffers=16MB \
        -c default_statistics_target=100 \
        -c random_page_cost=1.1 \
        -c effective_io_concurrency=200 \
        -c work_mem=4MB \
        -c min_wal_size=1GB \
        -c max_wal_size=4GB
    
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 5
    
    # Wait for PostgreSQL to be ready
    for i in {1..30}; do
        if docker exec tradesense-postgres pg_isready -U $DB_USER > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} PostgreSQL is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Create optimized configuration
    echo ""
    echo "🔧 Applying production optimizations..."
    
    docker exec tradesense-postgres psql -U $DB_USER -d $DB_NAME <<EOF
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application user with limited privileges (optional)
-- CREATE USER tradesense_app WITH PASSWORD '$DB_PASSWORD';
-- GRANT CONNECT ON DATABASE $DB_NAME TO tradesense_app;
-- GRANT USAGE ON SCHEMA public TO tradesense_app;
-- GRANT CREATE ON SCHEMA public TO tradesense_app;
EOF

else
    # Option 2: Native PostgreSQL installation
    echo ""
    echo "🖥️  Using native PostgreSQL installation..."
    
    # Create database and user
    sudo -u postgres psql <<EOF
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Enable extensions
\c $DB_NAME
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
EOF
fi

# Create .env file with database configuration
echo ""
echo "📝 Creating environment configuration..."

cat > .env.production <<EOF
# PostgreSQL Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5433/$DB_NAME

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# PostgreSQL Specific
PG_HOST=localhost
PG_PORT=5433
PG_DATABASE=$DB_NAME
PG_USER=$DB_USER
PG_PASSWORD=$DB_PASSWORD
EOF

# Create database optimization script
cat > optimize_postgres.sql <<'EOF'
-- Performance optimization for TradeSense

-- Indexes for trades table
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_user_symbol ON trades(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_user_date_symbol ON trades(user_id, entry_time, symbol);

-- Indexes for other tables
CREATE INDEX IF NOT EXISTS idx_portfolio_user_date ON portfolios(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_trade_notes_trade_id ON trade_notes(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_tags_trade_id ON trade_tags(trade_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_user_id ON journal_entries(user_id);

-- Full text search index for journal entries
CREATE INDEX IF NOT EXISTS idx_journal_entries_content_gin 
ON journal_entries USING gin(to_tsvector('english', content));

-- Partial indexes for common filters
CREATE INDEX IF NOT EXISTS idx_trades_winning ON trades(user_id, pnl) WHERE pnl > 0;
CREATE INDEX IF NOT EXISTS idx_trades_losing ON trades(user_id, pnl) WHERE pnl < 0;

-- Update table statistics
ANALYZE;
EOF

# Test connection
echo ""
echo "🔍 Testing database connection..."

if [ "$USE_DOCKER" = true ]; then
    if docker exec tradesense-postgres psql -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Database connection successful!"
    else
        echo -e "${RED}✗${NC} Failed to connect to database"
        exit 1
    fi
else
    if PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Database connection successful!"
    else
        echo -e "${RED}✗${NC} Failed to connect to database"
        exit 1
    fi
fi

# Create backup script
cat > backup_postgres.sh <<'EOF'
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
EOF

chmod +x backup_postgres.sh

# Summary
echo ""
echo "=================================="
echo -e "${GREEN}✅ PostgreSQL setup complete!${NC}"
echo "=================================="
echo ""
echo "📊 Database Information:"
echo "  - Database: $DB_NAME"
echo "  - User: $DB_USER"
echo "  - Password: $DB_PASSWORD"
echo "  - Host: localhost"
echo "  - Port: 5433"
echo ""
echo "🔗 Connection string:"
echo "  postgresql://$DB_USER:$DB_PASSWORD@localhost:5433/$DB_NAME"
echo ""
echo "📁 Files created:"
echo "  - .env.production (database configuration)"
echo "  - optimize_postgres.sql (performance indexes)"
echo "  - backup_postgres.sh (backup script)"
echo ""
echo "🚀 Next steps:"
echo "  1. Run migrations: cd src/backend && alembic upgrade head"
echo "  2. Apply optimizations: psql -U $DB_USER -d $DB_NAME -f optimize_postgres.sql"
echo "  3. Update your application to use PostgreSQL"
echo ""
if [ "$USE_DOCKER" = true ]; then
    echo "🐳 Docker commands:"
    echo "  - View logs: docker logs tradesense-postgres"
    echo "  - Connect: docker exec -it tradesense-postgres psql -U $DB_USER -d $DB_NAME"
    echo "  - Stop: docker stop tradesense-postgres"
    echo "  - Start: docker start tradesense-postgres"
fi