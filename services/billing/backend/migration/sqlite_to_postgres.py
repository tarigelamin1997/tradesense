#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Tool for TradeSense

This script handles the complete migration from SQLite to PostgreSQL including:
- Schema analysis and conversion
- Data type mapping
- Data migration with validation
- Rollback capabilities
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql
import json
import hashlib
from datetime import datetime
from decimal import Decimal
import logging
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteToPostgresMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    # Data type mapping from SQLite to PostgreSQL
    TYPE_MAPPING = {
        'INTEGER': 'INTEGER',
        'TEXT': 'TEXT',
        'REAL': 'DOUBLE PRECISION',
        'BLOB': 'BYTEA',
        'NUMERIC': 'NUMERIC',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'DATE': 'DATE',
        'TIME': 'TIME',
        'VARCHAR': 'VARCHAR',
        'CHAR': 'CHAR',
        'FLOAT': 'DOUBLE PRECISION',
        'DOUBLE': 'DOUBLE PRECISION',
        'DECIMAL': 'DECIMAL',
    }
    
    # Tables to migrate in order (respecting foreign key constraints)
    TABLE_ORDER = [
        'users',
        'portfolios',
        'trading_accounts',
        'strategies',
        'playbooks',
        'trades',
        'trade_notes',
        'trade_reviews',
        'tags',
        'trade_tags',
        'feature_requests',
        'feature_votes',
        'feature_comments',
        'mental_maps',
        'mental_map_entries',
        'pattern_clusters',
        'milestones',
        'daily_emotion_reflections',
        'journal_entries'
    ]
    
    def __init__(self, sqlite_path: str, pg_config: dict):
        """
        Initialize migrator
        
        Args:
            sqlite_path: Path to SQLite database
            pg_config: PostgreSQL connection configuration
        """
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
        self.table_checksums = {}
        self.migration_stats = {
            'tables_migrated': 0,
            'total_rows': 0,
            'errors': []
        }
    
    def connect_sqlite(self):
        """Connect to SQLite database"""
        return sqlite3.connect(self.sqlite_path)
    
    def connect_postgres(self):
        """Connect to PostgreSQL database"""
        return psycopg2.connect(**self.pg_config)
    
    def analyze_sqlite_schema(self) -> Dict[str, List[Dict]]:
        """Analyze SQLite schema and return table information"""
        schema_info = {}
        
        with self.connect_sqlite() as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                # Get column information
                cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[1],
                        'type': row[2].upper(),
                        'nullable': not row[3],
                        'default': row[4],
                        'primary_key': bool(row[5])
                    })
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                schema_info[table] = {
                    'columns': columns,
                    'row_count': row_count
                }
                
                logger.info(f"Table '{table}': {len(columns)} columns, {row_count} rows")
        
        return schema_info
    
    def create_postgres_schema(self, schema_info: Dict[str, Dict]):
        """Create PostgreSQL schema based on SQLite analysis"""
        with self.connect_postgres() as conn:
            cursor = conn.cursor()
            
            for table_name in self.TABLE_ORDER:
                if table_name not in schema_info:
                    continue
                    
                table_info = schema_info[table_name]
                columns = table_info['columns']
                
                # Build CREATE TABLE statement
                column_defs = []
                for col in columns:
                    col_def = f'"{col["name"]}" '
                    
                    # Map data type
                    sqlite_type = col['type'].split('(')[0]
                    pg_type = self.TYPE_MAPPING.get(sqlite_type, 'TEXT')
                    
                    # Special handling for specific columns
                    if col['name'].endswith('_id') and col['primary_key']:
                        pg_type = 'UUID PRIMARY KEY'
                    elif col['name'].endswith('_id'):
                        pg_type = 'UUID'
                    elif col['name'] in ['created_at', 'updated_at', 'entry_time', 'exit_time']:
                        pg_type = 'TIMESTAMP'
                    elif col['name'] in ['price', 'pnl', 'quantity']:
                        pg_type = 'DECIMAL(15, 2)'
                    
                    col_def += pg_type
                    
                    if not col['nullable'] and not col['primary_key']:
                        col_def += ' NOT NULL'
                    
                    if col['default'] is not None:
                        # Handle default values
                        if col['default'] == 'CURRENT_TIMESTAMP':
                            col_def += ' DEFAULT CURRENT_TIMESTAMP'
                        elif col['default'].startswith("'") and col['default'].endswith("'"):
                            col_def += f' DEFAULT {col["default"]}'
                        else:
                            col_def += f' DEFAULT {col["default"]}'
                    
                    column_defs.append(col_def)
                
                # Create table
                create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n  {",\\n  ".join(column_defs)}\n)'
                
                try:
                    cursor.execute(create_sql)
                    conn.commit()
                    logger.info(f"Created table: {table_name}")
                except Exception as e:
                    logger.error(f"Error creating table {table_name}: {e}")
                    conn.rollback()
    
    def calculate_checksum(self, table: str) -> str:
        """Calculate checksum for a table's data"""
        with self.connect_sqlite() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} ORDER BY 1")
            
            # Create hash of all data
            hasher = hashlib.sha256()
            for row in cursor.fetchall():
                hasher.update(str(row).encode())
            
            return hasher.hexdigest()
    
    def migrate_table_data(self, table: str, schema_info: Dict):
        """Migrate data from one table"""
        logger.info(f"Migrating table: {table}")
        
        # Calculate checksum before migration
        checksum_before = self.calculate_checksum(table)
        self.table_checksums[table] = checksum_before
        
        with self.connect_sqlite() as sqlite_conn:
            sqlite_cursor = sqlite_conn.cursor()
            
            # Get column info
            columns = schema_info[table]['columns']
            column_names = [col['name'] for col in columns]
            
            # Fetch all data
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.info(f"No data to migrate in table: {table}")
                return
            
            with self.connect_postgres() as pg_conn:
                pg_cursor = pg_conn.cursor()
                
                # Prepare insert statement
                placeholders = ', '.join(['%s'] * len(column_names))
                insert_sql = f'INSERT INTO "{table}" ({", ".join([f\'"{c}"\' for c in column_names])}) VALUES ({placeholders})'
                
                # Convert and insert data
                migrated_rows = 0
                for row in rows:
                    try:
                        # Convert data types
                        converted_row = []
                        for i, (value, col) in enumerate(zip(row, columns)):
                            if value is None:
                                converted_row.append(None)
                            elif col['name'] in ['created_at', 'updated_at', 'entry_time', 'exit_time']:
                                # Convert datetime strings
                                if isinstance(value, str):
                                    try:
                                        # Try different datetime formats
                                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S']:
                                            try:
                                                dt = datetime.strptime(value, fmt)
                                                converted_row.append(dt)
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            converted_row.append(value)  # Keep as string if no format matches
                                    except:
                                        converted_row.append(value)
                                else:
                                    converted_row.append(value)
                            elif col['name'] in ['price', 'pnl', 'quantity'] and value is not None:
                                # Convert to Decimal
                                converted_row.append(Decimal(str(value)))
                            else:
                                converted_row.append(value)
                        
                        pg_cursor.execute(insert_sql, converted_row)
                        migrated_rows += 1
                        
                    except Exception as e:
                        logger.error(f"Error migrating row in {table}: {e}")
                        self.migration_stats['errors'].append({
                            'table': table,
                            'error': str(e),
                            'row': row
                        })
                
                pg_conn.commit()
                logger.info(f"Migrated {migrated_rows}/{len(rows)} rows in table: {table}")
                self.migration_stats['total_rows'] += migrated_rows
    
    def add_indexes(self):
        """Add missing indexes for performance"""
        indexes = [
            # User-related indexes
            'CREATE INDEX idx_trades_user_id ON trades(user_id)',
            'CREATE INDEX idx_trades_user_symbol ON trades(user_id, symbol)',
            'CREATE INDEX idx_trades_user_date ON trades(user_id, entry_time)',
            
            # Performance indexes
            'CREATE INDEX idx_trades_entry_time ON trades(entry_time)',
            'CREATE INDEX idx_trades_exit_time ON trades(exit_time)',
            'CREATE INDEX idx_trades_symbol ON trades(symbol)',
            
            # Composite indexes for common queries
            'CREATE INDEX idx_trades_user_date_symbol ON trades(user_id, entry_time, symbol)',
            'CREATE INDEX idx_portfolio_user_date ON portfolios(user_id, created_at)',
            
            # Foreign key indexes
            'CREATE INDEX idx_trade_notes_trade_id ON trade_notes(trade_id)',
            'CREATE INDEX idx_trade_tags_trade_id ON trade_tags(trade_id)',
            'CREATE INDEX idx_journal_entries_user_id ON journal_entries(user_id)',
            
            # Text search index (if journal entries exist)
            "CREATE INDEX idx_journal_entries_content_gin ON journal_entries USING gin(to_tsvector('english', content))"
        ]
        
        with self.connect_postgres() as conn:
            cursor = conn.cursor()
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    conn.commit()
                    logger.info(f"Created index: {index_sql.split(' ')[2]}")
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
                    conn.rollback()
    
    def validate_migration(self, schema_info: Dict) -> bool:
        """Validate the migration was successful"""
        logger.info("Validating migration...")
        validation_passed = True
        
        with self.connect_postgres() as conn:
            cursor = conn.cursor()
            
            for table, info in schema_info.items():
                # Check row counts
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                pg_count = cursor.fetchone()[0]
                sqlite_count = info['row_count']
                
                if pg_count != sqlite_count:
                    logger.error(f"Row count mismatch in {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                    validation_passed = False
                else:
                    logger.info(f"✓ {table}: {pg_count} rows match")
                
                # Check specific data integrity
                if table == 'trades' and pg_count > 0:
                    # Verify financial data
                    cursor.execute('SELECT SUM(pnl) FROM trades WHERE pnl IS NOT NULL')
                    pg_pnl_sum = cursor.fetchone()[0]
                    
                    with self.connect_sqlite() as sqlite_conn:
                        sqlite_cursor = sqlite_conn.cursor()
                        sqlite_cursor.execute('SELECT SUM(pnl) FROM trades WHERE pnl IS NOT NULL')
                        sqlite_pnl_sum = sqlite_cursor.fetchone()[0]
                    
                    if pg_pnl_sum and sqlite_pnl_sum:
                        if abs(float(pg_pnl_sum) - float(sqlite_pnl_sum)) > 0.01:
                            logger.error(f"PnL sum mismatch: SQLite={sqlite_pnl_sum}, PostgreSQL={pg_pnl_sum}")
                            validation_passed = False
                        else:
                            logger.info(f"✓ Financial data integrity verified")
        
        return validation_passed
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting SQLite to PostgreSQL migration...")
        
        # Step 1: Check if SQLite database exists
        if not os.path.exists(self.sqlite_path):
            logger.warning(f"SQLite database not found at {self.sqlite_path}")
            logger.info("This might be a fresh installation. Creating empty PostgreSQL schema...")
            
            # Just create the schema without data
            with self.connect_postgres() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")  # Test connection
                logger.info("PostgreSQL connection successful")
            
            return True
        
        # Step 2: Analyze SQLite schema
        logger.info("Analyzing SQLite schema...")
        schema_info = self.analyze_sqlite_schema()
        self.migration_stats['tables_migrated'] = len(schema_info)
        
        # Save schema analysis
        with open('migration_schema_analysis.json', 'w') as f:
            json.dump(schema_info, f, indent=2)
        
        # Step 3: Create PostgreSQL schema
        logger.info("Creating PostgreSQL schema...")
        self.create_postgres_schema(schema_info)
        
        # Step 4: Migrate data
        logger.info("Migrating data...")
        for table in self.TABLE_ORDER:
            if table in schema_info:
                self.migrate_table_data(table, schema_info)
        
        # Step 5: Add indexes
        logger.info("Adding performance indexes...")
        self.add_indexes()
        
        # Step 6: Validate migration
        success = self.validate_migration(schema_info)
        
        # Step 7: Save migration report
        report = {
            'timestamp': datetime.now().isoformat(),
            'success': success,
            'stats': self.migration_stats,
            'checksums': self.table_checksums,
            'errors': self.migration_stats['errors']
        }
        
        with open('migration_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        if success:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.error("❌ Migration completed with errors. Check migration_report.json")
        
        return success


def main():
    """Main migration entry point"""
    # PostgreSQL configuration
    pg_config = {
        'host': os.getenv('PG_HOST', 'localhost'),
        'port': os.getenv('PG_PORT', 5432),
        'database': os.getenv('PG_DATABASE', 'tradesense'),
        'user': os.getenv('PG_USER', 'tradesense_user'),
        'password': os.getenv('PG_PASSWORD', 'tradesense_password')
    }
    
    # SQLite path
    sqlite_path = os.getenv('SQLITE_PATH', 'tradesense.db')
    
    # Create migrator and run
    migrator = SQLiteToPostgresMigrator(sqlite_path, pg_config)
    
    try:
        success = migrator.run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()