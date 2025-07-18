# TradeSense Database Schema Documentation
**Last Updated:** January 15, 2025  
**Database:** PostgreSQL 14+  
**ORM:** SQLAlchemy 2.0

## Entity Relationship Overview

```
users (1) ----< (N) trades
users (1) ----< (N) journal_entries
users (1) ----< (N) strategies
users (1) ----< (1) user_settings
users (1) ----< (1) subscriptions
trades (N) ----< (N) journal_entries (via trade_journal_links)
strategies (1) ----< (N) trades
```

## Table Schemas

### users
Primary user account table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verification_sent_at TIMESTAMP,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
);
```

### user_settings
User preferences and configuration
```sql
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    theme VARCHAR(20) DEFAULT 'light',
    notifications JSONB DEFAULT '{"email_alerts": true, "weekly_reports": true}',
    display_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE INDEX idx_user_settings_user_id (user_id)
);
```

### trades
Trading activity records
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    quantity DECIMAL(15, 4) NOT NULL,
    entry_price DECIMAL(15, 4) NOT NULL,
    exit_price DECIMAL(15, 4),
    entry_date TIMESTAMP NOT NULL,
    exit_date TIMESTAMP,
    commission DECIMAL(10, 2) DEFAULT 0,
    pnl DECIMAL(15, 2) GENERATED ALWAYS AS 
        (CASE 
            WHEN exit_price IS NOT NULL THEN
                CASE 
                    WHEN side = 'long' THEN (exit_price - entry_price) * quantity - commission
                    ELSE (entry_price - exit_price) * quantity - commission
                END
            ELSE NULL
        END) STORED,
    pnl_percent DECIMAL(8, 2) GENERATED ALWAYS AS
        (CASE
            WHEN exit_price IS NOT NULL AND entry_price > 0 THEN
                (pnl / (entry_price * quantity)) * 100
            ELSE NULL
        END) STORED,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    strategy_id INTEGER REFERENCES strategies(id),
    notes TEXT,
    tags TEXT[],
    broker VARCHAR(50),
    account_id VARCHAR(50),
    order_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_trades_user_id (user_id),
    INDEX idx_trades_symbol (symbol),
    INDEX idx_trades_entry_date (entry_date),
    INDEX idx_trades_status (status),
    INDEX idx_trades_user_symbol (user_id, symbol)
);
```

### journal_entries
Trading journal and notes
```sql
CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    mood VARCHAR(50),
    confidence INTEGER CHECK (confidence >= 1 AND confidence <= 10),
    tags TEXT[],
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_journal_user_id (user_id),
    INDEX idx_journal_created_at (created_at),
    INDEX idx_journal_mood (mood),
    FULLTEXT INDEX idx_journal_search (title, content)
);
```

### trade_journal_links
Many-to-many relationship between trades and journal entries
```sql
CREATE TABLE trade_journal_links (
    trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
    journal_entry_id INTEGER REFERENCES journal_entries(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (trade_id, journal_entry_id),
    INDEX idx_tjl_journal_id (journal_entry_id)
);
```

### strategies
Trading strategies/playbooks
```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rules JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    performance_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_strategies_user_id (user_id),
    UNIQUE INDEX idx_strategies_user_name (user_id, name)
);
```

### subscriptions
User subscription and billing information
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_id VARCHAR(50) NOT NULL,
    stripe_subscription_id VARCHAR(100) UNIQUE,
    stripe_customer_id VARCHAR(100),
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'canceled', 'past_due', 'trialing')),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP,
    trial_end TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_subscriptions_user_id (user_id),
    INDEX idx_subscriptions_stripe_id (stripe_subscription_id),
    INDEX idx_subscriptions_status (status)
);
```

### api_usage
Track API usage for rate limiting and billing
```sql
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_api_usage_user_id (user_id),
    INDEX idx_api_usage_created_at (created_at),
    INDEX idx_api_usage_user_created (user_id, created_at)
);
```

### import_history
Track CSV imports and their status
```sql
CREATE TABLE import_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    broker VARCHAR(50),
    total_rows INTEGER,
    imported_rows INTEGER,
    failed_rows INTEGER,
    errors JSONB DEFAULT '[]',
    status VARCHAR(20) CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_import_history_user_id (user_id),
    INDEX idx_import_history_status (status)
);
```

### notifications
User notifications queue
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_notifications_user_id (user_id),
    INDEX idx_notifications_is_read (is_read),
    INDEX idx_notifications_created_at (created_at)
);
```

### audit_logs
Security and compliance audit trail
```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_logs_user_id (user_id),
    INDEX idx_audit_logs_action (action),
    INDEX idx_audit_logs_created_at (created_at)
);
```

## Indexes Summary

### Performance Indexes
- User lookups by email/username
- Trade queries by user, symbol, date
- Journal full-text search
- API usage aggregation by user and time

### Composite Indexes
- `(user_id, symbol)` on trades for position calculations
- `(user_id, created_at)` on api_usage for usage reports
- `(user_id, name)` unique on strategies

## Migrations

### Applied Migrations
1. `001_initial_schema.sql` - Base tables
2. `002_add_email_verification.sql` - Email verification fields
3. `003_add_password_reset.sql` - Password reset fields
4. `004_add_user_settings.sql` - Settings table
5. `005_add_subscriptions.sql` - Billing tables
6. `006_add_audit_logs.sql` - Audit trail
7. `007_add_fulltext_search.sql` - Journal search
8. `008_add_generated_columns.sql` - PnL calculations

### Pending Migrations
- `009_add_team_workspaces.sql` - Multi-user support
- `010_add_social_features.sql` - Following/sharing
- `011_add_backtesting_tables.sql` - Strategy testing

## Data Types and Constraints

### JSON/JSONB Fields
- `user_settings.settings` - Flexible user preferences
- `user_settings.notifications` - Notification preferences
- `strategies.rules` - Strategy configuration
- `strategies.performance_metrics` - Calculated metrics
- `import_history.errors` - Import error details
- `notifications.data` - Notification payload

### Enums (Check Constraints)
- `trades.side`: 'long', 'short'
- `trades.status`: 'open', 'closed'
- `subscriptions.status`: 'active', 'canceled', 'past_due', 'trialing'
- `import_history.status`: 'pending', 'processing', 'completed', 'failed'

### Calculated Fields
- `trades.pnl` - Auto-calculated P&L
- `trades.pnl_percent` - Auto-calculated P&L percentage

## Performance Considerations

### Query Patterns
1. **User Dashboard**: Joins users → trades → strategies
2. **Portfolio View**: Aggregates trades by symbol
3. **Journal Search**: Full-text search on content
4. **Analytics**: Time-series aggregation on trades

### Optimization Notes
- Partial indexes on `trades` where `status = 'open'`
- Materialized views for portfolio calculations (planned)
- Partitioning for `api_usage` by month (at scale)
- Connection pooling configured for 50 connections

## Backup and Recovery

### Backup Schedule
- **Full backup**: Daily at 02:00 UTC
- **Incremental**: Every 6 hours
- **WAL archiving**: Continuous
- **Retention**: 30 days

### Critical Tables
Priority for backup/restore:
1. users, user_settings
2. trades, journal_entries
3. subscriptions
4. strategies

---

**Note:** This schema represents the current production state. Test and development databases may have additional experimental tables.