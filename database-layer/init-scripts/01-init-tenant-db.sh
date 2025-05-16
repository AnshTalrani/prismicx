#!/bin/bash
set -e

# Function to create a new database and user
create_tenant_db() {
    local db_name=$1
    local user_name="${db_name}_user"
    local password="${db_name}_password"  # Should be changed in production

    # Create user
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE USER $user_name WITH PASSWORD '$password';
EOSQL

    # Create database
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        CREATE DATABASE $db_name;
        GRANT ALL PRIVILEGES ON DATABASE $db_name TO $user_name;
EOSQL

    # Connect to the new database and create schema
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db_name" <<-EOSQL
        -- Create extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";

        -- Create schemas
        CREATE SCHEMA IF NOT EXISTS tenant;
        GRANT ALL ON SCHEMA tenant TO $user_name;

        -- Set search path
        ALTER DATABASE $db_name SET search_path TO tenant,public;

        -- Create basic tables
        CREATE TABLE IF NOT EXISTS tenant.settings (
            id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
            key VARCHAR(255) NOT NULL,
            value JSONB NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE UNIQUE INDEX ON tenant.settings (key);

        -- Grant privileges
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tenant TO $user_name;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA tenant TO $user_name;
EOSQL
}

# Create databases for each tenant
if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Creating multiple databases: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        echo "Creating database: $db"
        create_tenant_db $db
    done
    echo "Multiple databases created"
fi 