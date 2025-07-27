-- Mobile API Tables Migration
-- Adds tables for mobile device management, push notifications, and mobile-specific features

-- Mobile devices table
CREATE TABLE IF NOT EXISTS mobile_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_type VARCHAR(50) NOT NULL, -- ios, android, tablet_ios, tablet_android
    os_version VARCHAR(50),
    app_version VARCHAR(50),
    push_token TEXT,
    push_platform VARCHAR(50), -- ios, android
    push_notifications_enabled BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(100),
    language VARCHAR(10),
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_mobile_devices_user (user_id),
    INDEX idx_mobile_devices_active (is_active, last_active_at)
);

-- Mobile refresh tokens
CREATE TABLE IF NOT EXISTS mobile_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_refresh_tokens_user (user_id),
    INDEX idx_refresh_tokens_device (device_id),
    INDEX idx_refresh_tokens_token (token),
    INDEX idx_refresh_tokens_expiry (expires_at, revoked)
);

-- Mobile biometric authentication
CREATE TABLE IF NOT EXISTS mobile_biometric_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    biometric_type VARCHAR(50) NOT NULL, -- face_id, touch_id, fingerprint
    public_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_device (user_id, device_id),
    INDEX idx_biometric_keys_user (user_id)
);

-- Mobile biometric tokens for quick login
CREATE TABLE IF NOT EXISTS mobile_biometric_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_device_token (user_id, device_id),
    INDEX idx_biometric_tokens_token (token)
);

-- Mobile notifications
CREATE TABLE IF NOT EXISTS mobile_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- trade, alert, account, system, marketing
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    data JSONB,
    action_url VARCHAR(500),
    icon VARCHAR(255),
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_notifications_user (user_id, read, timestamp DESC),
    INDEX idx_notifications_type (type, timestamp DESC)
);

-- Watchlist for mobile
CREATE TABLE IF NOT EXISTS watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    notes TEXT,
    alerts_enabled BOOLEAN DEFAULT TRUE,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_symbol (user_id, symbol),
    INDEX idx_watchlist_user (user_id, position)
);

-- Trading accounts (for multiple broker support)
CREATE TABLE IF NOT EXISTS trading_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_name VARCHAR(255),
    cash_balance DECIMAL(15, 2) DEFAULT 0,
    starting_capital DECIMAL(15, 2) DEFAULT 100000,
    margin_available DECIMAL(15, 2) DEFAULT 0,
    margin_used DECIMAL(15, 2) DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_trading_accounts_user (user_id, is_primary)
);

-- Portfolio history for performance tracking
CREATE TABLE IF NOT EXISTS portfolio_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    portfolio_value DECIMAL(15, 2) NOT NULL,
    cash_balance DECIMAL(15, 2) NOT NULL,
    positions_value DECIMAL(15, 2) NOT NULL,
    daily_pnl DECIMAL(15, 2),
    daily_pnl_percent DECIMAL(8, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_date (user_id, date),
    INDEX idx_portfolio_history_user (user_id, date DESC)
);

-- Linked brokerage accounts
CREATE TABLE IF NOT EXISTS linked_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    broker_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(255) NOT NULL, -- encrypted
    account_type VARCHAR(50) NOT NULL, -- individual, margin, ira, etc.
    access_token TEXT, -- encrypted
    refresh_token TEXT, -- encrypted
    is_primary BOOLEAN DEFAULT FALSE,
    last_sync_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- active, disconnected, error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_linked_accounts_user (user_id, is_primary)
);

-- Data export jobs
CREATE TABLE IF NOT EXISTS data_export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    format VARCHAR(20) NOT NULL, -- csv, json, pdf
    options JSONB,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    file_url TEXT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_export_jobs_user (user_id, created_at DESC),
    INDEX idx_export_jobs_status (status, created_at)
);

-- Add mobile-specific columns to existing tables
ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS mobile_settings JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS security_preferences JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
    ADD COLUMN IF NOT EXISTS bio TEXT,
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

ALTER TABLE trades
    ADD COLUMN IF NOT EXISTS asset_type VARCHAR(50) DEFAULT 'stock',
    ADD COLUMN IF NOT EXISTS strategy VARCHAR(100),
    ADD COLUMN IF NOT EXISTS risk_reward_ratio DECIMAL(8, 2);

-- Add indexes for mobile performance
CREATE INDEX IF NOT EXISTS idx_trades_user_symbol ON trades(user_id, symbol, status);
CREATE INDEX IF NOT EXISTS idx_trades_user_time ON trades(user_id, entry_time DESC, exit_time DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time ON market_data(symbol, timestamp DESC);

-- Create functions for mobile features

-- Function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_mobile_tokens()
RETURNS void AS $$
BEGIN
    -- Delete expired refresh tokens
    DELETE FROM mobile_refresh_tokens
    WHERE expires_at < CURRENT_TIMESTAMP
    OR (revoked = TRUE AND revoked_at < CURRENT_TIMESTAMP - INTERVAL '30 days');
    
    -- Delete old notifications
    DELETE FROM mobile_notifications
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '90 days'
    AND read = TRUE;
    
    -- Mark inactive devices
    UPDATE mobile_devices
    SET is_active = FALSE
    WHERE last_active_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
    AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to update portfolio history
CREATE OR REPLACE FUNCTION update_portfolio_history(p_user_id UUID)
RETURNS void AS $$
DECLARE
    v_portfolio_value DECIMAL(15, 2);
    v_cash_balance DECIMAL(15, 2);
    v_positions_value DECIMAL(15, 2);
    v_yesterday_value DECIMAL(15, 2);
    v_daily_pnl DECIMAL(15, 2);
    v_daily_pnl_percent DECIMAL(8, 4);
BEGIN
    -- Get current cash balance
    SELECT COALESCE(cash_balance, 100000)
    INTO v_cash_balance
    FROM trading_accounts
    WHERE user_id = p_user_id
    AND is_primary = TRUE
    LIMIT 1;
    
    -- Calculate positions value
    SELECT COALESCE(SUM(
        CASE 
            WHEN t.type = 'long' THEN t.shares * md.price
            ELSE -t.shares * md.price
        END
    ), 0)
    INTO v_positions_value
    FROM trades t
    JOIN (
        SELECT DISTINCT ON (symbol) symbol, price
        FROM market_data
        ORDER BY symbol, timestamp DESC
    ) md ON t.symbol = md.symbol
    WHERE t.user_id = p_user_id
    AND t.status = 'open';
    
    -- Calculate total portfolio value
    v_portfolio_value := v_cash_balance + v_positions_value;
    
    -- Get yesterday's value
    SELECT portfolio_value
    INTO v_yesterday_value
    FROM portfolio_history
    WHERE user_id = p_user_id
    AND date = CURRENT_DATE - INTERVAL '1 day';
    
    -- Calculate daily P&L
    IF v_yesterday_value IS NOT NULL THEN
        v_daily_pnl := v_portfolio_value - v_yesterday_value;
        v_daily_pnl_percent := (v_daily_pnl / v_yesterday_value) * 100;
    ELSE
        v_daily_pnl := 0;
        v_daily_pnl_percent := 0;
    END IF;
    
    -- Insert or update today's record
    INSERT INTO portfolio_history (
        user_id, date, portfolio_value, cash_balance, 
        positions_value, daily_pnl, daily_pnl_percent
    ) VALUES (
        p_user_id, CURRENT_DATE, v_portfolio_value, v_cash_balance,
        v_positions_value, v_daily_pnl, v_daily_pnl_percent
    )
    ON CONFLICT (user_id, date) DO UPDATE SET
        portfolio_value = EXCLUDED.portfolio_value,
        cash_balance = EXCLUDED.cash_balance,
        positions_value = EXCLUDED.positions_value,
        daily_pnl = EXCLUDED.daily_pnl,
        daily_pnl_percent = EXCLUDED.daily_pnl_percent,
        created_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job to update portfolio history daily
-- This would be run by a cron job or scheduler
-- SELECT update_portfolio_history(user_id) FROM users WHERE is_active = TRUE;

-- Create scheduled job to clean up expired tokens
-- This would be run daily
-- SELECT cleanup_expired_mobile_tokens();
