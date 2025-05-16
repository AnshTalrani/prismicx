"""
Database connection module for the Plugin Repository Service.

This module provides database connection functionality for PostgreSQL
using SQLAlchemy, with connection pooling and async support.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Database client for PostgreSQL connections."""
    
    def __init__(
        self, 
        host: str, 
        port: int,
        user: str,
        password: str,
        database: str,
        min_pool_size: int = 5,
        max_pool_size: int = 20
    ):
        """
        Initialize the database client.
        
        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.engine = None
        self.async_session_factory = None
        
    async def initialize(self) -> None:
        """Initialize the database connection engine."""
        try:
            connection_url = (
                f"postgresql+asyncpg://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}"
            )
            
            self.engine = create_async_engine(
                connection_url,
                echo=False,  # Set to True for debugging SQL
                pool_size=self.min_pool_size,
                max_overflow=self.max_pool_size - self.min_pool_size,
                pool_timeout=30,  # 30 seconds
                pool_recycle=1800,  # 30 minutes
            )
            
            self.async_session_factory = sessionmaker(
                self.engine, expire_on_commit=False, class_=AsyncSession
            )
            
            logger.info(
                f"Initialized database connection to {self.host}:{self.port}/{self.database}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise
    
    @asynccontextmanager
    async def session(self):
        """
        Get a database session.
        
        Yields:
            AsyncSession: A SQLAlchemy async session
        """
        if not self.async_session_factory:
            await self.initialize()
            
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Database session error: {str(e)}")
                await session.rollback()
                raise
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        async with self.session() as session:
            result = await session.execute(query, params or {})
            return result
    
    async def close(self) -> None:
        """Close the database connection engine."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Closed database connection")
    
    async def health_check(self) -> bool:
        """
        Check database connection health.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            async with self.session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False 