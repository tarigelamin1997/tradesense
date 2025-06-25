
#!/bin/bash
set -e

echo "🗄️ Initializing TradeSense Database..."

# Wait for database to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

# Run database migrations
python -c "
from backend.db.connection import init_database
from backend.models.trade import Base
from sqlalchemy import create_engine
import os

engine = create_engine(os.getenv('DATABASE_URL'))
Base.metadata.create_all(bind=engine)
print('✅ Database tables created successfully')
"

echo "✅ Database initialization complete"
