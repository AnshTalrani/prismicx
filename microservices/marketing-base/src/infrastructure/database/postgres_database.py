"""
PostgreSQL database access module with multi-tenant support.

This module provides a PostgreSQL database access layer that supports
the schema-based multi-tenant architecture described in the microservice documentation.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool

from ...config.app_config import get_config
from ..tenant.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class PostgresDatabase:
    """PostgreSQL database access class with tenant awareness."""
    
    def __init__(self, 
                 connection_string: Optional[str] = None, 
                 database_name: Optional[str] = None,
                 tenant_aware: bool = True,
                 read_only: bool = False):
        """
        Initialize the database connection.
        
        Args:
            connection_string: PostgreSQL connection string. If None, uses configuration.
            database_name: PostgreSQL database name. If None, uses configuration.
            tenant_aware: Whether this database uses tenant schemas.
            read_only: Whether this connection should be read-only.
        """
        config = get_config()
        self.connection_string = connection_string or config.postgres_uri
        self.database_name = database_name or config.postgres_database
        self.tenant_aware = tenant_aware
        self.read_only = read_only
        self.pool: Optional[Pool] = None
        
    async def initialize(self):
        """Initialize the connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.connection_string,
                min_size=5,
                max_size=20
            )
            logger.info(f"Connected to PostgreSQL database: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    async def close(self):
        """Close all connections in the pool."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def connection(self):
        """
        Get a connection from the pool with tenant context.
        
        This context manager gets a connection from the pool and sets the
        appropriate schema based on the current tenant context.
        
        Yields:
            A PostgreSQL connection.
        """
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            # Set the read-only mode if specified
            if self.read_only:
                await conn.execute("SET default_transaction_read_only = on")
            
            # Set the tenant schema if tenant_aware is enabled
            if self.tenant_aware:
                tenant_id = TenantContext.get_current_tenant()
                if not tenant_id:
                    logger.error("No tenant specified in tenant-aware database operation")
                    raise ValueError("No tenant specified for tenant-aware database operation")
                
                # Set the search_path to the tenant's schema
                await conn.execute(f"SET search_path TO {tenant_id}")
                await conn.execute(f"SET app.current_tenant = '{tenant_id}'")
                
            yield conn
            
            # Reset read-only mode when we're done
            if self.read_only:
                await conn.execute("SET default_transaction_read_only = off")
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            
        Returns:
            List of rows as dictionaries.
        """
        async with self.connection() as conn:
            try:
                stmt = await conn.prepare(query)
                result = await stmt.fetch(*args)
                return [dict(row) for row in result]
            except Exception as e:
                logger.error(f"Database error in execute_query: {str(e)}, Query: {query}")
                raise
    
    async def execute(self, query: str, *args) -> str:
        """
        Execute a query and return the affected row count.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            
        Returns:
            Command tag string.
        """
        if self.read_only and not query.strip().upper().startswith(("SELECT", "WITH", "SHOW", "EXPLAIN")):
            logger.error("Attempted to execute a write operation on a read-only connection")
            raise PermissionError("This database connection is read-only")
            
        async with self.connection() as conn:
            try:
                return await conn.execute(query, *args)
            except Exception as e:
                logger.error(f"Database error in execute: {str(e)}, Query: {query}")
                raise
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return the first result row.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            
        Returns:
            Row as dictionary if found, None otherwise.
        """
        async with self.connection() as conn:
            try:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Database error in fetch_one: {str(e)}, Query: {query}")
                raise
    
    async def begin_transaction(self):
        """
        Begin a transaction.
        
        Returns:
            Transaction object.
        """
        if not self.pool:
            await self.initialize()
            
        conn = await self.pool.acquire()
        
        # Set read-only mode if specified
        if self.read_only:
            await conn.execute("SET default_transaction_read_only = on")
        
        # Set tenant schema if applicable
        if self.tenant_aware:
            tenant_id = TenantContext.get_current_tenant()
            if tenant_id:
                await conn.execute(f"SET search_path TO {tenant_id}")
                await conn.execute(f"SET app.current_tenant = '{tenant_id}'")
        
        tx = conn.transaction()
        await tx.start()
        
        # Return the transaction and connection for later use
        return tx, conn
    
    async def commit_transaction(self, tx, conn):
        """
        Commit a transaction.
        
        Args:
            tx: Transaction object.
            conn: Connection object.
        """
        try:
            await tx.commit()
        except Exception as e:
            logger.error(f"Error committing transaction: {str(e)}")
            raise
        finally:
            # Reset read-only mode
            if self.read_only:
                await conn.execute("SET default_transaction_read_only = off")
            await self.pool.release(conn)
    
    async def rollback_transaction(self, tx, conn):
        """
        Rollback a transaction.
        
        Args:
            tx: Transaction object.
            conn: Connection object.
        """
        try:
            await tx.rollback()
        except Exception as e:
            logger.error(f"Error rolling back transaction: {str(e)}")
        finally:
            # Reset read-only mode
            if self.read_only:
                await conn.execute("SET default_transaction_read_only = off")
            await self.pool.release(conn) 