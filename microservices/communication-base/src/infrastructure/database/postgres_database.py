"""
PostgreSQL Database Module

This module provides a database adapter for PostgreSQL database operations.
It handles connection pooling and queries.
"""

import logging
import asyncpg
from typing import Dict, List, Any, Optional, Union
from contextlib import asynccontextmanager

import structlog

from ...config.settings import get_settings

logger = structlog.get_logger(__name__)


class PostgresDatabase:
    """
    PostgreSQL database adapter.
    
    This class manages PostgreSQL connections and provides methods for
    executing SQL queries.
    """
    
    def __init__(self):
        """Initialize the PostgreSQL database adapter."""
        self.pool = None
        self.settings = get_settings()
        self.connection_params = {
            "host": self.settings.postgres_host,
            "port": self.settings.postgres_port,
            "user": self.settings.postgres_user,
            "password": self.settings.postgres_password,
            "database": self.settings.postgres_db,
        }
        
        logger.info("PostgreSQL database adapter initialized")
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(**self.connection_params)
                logger.info("Database connection pool initialized")
            except Exception as e:
                logger.error(f"Error initializing database pool: {str(e)}")
                raise
    
    @asynccontextmanager
    async def connection(self):
        """
        Get a database connection from the pool.
        
        Yields:
            Database connection.
        """
        if self.pool is None:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            yield conn
    
    async def execute_query(
        self, query: str, params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return results as a list of dictionaries.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            
        Returns:
            Query results as a list of dictionaries.
        """
        async with self.connection() as conn:
            results = await conn.fetch(query, *(params or []))
            return [dict(row) for row in results]
    
    async def execute(
        self, query: str, params: Optional[List[Any]] = None
    ) -> str:
        """
        Execute a query and return execution status.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            
        Returns:
            Status message.
        """
        async with self.connection() as conn:
            await conn.execute(query, *(params or []))
            return "Query executed successfully"
    
    async def fetch_one(
        self, query: str, params: Optional[List[Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return a single result.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
            
        Returns:
            Single result as a dictionary or None.
        """
        async with self.connection() as conn:
            result = await conn.fetchrow(query, *(params or []))
            return dict(result) if result else None
    
    @asynccontextmanager
    async def begin_transaction(self):
        """
        Begin a database transaction.
        
        Yields:
            Database transaction.
        """
        async with self.connection() as conn:
            async with conn.transaction() as transaction:
                yield transaction
    
    async def commit_transaction(self, transaction) -> None:
        """
        Commit a database transaction.
        
        Args:
            transaction: Transaction to commit.
        """
        # Transaction is automatically committed when exiting the context manager
        pass
    
    async def rollback_transaction(self, transaction) -> None:
        """
        Rollback a database transaction.
        
        Args:
            transaction: Transaction to rollback.
        """
        # Transaction is automatically rolled back on exception when exiting the context manager
        pass 