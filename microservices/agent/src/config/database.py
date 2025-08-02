"""
DEPRECATED: Direct MongoDB connection module.

This module is kept for backward compatibility but is no longer actively used.
The agent microservice now uses the TaskRepositoryAdapter which connects to the
Task Repository Service instead of directly to MongoDB.
"""
import os
import logging
from typing import Optional, NoReturn
import warnings

logger = logging.getLogger(__name__)

# Issue a deprecation warning when this module is imported
warnings.warn(
    "Direct MongoDB connections are deprecated. Use TaskRepositoryAdapter instead.",
    DeprecationWarning,
    stacklevel=2
)

def get_mongodb_client() -> NoReturn:
    """
    DEPRECATED: This function is no longer supported.
    
    The agent microservice now uses TaskRepositoryAdapter instead of direct MongoDB access.
    Use the task repository service for all data persistence operations.
    
    Raises:
        NotImplementedError: Always raises this error when called
    """
    raise NotImplementedError(
        "Direct MongoDB access has been deprecated. "
        "Use the TaskRepositoryAdapter instead which connects to the task repository service."
    )

def get_database(db_name: Optional[str] = None) -> NoReturn:
    """
    DEPRECATED: This function is no longer supported.
    
    The agent microservice now uses TaskRepositoryAdapter instead of direct MongoDB access.
    Use the task repository service for all data persistence operations.
    
    Args:
        db_name: Optional database name (unused)
        
    Raises:
        NotImplementedError: Always raises this error when called
    """
    raise NotImplementedError(
        "Direct MongoDB access has been deprecated. "
        "Use the TaskRepositoryAdapter instead which connects to the task repository service."
    ) 