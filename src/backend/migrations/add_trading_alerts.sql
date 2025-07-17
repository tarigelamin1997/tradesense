-- Trading Alerts Migration: Add automated trading alerts system
-- Run this migration to add trading alerts support to TradeSense

-- 1. Create alerts table
CREATE TABLE IF NOT EXISTS trading_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    alert_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL DEFAULT '[]',
    channels VARCHAR[] NOT NULL DEFAULT ARRAY[]::VARCHAR[],
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    
    -- Scope
    symbols VARCHAR[] DEFAULT NULL,
    strategies VARCHAR[] DEFAULT NULL,
    
    -- Behavior
    cooldown_minutes INTEGER NOT NULL DEFAULT 60,
    max_triggers_per_day INTEGER DEFAULT NULL,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Notification settings
    notification_template JSONB DEFAULT NULL,
    webhook_url TEXT DEFAULT NULL,
    custom_data JSONB DEFAULT NULL,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'triggered', 'snoozed', 'disabled', 'expired', 'deleted')),
    last_triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    trigger_count INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Indexes for performance
    CONSTRAINT alert_name_unique UNIQUE(user_id, name)
);

CREATE INDEX idx_trading_alerts_user_id ON trading_alerts(user_id);
CREATE INDEX idx_trading_alerts_status ON trading_alerts(status);
CREATE INDEX idx_trading_alerts_type ON trading_alerts(alert_type);
CREATE INDEX idx_trading_alerts_last_triggered ON trading_alerts(last_triggered_at);
CREATE INDEX idx_trading_alerts_expires ON trading_alerts(expires_at);

-- 2. Create alert history table
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES trading_alerts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    trigger_data JSONB DEFAULT '{}',
    channels_notified VARCHAR[] DEFAULT ARRAY[]::VARCHAR[],
    notification_status JSONB DEFAULT '{}',
    error_message TEXT DEFAULT NULL
);

CREATE INDEX idx_alert_history_alert_id ON alert_history(alert_id);
CREATE INDEX idx_alert_history_user_id ON alert_history(user_id);
CREATE INDEX idx_alert_history_triggered_at ON alert_history(triggered_at);

-- 3. Create alert templates table (predefined alerts)
CREATE TABLE IF NOT EXISTS alert_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    default_conditions JSONB NOT NULL,
    default_channels VARCHAR[] NOT NULL DEFAULT ARRAY['email', 'in_app']::VARCHAR[],
    default_priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alert_templates_category ON alert_templates(category);
CREATE INDEX idx_alert_templates_active ON alert_templates(is_active);

-- 4. Create notification preferences extension for users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS notification_preferences JSONB DEFAULT '{"email": true, "sms": false, "in_app": true, "push": false}',
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS alert_settings JSONB DEFAULT '{}';

-- 5. Create market data cache table for real-time alerts
CREATE TABLE IF NOT EXISTS market_data_cache (
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    data_value JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (symbol, data_type)
);

CREATE INDEX idx_market_data_cache_expires ON market_data_cache(expires_at);

-- 6. Insert default alert templates
INSERT INTO alert_templates (name, description, category, alert_type, default_conditions, default_priority) VALUES
-- Price alerts
('Price Above Target', 'Alert when price goes above specified target', 'price', 'price_above', 
 '[{"field": "current_price", "operator": "gt", "value": 0}]', 'high'),
 
('Price Below Target', 'Alert when price falls below specified target', 'price', 'price_below',
 '[{"field": "current_price", "operator": "lt", "value": 0}]', 'high'),
 
('Price Change %', 'Alert on significant price percentage change', 'price', 'price_change_percent',
 '[{"field": "price_change_percent", "operator": "gt", "value": 5}]', 'medium'),

-- Performance alerts
('Daily P&L Target', 'Alert when daily P&L reaches target', 'performance', 'daily_pnl',
 '[{"field": "current_value", "operator": "gt", "value": 1000}]', 'medium'),
 
('Win Rate Drop', 'Alert when win rate drops below threshold', 'performance', 'win_rate',
 '[{"field": "current_value", "operator": "lt", "value": 50}]', 'high'),
 
('Loss Streak Warning', 'Alert on consecutive losses', 'performance', 'loss_streak',
 '[{"field": "current_value", "operator": "gte", "value": 3}]', 'high'),

-- Risk alerts
('Drawdown Limit', 'Alert when drawdown exceeds limit', 'risk', 'drawdown',
 '[{"field": "current_value", "operator": "gt", "value": 10}]', 'critical'),
 
('Position Size Warning', 'Alert on large position sizes', 'risk', 'position_size',
 '[{"field": "position_size_percent", "operator": "gt", "value": 25}]', 'high'),

-- Pattern alerts
('Pattern Detected', 'Alert when specific pattern is found', 'pattern', 'pattern_detected',
 '[{"field": "pattern_confidence", "operator": "gt", "value": 80}]', 'medium'),

-- Account alerts
('Low Account Balance', 'Alert when account balance is low', 'account', 'account_balance',
 '[{"field": "account_balance", "operator": "lt", "value": 1000}]', 'critical'),
 
('Trade Executed', 'Alert on trade execution', 'account', 'trade_execution',
 '[{"field": "trade_status", "operator": "eq", "value": "executed"}]', 'low');

-- 7. Create function to cleanup expired alerts
CREATE OR REPLACE FUNCTION cleanup_expired_alerts()
RETURNS void AS $$
BEGIN
    -- Mark expired alerts
    UPDATE trading_alerts
    SET status = 'expired'
    WHERE status = 'active'
    AND expires_at IS NOT NULL
    AND expires_at < NOW();
    
    -- Delete old history (keep 90 days)
    DELETE FROM alert_history
    WHERE triggered_at < NOW() - INTERVAL '90 days';
    
    -- Clean market data cache
    DELETE FROM market_data_cache
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 8. Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_trading_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_trading_alerts_updated_at 
    BEFORE UPDATE ON trading_alerts 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_trading_alerts_updated_at();

-- 9. Create view for alert statistics
CREATE OR REPLACE VIEW alert_statistics AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT a.id) as total_alerts,
    COUNT(DISTINCT CASE WHEN a.status = 'active' THEN a.id END) as active_alerts,
    COUNT(DISTINCT ah.id) as total_triggers,
    COUNT(DISTINCT CASE WHEN ah.triggered_at > NOW() - INTERVAL '24 hours' THEN ah.id END) as triggers_24h,
    COUNT(DISTINCT CASE WHEN ah.triggered_at > NOW() - INTERVAL '7 days' THEN ah.id END) as triggers_7d,
    MAX(ah.triggered_at) as last_trigger
FROM users u
LEFT JOIN trading_alerts a ON u.id = a.user_id AND a.status != 'deleted'
LEFT JOIN alert_history ah ON a.id = ah.alert_id
GROUP BY u.id, u.username;

-- 10. Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON trading_alerts TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON alert_history TO tradesense_app;
GRANT SELECT ON alert_templates TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON market_data_cache TO tradesense_app;
GRANT SELECT ON alert_statistics TO tradesense_app;

-- 11. Add sample notification preferences for existing users
UPDATE users 
SET notification_preferences = jsonb_build_object(
    'email', COALESCE((notification_preferences->>'email')::boolean, true),
    'sms', COALESCE((notification_preferences->>'sms')::boolean, false),
    'in_app', COALESCE((notification_preferences->>'in_app')::boolean, true),
    'push', COALESCE((notification_preferences->>'push')::boolean, false),
    'quiet_hours', COALESCE(notification_preferences->'quiet_hours', '{"enabled": false, "start": "22:00", "end": "08:00"}'::jsonb)
)
WHERE notification_preferences IS NULL OR notification_preferences = '{}'::jsonb;