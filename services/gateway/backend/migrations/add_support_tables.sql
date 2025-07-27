-- Support system tables for TradeSense
-- Includes knowledge base articles and article ratings

-- Create knowledge base articles table
CREATE TABLE IF NOT EXISTS kb_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[],
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    is_published BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    related_articles UUID[],
    attachments JSONB,
    search_vector tsvector,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_kb_articles_slug (slug),
    INDEX idx_kb_articles_category (category),
    INDEX idx_kb_articles_published (is_published),
    INDEX idx_kb_articles_search (search_vector) USING gin
);

-- Create article ratings table
CREATE TABLE IF NOT EXISTS kb_article_ratings (
    id SERIAL PRIMARY KEY,
    article_id UUID NOT NULL REFERENCES kb_articles(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    helpful BOOLEAN NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(article_id, user_id),
    INDEX idx_article_ratings_article (article_id),
    INDEX idx_article_ratings_user (user_id)
);

-- Create ticket attachments table
CREATE TABLE IF NOT EXISTS ticket_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    message_id INTEGER REFERENCES support_ticket_messages(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    content_type VARCHAR(100),
    storage_path TEXT NOT NULL,
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_ticket_attachments_ticket (ticket_id),
    INDEX idx_ticket_attachments_message (message_id)
);

-- Create canned responses table for support efficiency
CREATE TABLE IF NOT EXISTS support_canned_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT[],
    usage_count INTEGER DEFAULT 0,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_canned_responses_category (category),
    INDEX idx_canned_responses_created_by (created_by)
);

-- Create support team assignments table
CREATE TABLE IF NOT EXISTS support_team_assignments (
    id SERIAL PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    specialization VARCHAR(50)[],
    max_tickets INTEGER DEFAULT 20,
    is_available BOOLEAN DEFAULT TRUE,
    last_assigned_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(agent_id),
    INDEX idx_team_assignments_available (is_available),
    INDEX idx_team_assignments_last_assigned (last_assigned_at)
);

-- Create ticket SLA tracking table
CREATE TABLE IF NOT EXISTS ticket_sla_breaches (
    id SERIAL PRIMARY KEY,
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    breach_type VARCHAR(50) NOT NULL, -- first_response, resolution
    expected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    breached_at TIMESTAMP WITH TIME ZONE NOT NULL,
    breach_duration INTERVAL,
    
    INDEX idx_sla_breaches_ticket (ticket_id),
    INDEX idx_sla_breaches_type (breach_type),
    INDEX idx_sla_breaches_date (breached_at)
);

-- Create ticket satisfaction ratings
CREATE TABLE IF NOT EXISTS ticket_satisfaction_ratings (
    id SERIAL PRIMARY KEY,
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    rated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(ticket_id),
    INDEX idx_satisfaction_ratings_rating (rating)
);

-- Add missing columns to support_tickets if they don't exist
ALTER TABLE support_tickets 
ADD COLUMN IF NOT EXISTS first_response_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS tags TEXT[],
ADD COLUMN IF NOT EXISTS is_spam BOOLEAN DEFAULT FALSE;

-- Create function to update KB article search vector
CREATE OR REPLACE FUNCTION update_kb_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english',
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.summary, '') || ' ' ||
        COALESCE(NEW.content, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for search vector
DROP TRIGGER IF EXISTS trigger_update_kb_search_vector ON kb_articles;
CREATE TRIGGER trigger_update_kb_search_vector
BEFORE INSERT OR UPDATE ON kb_articles
FOR EACH ROW
EXECUTE FUNCTION update_kb_search_vector();

-- Create function to track first response time
CREATE OR REPLACE FUNCTION track_first_response()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is the first non-internal message from support
    IF NOT NEW.is_internal AND NEW.user_id != (
        SELECT user_id FROM support_tickets WHERE id = NEW.ticket_id
    ) THEN
        UPDATE support_tickets
        SET first_response_at = NEW.created_at
        WHERE id = NEW.ticket_id
        AND first_response_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for first response tracking
DROP TRIGGER IF EXISTS trigger_track_first_response ON support_ticket_messages;
CREATE TRIGGER trigger_track_first_response
AFTER INSERT ON support_ticket_messages
FOR EACH ROW
EXECUTE FUNCTION track_first_response();

-- Insert some default KB articles
INSERT INTO kb_articles (title, slug, category, summary, content, tags, author_id, is_published)
VALUES 
(
    'Getting Started with TradeSense',
    'getting-started',
    'basics',
    'Learn the basics of using TradeSense to track and analyze your trades',
    E'# Getting Started with TradeSense\n\nWelcome to TradeSense! This guide will help you get started with our platform.\n\n## Creating Your Account\n\n1. Click "Sign Up" on the homepage\n2. Enter your email and create a secure password\n3. Verify your email address\n4. Complete your profile\n\n## Importing Your First Trades\n\n### Manual Entry\n1. Go to Dashboard > Add Trade\n2. Fill in trade details\n3. Click Save\n\n### CSV Import\n1. Go to Dashboard > Import\n2. Download our CSV template\n3. Fill in your trades\n4. Upload the file\n\n## Understanding the Analytics\n\nOur analytics dashboard provides:\n- Win/loss ratio\n- Average profit/loss\n- Performance by strategy\n- Risk metrics\n\n## Next Steps\n\n- Explore the Analytics section\n- Set up your trading strategies\n- Configure alerts and notifications',
    ARRAY['getting-started', 'basics', 'tutorial'],
    (SELECT id FROM users WHERE email = 'admin@tradesense.com' LIMIT 1),
    true
),
(
    'Understanding Subscription Plans',
    'subscription-plans',
    'billing',
    'Compare features and pricing across our subscription tiers',
    E'# TradeSense Subscription Plans\n\n## Free Plan\n- 100 trades per month\n- Basic analytics\n- Email support\n- CSV export\n\n## Pro Plan ($49.99/month)\n- Unlimited trades\n- Advanced analytics\n- Priority support\n- API access\n- Real-time sync\n- Custom reports\n\n## Premium Plan ($99.99/month)\n- Everything in Pro\n- Real-time alerts\n- Phone support\n- White-label reports\n- Team collaboration\n- Advanced risk analytics\n\n## Changing Plans\n\n1. Go to Settings > Subscription\n2. Select your new plan\n3. Confirm changes\n\nChanges take effect immediately. When upgrading, you''ll be charged a prorated amount. When downgrading, credit is applied to future bills.\n\n## FAQ\n\n**Can I cancel anytime?**\nYes, you can cancel your subscription at any time. You''ll continue to have access until the end of your billing period.\n\n**Is there a free trial?**\nYes, Pro and Premium plans include a 14-day free trial for new users.',
    ARRAY['subscription', 'billing', 'pricing', 'plans'],
    (SELECT id FROM users WHERE email = 'admin@tradesense.com' LIMIT 1),
    true
),
(
    'How to Export Your Data',
    'data-export-guide',
    'features',
    'Export your trading data in various formats for analysis or backup',
    E'# Exporting Your Data\n\nTradeSense allows you to export your data in multiple formats.\n\n## Available Export Formats\n\n- **CSV**: Compatible with Excel and Google Sheets\n- **JSON**: For developers and API integration\n- **PDF**: Professional reports for sharing\n\n## How to Export\n\n1. Navigate to Analytics > Export Data\n2. Select date range\n3. Choose format\n4. Select data to include:\n   - Trades\n   - Analytics\n   - Performance metrics\n5. Click "Export"\n\n## GDPR Compliance\n\nFor GDPR data requests:\n1. Go to Settings > Privacy\n2. Click "Request My Data"\n3. You''ll receive a complete data package within 48 hours\n\n## Automated Exports\n\nPro and Premium users can set up automated exports:\n1. Go to Settings > Automation\n2. Configure export schedule\n3. Choose destination (email, cloud storage)',
    ARRAY['export', 'data', 'csv', 'backup', 'gdpr'],
    (SELECT id FROM users WHERE email = 'admin@tradesense.com' LIMIT 1),
    true
);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON kb_articles TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON kb_article_ratings TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ticket_attachments TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON support_canned_responses TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON support_team_assignments TO tradesense_app;
GRANT SELECT, INSERT ON ticket_sla_breaches TO tradesense_app;
GRANT SELECT, INSERT ON ticket_satisfaction_ratings TO tradesense_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO tradesense_app;