-- MFA Migration: Add Multi-Factor Authentication Tables
-- Run this migration to add MFA support to TradeSense

-- 1. Add MFA columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS mfa_methods VARCHAR[] DEFAULT ARRAY[]::VARCHAR[];

-- 2. Create MFA devices table
CREATE TABLE IF NOT EXISTS mfa_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('totp', 'sms', 'email')),
    device_name VARCHAR(100) NOT NULL,
    secret_encrypted TEXT,
    phone_number VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'disabled')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP WITH TIME ZONE,
    disabled_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, device_type, status)
);

CREATE INDEX idx_mfa_devices_user_id ON mfa_devices(user_id);
CREATE INDEX idx_mfa_devices_status ON mfa_devices(status);
CREATE INDEX idx_mfa_devices_type_status ON mfa_devices(device_type, status);

-- 3. Create backup codes table
CREATE TABLE IF NOT EXISTS mfa_backup_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'used', 'disabled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, code_hash)
);

CREATE INDEX idx_mfa_backup_codes_user_id ON mfa_backup_codes(user_id);
CREATE INDEX idx_mfa_backup_codes_status ON mfa_backup_codes(status);

-- 4. Create verification codes table (for SMS/Email codes)
CREATE TABLE IF NOT EXISTS mfa_verification_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash VARCHAR(64) NOT NULL,
    method VARCHAR(20) NOT NULL CHECK (method IN ('sms', 'email')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mfa_verification_codes_user_id ON mfa_verification_codes(user_id);
CREATE INDEX idx_mfa_verification_codes_expires ON mfa_verification_codes(expires_at);

-- 5. Create MFA auth attempts table (for rate limiting)
CREATE TABLE IF NOT EXISTS mfa_auth_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method VARCHAR(20) NOT NULL,
    success BOOLEAN NOT NULL,
    ip_address INET,
    user_agent TEXT,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mfa_auth_attempts_user_id ON mfa_auth_attempts(user_id);
CREATE INDEX idx_mfa_auth_attempts_attempted_at ON mfa_auth_attempts(attempted_at);
CREATE INDEX idx_mfa_auth_attempts_user_success ON mfa_auth_attempts(user_id, success);

-- 6. Create trusted devices table
CREATE TABLE IF NOT EXISTS mfa_trusted_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(64) NOT NULL,
    device_name VARCHAR(100),
    trust_token VARCHAR(255) NOT NULL,
    last_ip_address INET,
    last_user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(user_id, device_fingerprint)
);

CREATE INDEX idx_mfa_trusted_devices_user_id ON mfa_trusted_devices(user_id);
CREATE INDEX idx_mfa_trusted_devices_token ON mfa_trusted_devices(trust_token);
CREATE INDEX idx_mfa_trusted_devices_expires ON mfa_trusted_devices(expires_at);

-- 7. Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_mfa_devices_updated_at 
    BEFORE UPDATE ON mfa_devices 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at_column();

-- 8. Add security metrics for monitoring
CREATE TABLE IF NOT EXISTS mfa_security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mfa_security_events_user_id ON mfa_security_events(user_id);
CREATE INDEX idx_mfa_security_events_type ON mfa_security_events(event_type);
CREATE INDEX idx_mfa_security_events_created_at ON mfa_security_events(created_at);

-- 9. Insert initial MFA security event
INSERT INTO mfa_security_events (event_type, event_data)
VALUES ('mfa_tables_created', '{"migration": "add_mfa_tables", "version": "1.0.0"}');

-- 10. Create view for MFA admin dashboard
CREATE OR REPLACE VIEW mfa_admin_stats AS
SELECT 
    COUNT(DISTINCT CASE WHEN mfa_enabled THEN id END) as users_with_mfa,
    COUNT(DISTINCT CASE WHEN NOT mfa_enabled THEN id END) as users_without_mfa,
    (SELECT COUNT(*) FROM mfa_devices WHERE status = 'active' AND device_type = 'totp') as totp_devices,
    (SELECT COUNT(*) FROM mfa_devices WHERE status = 'active' AND device_type = 'sms') as sms_devices,
    (SELECT COUNT(*) FROM mfa_devices WHERE status = 'active' AND device_type = 'email') as email_devices,
    (SELECT COUNT(DISTINCT user_id) FROM mfa_backup_codes WHERE status = 'active') as users_with_backup_codes,
    (SELECT COUNT(*) FROM mfa_auth_attempts WHERE attempted_at > NOW() - INTERVAL '24 hours' AND success = true) as successful_auths_24h,
    (SELECT COUNT(*) FROM mfa_auth_attempts WHERE attempted_at > NOW() - INTERVAL '24 hours' AND success = false) as failed_auths_24h
FROM users;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_devices TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_backup_codes TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_verification_codes TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_auth_attempts TO tradesense_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON mfa_trusted_devices TO tradesense_app;
GRANT SELECT, INSERT ON mfa_security_events TO tradesense_app;
GRANT SELECT ON mfa_admin_stats TO tradesense_app;

-- Create cleanup function for expired codes
CREATE OR REPLACE FUNCTION cleanup_expired_mfa_codes()
RETURNS void AS $$
BEGIN
    -- Delete expired verification codes
    DELETE FROM mfa_verification_codes 
    WHERE expires_at < NOW() - INTERVAL '1 hour';
    
    -- Delete old auth attempts (keep 30 days)
    DELETE FROM mfa_auth_attempts
    WHERE attempted_at < NOW() - INTERVAL '30 days';
    
    -- Delete expired trusted devices
    DELETE FROM mfa_trusted_devices
    WHERE expires_at < NOW();
    
    -- Log cleanup
    INSERT INTO mfa_security_events (event_type, event_data)
    VALUES ('mfa_cleanup', jsonb_build_object(
        'cleaned_at', NOW(),
        'verification_codes_deleted', (SELECT COUNT(*) FROM mfa_verification_codes WHERE expires_at < NOW() - INTERVAL '1 hour'),
        'auth_attempts_deleted', (SELECT COUNT(*) FROM mfa_auth_attempts WHERE attempted_at < NOW() - INTERVAL '30 days'),
        'trusted_devices_deleted', (SELECT COUNT(*) FROM mfa_trusted_devices WHERE expires_at < NOW())
    ));
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (requires pg_cron extension or external scheduler)
-- SELECT cron.schedule('cleanup-mfa-codes', '0 */6 * * *', 'SELECT cleanup_expired_mfa_codes();');