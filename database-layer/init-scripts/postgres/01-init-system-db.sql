-- Create database for system-wide users
CREATE DATABASE system_users;

-- Connect to the system_users database
\c system_users

-- Create schema for user data
CREATE SCHEMA IF NOT EXISTS user_data;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user table with multi-tenant support
CREATE TABLE user_data.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Create indexes for efficient querying
CREATE UNIQUE INDEX users_email_tenant_idx ON user_data.users(email, tenant_id);
CREATE INDEX users_tenant_id_idx ON user_data.users(tenant_id);
CREATE INDEX users_status_idx ON user_data.users(status);

-- Create row-level security policy for tenant isolation
ALTER TABLE user_data.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy 
    ON user_data.users
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE));

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION user_data.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update the updated_at column
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON user_data.users
    FOR EACH ROW
    EXECUTE FUNCTION user_data.update_updated_at_column();

-- Create service-specific role for user data service
CREATE ROLE user_service WITH LOGIN PASSWORD 'password';
GRANT CONNECT ON DATABASE system_users TO user_service;
GRANT USAGE ON SCHEMA user_data TO user_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA user_data TO user_service;
ALTER ROLE user_service SET app.current_tenant_id TO '';

-- Create sample users for testing
INSERT INTO user_data.users (tenant_id, username, email, password_hash, first_name, last_name, role, status)
VALUES 
    ('tenant-001', 'user1', 'user1@example.com', 'hashed_password', 'John', 'Doe', 'admin', 'active'),
    ('tenant-001', 'user2', 'user2@example.com', 'hashed_password', 'Jane', 'Smith', 'user', 'active'),
    ('tenant-002', 'user3', 'user3@example.com', 'hashed_password', 'Alice', 'Johnson', 'admin', 'active');

-- Create schema for user preferences
CREATE SCHEMA IF NOT EXISTS user_preferences;

-- Create user preferences table
CREATE TABLE user_preferences.preferences (
    user_id UUID NOT NULL REFERENCES user_data.users(id) ON DELETE CASCADE,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, preference_key)
);

-- Create index for efficient querying
CREATE INDEX preferences_user_id_idx ON user_preferences.preferences(user_id);

-- Create trigger for updating the updated_at column
CREATE TRIGGER update_preferences_updated_at
    BEFORE UPDATE ON user_preferences.preferences
    FOR EACH ROW
    EXECUTE FUNCTION user_data.update_updated_at_column();

-- Grant permissions to user_service role
GRANT USAGE ON SCHEMA user_preferences TO user_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA user_preferences TO user_service; 