"""
Database initializer for the Agent microservice.

Initializes the PostgreSQL database and required tables for the Agent microservice.
"""
import logging
import os
import asyncio
import asyncpg
from typing import Optional, List

from src.postgres_migration.config.postgres_config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USERNAME, DB_PASSWORD,
    CREATE_TABLES_SQL, DEFAULT_SCHEMA
)
from src.postgres_migration.infrastructure.clients.tenant_mgmt_client import list_tenants

logger = logging.getLogger(__name__)

async def initialize_database() -> bool:
    """
    Initialize the PostgreSQL database for the Agent microservice.
    
    Creates the database if it doesn't exist, initializes the schema,
    and creates required tables for the Agent microservice.
    
    Returns:
        Success status
    """
    logger.info("Initializing PostgreSQL database for Agent microservice")
    
    # Database connection string
    dsn = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        # Connect to PostgreSQL server to create database if it doesn't exist
        sys_conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            database="postgres"  # Connect to system database first
        )
        
        # Check if database exists
        db_exists = await sys_conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            DB_NAME
        )
        
        if not db_exists:
            # Create database
            await sys_conn.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(f"Created database {DB_NAME}")
        
        await sys_conn.close()
        
        # Connect to the agent database
        conn = await asyncpg.connect(dsn=dsn)
        
        # Create public schema tables
        logger.info("Creating tables in public schema")
        await conn.execute(CREATE_TABLES_SQL.format(schema=DEFAULT_SCHEMA))
        
        # Close connection
        await conn.close()
        
        # Initialize schemas for existing tenants
        await initialize_tenant_schemas()
        
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

async def initialize_tenant_schemas() -> bool:
    """
    Initialize schemas for existing tenants.
    
    Retrieves tenants from the Tenant Management Service and creates
    schemas for each tenant with the required tables.
    
    Returns:
        Success status
    """
    logger.info("Initializing schemas for existing tenants")
    
    try:
        # Get list of tenants from Tenant Management Service
        tenants = await list_tenants(limit=1000)
        if not tenants:
            logger.warning("No tenants found")
            return True
        
        logger.info(f"Retrieved {len(tenants)} tenants")
        
        # Database connection string
        dsn = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        conn = await asyncpg.connect(dsn=dsn)
        
        # Initialize schemas for each tenant
        for tenant in tenants:
            tenant_id = tenant.get("id")
            if not tenant_id:
                continue
                
            # Create schema name
            schema_name = f"tenant_{tenant_id}"
            
            # Create schema if it doesn't exist
            await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            
            # Create tables in schema
            sql = CREATE_TABLES_SQL.format(schema=schema_name)
            await conn.execute(sql)
            
            logger.info(f"Initialized schema {schema_name} for tenant {tenant_id}")
        
        # Close connection
        await conn.close()
        
        logger.info("Tenant schema initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing tenant schemas: {str(e)}")
        return False

async def initialize_tenant_schema(tenant_id: str) -> bool:
    """
    Initialize schema for a specific tenant.
    
    Creates a schema for the specified tenant with the required tables.
    
    Args:
        tenant_id: Tenant identifier
        
    Returns:
        Success status
    """
    logger.info(f"Initializing schema for tenant {tenant_id}")
    
    try:
        # Database connection string
        dsn = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        conn = await asyncpg.connect(dsn=dsn)
        
        # Create schema name
        schema_name = f"tenant_{tenant_id}"
        
        # Create schema if it doesn't exist
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        
        # Create tables in schema
        sql = CREATE_TABLES_SQL.format(schema=schema_name)
        await conn.execute(sql)
        
        # Close connection
        await conn.close()
        
        logger.info(f"Schema {schema_name} initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing schema for tenant {tenant_id}: {str(e)}")
        return False 