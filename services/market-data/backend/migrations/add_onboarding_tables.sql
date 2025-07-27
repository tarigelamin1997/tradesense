-- Onboarding system tables for TradeSense
-- Tracks user progress through setup process

-- Create user onboarding state table
CREATE TABLE IF NOT EXISTS user_onboarding (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    onboarding_step VARCHAR(50) NOT NULL DEFAULT 'welcome',
    onboarding_data JSONB DEFAULT '{}'::jsonb,
    onboarding_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_onboarding_step (onboarding_step),
    INDEX idx_onboarding_completed (onboarding_completed_at)
);

-- Create onboarding events table for analytics
CREATE TABLE IF NOT EXISTS onboarding_events (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_onboarding_events_user (user_id),
    INDEX idx_onboarding_events_type (event_type),
    INDEX idx_onboarding_events_created (created_at)
);

-- Create onboarding tips table
CREATE TABLE IF NOT EXISTS onboarding_tips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tip_key VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    link VARCHAR(255),
    target_day INTEGER, -- Day after signup to show this tip
    target_step VARCHAR(50), -- Onboarding step to show this tip
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_tips_active (is_active),
    INDEX idx_tips_day (target_day),
    INDEX idx_tips_step (target_step)
);

-- Create user tips viewed table
CREATE TABLE IF NOT EXISTS user_tips_viewed (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tip_id UUID NOT NULL REFERENCES onboarding_tips(id) ON DELETE CASCADE,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    clicked BOOLEAN DEFAULT FALSE,
    
    UNIQUE(user_id, tip_id),
    INDEX idx_user_tips_user (user_id),
    INDEX idx_user_tips_viewed (viewed_at)
);

-- Add onboarding columns to users table if not exists
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS onboarding_skipped BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;

-- Create function to initialize onboarding for new users
CREATE OR REPLACE FUNCTION initialize_user_onboarding()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_onboarding (user_id, onboarding_step)
    VALUES (NEW.id, 'welcome')
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for new user onboarding
DROP TRIGGER IF EXISTS trigger_initialize_onboarding ON users;
CREATE TRIGGER trigger_initialize_onboarding
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION initialize_user_onboarding();

-- Insert default onboarding tips
INSERT INTO onboarding_tips (tip_key, title, content, link, target_day, priority)
VALUES 
(
    'import_trades_day1',
    'Import Your Trades',
    'You can import trades from CSV or connect to your broker for automatic sync',
    '/trades/import',
    1,
    100
),
(
    'basic_analytics_day1',
    'View Your Performance',
    'Check your win rate and P&L in the Analytics dashboard',
    '/analytics',
    1,
    90
),
(
    'set_goals_day3',
    'Set Trading Goals',
    'Define your trading objectives and track progress',
    '/settings/goals',
    3,
    100
),
(
    'journal_entry_day3',
    'Start Journaling',
    'Document your trades and thoughts for better insights',
    '/journal',
    3,
    90
),
(
    'advanced_analytics_day7',
    'Explore Advanced Analytics',
    'Dive deeper into your trading patterns and performance',
    '/analytics/advanced',
    7,
    100
),
(
    'upgrade_prompt_day7',
    'Unlock More Features',
    'Upgrade to Pro for unlimited trades and advanced features',
    '/subscription',
    7,
    80
)
ON CONFLICT (tip_key) DO UPDATE
SET 
    title = EXCLUDED.title,
    content = EXCLUDED.content,
    link = EXCLUDED.link,
    target_day = EXCLUDED.target_day,
    priority = EXCLUDED.priority;

-- Create function to get relevant tips for user
CREATE OR REPLACE FUNCTION get_user_tips(
    p_user_id UUID,
    p_account_age_days INTEGER
)
RETURNS TABLE (
    id UUID,
    title VARCHAR,
    content TEXT,
    link VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.content,
        t.link
    FROM onboarding_tips t
    LEFT JOIN user_tips_viewed utv ON t.id = utv.tip_id AND utv.user_id = p_user_id
    WHERE t.is_active = TRUE
    AND (t.target_day IS NULL OR t.target_day <= p_account_age_days)
    AND utv.id IS NULL -- Not yet viewed
    ORDER BY t.priority DESC, t.created_at
    LIMIT 3;
END;
$$ LANGUAGE plpgsql;

-- Create analytics view for onboarding funnel
CREATE OR REPLACE VIEW onboarding_funnel_analytics AS
SELECT 
    onboarding_step,
    COUNT(DISTINCT user_id) as users_reached,
    COUNT(DISTINCT CASE WHEN onboarding_completed_at IS NOT NULL THEN user_id END) as users_completed,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600)::float as avg_hours_in_step
FROM user_onboarding
GROUP BY onboarding_step;

-- Create view for onboarding completion rate by cohort
CREATE OR REPLACE VIEW onboarding_completion_by_cohort AS
SELECT 
    DATE_TRUNC('week', u.created_at) as cohort_week,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT CASE WHEN uo.onboarding_completed_at IS NOT NULL THEN u.id END) as completed_users,
    AVG(CASE WHEN uo.onboarding_completed_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (uo.onboarding_completed_at - u.created_at))/3600 
        ELSE NULL END)::float as avg_completion_hours
FROM users u
LEFT JOIN user_onboarding uo ON u.id = uo.user_id
GROUP BY cohort_week
ORDER BY cohort_week DESC;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON user_onboarding TO tradesense_app;
GRANT SELECT, INSERT ON onboarding_events TO tradesense_app;
GRANT SELECT ON onboarding_tips TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON user_tips_viewed TO tradesense_app;
GRANT SELECT ON onboarding_funnel_analytics TO tradesense_app;
GRANT SELECT ON onboarding_completion_by_cohort TO tradesense_app;