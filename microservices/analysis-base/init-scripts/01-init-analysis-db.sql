/*
 * Analysis Database Initialization Script
 *
 * This script initializes the analysis database with the necessary schemas,
 * tables, roles, and permissions for the tenant-aware analysis microservice.
 */

-- Create database if it doesn't exist
-- Note: This must be run as superuser
-- CREATE DATABASE analysis_db;

-- Connect to the database
-- \c analysis_db;

-- Create roles for the service
CREATE ROLE analysis_admin WITH LOGIN PASSWORD 'admin_password';
CREATE ROLE analysis_service WITH LOGIN PASSWORD 'password';
CREATE ROLE analysis_readonly WITH LOGIN PASSWORD 'readonly_password';

-- Grant appropriate permissions
ALTER ROLE analysis_admin WITH SUPERUSER;
GRANT analysis_readonly TO analysis_service;

-- Create public schema objects for system-wide data
CREATE TABLE IF NOT EXISTS public.tenants (
    tenant_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.analysis_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create template table for tenant schemas
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id VARCHAR) RETURNS VOID AS $$
BEGIN
    -- Create schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', tenant_id);
    
    -- Create tables in the schema
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.analysis_results (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            results JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )', tenant_id);
    
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I.analysis_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )', tenant_id);
    
    -- Grant permissions on the schema
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO analysis_service', tenant_id);
    EXECUTE format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO analysis_admin', tenant_id);
    EXECUTE format('GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA %I TO analysis_service', tenant_id);
    EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO analysis_readonly', tenant_id);
    
    -- Grant permissions on sequences
    EXECUTE format('GRANT USAGE ON ALL SEQUENCES IN SCHEMA %I TO analysis_service', tenant_id);
END;
$$ LANGUAGE plpgsql;

-- Create test tenant schemas
SELECT create_tenant_schema('tenant_test001');
SELECT create_tenant_schema('tenant_test002');

-- Insert test data for the tenants
INSERT INTO public.tenants (tenant_id, name, status)
VALUES 
    ('tenant_test001', 'Test Tenant 1', 'active'),
    ('tenant_test002', 'Test Tenant 2', 'active');

-- Set ownership and permissions
ALTER TABLE public.tenants OWNER TO analysis_admin;
GRANT SELECT ON public.tenants TO analysis_service;
GRANT SELECT ON public.tenants TO analysis_readonly;

ALTER TABLE public.analysis_categories OWNER TO analysis_admin;
GRANT SELECT, INSERT, UPDATE ON public.analysis_categories TO analysis_service;
GRANT SELECT ON public.analysis_categories TO analysis_readonly;

-- Grant permissions to create new schemas
GRANT CREATE ON DATABASE analysis_db TO analysis_admin;

-- Enable row-level security for multi-tenant tables if needed
-- ALTER TABLE public.shared_table ENABLE ROW LEVEL SECURITY; 