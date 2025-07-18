-- GDPR compliance tables for TradeSense
-- Handles data export requests, privacy settings, and consent management

-- Create GDPR requests table
CREATE TABLE IF NOT EXISTS gdpr_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('export', 'deletion')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    file_path TEXT,
    download_url TEXT,
    error_message TEXT,
    
    INDEX idx_gdpr_requests_user (user_id),
    INDEX idx_gdpr_requests_status (status),
    INDEX idx_gdpr_requests_expires (expires_at)
);

-- Create user privacy settings table
CREATE TABLE IF NOT EXISTS user_privacy_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    analytics_enabled BOOLEAN DEFAULT TRUE,
    marketing_emails BOOLEAN DEFAULT TRUE,
    data_sharing BOOLEAN DEFAULT FALSE,
    cookie_preferences JSONB DEFAULT '{"necessary": true, "analytics": true, "marketing": false}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create consent log table
CREATE TABLE IF NOT EXISTS consent_log (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('granted', 'withdrawn')),
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_consent_log_user (user_id),
    INDEX idx_consent_log_type (consent_type),
    INDEX idx_consent_log_timestamp (timestamp)
);

-- Create account deletion feedback table
CREATE TABLE IF NOT EXISTS account_deletion_feedback (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,  -- Don't cascade delete, keep for analytics
    reason VARCHAR(50),
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_deletion_feedback_reason (reason),
    INDEX idx_deletion_feedback_created (created_at)
);

-- Create data processing activities table (GDPR Article 30)
CREATE TABLE IF NOT EXISTS data_processing_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    purpose TEXT NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    data_categories TEXT[],
    data_subjects TEXT[],
    recipients TEXT[],
    retention_period VARCHAR(100),
    security_measures TEXT,
    third_countries BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add GDPR-related columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS last_privacy_update TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS consent_version INTEGER DEFAULT 1;

-- Create function to anonymize user data
CREATE OR REPLACE FUNCTION anonymize_user_data(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Anonymize user record
    UPDATE users
    SET 
        email = CONCAT('deleted_', p_user_id, '@tradesense.com'),
        full_name = 'Deleted User',
        phone_number = NULL,
        stripe_customer_id = NULL,
        stripe_subscription_id = NULL,
        api_key = NULL,
        api_secret = NULL,
        metadata = '{}'::jsonb,
        settings = '{}'::jsonb,
        is_active = FALSE,
        deleted_at = NOW()
    WHERE id = p_user_id;
    
    -- Anonymize trades
    UPDATE trades
    SET notes = 'REDACTED'
    WHERE user_id = p_user_id;
    
    -- Anonymize journal entries
    UPDATE journal_entries
    SET 
        title = 'REDACTED',
        content = 'REDACTED'
    WHERE user_id = p_user_id;
    
    -- Delete sensitive support data
    UPDATE support_ticket_messages
    SET message = 'REDACTED'
    WHERE ticket_id IN (
        SELECT id FROM support_tickets WHERE user_id = p_user_id
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to generate GDPR export
CREATE OR REPLACE FUNCTION generate_gdpr_export(p_user_id UUID)
RETURNS TABLE (
    category TEXT,
    data JSONB
) AS $$
BEGIN
    -- User profile data
    RETURN QUERY
    SELECT 
        'user_profile'::TEXT,
        row_to_json(u.*)::JSONB
    FROM users u
    WHERE u.id = p_user_id;
    
    -- Trades data
    RETURN QUERY
    SELECT 
        'trades'::TEXT,
        jsonb_agg(row_to_json(t.*))::JSONB
    FROM trades t
    WHERE t.user_id = p_user_id;
    
    -- Add more categories as needed...
END;
$$ LANGUAGE plpgsql;

-- Insert default data processing activities
INSERT INTO data_processing_activities (
    name, purpose, legal_basis, data_categories, 
    data_subjects, recipients, retention_period, security_measures
) VALUES 
(
    'User Account Management',
    'Provide trading analytics services',
    'Contract',
    ARRAY['Account data', 'Contact information', 'Trading data'],
    ARRAY['Registered users'],
    ARRAY['Internal staff', 'Cloud service providers'],
    'Until account deletion',
    'Encryption at rest and in transit, access controls, regular security audits'
),
(
    'Payment Processing',
    'Process subscription payments',
    'Contract',
    ARRAY['Payment information', 'Transaction history'],
    ARRAY['Paying customers'],
    ARRAY['Stripe (payment processor)'],
    '7 years (legal requirement)',
    'PCI DSS compliance, tokenization, secure payment gateway'
),
(
    'Analytics and Improvement',
    'Improve service quality and user experience',
    'Legitimate interest',
    ARRAY['Usage data', 'Performance metrics'],
    ARRAY['All users'],
    ARRAY['Internal analytics team'],
    '2 years',
    'Anonymization, aggregation, secure analytics platform'
),
(
    'Customer Support',
    'Provide customer service',
    'Contract',
    ARRAY['Support communications', 'Account data'],
    ARRAY['Users requesting support'],
    ARRAY['Support team'],
    '3 years',
    'Access controls, secure ticketing system'
)
ON CONFLICT DO NOTHING;

-- Create trigger to update privacy settings timestamp
CREATE OR REPLACE FUNCTION update_privacy_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- Also update user's last privacy update
    UPDATE users 
    SET last_privacy_update = NOW()
    WHERE id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_privacy_settings ON user_privacy_settings;
CREATE TRIGGER trigger_update_privacy_settings
BEFORE UPDATE ON user_privacy_settings
FOR EACH ROW
EXECUTE FUNCTION update_privacy_settings_timestamp();

-- Create view for data retention policy
CREATE OR REPLACE VIEW data_retention_policy AS
SELECT 
    'User Account Data' as data_type,
    'Until account deletion' as retention_period,
    'Core service data' as description
UNION ALL
SELECT 
    'Trading Records' as data_type,
    'Until account deletion' as retention_period,
    'User trading history and analytics' as description
UNION ALL
SELECT 
    'Payment Records' as data_type,
    '7 years' as retention_period,
    'Legal requirement for financial records' as description
UNION ALL
SELECT 
    'Support Tickets' as data_type,
    '3 years' as retention_period,
    'Customer service history' as description
UNION ALL
SELECT 
    'Analytics Events' as data_type,
    '2 years' as retention_period,
    'Anonymous usage data' as description
UNION ALL
SELECT 
    'Audit Logs' as data_type,
    '1 year' as retention_period,
    'Security and compliance logs' as description;

-- Create function to clean up expired data
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS VOID AS $$
BEGIN
    -- Delete expired GDPR export files
    DELETE FROM gdpr_requests
    WHERE request_type = 'export'
    AND status = 'completed'
    AND expires_at < NOW();
    
    -- Delete old analytics events
    DELETE FROM analytics_events
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Delete old consent logs
    DELETE FROM consent_log
    WHERE timestamp < NOW() - INTERVAL '5 years';
    
    -- Clean up other expired data...
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON gdpr_requests TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON user_privacy_settings TO tradesense_app;
GRANT SELECT, INSERT ON consent_log TO tradesense_app;
GRANT SELECT, INSERT ON account_deletion_feedback TO tradesense_app;
GRANT SELECT ON data_processing_activities TO tradesense_app;
GRANT SELECT ON data_retention_policy TO tradesense_app;
GRANT EXECUTE ON FUNCTION anonymize_user_data TO tradesense_app;
GRANT EXECUTE ON FUNCTION generate_gdpr_export TO tradesense_app;
GRANT EXECUTE ON FUNCTION cleanup_expired_data TO tradesense_app;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_analytics_events_created ON analytics_events(created_at);
CREATE INDEX IF NOT EXISTS idx_gdpr_requests_processing ON gdpr_requests(status) WHERE status IN ('pending', 'processing');