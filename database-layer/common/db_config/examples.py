"""
Example usage of the PostgreSQL configuration module.

This module demonstrates how to use the PostgreSQL configuration module
with asyncpg and other database clients.
"""

import asyncio
import asyncpg
import logging
from typing import Dict, List, Optional, Any

from .postgres_config import postgres_config, PostgresSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_direct_connection():
    """Example of using a direct connection with the config."""
    # Get connection parameters
    conn_params = postgres_config.get_connection_params()
    
    logger.info(f"Connecting to PostgreSQL with parameters: {conn_params}")
    
    # Create a connection
    conn = await asyncpg.connect(
        host=conn_params["host"],
        port=conn_params["port"],
        user=conn_params["user"],
        password=conn_params["password"],
        database=conn_params["database"],
    )
    
    try:
        # Execute a simple query
        version = await conn.fetchval("SELECT version()")
        logger.info(f"Connected to PostgreSQL: {version}")
        
        # Example query
        result = await conn.fetch("SELECT 1 as id, 'example' as name")
        logger.info(f"Query result: {result}")
    finally:
        # Close the connection
        await conn.close()
        logger.info("Connection closed")


async def example_connection_pool():
    """Example of using a connection pool with the config."""
    # Get a connection string
    conn_string = postgres_config.get_connection_string()
    
    logger.info(f"Creating pool with connection string: {conn_string}")
    
    # Create a connection pool
    pool = await asyncpg.create_pool(
        dsn=conn_string,
        min_size=3,
        max_size=10
    )
    
    try:
        # Use the pool for queries
        async with pool.acquire() as conn:
            result = await conn.fetch("SELECT 1 as id, 'example' as name")
            logger.info(f"Query result from pool: {result}")
    finally:
        # Close the pool
        await pool.close()
        logger.info("Connection pool closed")


async def example_service_specific_config():
    """Example of using service-specific configuration."""
    # Get service-specific connection string
    marketing_conn_string = postgres_config.get_connection_string("marketing")
    crm_conn_string = postgres_config.get_connection_string("crm")
    
    logger.info(f"Marketing service connection string: {marketing_conn_string}")
    logger.info(f"CRM service connection string: {crm_conn_string}")
    
    # Direct access to settings
    marketing_settings = postgres_config.get_settings("marketing")
    logger.info(f"Marketing host: {marketing_settings.PG_HOST}")
    logger.info(f"Marketing port: {marketing_settings.PG_PORT}")


async def example_custom_settings():
    """Example of creating and using custom settings."""
    # Create custom settings
    custom_settings = PostgresSettings(
        PG_HOST="custom-postgres-host",
        PG_PORT=5433,
        PG_DATABASE="custom_db",
        PG_USER="app_user",
        PG_PASSWORD="app_password",
        PG_SSL_MODE="require"
    )
    
    # Manually create a connection string from custom settings
    conn_string = (
        f"postgresql://{custom_settings.PG_USER}:{custom_settings.PG_PASSWORD}"
        f"@{custom_settings.PG_HOST}:{custom_settings.PG_PORT}/{custom_settings.PG_DATABASE}"
        f"?sslmode={custom_settings.PG_SSL_MODE}"
    )
    
    logger.info(f"Custom connection string: {conn_string}")


async def main():
    """Run the examples."""
    logger.info("Starting PostgreSQL configuration examples")
    
    try:
        # Example of service-specific configuration
        await example_service_specific_config()
        
        # Example of custom settings
        await example_custom_settings()
        
        # Uncomment to test actual database connections (requires database access)
        # await example_direct_connection()
        # await example_connection_pool()
    except Exception as e:
        logger.error(f"Error in examples: {str(e)}")
    
    logger.info("Examples completed")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 