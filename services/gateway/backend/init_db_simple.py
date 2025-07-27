#!/usr/bin/env python3
"""
Simplified database initialization script
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.ext.declarative import declarative_base

# Database URL
DATABASE_URL = 'postgresql://tradesense_user:2ca9bfcf1a40257caa7b4be903c7fe22@localhost:5433/tradesense'

print("🚀 Initializing TradeSense PostgreSQL Database...")
print("=" * 50)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Test connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to PostgreSQL: {version}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Create the complete schema
print("\n📊 Creating database schema...")

# Use text() for raw SQL DDL statements
schema_sql = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    stripe_customer_id VARCHAR(255) UNIQUE,
    subscription_status VARCHAR(50) DEFAULT 'free',
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    role VARCHAR(50) DEFAULT 'user',
    email_notifications BOOLEAN DEFAULT TRUE,
    mobile_notifications BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    theme VARCHAR(50) DEFAULT 'light',
    timezone VARCHAR(100) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    onboarding_completed BOOLEAN DEFAULT FALSE
);

-- Trading accounts table
CREATE TABLE IF NOT EXISTS trading_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    broker VARCHAR(100),
    account_type VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    initial_balance DECIMAL(15, 2),
    current_balance DECIMAL(15, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trading_account_id INTEGER REFERENCES trading_accounts(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE SET NULL,
    trading_account_id INTEGER REFERENCES trading_accounts(id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('buy', 'sell', 'short', 'cover')),
    quantity DECIMAL(15, 6) NOT NULL,
    entry_price DECIMAL(15, 6) NOT NULL,
    exit_price DECIMAL(15, 6),
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_date TIMESTAMP WITH TIME ZONE,
    pnl DECIMAL(15, 2),
    pnl_percentage DECIMAL(10, 4),
    commission DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'pending')),
    stop_loss DECIMAL(15, 6),
    take_profit DECIMAL(15, 6),
    risk_reward_ratio DECIMAL(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#808080',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Trade tags association table
CREATE TABLE IF NOT EXISTS trade_tags (
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (trade_id, tag_id)
);

-- Trade reviews table
CREATE TABLE IF NOT EXISTS trade_reviews (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    lessons_learned TEXT,
    mistakes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trade notes table
CREATE TABLE IF NOT EXISTS trade_notes (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    note_type VARCHAR(50) DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Playbooks table
CREATE TABLE IF NOT EXISTS playbooks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules TEXT,
    entry_criteria TEXT,
    exit_criteria TEXT,
    risk_management TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mental map entries table
CREATE TABLE IF NOT EXISTS mental_map_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    emotional_state VARCHAR(50),
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 10),
    market_sentiment VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Pattern clusters table
CREATE TABLE IF NOT EXISTS pattern_clusters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100),
    description TEXT,
    success_rate DECIMAL(5, 2),
    avg_return DECIMAL(10, 4),
    sample_size INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Milestones table
CREATE TABLE IF NOT EXISTS milestones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_value DECIMAL(15, 2),
    current_value DECIMAL(15, 2) DEFAULT 0,
    milestone_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'in_progress',
    achieved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Daily emotion reflections table
CREATE TABLE IF NOT EXISTS daily_emotion_reflections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    pre_market_mood VARCHAR(50),
    post_market_mood VARCHAR(50),
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    stress_level INTEGER CHECK (stress_level >= 1 AND stress_level <= 10),
    confidence_level INTEGER CHECK (confidence_level >= 1 AND confidence_level <= 10),
    reflection_notes TEXT,
    gratitude_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Feature requests table
CREATE TABLE IF NOT EXISTS feature_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Feature votes table
CREATE TABLE IF NOT EXISTS feature_votes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_request_id INTEGER NOT NULL REFERENCES feature_requests(id) ON DELETE CASCADE,
    vote_type VARCHAR(10) CHECK (vote_type IN ('up', 'down')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, feature_request_id)
);

-- Feature comments table
CREATE TABLE IF NOT EXISTS feature_comments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_request_id INTEGER NOT NULL REFERENCES feature_requests(id) ON DELETE CASCADE,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Billing plans table
CREATE TABLE IF NOT EXISTS billing_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    billing_period VARCHAR(20) NOT NULL,
    features JSONB,
    stripe_price_id VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    billing_plan_id INTEGER NOT NULL REFERENCES billing_plans(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Payment history table
CREATE TABLE IF NOT EXISTS payment_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL,
    stripe_payment_intent_id VARCHAR(255),
    payment_method VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_portfolio_id ON trades(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_entry_date ON trades(entry_date);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_reviews_trade_id ON trade_reviews(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_notes_trade_id ON trade_notes(trade_id);
CREATE INDEX IF NOT EXISTS idx_mental_map_entries_user_date ON mental_map_entries(user_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_emotion_reflections_user_date ON daily_emotion_reflections(user_id, date);
CREATE INDEX IF NOT EXISTS idx_feature_requests_status ON feature_requests(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_history_user_id ON payment_history(user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables with updated_at column
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%s_updated_at ON %s', t, t);
        EXECUTE format('CREATE TRIGGER update_%s_updated_at BEFORE UPDATE ON %s FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END $$;
"""

try:
    # Execute the schema creation
    with engine.begin() as conn:
        conn.execute(text(schema_sql))
    print("✅ Database schema created successfully!")
    
    # List created tables
    print("\n📋 Created tables:")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        for table in tables:
            print(f"  ✓ {table}")
    
    print(f"\n✅ Database initialized successfully with {len(tables)} tables!")
    
except Exception as e:
    print(f"\n❌ Error creating schema: {e}")
    sys.exit(1)