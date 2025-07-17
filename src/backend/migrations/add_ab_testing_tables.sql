-- A/B Testing tables for TradeSense
-- Tracks experiments, assignments, and conversion events

-- Create experiments table
CREATE TABLE IF NOT EXISTS experiments (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'running', 'paused', 'completed', 'archived')),
    variants JSONB NOT NULL,
    metrics JSONB NOT NULL,
    targeting_rules JSONB DEFAULT '{}'::jsonb,
    assignment_method VARCHAR(20) NOT NULL DEFAULT 'deterministic',
    min_sample_size INTEGER DEFAULT 1000,
    max_duration_days INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    
    INDEX idx_experiments_status (status),
    INDEX idx_experiments_created (created_at),
    INDEX idx_experiments_started (started_at)
);

-- Create variant assignments table
CREATE TABLE IF NOT EXISTS experiment_assignments (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id),
    user_id UUID NOT NULL REFERENCES users(id),
    variant_id VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(experiment_id, user_id),
    INDEX idx_assignments_experiment (experiment_id),
    INDEX idx_assignments_user (user_id),
    INDEX idx_assignments_variant (variant_id),
    INDEX idx_assignments_time (assigned_at)
);

-- Create experiment events table
CREATE TABLE IF NOT EXISTS experiment_events (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id),
    user_id UUID NOT NULL REFERENCES users(id),
    variant_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'assignment', 'conversion', 'exposure'
    metric_id VARCHAR(100),
    value DECIMAL(10, 2) DEFAULT 1.0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_exp_events_experiment (experiment_id),
    INDEX idx_exp_events_user (user_id),
    INDEX idx_exp_events_variant (variant_id),
    INDEX idx_exp_events_type (event_type),
    INDEX idx_exp_events_metric (metric_id),
    INDEX idx_exp_events_created (created_at)
);

-- Create experiment results cache table
CREATE TABLE IF NOT EXISTS experiment_results (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL REFERENCES experiments(id),
    metric_id VARCHAR(100) NOT NULL,
    variant_id VARCHAR(100) NOT NULL,
    sample_size INTEGER NOT NULL,
    conversions INTEGER NOT NULL,
    conversion_rate DECIMAL(5, 4),
    confidence_interval_lower DECIMAL(5, 4),
    confidence_interval_upper DECIMAL(5, 4),
    p_value DECIMAL(10, 9),
    is_significant BOOLEAN,
    lift DECIMAL(8, 4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(experiment_id, metric_id, variant_id),
    INDEX idx_results_experiment (experiment_id),
    INDEX idx_results_calculated (calculated_at)
);

-- Create feature flag evaluations table (for feature flag experiments)
CREATE TABLE IF NOT EXISTS feature_flag_evaluations (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    flag_key VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    experiment_id VARCHAR(100) REFERENCES experiments(id),
    variant_id VARCHAR(100),
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_flag_eval_user (user_id),
    INDEX idx_flag_eval_key (flag_key),
    INDEX idx_flag_eval_experiment (experiment_id),
    INDEX idx_flag_eval_time (evaluated_at)
);

-- Create function to track experiment event
CREATE OR REPLACE FUNCTION track_experiment_event(
    p_experiment_id VARCHAR(100),
    p_user_id UUID,
    p_variant_id VARCHAR(100),
    p_event_type VARCHAR(50),
    p_metric_id VARCHAR(100) DEFAULT NULL,
    p_value DECIMAL DEFAULT 1.0,
    p_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO experiment_events (
        experiment_id, user_id, variant_id, event_type,
        metric_id, value, metadata
    ) VALUES (
        p_experiment_id, p_user_id, p_variant_id, p_event_type,
        p_metric_id, p_value, p_metadata
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to get experiment stats
CREATE OR REPLACE FUNCTION get_experiment_stats(
    p_experiment_id VARCHAR(100),
    p_metric_id VARCHAR(100)
)
RETURNS TABLE (
    variant_id VARCHAR(100),
    sample_size BIGINT,
    conversions BIGINT,
    conversion_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.variant_id,
        COUNT(DISTINCT CASE WHEN e.event_type = 'assignment' THEN e.user_id END) as sample_size,
        COUNT(DISTINCT CASE WHEN e.event_type = 'conversion' AND e.metric_id = p_metric_id THEN e.user_id END) as conversions,
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'assignment' THEN e.user_id END) > 0
            THEN COUNT(DISTINCT CASE WHEN e.event_type = 'conversion' AND e.metric_id = p_metric_id THEN e.user_id END)::DECIMAL / 
                 COUNT(DISTINCT CASE WHEN e.event_type = 'assignment' THEN e.user_id END)
            ELSE 0
        END as conversion_rate
    FROM experiment_events e
    WHERE e.experiment_id = p_experiment_id
    GROUP BY e.variant_id;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for experiment dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS experiment_dashboard AS
SELECT 
    e.id,
    e.name,
    e.status,
    e.created_at,
    e.started_at,
    COUNT(DISTINCT ea.user_id) as total_participants,
    COUNT(DISTINCT CASE WHEN ee.event_type = 'conversion' THEN ee.user_id END) as total_conversions,
    EXTRACT(EPOCH FROM (COALESCE(e.ended_at, NOW()) - e.started_at))/86400 as days_running
FROM experiments e
LEFT JOIN experiment_assignments ea ON e.id = ea.experiment_id
LEFT JOIN experiment_events ee ON e.id = ee.experiment_id
GROUP BY e.id, e.name, e.status, e.created_at, e.started_at, e.ended_at;

CREATE INDEX idx_exp_dashboard_status ON experiment_dashboard(status);

-- Create view for experiment funnel analysis
CREATE OR REPLACE VIEW experiment_funnel_analysis AS
SELECT 
    e.experiment_id,
    e.variant_id,
    COUNT(DISTINCT CASE WHEN e.event_type = 'assignment' THEN e.user_id END) as assigned_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'exposure' THEN e.user_id END) as exposed_users,
    COUNT(DISTINCT CASE WHEN e.event_type = 'conversion' THEN e.user_id END) as converted_users,
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'assignment' THEN e.user_id END) > 0
        THEN COUNT(DISTINCT CASE WHEN e.event_type = 'exposure' THEN e.user_id END)::DECIMAL / 
             COUNT(DISTINCT CASE WHEN e.event_type = 'assignment' THEN e.user_id END)
        ELSE 0
    END as exposure_rate,
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'exposure' THEN e.user_id END) > 0
        THEN COUNT(DISTINCT CASE WHEN e.event_type = 'conversion' THEN e.user_id END)::DECIMAL / 
             COUNT(DISTINCT CASE WHEN e.event_type = 'exposure' THEN e.user_id END)
        ELSE 0
    END as conversion_rate
FROM experiment_events e
GROUP BY e.experiment_id, e.variant_id;

-- Insert sample experiments for testing
INSERT INTO experiments (
    id, name, description, hypothesis, status,
    variants, metrics, targeting_rules
) VALUES 
(
    'homepage_cta_test',
    'Homepage CTA Button Test',
    'Test different CTA button colors and text',
    'Green CTA button with "Start Free Trial" will increase signups by 20%',
    'draft',
    '[
        {"id": "control", "name": "Blue Get Started", "weight": 0.5, "is_control": true, "config": {"color": "blue", "text": "Get Started"}},
        {"id": "green_trial", "name": "Green Free Trial", "weight": 0.5, "config": {"color": "green", "text": "Start Free Trial"}}
    ]'::jsonb,
    '[
        {"id": "signup_rate", "name": "Signup Rate", "type": "conversion", "event_name": "user_registered", "is_primary": true},
        {"id": "click_rate", "name": "CTA Click Rate", "type": "engagement", "event_name": "cta_clicked"}
    ]'::jsonb,
    '{"percentage_rollout": {"percentage": 50}}'::jsonb
),
(
    'trial_duration_test',
    'Free Trial Duration Test',
    'Test 14-day vs 30-day free trial',
    '30-day trial will increase paid conversions by 15%',
    'draft',
    '[
        {"id": "control", "name": "14-day trial", "weight": 0.5, "is_control": true, "config": {"trial_days": 14}},
        {"id": "extended", "name": "30-day trial", "weight": 0.5, "config": {"trial_days": 30}}
    ]'::jsonb,
    '[
        {"id": "trial_to_paid", "name": "Trial to Paid Conversion", "type": "conversion", "event_name": "subscription_started", "is_primary": true},
        {"id": "trial_activation", "name": "Trial Activation Rate", "type": "engagement", "event_name": "trial_activated"}
    ]'::jsonb,
    '{"new_users_only": {"max_days": 1}}'::jsonb
)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON experiments TO tradesense_app;
GRANT SELECT, INSERT ON experiment_assignments TO tradesense_app;
GRANT SELECT, INSERT ON experiment_events TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON experiment_results TO tradesense_app;
GRANT SELECT, INSERT ON feature_flag_evaluations TO tradesense_app;
GRANT SELECT ON experiment_dashboard TO tradesense_app;
GRANT SELECT ON experiment_funnel_analysis TO tradesense_app;
GRANT EXECUTE ON FUNCTION track_experiment_event TO tradesense_app;
GRANT EXECUTE ON FUNCTION get_experiment_stats TO tradesense_app;

-- Create trigger to refresh experiment dashboard
CREATE OR REPLACE FUNCTION refresh_experiment_dashboard()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY experiment_dashboard;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_refresh_exp_dashboard ON experiment_events;
CREATE TRIGGER trigger_refresh_exp_dashboard
AFTER INSERT ON experiment_events
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_experiment_dashboard();