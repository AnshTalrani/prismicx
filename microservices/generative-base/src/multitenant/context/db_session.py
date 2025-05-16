"""
Database Session Module

This module provides database session management with tenant awareness.
It includes a session factory that applies tenant context to database sessions.
"""

import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from ..tenant.tenant_context import TenantContext
from ...common.config import get_settings

logger = logging.getLogger(__name__)

# Global engine variable
_engine: Optional[AsyncEngine] = None
_session_factory = None


def get_engine() -> AsyncEngine:
    """
    Get the SQLAlchemy async engine.
    
    Returns:
        The async engine instance.
    """
    global _engine
    
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url
        
        if not database_url:
            raise ValueError("Database URL not configured")
            
        _engine = create_async_engine(
            database_url,
            echo=settings.sql_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True
        )
        
    return _engine


def get_session_factory():
    """
    Get the SQLAlchemy session factory.
    
    Returns:
        The session factory function.
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session.
    
    This is a basic session without tenant context. For tenant-aware
    sessions, use get_tenant_db_session from tenant_db_context.py.
    
    Yields:
        A database session.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def close_db_connections():
    """Close all database connections."""
    global _engine
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed") 