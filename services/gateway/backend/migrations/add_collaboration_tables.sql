-- Real-time Collaboration Tables Migration
-- Adds tables for teams, workspaces, and collaborative features

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_teams_owner (owner_id),
    INDEX idx_teams_name (name)
);

-- Team members
CREATE TABLE IF NOT EXISTS team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member', -- owner, admin, member, viewer
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    invited_by UUID REFERENCES users(id),
    
    UNIQUE KEY unique_team_member (team_id, user_id),
    INDEX idx_team_members_user (user_id),
    INDEX idx_team_members_team (team_id, role)
);

-- Team invitations
CREATE TABLE IF NOT EXISTS team_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    token VARCHAR(255) UNIQUE NOT NULL,
    invited_by UUID NOT NULL REFERENCES users(id),
    accepted BOOLEAN DEFAULT FALSE,
    accepted_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_invitations_token (token),
    INDEX idx_invitations_email (email),
    INDEX idx_invitations_expiry (expires_at, accepted)
);

-- Workspaces within teams
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_workspaces_team (team_id, is_active),
    INDEX idx_workspaces_name (name)
);

-- Shared resources in workspaces
CREATE TABLE IF NOT EXISTS shared_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- portfolio, strategy, watchlist, etc.
    resource_id VARCHAR(255) NOT NULL,
    shared_by UUID NOT NULL REFERENCES users(id),
    permissions JSONB NOT NULL DEFAULT '["view"]', -- view, comment, edit, delete
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_workspace_resource (workspace_id, resource_type, resource_id),
    INDEX idx_shared_resources_workspace (workspace_id),
    INDEX idx_shared_resources_type (resource_type, resource_id)
);

-- Collaboration sessions (for real-time tracking)
CREATE TABLE IF NOT EXISTS collaboration_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_info JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    INDEX idx_sessions_workspace (workspace_id, ended_at),
    INDEX idx_sessions_user (user_id, ended_at),
    INDEX idx_sessions_activity (last_activity)
);

-- Collaboration changes log
CREATE TABLE IF NOT EXISTS collaboration_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    change_type VARCHAR(50) NOT NULL, -- create, update, delete, comment, etc.
    change_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_changes_workspace (workspace_id, created_at DESC),
    INDEX idx_changes_resource (resource_type, resource_id, created_at DESC),
    INDEX idx_changes_user (user_id, created_at DESC)
);

-- Comments on shared resources
CREATE TABLE IF NOT EXISTS resource_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    comment_text TEXT NOT NULL,
    parent_id UUID REFERENCES resource_comments(id) ON DELETE CASCADE,
    edited BOOLEAN DEFAULT FALSE,
    edited_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_comments_workspace (workspace_id),
    INDEX idx_comments_resource (resource_type, resource_id, created_at DESC),
    INDEX idx_comments_parent (parent_id)
);

-- Workspace activity feed
CREATE TABLE IF NOT EXISTS workspace_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_activities_workspace (workspace_id, created_at DESC),
    INDEX idx_activities_user (user_id, created_at DESC)
);

-- Collaborative annotations
CREATE TABLE IF NOT EXISTS resource_annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    annotation_type VARCHAR(50) NOT NULL, -- highlight, note, drawing, etc.
    annotation_data JSONB NOT NULL,
    position JSONB, -- coordinates or location data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_annotations_resource (resource_type, resource_id),
    INDEX idx_annotations_workspace (workspace_id)
);

-- Collaborative portfolios
CREATE TABLE IF NOT EXISTS collaborative_portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_collab_portfolios_workspace (workspace_id)
);

-- Collaborative strategies
CREATE TABLE IF NOT EXISTS collaborative_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rules JSONB NOT NULL DEFAULT '{}',
    backtest_results JSONB,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_collab_strategies_workspace (workspace_id)
);

-- Screen sharing sessions
CREATE TABLE IF NOT EXISTS screen_sharing_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stream_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    recording_url TEXT,
    
    INDEX idx_screen_sharing_workspace (workspace_id, ended_at),
    INDEX idx_screen_sharing_user (user_id, ended_at)
);

-- Add collaboration-related columns to existing tables
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS collaboration_preferences JSONB DEFAULT '{}';

ALTER TABLE trades
    ADD COLUMN IF NOT EXISTS shared_in_workspaces JSONB DEFAULT '[]';

ALTER TABLE strategies
    ADD COLUMN IF NOT EXISTS is_collaborative BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);

-- Functions for collaboration features

-- Function to log workspace activity
CREATE OR REPLACE FUNCTION log_workspace_activity(
    p_workspace_id UUID,
    p_user_id UUID,
    p_activity_type VARCHAR,
    p_activity_data JSONB
)
RETURNS UUID AS $$
DECLARE
    v_activity_id UUID;
BEGIN
    INSERT INTO workspace_activities (
        workspace_id, user_id, activity_type, activity_data
    ) VALUES (
        p_workspace_id, p_user_id, p_activity_type, p_activity_data
    ) RETURNING id INTO v_activity_id;
    
    -- Clean up old activities (keep last 1000 per workspace)
    DELETE FROM workspace_activities
    WHERE workspace_id = p_workspace_id
    AND id NOT IN (
        SELECT id FROM workspace_activities
        WHERE workspace_id = p_workspace_id
        ORDER BY created_at DESC
        LIMIT 1000
    );
    
    RETURN v_activity_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get workspace members with online status
CREATE OR REPLACE FUNCTION get_workspace_members(p_workspace_id UUID)
RETURNS TABLE (
    user_id UUID,
    username VARCHAR,
    avatar_url VARCHAR,
    role VARCHAR,
    is_online BOOLEAN,
    last_activity TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as user_id,
        u.username,
        u.avatar_url,
        tm.role,
        CASE 
            WHEN cs.last_activity > NOW() - INTERVAL '5 minutes' 
            AND cs.ended_at IS NULL 
            THEN TRUE 
            ELSE FALSE 
        END as is_online,
        cs.last_activity
    FROM workspaces w
    JOIN team_members tm ON w.team_id = tm.team_id
    JOIN users u ON tm.user_id = u.id
    LEFT JOIN collaboration_sessions cs ON 
        cs.user_id = u.id 
        AND cs.workspace_id = w.id
        AND cs.ended_at IS NULL
    WHERE w.id = p_workspace_id
    ORDER BY is_online DESC, u.username;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update collaboration session activity
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE collaboration_sessions
    SET last_activity = NOW()
    WHERE workspace_id = NEW.workspace_id
    AND user_id = NEW.user_id
    AND ended_at IS NULL;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_activity
AFTER INSERT ON collaboration_changes
FOR EACH ROW
EXECUTE FUNCTION update_session_activity();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_collaboration_composite 
ON shared_resources(workspace_id, resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_changes_composite 
ON collaboration_changes(workspace_id, resource_type, resource_id, created_at DESC);
