"""
PostgreSQL database access module with batch processing support.

This module provides a PostgreSQL database access layer that supports
batch processing without requiring tenant schema switching.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool

from ...common.config import get_settings

logger = logging.getLogger(__name__)


class PostgresDatabase:
    """PostgreSQL database access class with batch awareness."""
    
    def __init__(self, 
                 connection_string: Optional[str] = None, 
                 database_name: Optional[str] = None,
                 read_only: bool = False):
        """
        Initialize the database connection.
        
        Args:
            connection_string: PostgreSQL connection string. If None, uses configuration.
            database_name: PostgreSQL database name. If None, uses configuration.
            read_only: Whether this connection should be read-only.
        """
        config = get_settings()
        self.connection_string = connection_string or config.postgres_uri
        self.database_name = database_name or config.postgres_database
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
    async def connection(self, batch_id: Optional[str] = None):
        """
        Get a connection from the pool with optional batch tagging.
        
        This context manager gets a connection from the pool and optionally
        sets application_name for monitoring purposes.
        
        Args:
            batch_id: Optional batch identifier for monitoring.
            
        Yields:
            A PostgreSQL connection.
        """
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            # Set the read-only mode if specified
            if self.read_only:
                await conn.execute("SET default_transaction_read_only = on")
            
            # Set batch identifier as application_name for monitoring
            if batch_id:
                await conn.execute(f"SET application_name = 'batch_{batch_id}'")
                
            yield conn
            
            # Reset read-only mode when we're done
            if self.read_only:
                await conn.execute("SET default_transaction_read_only = off")
    
    async def execute(self, query: str, *args, batch_id: Optional[str] = None):
        """
        Execute a query without returning a result.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            batch_id: Optional batch identifier for monitoring.
        """
        async with self.connection(batch_id) as conn:
            try:
                await conn.execute(query, *args)
            except Exception as e:
                logger.error(f"Database error in execute: {str(e)}, Query: {query}")
                raise
    
    async def fetch(self, query: str, *args, batch_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            batch_id: Optional batch identifier for monitoring.
            
        Returns:
            List of rows as dictionaries.
        """
        async with self.connection(batch_id) as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Database error in fetch: {str(e)}, Query: {query}")
                raise
    
    async def fetchval(self, query: str, *args, batch_id: Optional[str] = None) -> Any:
        """
        Execute a query and return a single value.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            batch_id: Optional batch identifier for monitoring.
            
        Returns:
            The first value of the first row.
        """
        async with self.connection(batch_id) as conn:
            try:
                return await conn.fetchval(query, *args)
            except Exception as e:
                logger.error(f"Database error in fetchval: {str(e)}, Query: {query}")
                raise
    
    async def fetch_one(self, query: str, *args, batch_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return the first result row.
        
        Args:
            query: SQL query string.
            args: Query parameters.
            batch_id: Optional batch identifier for monitoring.
            
        Returns:
            Row as dictionary if found, None otherwise.
        """
        async with self.connection(batch_id) as conn:
            try:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Database error in fetch_one: {str(e)}, Query: {query}")
                raise
    
    async def begin_transaction(self, batch_id: Optional[str] = None):
        """
        Begin a transaction.
        
        Args:
            batch_id: Optional batch identifier for monitoring.
            
        Returns:
            Transaction object.
        """
        if not self.pool:
            await self.initialize()
            
        conn = await self.pool.acquire()
        
        # Set read-only mode if specified
        if self.read_only:
            await conn.execute("SET default_transaction_read_only = on")
        
        # Set batch identifier as application_name for monitoring
        if batch_id:
            await conn.execute(f"SET application_name = 'batch_{batch_id}'")
        
        tx = conn.transaction()
        await tx.start()
        
        # Return the transaction and connection for later use
        return tx, conn 