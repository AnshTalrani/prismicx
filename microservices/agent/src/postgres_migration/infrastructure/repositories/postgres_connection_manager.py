"""
PostgreSQL Connection Manager for multi-tenant databases.

Provides connection pooling and tenant-aware database connections.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
import asyncpg
from asyncpg.pool import Pool
from functools import wraps

from src.postgres_migration.config.postgres_config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USERNAME, DB_PASSWORD,
    DB_MIN_POOL_SIZE, DB_MAX_POOL_SIZE, DB_TENANT_AWARE,
    CREATE_TABLES_SQL, DEFAULT_SCHEMA
)
from src.postgres_migration.utils.tenant_context import get_tenant_schema

logger = logging.getLogger(__name__)

# Global connection pools
_default_pool: Optional[Pool] = None
_tenant_pools: Dict[str, Pool] = {}

async def initialize_pool(schema: Optional[str] = None) -> Pool:
    """
    Initialize a connection pool for a specific schema.
    
    Args:
        schema: Schema name or None for default schema
        
    Returns:
        Connection pool
    """
    dsn = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        # Create connection pool
        pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=DB_MIN_POOL_SIZE,
            max_size=DB_MAX_POOL_SIZE,
            command_timeout=10
        )
        
        if schema and schema != DEFAULT_SCHEMA:
            # Create schema if it doesn't exist
            async with pool.acquire() as conn:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                
                # Create tables in schema
                sql = CREATE_TABLES_SQL.format(schema=schema)
                await conn.execute(sql)
                
                logger.info(f"Initialized schema {schema} with required tables")
        
        return pool
    except Exception as e:
        logger.error(f"Failed to initialize connection pool: {str(e)}")
        raise

async def get_pool(schema: Optional[str] = None) -> Pool:
    """
    Get a connection pool for the specified schema.
    
    Args:
        schema: Schema name or None for default pool
        
    Returns:
        Connection pool
    """
    global _default_pool, _tenant_pools
    
    if not schema or schema == DEFAULT_SCHEMA:
        # Initialize default pool if needed
        if _default_pool is None:
            _default_pool = await initialize_pool()
        return _default_pool
    
    # Check if pool exists for this schema
    if schema not in _tenant_pools:
        # Initialize new pool for this schema
        _tenant_pools[schema] = await initialize_pool(schema)
    
    return _tenant_pools[schema]

async def close_pools() -> None:
    """Close all connection pools."""
    global _default_pool, _tenant_pools
    
    try:
        # Close default pool
        if _default_pool is not None:
            await _default_pool.close()
            _default_pool = None
        
        # Close tenant pools
        for schema, pool in _tenant_pools.items():
            await pool.close()
        _tenant_pools = {}
        
        logger.info("Closed all database connection pools")
    except Exception as e:
        logger.error(f"Error closing database connection pools: {str(e)}")

async def execute_tenant_aware(query: str, *args, schema: Optional[str] = None) -> Optional[str]:
    """
    Execute a query in a tenant-aware context.
    
    Args:
        query: SQL query to execute
        args: Query arguments
        schema: Explicit schema name or None to use current tenant context
        
    Returns:
        Query result status
    """
    if schema is None and DB_TENANT_AWARE:
        schema = get_tenant_schema()
    
    pool = await get_pool(schema)
    
    async with pool.acquire() as conn:
        if schema and schema != DEFAULT_SCHEMA:
            # Set search path to tenant schema
            await conn.execute(f"SET search_path TO {schema}")
        
        return await conn.execute(query, *args)

async def fetch_tenant_aware(query: str, *args, schema: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch rows from a query in a tenant-aware context.
    
    Args:
        query: SQL query to execute
        args: Query arguments
        schema: Explicit schema name or None to use current tenant context
        
    Returns:
        List of rows as dictionaries
    """
    if schema is None and DB_TENANT_AWARE:
        schema = get_tenant_schema()
    
    pool = await get_pool(schema)
    
    async with pool.acquire() as conn:
        if schema and schema != DEFAULT_SCHEMA:
            # Set search path to tenant schema
            await conn.execute(f"SET search_path TO {schema}")
        
        # Execute query and fetch results
        rows = await conn.fetch(query, *args)
        
        # Convert records to dictionaries
        return [dict(row) for row in rows]

async def fetch_one_tenant_aware(query: str, *args, schema: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a single row from a query in a tenant-aware context.
    
    Args:
        query: SQL query to execute
        args: Query arguments
        schema: Explicit schema name or None to use current tenant context
        
    Returns:
        Row as dictionary or None if not found
    """
    if schema is None and DB_TENANT_AWARE:
        schema = get_tenant_schema()
    
    pool = await get_pool(schema)
    
    async with pool.acquire() as conn:
        if schema and schema != DEFAULT_SCHEMA:
            # Set search path to tenant schema
            await conn.execute(f"SET search_path TO {schema}")
        
        # Execute query and fetch one result
        row = await conn.fetchrow(query, *args)
        
        # Convert record to dictionary if found
        return dict(row) if row else None 