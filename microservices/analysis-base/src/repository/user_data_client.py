"""
User Data Service Client

This module provides a client for interacting with the User Data Service.
Used to validate user permissions and roles.
"""

import os
import logging
import structlog
import httpx
from typing import Dict, Any, Optional, List, Set
import asyncio
from datetime import datetime, timedelta

# Configure structured logging
logger = structlog.get_logger(__name__)

# Cache expiration time for user info (5 minutes)
USER_CACHE_EXPIRY = timedelta(minutes=5)


class UserDataClient:
    """
    Client for the User Data Service.
    
    Provides methods to validate users, permissions, and roles.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the user data client.
        
        Args:
            base_url: User Data Service URL (default from environment)
            api_key: API key for authentication (default from environment)
        """
        self.base_url = base_url or os.environ.get(
            "USER_DATA_URL", "http://user-data-service:8502"
        )
        self.api_key = api_key or os.environ.get("USER_DATA_API_KEY", "")
        
        # Request timeout in seconds
        self.timeout = float(os.environ.get("USER_DATA_TIMEOUT", "5.0"))
        
        # Initialize user cache
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        logger.info(
            "Initialized user data client",
            base_url=self.base_url
        )
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information.
        
        Args:
            user_id: User identifier
            
        Returns:
            User information or None if not found
        """
        # Check cache first
        if user_id in self.user_cache:
            cache_time = self.cache_timestamps.get(user_id)
            if cache_time and datetime.now() - cache_time < USER_CACHE_EXPIRY:
                logger.debug(
                    "Using cached user info",
                    user_id=user_id
                )
                return self.user_cache[user_id]
        
        # Cache miss or expired, fetch from service
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    user_info = response.json()
                    # Update cache
                    self.user_cache[user_id] = user_info
                    self.cache_timestamps[user_id] = datetime.now()
                    return user_info
                elif response.status_code == 404:
                    logger.warning(
                        "User not found",
                        user_id=user_id
                    )
                    return None
                else:
                    logger.error(
                        "Failed to get user info",
                        user_id=user_id,
                        status_code=response.status_code,
                        error=response.text
                    )
                    return None
        except Exception as e:
            logger.error(
                "Error contacting user data service",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_user_permissions(self, user_id: str, tenant_id: Optional[str] = None) -> Set[str]:
        """
        Get the permissions for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Optional tenant identifier for tenant-specific permissions
            
        Returns:
            Set of permission strings
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                if tenant_id:
                    headers["x-tenant-id"] = tenant_id
                
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}/permissions",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return set(response.json().get("permissions", []))
                else:
                    logger.error(
                        "Failed to get user permissions",
                        user_id=user_id,
                        tenant_id=tenant_id,
                        status_code=response.status_code,
                        error=response.text
                    )
                    return set()
        except Exception as e:
            logger.error(
                "Error contacting user data service for permissions",
                user_id=user_id,
                tenant_id=tenant_id,
                error=str(e)
            )
            return set()
    
    async def get_user_roles(self, user_id: str, tenant_id: Optional[str] = None) -> List[str]:
        """
        Get the roles for a user.
        
        Args:
            user_id: User identifier
            tenant_id: Optional tenant identifier for tenant-specific roles
            
        Returns:
            List of role strings
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key
                if tenant_id:
                    headers["x-tenant-id"] = tenant_id
                
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}/roles",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json().get("roles", [])
                else:
                    logger.error(
                        "Failed to get user roles",
                        user_id=user_id,
                        tenant_id=tenant_id,
                        status_code=response.status_code,
                        error=response.text
                    )
                    return []
        except Exception as e:
            logger.error(
                "Error contacting user data service for roles",
                user_id=user_id,
                tenant_id=tenant_id,
                error=str(e)
            )
            return []
    
    async def has_permission(
        self, user_id: str, permission: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User identifier
            permission: Permission to check
            tenant_id: Optional tenant identifier for tenant-specific permissions
            
        Returns:
            True if the user has the permission, False otherwise
        """
        permissions = await self.get_user_permissions(user_id, tenant_id)
        
        # Check for the specific permission or admin permission
        return permission in permissions or "admin" in permissions
    
    async def has_role(
        self, user_id: str, role: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if a user has a specific role.
        
        Args:
            user_id: User identifier
            role: Role to check
            tenant_id: Optional tenant identifier for tenant-specific roles
            
        Returns:
            True if the user has the role, False otherwise
        """
        roles = await self.get_user_roles(user_id, tenant_id)
        
        # Check for the specific role or admin role
        return role in roles or "admin" in roles
    
    def clear_cache(self, user_id: Optional[str] = None):
        """
        Clear the user info cache.
        
        Args:
            user_id: Specific user to clear from cache, or None for all
        """
        if user_id:
            if user_id in self.user_cache:
                del self.user_cache[user_id]
                del self.cache_timestamps[user_id]
        else:
            self.user_cache.clear()
            self.cache_timestamps.clear()


# Global user data client instance
user_data_client = UserDataClient() 