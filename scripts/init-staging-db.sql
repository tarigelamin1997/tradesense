-- TradeSense Staging Database Initialization Script
-- Creates necessary extensions, schemas, and initial data for staging environment

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS staging_analytics;

-- Set search path
SET search_path TO staging, public;

-- Create audit table for staging environment
CREATE TABLE IF NOT EXISTS staging.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT
);

-- Create index on audit log
CREATE INDEX idx_audit_log_timestamp ON staging.audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_user_id ON staging.audit_log(user_id);
CREATE INDEX idx_audit_log_table_operation ON staging.audit_log(table_name, operation);

-- Create function for audit logging
CREATE OR REPLACE FUNCTION staging.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO staging.audit_log(table_name, operation, user_id, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, current_setting('app.current_user_id', true)::UUID, row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO staging.audit_log(table_name, operation, user_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, current_setting('app.current_user_id', true)::UUID, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO staging.audit_log(table_name, operation, user_id, old_data)
        VALUES (TG_TABLE_NAME, TG_OP, current_setting('app.current_user_id', true)::UUID, row_to_json(OLD));
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create performance monitoring table
CREATE TABLE IF NOT EXISTS staging.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT
);

-- Create indexes for performance metrics
CREATE INDEX idx_perf_metrics_timestamp ON staging.performance_metrics(timestamp DESC);
CREATE INDEX idx_perf_metrics_endpoint ON staging.performance_metrics(endpoint, method);
CREATE INDEX idx_perf_metrics_user ON staging.performance_metrics(user_id);
CREATE INDEX idx_perf_metrics_status ON staging.performance_metrics(status_code);

-- Create staging test users
INSERT INTO users (id, username, email, full_name, password_hash, is_active, is_verified, subscription_tier, created_at)
VALUES 
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'staging_admin', 'admin@staging.tradesense.com', 'Staging Admin', '$2b$12$staging.admin.password.hash', true, true, 'enterprise', NOW()),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'staging_pro', 'pro@staging.tradesense.com', 'Staging Pro User', '$2b$12$staging.pro.password.hash', true, true, 'pro', NOW()),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'staging_free', 'free@staging.tradesense.com', 'Staging Free User', '$2b$12$staging.free.password.hash', true, true, 'free', NOW()),
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'staging_test', 'test@staging.tradesense.com', 'Staging Test User', '$2b$12$staging.test.password.hash', true, false, 'free', NOW())
ON CONFLICT (id) DO NOTHING;

-- Create sample trades for testing
INSERT INTO trades (user_id, symbol, entry_time, exit_time, entry_price, exit_price, quantity, side, profit_loss, commission, notes, tags, created_at)
SELECT 
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12'::UUID,
    (ARRAY['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'SPY', 'QQQ', 'NVDA'])[floor(random() * 8 + 1)],
    NOW() - (random() * interval '30 days'),
    NOW() - (random() * interval '29 days'),
    100 + (random() * 100),
    100 + (random() * 100),
    floor(random() * 100 + 1),
    CASE WHEN random() > 0.5 THEN 'long' ELSE 'short' END,
    (random() - 0.5) * 1000,
    5 + (random() * 10),
    'Staging test trade',
    ARRAY['staging', 'test'],
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 50);

-- Create staging-specific views
CREATE OR REPLACE VIEW staging.active_sessions AS
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    backend_start,
    state,
    query_start,
    state_change,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE datname = current_database()
AND pid <> pg_backend_pid();

-- Create materialized view for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS staging_analytics.daily_trading_summary AS
SELECT 
    date_trunc('day', exit_time) as trading_day,
    user_id,
    COUNT(*) as total_trades,
    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
    SUM(profit_loss) as total_pnl,
    AVG(profit_loss) as avg_pnl,
    MAX(profit_loss) as best_trade,
    MIN(profit_loss) as worst_trade,
    SUM(quantity * entry_price) as total_volume
FROM trades
WHERE exit_time IS NOT NULL
GROUP BY date_trunc('day', exit_time), user_id;

-- Create index on materialized view
CREATE INDEX idx_daily_summary_day ON staging_analytics.daily_trading_summary(trading_day DESC);
CREATE INDEX idx_daily_summary_user ON staging_analytics.daily_trading_summary(user_id);

-- Refresh materialized view
REFRESH MATERIALIZED VIEW staging_analytics.daily_trading_summary;

-- Grant permissions
GRANT USAGE ON SCHEMA staging TO tradesense_staging;
GRANT USAGE ON SCHEMA staging_analytics TO tradesense_staging;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO tradesense_staging;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging_analytics TO tradesense_staging;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging TO tradesense_staging;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging_analytics TO tradesense_staging;

-- Create scheduled job to refresh materialized views (requires pg_cron extension)
-- SELECT cron.schedule('refresh-staging-analytics', '0 * * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY staging_analytics.daily_trading_summary;');

-- Output initialization complete message
DO $$
BEGIN
    RAISE NOTICE 'Staging database initialization completed successfully';
    RAISE NOTICE 'Test users created:';
    RAISE NOTICE '  - staging_admin (enterprise tier)';
    RAISE NOTICE '  - staging_pro (pro tier)';
    RAISE NOTICE '  - staging_free (free tier)';
    RAISE NOTICE '  - staging_test (unverified user)';
    RAISE NOTICE '50 sample trades created for staging_pro user';
END $$;