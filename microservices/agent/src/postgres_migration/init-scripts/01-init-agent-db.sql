-- Initialize Agent service database for PostgreSQL
-- This script creates the agent_db database, users, and required schemas

-- Create agent service database
CREATE DATABASE agent_db;

-- Connect to the agent_db database
\c agent_db;

-- Create agent service roles
CREATE ROLE agent_admin WITH NOLOGIN;
CREATE ROLE agent_readonly WITH NOLOGIN;

-- Grant privileges to roles
GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;

-- Create application user
CREATE USER agent_service WITH PASSWORD 'password';
GRANT agent_admin TO agent_service;

-- Create public schema tables
CREATE TABLE IF NOT EXISTS public.contexts (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL,
    priority INT DEFAULT 5,
    request JSONB NOT NULL,
    template JSONB NOT NULL,
    results JSONB,
    tags JSONB,
    metadata JSONB,
    parent_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS public.batch_contexts (
    id VARCHAR(100) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    total_items INT DEFAULT 0,
    completed_items INT DEFAULT 0,
    failed_items INT DEFAULT 0,
    skipped_items INT DEFAULT 0,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS public.context_references (
    id SERIAL PRIMARY KEY,
    context_id VARCHAR(100) NOT NULL,
    ref_type VARCHAR(50) NOT NULL,
    ref_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT context_ref_unique UNIQUE (context_id, ref_type, ref_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_contexts_status ON public.contexts(status);
CREATE INDEX IF NOT EXISTS idx_contexts_created_at ON public.contexts(created_at);
CREATE INDEX IF NOT EXISTS idx_contexts_parent_id ON public.contexts(parent_id);
CREATE INDEX IF NOT EXISTS idx_batch_contexts_status ON public.batch_contexts(status);

-- Grant privileges on tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agent_admin;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO agent_admin;

-- Create a function to ensure that all new schemas get the same tables
CREATE OR REPLACE FUNCTION create_tenant_schema(schema_name TEXT) RETURNS VOID AS
$$
BEGIN
    -- Create schema if not exists
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);
    
    -- Create contexts table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.contexts (
            id VARCHAR(100) PRIMARY KEY,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP WITH TIME ZONE,
            status VARCHAR(50) NOT NULL,
            priority INT DEFAULT 5,
            request JSONB NOT NULL,
            template JSONB NOT NULL,
            results JSONB,
            tags JSONB,
            metadata JSONB,
            parent_id VARCHAR(100)
        )', schema_name);
    
    -- Create batch_contexts table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.batch_contexts (
            id VARCHAR(100) PRIMARY KEY,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            total_items INT DEFAULT 0,
            completed_items INT DEFAULT 0,
            failed_items INT DEFAULT 0,
            skipped_items INT DEFAULT 0,
            metadata JSONB
        )', schema_name);
    
    -- Create context_references table
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.context_references (
            id SERIAL PRIMARY KEY,
            context_id VARCHAR(100) NOT NULL,
            ref_type VARCHAR(50) NOT NULL,
            ref_id VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB,
            CONSTRAINT context_ref_unique UNIQUE (context_id, ref_type, ref_id)
        )', schema_name);
    
    -- Create indexes
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_contexts_status ON %I.contexts(status)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_contexts_created_at ON %I.contexts(created_at)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_contexts_parent_id ON %I.contexts(parent_id)', schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_batch_contexts_status ON %I.batch_contexts(status)', schema_name);
    
    -- Grant privileges
    EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO agent_admin', schema_name);
    EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO agent_readonly', schema_name);
    EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO agent_admin', schema_name);
END;
$$ LANGUAGE plpgsql; 