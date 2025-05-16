"""
Dependencies Module

This module provides dependency injection functions for the API endpoints.
"""

import logging
from typing import AsyncGenerator, Optional
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from .multitenant import (
    get_db_session,
    get_db_session_with_batch,
)

logger = logging.getLogger(__name__)


async def get_batch_id(x_batch_id: Optional[str] = Header(None, alias="X-Batch-ID")) -> Optional[str]:
    """
    Extract batch ID from the request header.
    
    Args:
        x_batch_id: The batch ID from the X-Batch-ID header.
        
    Returns:
        The batch ID or None if not provided.
    """
    return x_batch_id


async def get_db(
    batch_id: Optional[str] = Depends(get_batch_id)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session with optional batch context.
    
    This function yields a database session with batch context for monitoring,
    but WITHOUT tenant schema switching.
    
    Args:
        batch_id: The batch ID from the request header.
        
    Yields:
        A database session.
    """
    async for session in get_db_session_with_batch(get_db_session, batch_id):
        yield session


# Legacy function maintained for backward compatibility
# This no longer switches schemas but provides the same interface
async def get_tenant_db(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> AsyncGenerator[AsyncSession, None]:
    """
    Legacy function that maintains backward compatibility.
    Now just returns a regular database session without schema switching.
    
    Args:
        tenant_id: Ignored, maintained for compatibility.
        
    Yields:
        A database session.
    """
    async for session in get_db_session():
        yield session 