"""
Authentication module for the Management Systems microservice.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = HTTPBearer()

class CurrentUser:
    """Current user model for authentication."""
    def __init__(self, user_id: str, email: str = None, roles: list = None):
        self.user_id = user_id
        self.email = email
        self.roles = roles or []

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> CurrentUser:
    """
    Get the current authenticated user from the token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # For local testing, create a mock user
        # In production, this would validate the JWT token
        token = credentials.credentials
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Mock user for local testing
        # In production, decode and validate JWT token here
        mock_user = CurrentUser(
            user_id="test_user_123",
            email="test@example.com",
            roles=["admin", "user"]
        )
        
        logger.info(f"Authenticated user: {mock_user.user_id}")
        return mock_user
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
) -> Optional[CurrentUser]:
    """
    Get the current user if authenticated, otherwise return None.
    
    Args:
        credentials: Optional HTTP authorization credentials
        
    Returns:
        Current user information or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
