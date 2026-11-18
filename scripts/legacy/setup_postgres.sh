#!/bin/bash
# PostgreSQL Setup Script for TradeSense

echo "=== PostgreSQL Setup for TradeSense ==="
echo

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed!"
    echo
    echo "Please install PostgreSQL using one of these methods:"
    echo
    echo "For Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install postgresql postgresql-contrib"
    echo
    echo "For macOS (using Homebrew):"
    echo "  brew install postgresql"
    echo "  brew services start postgresql"
    echo
    echo "For other systems, visit: https://www.postgresql.org/download/"
    exit 1
fi

echo "✓ PostgreSQL is installed"
psql --version

# Check if PostgreSQL service is running
if systemctl is-active --quiet postgresql 2>/dev/null || brew services list 2>/dev/null | grep -q "postgresql.*started"; then
    echo "✓ PostgreSQL service is running"
else
    echo "⚠ PostgreSQL service might not be running"
    echo "Try: sudo systemctl start postgresql"
    echo "Or:  brew services start postgresql (macOS)"
fi

echo
echo "=== Creating TradeSense Databases ==="
echo "You may be prompted for the postgres user password."
echo

# Create databases
sudo -u postgres psql <<EOF 2>/dev/null || psql -U postgres <<EOF
-- Create main database
CREATE DATABASE tradesense;

-- Create test database  
CREATE DATABASE tradesense_test;

-- Set password for postgres user (if not already set)
ALTER USER postgres PASSWORD 'postgres';

-- List databases to confirm
\l tradesense
\l tradesense_test
EOF

if [ $? -eq 0 ]; then
    echo
    echo "✅ Databases created successfully!"
else
    echo
    echo "⚠ There was an issue creating databases."
    echo "You can manually create them with:"
    echo "  sudo -u postgres createdb tradesense"
    echo "  sudo -u postgres createdb tradesense_test"
fi

echo
echo "=== Next Steps ==="
echo "1. The .env file has been configured with PostgreSQL settings"
echo "2. Run the migration script to import existing users:"
echo "   cd src/backend"
echo "   python migrate_to_postgres.py"
echo "3. Test the connection:"
echo "   python test_postgres.py"
echo "4. Update your application to use PostgreSQL"
echo
echo "Current .env database settings:"
grep "DATABASE_URL" .env | head -3

echo
echo "✅ PostgreSQL setup complete!"