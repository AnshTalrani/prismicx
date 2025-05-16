"""
Tenant Database Adapter Module

This module provides adapters for connecting to tenant-specific databases.
It ensures proper isolation between tenant data.
"""

import logging
import os
from typing import Optional, Dict, Any, List, AsyncGenerator, Callable
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from .tenant_context import TenantContext
from .tenant_service import TenantService, get_tenant_service

logger = logging.getLogger(__name__)


class TenantDatabaseAdapter:
    """
    Adapter for tenant-specific database connections.
    
    This class manages database connections for different tenants,
    ensuring proper isolation of tenant data.
    """
    
    def __init__(
        self,
        default_db_url: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        tenant_service: Optional[TenantService] = None
    ):
        """
        Initialize the tenant database adapter.
        
        Args:
            default_db_url: Default database URL for system-wide operations.
            pool_size: Connection pool size for each tenant.
            max_overflow: Maximum overflow connections for each tenant.
            tenant_service: Service for retrieving tenant information.
        """
        self.default_db_url = default_db_url or os.environ.get(
            "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/app"
        )
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.tenant_service = tenant_service or get_tenant_service()
        
        # Cache of database engines by tenant ID
        self._engines: Dict[str, AsyncEngine] = {}
        # Cache of session factories by tenant ID
        self._session_factories: Dict[str, Callable[[], AsyncSession]] = {}
    
    async def get_engine(self, tenant_id: Optional[str] = None) -> AsyncEngine:
        """
        Get a database engine for a specific tenant.
        
        Args:
            tenant_id: The tenant ID to get an engine for. If None, uses current tenant context.
            
        Returns:
            A SQLAlchemy async engine for the tenant.
        """
        # If no tenant ID provided, try to get from context
        if tenant_id is None:
            tenant_id = TenantContext.get_current_tenant()
            
        # If no tenant ID available, return default engine
        if not tenant_id:
            return await self._get_default_engine()
            
        # Check if engine already exists in cache
        if tenant_id in self._engines:
            return self._engines[tenant_id]
            
        # Get tenant information
        tenant_info = await self.tenant_service.get_tenant_info(tenant_id)
        if not tenant_info:
            logger.warning(f"Tenant not found: {tenant_id}, using default engine")
            return await self._get_default_engine()
            
        # Create and cache engine
        db_url = tenant_info.get("database_url", self.default_db_url)
        engine = create_async_engine(
            db_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,
            pool_recycle=300,  # Recycle connections after 5 minutes
            echo=False
        )
        self._engines[tenant_id] = engine
        
        return engine
    
    async def _get_default_engine(self) -> AsyncEngine:
        """
        Get the default database engine for system-wide operations.
        
        Returns:
            The default SQLAlchemy async engine.
        """
        if "default" not in self._engines:
            self._engines["default"] = create_async_engine(
                self.default_db_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle connections after 5 minutes
                echo=False
            )
        return self._engines["default"]
    
    async def get_session_factory(
        self, tenant_id: Optional[str] = None
    ) -> Callable[[], AsyncSession]:
        """
        Get a session factory for a specific tenant.
        
        Args:
            tenant_id: The tenant ID to get a session factory for.
            
        Returns:
            A function that creates new database sessions.
        """
        # If no tenant ID provided, try to get from context
        if tenant_id is None:
            tenant_id = TenantContext.get_current_tenant()
            
        # If no tenant ID available, use default
        cache_key = tenant_id or "default"
        
        # Check if session factory already exists in cache
        if cache_key in self._session_factories:
            return self._session_factories[cache_key]
            
        # Get engine for tenant
        engine = await self.get_engine(tenant_id)
        
        # Create and cache session factory
        session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        self._session_factories[cache_key] = session_factory
        
        return session_factory
    
    @asynccontextmanager
    async def session(
        self, tenant_id: Optional[str] = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session for a specific tenant.
        
        Args:
            tenant_id: The tenant ID to get a session for.
            
        Yields:
            An async database session for the tenant.
        """
        # Get current tenant ID if not provided
        if tenant_id is None:
            tenant_id = TenantContext.get_current_tenant()
            
        # Get session factory
        session_factory = await self.get_session_factory(tenant_id)
        
        # Create session
        async with session_factory() as session:
            # If tenant uses schema isolation, set search path
            if tenant_id:
                tenant_info = await self.tenant_service.get_tenant_info(tenant_id)
                if tenant_info and tenant_info.get("schema_name"):
                    schema_name = tenant_info["schema_name"]
                    await session.execute(text(f'SET search_path TO "{schema_name}"'))
                    
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
                
    @asynccontextmanager
    async def system_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session for system-wide operations.
        
        This session always uses the public schema regardless of tenant context.
        
        Yields:
            An async database session for system-wide operations.
        """
        # Get default session factory
        session_factory = await self.get_session_factory("default")
        
        # Create session
        async with session_factory() as session:
            # Always use public schema for system operations
            await session.execute(text('SET search_path TO "public"'))
                
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


# Global database adapter instance
_db_adapter: Optional[TenantDatabaseAdapter] = None


def get_database_adapter() -> TenantDatabaseAdapter:
    """
    Get the global tenant database adapter instance.
    
    Returns:
        The tenant database adapter instance.
    """
    global _db_adapter
    if _db_adapter is None:
        _db_adapter = TenantDatabaseAdapter()
    return _db_adapter


@asynccontextmanager
async def get_db_session(
    tenant_id: Optional[str] = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session for the current tenant.
    
    This is a convenience wrapper around TenantDatabaseAdapter.session().
    
    Args:
        tenant_id: Optional tenant ID to override the current tenant context.
        
    Yields:
        An async database session for the tenant.
    """
    adapter = get_database_adapter()
    async with adapter.session(tenant_id) as session:
        yield session


@asynccontextmanager
async def get_system_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session for system-wide operations.
    
    This is a convenience wrapper around TenantDatabaseAdapter.system_session().
    
    Yields:
        An async database session for system-wide operations.
    """
    adapter = get_database_adapter()
    async with adapter.system_session() as session:
        yield session 