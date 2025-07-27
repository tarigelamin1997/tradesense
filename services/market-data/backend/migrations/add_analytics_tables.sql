-- Analytics tables for TradeSense
-- Stores user events and analytics data

-- Create user_events table
CREATE TABLE IF NOT EXISTS user_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    properties JSONB,
    page_url TEXT,
    referrer_url TEXT,
    user_agent TEXT,
    ip_address_hash VARCHAR(32),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_user_events_user_id (user_id),
    INDEX idx_user_events_session_id (session_id),
    INDEX idx_user_events_event_type (event_type),
    INDEX idx_user_events_timestamp (timestamp),
    INDEX idx_user_events_user_timestamp (user_id, timestamp)
);

-- Create table for aggregated metrics (for faster queries)
CREATE TABLE IF NOT EXISTS analytics_daily_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicates
    UNIQUE(date, metric_type),
    INDEX idx_daily_metrics_date (date),
    INDEX idx_daily_metrics_type (metric_type)
);

-- Create table for user segments
CREATE TABLE IF NOT EXISTS user_segments (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    segment_name VARCHAR(50) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    removed_at TIMESTAMP WITH TIME ZONE,
    properties JSONB,
    
    INDEX idx_user_segments_user_id (user_id),
    INDEX idx_user_segments_segment (segment_name),
    INDEX idx_user_segments_active (user_id, segment_name) WHERE removed_at IS NULL
);

-- Create table for feature adoption tracking
CREATE TABLE IF NOT EXISTS feature_adoption (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    first_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    usage_count INTEGER DEFAULT 1,
    adopted BOOLEAN DEFAULT TRUE,
    properties JSONB,
    
    UNIQUE(user_id, feature_name),
    INDEX idx_feature_adoption_user (user_id),
    INDEX idx_feature_adoption_feature (feature_name)
);

-- Create table for conversion funnel tracking
CREATE TABLE IF NOT EXISTS funnel_events (
    id SERIAL PRIMARY KEY,
    funnel_id VARCHAR(100) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    time_since_previous_step INTERVAL,
    properties JSONB,
    
    INDEX idx_funnel_events_funnel (funnel_id),
    INDEX idx_funnel_events_user (user_id),
    INDEX idx_funnel_events_funnel_user (funnel_id, user_id)
);

-- Create table for A/B test assignments (for future use)
CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    test_name VARCHAR(100) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    properties JSONB,
    
    UNIQUE(user_id, test_name),
    INDEX idx_ab_test_user (user_id),
    INDEX idx_ab_test_name (test_name)
);

-- Create materialized view for user engagement scores
CREATE MATERIALIZED VIEW IF NOT EXISTS user_engagement_scores AS
SELECT 
    u.id as user_id,
    u.email,
    u.subscription_tier,
    COUNT(DISTINCT DATE(e.timestamp)) as active_days_30d,
    COUNT(DISTINCT e.session_id) as sessions_30d,
    COUNT(e.event_id) as total_events_30d,
    COUNT(DISTINCT e.event_type) as unique_events_30d,
    MAX(e.timestamp) as last_activity,
    CASE 
        WHEN COUNT(e.event_id) > 100 AND COUNT(DISTINCT DATE(e.timestamp)) > 20 THEN 'power_user'
        WHEN COUNT(e.event_id) > 50 AND COUNT(DISTINCT DATE(e.timestamp)) > 10 THEN 'active'
        WHEN COUNT(e.event_id) > 10 THEN 'casual'
        ELSE 'inactive'
    END as engagement_level
FROM users u
LEFT JOIN user_events e ON u.id = e.user_id 
    AND e.timestamp > NOW() - INTERVAL '30 days'
GROUP BY u.id, u.email, u.subscription_tier;

-- Create index on materialized view
CREATE INDEX idx_engagement_scores_user ON user_engagement_scores(user_id);
CREATE INDEX idx_engagement_scores_level ON user_engagement_scores(engagement_level);

-- Function to refresh engagement scores
CREATE OR REPLACE FUNCTION refresh_engagement_scores()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_engagement_scores;
END;
$$ LANGUAGE plpgsql;

-- Create alerts table (for storing alert history)
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    fired_at TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    tags TEXT[],
    runbook_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_alerts_name (name),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_status (status),
    INDEX idx_alerts_fired_at (fired_at)
);

-- Create API request logs table (for performance analytics)
CREATE TABLE IF NOT EXISTS api_requests (
    id SERIAL PRIMARY KEY,
    request_id UUID DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms FLOAT NOT NULL,
    request_size INTEGER,
    response_size INTEGER,
    ip_address_hash VARCHAR(32),
    user_agent TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_api_requests_user (user_id),
    INDEX idx_api_requests_endpoint (endpoint),
    INDEX idx_api_requests_created (created_at),
    INDEX idx_api_requests_status (status_code)
);

-- Create application logs table
CREATE TABLE IF NOT EXISTS application_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,
    logger VARCHAR(255),
    message TEXT NOT NULL,
    context JSONB,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    request_id UUID,
    
    INDEX idx_app_logs_timestamp (timestamp),
    INDEX idx_app_logs_level (level),
    INDEX idx_app_logs_user (user_id),
    INDEX idx_app_logs_request (request_id)
);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON user_events TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON analytics_daily_metrics TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON user_segments TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON feature_adoption TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON funnel_events TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON ab_test_assignments TO tradesense_app;
GRANT SELECT ON user_engagement_scores TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON alerts TO tradesense_app;
GRANT SELECT, INSERT ON api_requests TO tradesense_app;
GRANT SELECT, INSERT ON application_logs TO tradesense_app;

-- Create scheduled job to refresh engagement scores (using pg_cron if available)
-- This would be set up separately in production
-- SELECT cron.schedule('refresh-engagement-scores', '0 */6 * * *', 'SELECT refresh_engagement_scores();');