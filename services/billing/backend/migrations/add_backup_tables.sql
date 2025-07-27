-- Backup system tables for TradeSense
-- Tracks backup jobs, schedules, and restore operations

-- Create backups table
CREATE TABLE IF NOT EXISTS backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_name VARCHAR(255) NOT NULL,
    backup_type VARCHAR(50) NOT NULL CHECK (backup_type IN ('database', 'files', 'full')),
    backup_subtype VARCHAR(50) CHECK (backup_subtype IN ('full', 'incremental', 'differential')),
    backup_frequency VARCHAR(20) CHECK (backup_frequency IN ('daily', 'weekly', 'monthly', 'yearly', 'manual')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'deleted')),
    file_path TEXT,
    file_size BIGINT,
    remote_path TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_backups_status (status),
    INDEX idx_backups_type (backup_type),
    INDEX idx_backups_created (created_at),
    INDEX idx_backups_name (backup_name)
);

-- Create backup schedules table
CREATE TABLE IF NOT EXISTS backup_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    backup_type VARCHAR(50) NOT NULL,
    schedule_type VARCHAR(20) NOT NULL CHECK (schedule_type IN ('cron', 'interval', 'time')),
    schedule_config JSONB NOT NULL,
    destination VARCHAR(20) NOT NULL DEFAULT 'local' CHECK (destination IN ('local', 's3', 'gcs', 'azure')),
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_schedules_active (is_active),
    INDEX idx_schedules_next_run (next_run_at)
);

-- Create restore operations table
CREATE TABLE IF NOT EXISTS restore_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_id UUID NOT NULL REFERENCES backups(id),
    restore_point_id UUID REFERENCES backups(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    target_database VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    performed_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_restores_backup (backup_id),
    INDEX idx_restores_status (status),
    INDEX idx_restores_created (created_at)
);

-- Create backup verification table
CREATE TABLE IF NOT EXISTS backup_verifications (
    id SERIAL PRIMARY KEY,
    backup_id UUID NOT NULL REFERENCES backups(id),
    verification_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('passed', 'failed', 'warning')),
    checks JSONB NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_verifications_backup (backup_id),
    INDEX idx_verifications_status (status),
    INDEX idx_verifications_date (verified_at)
);

-- Create backup retention policies table
CREATE TABLE IF NOT EXISTS backup_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    backup_type VARCHAR(50),
    retention_days INTEGER NOT NULL,
    priority INTEGER DEFAULT 0,
    conditions JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_retention_active (is_active),
    INDEX idx_retention_type (backup_type)
);

-- Create backup metrics table for monitoring
CREATE TABLE IF NOT EXISTS backup_metrics (
    id SERIAL PRIMARY KEY,
    backup_id UUID REFERENCES backups(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL,
    unit VARCHAR(50),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_metrics_backup (backup_id),
    INDEX idx_metrics_name (metric_name),
    INDEX idx_metrics_time (recorded_at)
);

-- Add backup-related columns to existing tables
ALTER TABLE users
ADD COLUMN IF NOT EXISTS backup_encryption_key TEXT,
ADD COLUMN IF NOT EXISTS backup_notifications_enabled BOOLEAN DEFAULT TRUE;

-- Create function to calculate next backup time
CREATE OR REPLACE FUNCTION calculate_next_backup_time(
    schedule_type VARCHAR,
    schedule_config JSONB,
    last_run TIMESTAMP WITH TIME ZONE
)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    next_run TIMESTAMP WITH TIME ZONE;
BEGIN
    IF schedule_type = 'interval' THEN
        -- Interval-based schedule (e.g., every 6 hours)
        next_run := COALESCE(last_run, NOW()) + (schedule_config->>'interval')::INTERVAL;
    ELSIF schedule_type = 'time' THEN
        -- Time-based schedule (e.g., daily at 2 AM)
        next_run := date_trunc('day', COALESCE(last_run, NOW())) + (schedule_config->>'time')::TIME;
        IF next_run <= NOW() THEN
            next_run := next_run + INTERVAL '1 day';
        END IF;
    ELSIF schedule_type = 'cron' THEN
        -- Cron expression (requires pg_cron extension)
        -- Simplified implementation
        next_run := NOW() + INTERVAL '1 day';
    END IF;
    
    RETURN next_run;
END;
$$ LANGUAGE plpgsql;

-- Create function to get backup statistics
CREATE OR REPLACE FUNCTION get_backup_statistics(
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    backup_type VARCHAR,
    total_count BIGINT,
    success_count BIGINT,
    failed_count BIGINT,
    total_size_gb DECIMAL,
    avg_duration_minutes DECIMAL,
    success_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.backup_type,
        COUNT(*) as total_count,
        COUNT(CASE WHEN b.status = 'completed' THEN 1 END) as success_count,
        COUNT(CASE WHEN b.status = 'failed' THEN 1 END) as failed_count,
        ROUND(SUM(b.file_size) / 1024.0 / 1024.0 / 1024.0, 2) as total_size_gb,
        ROUND(AVG(
            EXTRACT(EPOCH FROM (b.completed_at - b.started_at)) / 60.0
        )::DECIMAL, 2) as avg_duration_minutes,
        ROUND(
            COUNT(CASE WHEN b.status = 'completed' THEN 1 END)::DECIMAL / 
            NULLIF(COUNT(*), 0) * 100, 2
        ) as success_rate
    FROM backups b
    WHERE b.created_at >= NOW() - INTERVAL '1 day' * p_days
    GROUP BY b.backup_type;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update schedule next run time
CREATE OR REPLACE FUNCTION update_schedule_next_run()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.last_run_at IS DISTINCT FROM OLD.last_run_at THEN
        NEW.next_run_at = calculate_next_backup_time(
            NEW.schedule_type,
            NEW.schedule_config,
            NEW.last_run_at
        );
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_schedule_next_run ON backup_schedules;
CREATE TRIGGER trigger_update_schedule_next_run
BEFORE UPDATE ON backup_schedules
FOR EACH ROW
EXECUTE FUNCTION update_schedule_next_run();

-- Insert default backup schedules
INSERT INTO backup_schedules (
    name, backup_type, schedule_type, schedule_config, destination
) VALUES 
(
    'Daily Database Backup',
    'database',
    'time',
    '{"time": "02:00:00", "timezone": "UTC"}'::jsonb,
    'local'
),
(
    'Daily Files Backup',
    'files',
    'time',
    '{"time": "03:00:00", "timezone": "UTC"}'::jsonb,
    'local'
),
(
    'Weekly Full Backup',
    'full',
    'time',
    '{"time": "04:00:00", "timezone": "UTC", "day_of_week": 0}'::jsonb,
    's3'
)
ON CONFLICT DO NOTHING;

-- Insert default retention policies
INSERT INTO backup_retention_policies (
    name, backup_type, retention_days, priority
) VALUES 
('Daily Backups', NULL, 7, 1),
('Weekly Backups', NULL, 30, 2),
('Monthly Backups', NULL, 365, 3),
('Database Backups', 'database', 14, 1),
('File Backups', 'files', 30, 1)
ON CONFLICT DO NOTHING;

-- Create view for backup status dashboard
CREATE OR REPLACE VIEW backup_status_dashboard AS
SELECT 
    b.backup_type,
    b.status,
    COUNT(*) as count,
    MAX(b.created_at) as last_backup,
    SUM(b.file_size) as total_size,
    AVG(EXTRACT(EPOCH FROM (b.completed_at - b.started_at))) as avg_duration_seconds
FROM backups b
WHERE b.created_at >= NOW() - INTERVAL '7 days'
GROUP BY b.backup_type, b.status;

-- Create view for upcoming backups
CREATE OR REPLACE VIEW upcoming_backups AS
SELECT 
    s.name,
    s.backup_type,
    s.next_run_at,
    s.destination,
    EXTRACT(EPOCH FROM (s.next_run_at - NOW())) / 3600 as hours_until_next
FROM backup_schedules s
WHERE s.is_active = TRUE
AND s.next_run_at > NOW()
ORDER BY s.next_run_at;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON backups TO tradesense_app;
GRANT SELECT, INSERT, UPDATE ON backup_schedules TO tradesense_app;
GRANT SELECT, INSERT ON restore_operations TO tradesense_app;
GRANT SELECT, INSERT ON backup_verifications TO tradesense_app;
GRANT SELECT ON backup_retention_policies TO tradesense_app;
GRANT SELECT, INSERT ON backup_metrics TO tradesense_app;
GRANT SELECT ON backup_status_dashboard TO tradesense_app;
GRANT SELECT ON upcoming_backups TO tradesense_app;

-- Add backup monitoring to Prometheus metrics
CREATE OR REPLACE FUNCTION backup_metrics_prometheus()
RETURNS TABLE (
    metric_name TEXT,
    metric_value DECIMAL,
    labels TEXT
) AS $$
BEGIN
    -- Backup success rate
    RETURN QUERY
    SELECT 
        'tradesense_backup_success_rate'::TEXT,
        ROUND(
            COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / 
            NULLIF(COUNT(*), 0) * 100, 2
        ),
        format('backup_type="%s"', backup_type)::TEXT
    FROM backups
    WHERE created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY backup_type;
    
    -- Backup sizes
    RETURN QUERY
    SELECT 
        'tradesense_backup_size_bytes'::TEXT,
        SUM(file_size)::DECIMAL,
        format('backup_type="%s"', backup_type)::TEXT
    FROM backups
    WHERE status = 'completed'
    AND created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY backup_type;
    
    -- Backup duration
    RETURN QUERY
    SELECT 
        'tradesense_backup_duration_seconds'::TEXT,
        AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::DECIMAL,
        format('backup_type="%s"', backup_type)::TEXT
    FROM backups
    WHERE status = 'completed'
    AND created_at >= NOW() - INTERVAL '24 hours'
    GROUP BY backup_type;
END;
$$ LANGUAGE plpgsql;