-- User Extensions PostgreSQL Initialization Script
-- This script creates tables for user extensions with multi-tenant support

-- Connect to the system_users database
\c system_users

-- Create schema for user extensions if it doesn't exist
CREATE SCHEMA IF NOT EXISTS user_extensions;

-- Create extension for UUID generation if not already created
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create base user extension table
CREATE TABLE user_extensions.extensions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_data.users(id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    extension_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for efficient querying
CREATE INDEX extensions_user_id_idx ON user_extensions.extensions(user_id);
CREATE INDEX extensions_tenant_id_idx ON user_extensions.extensions(tenant_id);
CREATE INDEX extensions_type_idx ON user_extensions.extensions(extension_type);
CREATE INDEX extensions_enabled_idx ON user_extensions.extensions(enabled);

-- Create a view for each tenant to isolate their data
CREATE OR REPLACE VIEW user_extensions.tenant_001_extensions AS
    SELECT * FROM user_extensions.extensions WHERE tenant_id = 'tenant-001';

CREATE OR REPLACE VIEW user_extensions.tenant_002_extensions AS
    SELECT * FROM user_extensions.extensions WHERE tenant_id = 'tenant-002';

CREATE OR REPLACE VIEW user_extensions.tenant_003_extensions AS
    SELECT * FROM user_extensions.extensions WHERE tenant_id = 'tenant-003';

-- Create row-level security policy for tenant isolation
ALTER TABLE user_extensions.extensions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy 
    ON user_extensions.extensions
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION user_extensions.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update the updated_at column
CREATE TRIGGER update_extensions_updated_at
    BEFORE UPDATE ON user_extensions.extensions
    FOR EACH ROW
    EXECUTE FUNCTION user_extensions.update_updated_at_column();

-- Create metrics table for extension usage tracking
CREATE TABLE user_extensions.extension_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extension_id UUID NOT NULL REFERENCES user_extensions.extensions(id) ON DELETE CASCADE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    feedback_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient querying
CREATE INDEX metrics_extension_id_idx ON user_extensions.extension_metrics(extension_id);

-- Create trigger to automatically update the updated_at column
CREATE TRIGGER update_metrics_updated_at
    BEFORE UPDATE ON user_extensions.extension_metrics
    FOR EACH ROW
    EXECUTE FUNCTION user_extensions.update_updated_at_column();

-- Create practicality factors table for extension evaluation
CREATE TABLE user_extensions.practicality_factors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extension_id UUID NOT NULL REFERENCES user_extensions.extensions(id) ON DELETE CASCADE,
    factor_name VARCHAR(100) NOT NULL,
    factor_value INTEGER NOT NULL CHECK (factor_value BETWEEN 1 AND 10),
    factor_weight FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(extension_id, factor_name)
);

-- Create index for efficient querying
CREATE INDEX factors_extension_id_idx ON user_extensions.practicality_factors(extension_id);

-- Create trigger to automatically update the updated_at column
CREATE TRIGGER update_factors_updated_at
    BEFORE UPDATE ON user_extensions.practicality_factors
    FOR EACH ROW
    EXECUTE FUNCTION user_extensions.update_updated_at_column();

-- Create service-specific role for user extension service
CREATE ROLE extension_service WITH LOGIN PASSWORD 'password';
GRANT CONNECT ON DATABASE system_users TO extension_service;
GRANT USAGE ON SCHEMA user_extensions TO extension_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA user_extensions TO extension_service;
ALTER ROLE extension_service SET app.current_tenant_id TO '';

-- Insert sample extension data
INSERT INTO user_extensions.extensions 
(user_id, tenant_id, extension_type, name, description, enabled, priority, metadata)
VALUES 
-- For tenant-001
((SELECT id FROM user_data.users WHERE email = 'user1@example.com'), 
  'tenant-001', 
  'productivity', 
  'Task Manager', 
  'Extension for managing tasks and priorities', 
  TRUE, 
  1, 
  '{"icon": "task_icon.png", "version": "1.0.0", "features": ["task creation", "task sorting", "reminders"]}'
),
((SELECT id FROM user_data.users WHERE email = 'user2@example.com'), 
  'tenant-001', 
  'communication', 
  'Team Chat', 
  'Extension for team communication', 
  TRUE, 
  2, 
  '{"icon": "chat_icon.png", "version": "1.2.0", "features": ["direct messaging", "channels", "file sharing"]}'
),
-- For tenant-002
((SELECT id FROM user_data.users WHERE email = 'user3@example.com'), 
  'tenant-002', 
  'analytics', 
  'Performance Dashboard', 
  'Extension for visualizing performance metrics', 
  TRUE, 
  1, 
  '{"icon": "dashboard_icon.png", "version": "2.1.0", "features": ["real-time data", "custom charts", "exports"]}'
);

-- Insert sample metrics data
INSERT INTO user_extensions.extension_metrics 
(extension_id, usage_count, last_used_at, feedback_score)
VALUES 
((SELECT id FROM user_extensions.extensions WHERE name = 'Task Manager'), 
  42, 
  CURRENT_TIMESTAMP - INTERVAL '2 days', 
  4.5
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Team Chat'), 
  87, 
  CURRENT_TIMESTAMP - INTERVAL '1 day', 
  4.8
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Performance Dashboard'), 
  15, 
  CURRENT_TIMESTAMP - INTERVAL '3 days', 
  3.9
);

-- Insert sample practicality factors
INSERT INTO user_extensions.practicality_factors 
(extension_id, factor_name, factor_value, factor_weight)
VALUES 
((SELECT id FROM user_extensions.extensions WHERE name = 'Task Manager'), 
  'Ease of Use', 
  8, 
  1.5
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Task Manager'), 
  'Feature Completeness', 
  7, 
  1.0
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Team Chat'), 
  'Ease of Use', 
  9, 
  1.5
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Team Chat'), 
  'Performance', 
  8, 
  1.2
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Performance Dashboard'), 
  'Data Accuracy', 
  9, 
  2.0
),
((SELECT id FROM user_extensions.extensions WHERE name = 'Performance Dashboard'), 
  'Visual Appeal', 
  7, 
  0.8
);

-- Create view for practicality score calculation
CREATE OR REPLACE VIEW user_extensions.extension_practicality AS
SELECT 
    e.id AS extension_id,
    e.name AS extension_name,
    e.tenant_id,
    SUM(pf.factor_value * pf.factor_weight) / SUM(pf.factor_weight) AS practicality_score,
    COUNT(pf.id) AS factor_count
FROM 
    user_extensions.extensions e
LEFT JOIN 
    user_extensions.practicality_factors pf ON e.id = pf.extension_id
GROUP BY 
    e.id, e.name, e.tenant_id; 