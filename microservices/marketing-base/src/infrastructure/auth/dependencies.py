"""
Authentication dependencies.

This module provides authentication and authorization dependencies for FastAPI.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from ...config.app_config import get_config

logger = logging.getLogger(__name__)

# Define API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


@dataclass
class User:
    """User model for authentication."""
    
    id: str
    username: str
    is_admin: bool = False


def get_current_user(api_key: str = Depends(API_KEY_HEADER)) -> User:
    """
    Get the current authenticated user.
    
    Args:
        api_key: API key from the request header
        
    Returns:
        User object
        
    Raises:
        HTTPException: If authentication fails
    """
    config = get_config()
    
    # Check API key
    if api_key != config.api_key:
        logger.warning(f"Invalid API key used: {api_key[:5]}***")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # In a real application, you would look up the user
    # associated with this API key in your database
    return User(
        id="default-user",
        username="system",
        is_admin=True
    )


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Ensure the current user is an administrator.
    
    Args:
        user: Current authenticated user
        
    Returns:
        User object if the user is an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    
    return user 