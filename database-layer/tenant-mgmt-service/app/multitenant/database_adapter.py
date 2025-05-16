"""
Database adapter module for handling tenant-specific database connections.
"""
import logging
from typing import Optional, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from .tenant_context import TenantContext

logger = logging.getLogger(__name__)

# A shared Base class for declarative models
Base = declarative_base()


class TenantDatabaseAdapter:
    """
    Adapter for handling tenant-specific database connections.
    
    This class provides methods to create database engines and sessions
    that are tenant-aware, automatically setting the correct schema for
    the current tenant.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize the database adapter.
        
        Args:
            database_url (str): Database URL to connect to
        """
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_tenant_session(self) -> AsyncSession:
        """
        Get a database session for the current tenant.
        
        This method creates a new database session and sets the PostgreSQL search_path
        to the current tenant's schema if a tenant is in context.
        
        Yields:
            AsyncSession: A database session for the current tenant
        """
        async with self.async_session() as session:
            # Get current tenant from context
            tenant_info = TenantContext.get_current_tenant()
            
            if tenant_info and tenant_info.schema_name:
                # Set search_path to tenant schema for this session
                schema_name = tenant_info.schema_name
                try:
                    await session.execute(text(f'SET search_path TO "{schema_name}"'))
                    logger.debug(f"Set search_path to {schema_name}")
                except Exception as e:
                    logger.error(f"Error setting search_path to {schema_name}: {str(e)}")
            
            try:
                yield session
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_system_session(self) -> AsyncSession:
        """
        Get a database session for system-wide operations.
        
        This method creates a new database session with search_path set to 'public'
        for system-wide operations (tenant management, etc.)
        
        Yields:
            AsyncSession: A database session for system-wide operations
        """
        async with self.async_session() as session:
            try:
                # Set search_path to public for system-wide operations
                await session.execute(text('SET search_path TO "public"'))
                yield session
            finally:
                await session.close()
    

# Global database adapter instance
_db_adapter: Optional[TenantDatabaseAdapter] = None


def get_database_adapter(database_url: Optional[str] = None) -> TenantDatabaseAdapter:
    """
    Get the global database adapter instance.
    
    Args:
        database_url (Optional[str]): Database URL to use if adapter not initialized
        
    Returns:
        TenantDatabaseAdapter: The global database adapter
    """
    global _db_adapter
    
    if _db_adapter is None:
        if database_url is None:
            from ..config import get_database_url
            database_url = get_database_url()
        
        _db_adapter = TenantDatabaseAdapter(database_url)
    
    return _db_adapter


@asynccontextmanager
async def get_tenant_db_session() -> AsyncSession:
    """
    Get a database session for the current tenant.
    
    Wrapper around TenantDatabaseAdapter.get_tenant_session() for dependency injection.
    
    Yields:
        AsyncSession: A database session for the current tenant
    """
    adapter = get_database_adapter()
    async with adapter.get_tenant_session() as session:
        yield session


@asynccontextmanager
async def get_system_db_session() -> AsyncSession:
    """
    Get a database session for system-wide operations.
    
    Wrapper around TenantDatabaseAdapter.get_system_session() for dependency injection.
    
    Yields:
        AsyncSession: A database session for system-wide operations
    """
    adapter = get_database_adapter()
    async with adapter.get_system_session() as session:
        yield session 