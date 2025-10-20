-- Catalyst State Database Schema
-- PostgreSQL initialization script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Task Execution State
-- ============================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    trace_id UUID NOT NULL,
    user_prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_phase VARCHAR(50),
    branch_name VARCHAR(255),
    commit_sha VARCHAR(40),
    preview_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    cost_total DECIMAL(10, 6) DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_trace ON tasks(trace_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);

-- ============================================
-- Projects
-- ============================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repo_url VARCHAR(512),
    repo_path VARCHAR(512),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_created ON projects(created_at DESC);

-- ============================================
-- Agent Events (Audit Trail)
-- ============================================

CREATE TABLE IF NOT EXISTS agent_events (
    id SERIAL PRIMARY KEY,
    trace_id UUID NOT NULL,
    task_id UUID,
    actor VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    routing_key VARCHAR(255),
    payload JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_trace ON agent_events(trace_id);
CREATE INDEX idx_events_task ON agent_events(task_id);
CREATE INDEX idx_events_actor ON agent_events(actor);
CREATE INDEX idx_events_type ON agent_events(event_type);
CREATE INDEX idx_events_created ON agent_events(created_at DESC);

-- ============================================
-- Preview Deployments
-- ============================================

CREATE TABLE IF NOT EXISTS preview_deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    deployment_mode VARCHAR(50) NOT NULL,
    preview_url VARCHAR(512),
    fallback_url VARCHAR(512),
    backend_url VARCHAR(512),
    container_ids TEXT[],
    network_id VARCHAR(128),
    status VARCHAR(50) DEFAULT 'deploying',
    health_status VARCHAR(50) DEFAULT 'unknown',
    deployed_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_health_check TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_preview_task ON preview_deployments(task_id);
CREATE INDEX idx_preview_status ON preview_deployments(status);
CREATE INDEX idx_preview_expires ON preview_deployments(expires_at);

-- ============================================
-- Explorer Scans
-- ============================================

CREATE TABLE IF NOT EXISTS explorer_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_type VARCHAR(50) NOT NULL, -- github, deployment, database
    target VARCHAR(512) NOT NULL,
    initiated_by UUID, -- User or task that triggered
    status VARCHAR(50) DEFAULT 'scanning',
    findings JSONB,
    tech_stack JSONB,
    security_score DECIMAL(5, 2),
    tech_debt_score DECIMAL(5, 2),
    can_replicate BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_scans_type ON explorer_scans(scan_type);
CREATE INDEX idx_scans_status ON explorer_scans(status);
CREATE INDEX idx_scans_created ON explorer_scans(created_at DESC);

-- ============================================
-- Cost Tracking (Enhanced)
-- ============================================

CREATE TABLE IF NOT EXISTS llm_usage (
    id SERIAL PRIMARY KEY,
    task_id UUID,
    agent_name VARCHAR(50),
    model VARCHAR(100),
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_total INTEGER,
    cost DECIMAL(10, 6),
    cache_hit BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_task ON llm_usage(task_id);
CREATE INDEX idx_usage_agent ON llm_usage(agent_name);
CREATE INDEX idx_usage_created ON llm_usage(created_at DESC);

-- ============================================
-- Functions & Triggers
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Initial Data
-- ============================================

-- Insert system user/project if needed
INSERT INTO projects (id, name, description, status)
VALUES (
    uuid_generate_v4(),
    'System',
    'System-generated project',
    'active'
) ON CONFLICT DO NOTHING;

-- ============================================
-- Cleanup Functions
-- ============================================

-- Function to cleanup expired previews
CREATE OR REPLACE FUNCTION cleanup_expired_previews()
RETURNS INTEGER AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    UPDATE preview_deployments
    SET status = 'expired'
    WHERE expires_at < NOW()
      AND status = 'healthy';
    
    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    RETURN cleaned_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get active task count
CREATE OR REPLACE FUNCTION get_active_task_count()
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'planning', 'architecting', 'coding', 'testing', 'reviewing', 'deploying'));
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Views for Monitoring
-- ============================================

CREATE OR REPLACE VIEW active_tasks AS
SELECT 
    t.id,
    t.project_id,
    t.trace_id,
    t.status,
    t.current_phase,
    t.created_at,
    EXTRACT(EPOCH FROM (NOW() - t.created_at)) as duration_seconds,
    t.cost_total
FROM tasks t
WHERE t.status IN ('pending', 'planning', 'architecting', 'coding', 'testing_and_reviewing', 'testing', 'reviewing', 'deploying')
ORDER BY t.created_at DESC;

CREATE OR REPLACE VIEW task_statistics AS
SELECT 
    status,
    COUNT(*) as count,
    AVG(cost_total) as avg_cost,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_duration_seconds
FROM tasks
WHERE completed_at IS NOT NULL
GROUP BY status;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO catalyst;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO catalyst;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Catalyst database initialized successfully!';
END $$;
