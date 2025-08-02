from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

async def get_session() -> AsyncSession:
    """
    Creates and returns a new database session.
    No schema switching is performed - all operations use a unified schema.
    """
    from ...config.database import async_session_factory
    return async_session_factory()

async def get_system_session() -> AsyncSession:
    """
    Creates and returns a new database session for system-wide operations.
    Uses the same session as get_session() since we no longer switch schemas.
    """
    return await get_session() 