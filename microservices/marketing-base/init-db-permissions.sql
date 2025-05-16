-- Initialize database users and permissions for marketing service

-- USER DATABASE: Read-only access for marketing service
\c user_db

-- Create marketing-specific read-only role
CREATE ROLE marketing_user_read;

-- Grant read-only permissions on all tables in user_data schema
GRANT USAGE ON SCHEMA user_data TO marketing_user_read;
GRANT SELECT ON ALL TABLES IN SCHEMA user_data TO marketing_user_read;
ALTER DEFAULT PRIVILEGES IN SCHEMA user_data GRANT SELECT ON TABLES TO marketing_user_read;

-- Create the user with password and assign to the role
CREATE USER user_readonly WITH PASSWORD 'password';
GRANT marketing_user_read TO user_readonly;

-- CRM DATABASE: Read/Write access for marketing service
\c crm_db

-- Create marketing-specific read/write role
CREATE ROLE marketing_crm_readwrite;

-- Grant read/write permissions on all tables in all tenant schemas
GRANT USAGE ON SCHEMA public TO marketing_crm_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO marketing_crm_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_crm_readwrite;

-- Create function to grant permissions on all tenant schemas
CREATE OR REPLACE FUNCTION grant_marketing_permissions_to_tenant_schemas()
RETURNS void AS $$
DECLARE
    schema_rec RECORD;
BEGIN
    FOR schema_rec IN (SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%') LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO marketing_crm_readwrite', schema_rec.schema_name);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO marketing_crm_readwrite', schema_rec.schema_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_crm_readwrite', schema_rec.schema_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute the function
SELECT grant_marketing_permissions_to_tenant_schemas();

-- Create a trigger function to automatically grant permissions on new tenant schemas
CREATE OR REPLACE FUNCTION grant_marketing_permissions_on_new_tenant()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands() WHERE command_tag = 'CREATE SCHEMA' LOOP
        IF obj.object_identity LIKE 'tenant_%' THEN
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO marketing_crm_readwrite', obj.object_identity);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_crm_readwrite', obj.object_identity);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create an event trigger for new schemas
CREATE EVENT TRIGGER grant_marketing_permissions_trigger
ON ddl_command_end
WHEN TAG IN ('CREATE SCHEMA')
EXECUTE FUNCTION grant_marketing_permissions_on_new_tenant();

-- Create the user with password and assign to the role
CREATE USER crm_readwrite WITH PASSWORD 'password';
GRANT marketing_crm_readwrite TO crm_readwrite;

-- PRODUCT DATABASE: Read/Write access for marketing service
\c product_db

-- Create marketing-specific read/write role
CREATE ROLE marketing_product_readwrite;

-- Grant read/write permissions on all tables in all tenant schemas
GRANT USAGE ON SCHEMA public TO marketing_product_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO marketing_product_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_product_readwrite;

-- Create function to grant permissions on all tenant schemas
CREATE OR REPLACE FUNCTION grant_marketing_product_permissions_to_tenant_schemas()
RETURNS void AS $$
DECLARE
    schema_rec RECORD;
BEGIN
    FOR schema_rec IN (SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%') LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO marketing_product_readwrite', schema_rec.schema_name);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO marketing_product_readwrite', schema_rec.schema_name);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_product_readwrite', schema_rec.schema_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute the function
SELECT grant_marketing_product_permissions_to_tenant_schemas();

-- Create a trigger function to automatically grant permissions on new tenant schemas
CREATE OR REPLACE FUNCTION grant_marketing_product_permissions_on_new_tenant()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands() WHERE command_tag = 'CREATE SCHEMA' LOOP
        IF obj.object_identity LIKE 'tenant_%' THEN
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO marketing_product_readwrite', obj.object_identity);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marketing_product_readwrite', obj.object_identity);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create an event trigger for new schemas
CREATE EVENT TRIGGER grant_marketing_product_permissions_trigger
ON ddl_command_end
WHEN TAG IN ('CREATE SCHEMA')
EXECUTE FUNCTION grant_marketing_product_permissions_on_new_tenant();

-- Create the user with password and assign to the role
CREATE USER product_readwrite WITH PASSWORD 'password';
GRANT marketing_product_readwrite TO product_readwrite;

-- MARKETING DATABASE: Admin access for marketing service
\c marketing_db

-- Create admin role for marketing service
CREATE ROLE marketing_admin_role;

-- Grant all privileges on all tables
GRANT ALL PRIVILEGES ON DATABASE marketing_db TO marketing_admin_role;
GRANT ALL PRIVILEGES ON SCHEMA public TO marketing_admin_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO marketing_admin_role;
ALTER DEFAULT PRIVILEGES GRANT ALL PRIVILEGES ON TABLES TO marketing_admin_role;

-- Create admin user
CREATE USER marketing_admin WITH PASSWORD 'password';
GRANT marketing_admin_role TO marketing_admin; 