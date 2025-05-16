"""
Database Context Module

This module provides context management for database operations without tenant schema switching.
It includes a simplified context manager that no longer switches schemas per tenant.
"""

import logging
from typing import Optional, AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseContext:
    """
    Database context manager for batch operations.
    
    This class provides methods for database operations without tenant schema switching.
    """
    
    @staticmethod
    async def apply_batch_context(session: AsyncSession, batch_id: Optional[str] = None) -> None:
        """
        Apply batch context to a database session for monitoring purposes only.
        This doesn't switch database schemas.
        
        Args:
            session: The database session.
            batch_id: Optional batch identifier for monitoring.
        """
        if batch_id:
            # Set application_name for monitoring/logging but don't switch schemas
            await session.execute(text(f"SET application_name = 'batch_{batch_id}'"))
            logger.debug(f"Applied batch context for monitoring: {batch_id}")


async def get_db_session_with_batch(
    session_factory,
    batch_id: Optional[str] = None
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with optional batch tagging.
    This does NOT switch database schemas like the previous tenant-based approach.
    
    Args:
        session_factory: A function that creates a new database session.
        batch_id: Optional batch identifier for monitoring.
        
    Yields:
        A database session.
    """
    async with session_factory() as session:
        if batch_id:
            await DatabaseContext.apply_batch_context(session, batch_id)
        yield session

# Maintain backward compatibility by aliasing the old function name
# This ensures existing code still works without changes
get_tenant_db_session = get_db_session_with_batch 