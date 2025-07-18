-- Feature flags system for TradeSense
-- Enables controlled feature rollouts and A/B testing

-- Create feature flags table
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL CHECK (type IN ('boolean', 'percentage', 'user_list', 'variant')),
    status VARCHAR(20) NOT NULL DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'scheduled', 'expired')),
    default_value JSONB,
    targeting_rules JSONB DEFAULT '[]'::jsonb,
    variants JSONB,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    INDEX idx_feature_flags_key (key),
    INDEX idx_feature_flags_status (status),
    INDEX idx_feature_flags_dates (start_date, end_date)
);

-- Create feature flag evaluations table for analytics
CREATE TABLE IF NOT EXISTS feature_flag_evaluations (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    value JSONB NOT NULL,
    context JSONB,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_flag_evaluations_flag (flag_key),
    INDEX idx_flag_evaluations_user (user_id),
    INDEX idx_flag_evaluations_time (evaluated_at)
);

-- Create feature flag overrides table for specific users
CREATE TABLE IF NOT EXISTS feature_flag_overrides (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(100) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    value JSONB NOT NULL,
    reason TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(flag_key, user_id),
    INDEX idx_flag_overrides_flag (flag_key),
    INDEX idx_flag_overrides_user (user_id),
    INDEX idx_flag_overrides_expires (expires_at)
);

-- Create A/B test results table
CREATE TABLE IF NOT EXISTS ab_test_results (
    id SERIAL PRIMARY KEY,
    flag_key VARCHAR(100) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_ab_results_flag (flag_key),
    INDEX idx_ab_results_variant (variant),
    INDEX idx_ab_results_metric (metric_name),
    INDEX idx_ab_results_time (recorded_at)
);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_feature_flag_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for timestamp update
DROP TRIGGER IF EXISTS trigger_update_feature_flag_timestamp ON feature_flags;
CREATE TRIGGER trigger_update_feature_flag_timestamp
BEFORE UPDATE ON feature_flags
FOR EACH ROW
EXECUTE FUNCTION update_feature_flag_timestamp();

-- Create function to clean up expired evaluations
CREATE OR REPLACE FUNCTION cleanup_old_flag_evaluations()
RETURNS void AS $$
BEGIN
    DELETE FROM feature_flag_evaluations
    WHERE evaluated_at < NOW() - INTERVAL '30 days';
    
    DELETE FROM ab_test_results
    WHERE recorded_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Insert some example feature flags
INSERT INTO feature_flags (key, name, description, type, status, default_value, targeting_rules)
VALUES 
(
    'advanced_analytics_beta',
    'Advanced Analytics Beta',
    'New advanced analytics dashboard with ML insights',
    'percentage',
    'active',
    'false',
    '[{
        "user_percentage": 20,
        "user_tiers": ["pro", "premium"]
    }]'::jsonb
),
(
    'collaborative_trading',
    'Collaborative Trading Features',
    'Share trades and strategies with team members',
    'boolean',
    'active',
    'false',
    '[{
        "user_tiers": ["premium"],
        "min_trades": 50
    }]'::jsonb
),
(
    'export_formats_test',
    'Export Format A/B Test',
    'Test different export format defaults',
    'variant',
    'active',
    '"csv"',
    '[{
        "user_percentage": 100
    }]'::jsonb
),
(
    'real_time_sync',
    'Real-Time Data Sync',
    'Enable real-time synchronization across devices',
    'boolean',
    'inactive',
    'false',
    '[]'::jsonb
)
ON CONFLICT (key) DO NOTHING;

-- Set variants for A/B test flag
UPDATE feature_flags
SET variants = '{
    "csv": {"weight": 40, "name": "CSV Export"},
    "excel": {"weight": 30, "name": "Excel Export"},
    "json": {"weight": 30, "name": "JSON Export"}
}'::jsonb
WHERE key = 'export_formats_test';

-- Grant permissions
GRANT SELECT ON feature_flags TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON feature_flags TO tradesense_app;
GRANT SELECT, INSERT ON feature_flag_evaluations TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON feature_flag_overrides TO tradesense_app;
GRANT SELECT, INSERT ON ab_test_results TO tradesense_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO tradesense_app;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_feature_flags_active ON feature_flags(key) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_flag_evaluations_recent ON feature_flag_evaluations(flag_key, evaluated_at) 
    WHERE evaluated_at > NOW() - INTERVAL '7 days';