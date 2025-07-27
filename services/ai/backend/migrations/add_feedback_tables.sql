-- Feedback System Tables
-- Stores user feedback submissions

-- Create feedback patterns table first (referenced by feedback)
CREATE TABLE IF NOT EXISTS feedback_patterns (
    id VARCHAR PRIMARY KEY,
    pattern_signature VARCHAR UNIQUE NOT NULL,
    pattern_type VARCHAR NOT NULL,
    occurrences INTEGER DEFAULT 1,
    affected_users INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    root_cause TEXT,
    resolution TEXT,
    CONSTRAINT pattern_signature_unique UNIQUE (pattern_signature)
);

-- Create index for pattern lookups
CREATE INDEX idx_feedback_patterns_signature ON feedback_patterns(pattern_signature);
CREATE INDEX idx_feedback_patterns_type ON feedback_patterns(pattern_type);

-- Create main feedback table
CREATE TABLE IF NOT EXISTS feedback (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
    type VARCHAR NOT NULL CHECK (type IN ('bug', 'feature', 'performance', 'ux', 'other')),
    severity VARCHAR NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR DEFAULT 'new' CHECK (status IN ('new', 'investigating', 'in_progress', 'resolved', 'closed')),
    
    -- Context data
    url TEXT,
    user_agent TEXT,
    screen_resolution VARCHAR,
    subscription_tier VARCHAR,
    
    -- Journey data (JSON)
    previous_pages TEXT,
    last_actions TEXT,
    error_logs TEXT,
    
    -- Additional details
    expected_behavior TEXT,
    actual_behavior TEXT,
    screenshot TEXT, -- Base64 encoded
    email VARCHAR,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    assigned_to VARCHAR,
    
    -- Analytics
    pattern_id VARCHAR REFERENCES feedback_patterns(id) ON DELETE SET NULL,
    duplicate_count INTEGER DEFAULT 0,
    affected_users INTEGER DEFAULT 1,
    first_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT feedback_user_fk FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT feedback_pattern_fk FOREIGN KEY (pattern_id) REFERENCES feedback_patterns(id) ON DELETE SET NULL
);

-- Create indexes for performance
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
CREATE INDEX idx_feedback_type ON feedback(type);
CREATE INDEX idx_feedback_severity ON feedback(severity);
CREATE INDEX idx_feedback_status ON feedback(status);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);
CREATE INDEX idx_feedback_pattern_id ON feedback(pattern_id);
CREATE INDEX idx_feedback_url ON feedback(url);

-- Create feedback impact tracking table
CREATE TABLE IF NOT EXISTS feedback_impact (
    feedback_id VARCHAR REFERENCES feedback(id) ON DELETE CASCADE,
    user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
    impact_score INTEGER CHECK (impact_score >= 1 AND impact_score <= 10),
    churn_risk BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (feedback_id, user_id)
);

-- Create index for impact analysis
CREATE INDEX idx_feedback_impact_user ON feedback_impact(user_id);
CREATE INDEX idx_feedback_impact_score ON feedback_impact(impact_score);

-- Comments for documentation
COMMENT ON TABLE feedback IS 'Stores user feedback submissions with context and tracking';
COMMENT ON TABLE feedback_patterns IS 'Detected patterns in feedback for trend analysis';
COMMENT ON TABLE feedback_impact IS 'Tracks the impact of feedback on users and churn risk';

COMMENT ON COLUMN feedback.type IS 'Type of feedback: bug, feature, performance, ux, other';
COMMENT ON COLUMN feedback.severity IS 'Severity level: critical, high, medium, low';
COMMENT ON COLUMN feedback.status IS 'Current status: new, investigating, in_progress, resolved, closed';
COMMENT ON COLUMN feedback.previous_pages IS 'JSON array of previously visited pages';
COMMENT ON COLUMN feedback.last_actions IS 'JSON array of user actions before feedback';
COMMENT ON COLUMN feedback.error_logs IS 'JSON array of JavaScript errors captured';
COMMENT ON COLUMN feedback_impact.impact_score IS 'Score from 1-10 indicating impact on user experience';