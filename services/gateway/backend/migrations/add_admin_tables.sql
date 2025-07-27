-- Admin tables for TradeSense
-- Stores admin activity logs and support tickets

-- Create admin activity log table
CREATE TABLE IF NOT EXISTS admin_activity_log (
    id SERIAL PRIMARY KEY,
    admin_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_admin_activity_admin (admin_id),
    INDEX idx_admin_activity_action (action),
    INDEX idx_admin_activity_target (target_user_id),
    INDEX idx_admin_activity_created (created_at)
);

-- Create support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_support_tickets_user (user_id),
    INDEX idx_support_tickets_status (status),
    INDEX idx_support_tickets_assigned (assigned_to),
    INDEX idx_support_tickets_created (created_at)
);

-- Create support ticket messages table
CREATE TABLE IF NOT EXISTS support_ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id UUID NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    attachments JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_ticket_messages_ticket (ticket_id),
    INDEX idx_ticket_messages_user (user_id)
);

-- Create user notes table (for admin notes about users)
CREATE TABLE IF NOT EXISTS user_admin_notes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    admin_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_user_notes_user (user_id),
    INDEX idx_user_notes_admin (admin_id)
);

-- Create subscription changes log
CREATE TABLE IF NOT EXISTS subscription_changes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_tier VARCHAR(20),
    new_tier VARCHAR(20),
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    reason VARCHAR(255),
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_subscription_changes_user (user_id),
    INDEX idx_subscription_changes_date (changed_at)
);

-- Create system announcements table
CREATE TABLE IF NOT EXISTS system_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info', -- info, warning, maintenance, update
    target_audience VARCHAR(20) DEFAULT 'all', -- all, free, pro, premium
    is_active BOOLEAN DEFAULT TRUE,
    show_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    show_until TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_announcements_active (is_active, show_from, show_until)
);

-- Create user impersonation log
CREATE TABLE IF NOT EXISTS user_impersonation_log (
    id SERIAL PRIMARY KEY,
    admin_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    target_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    
    INDEX idx_impersonation_admin (admin_id),
    INDEX idx_impersonation_target (target_user_id),
    INDEX idx_impersonation_time (started_at)
);

-- Add notes column to users table if not exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS notes TEXT;

-- Create function to log subscription changes
CREATE OR REPLACE FUNCTION log_subscription_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.subscription_tier IS DISTINCT FROM NEW.subscription_tier OR
       OLD.subscription_status IS DISTINCT FROM NEW.subscription_status THEN
        INSERT INTO subscription_changes (
            user_id,
            old_tier,
            new_tier,
            old_status,
            new_status,
            changed_at
        ) VALUES (
            NEW.id,
            OLD.subscription_tier,
            NEW.subscription_tier,
            OLD.subscription_status,
            NEW.subscription_status,
            NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for subscription changes
DROP TRIGGER IF EXISTS trigger_log_subscription_change ON users;
CREATE TRIGGER trigger_log_subscription_change
AFTER UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION log_subscription_change();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_activity_log TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON support_tickets TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON support_ticket_messages TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_admin_notes TO tradesense_app;
GRANT SELECT, INSERT ON subscription_changes TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON system_announcements TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON user_impersonation_log TO tradesense_app;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);