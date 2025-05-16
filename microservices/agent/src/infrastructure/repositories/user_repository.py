"""
User Repository

This module provides a repository for accessing user data from the system_users database.
"""
import logging
import os
from typing import Dict, Any, Optional, List
import asyncpg

from src.domain.entities.user import User

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Repository for accessing user data from the system_users database.
    
    This repository provides methods to retrieve and validate user information
    directly from the system_users database, improving efficiency for
    user-related operations in the agent microservice.
    """
    
    def __init__(self):
        """Initialize the user repository."""
        self.pool = None
        self.db_config = {
            "host": os.getenv("USER_DB_HOST", "postgres-system"),
            "port": int(os.getenv("USER_DB_PORT", "5432")),
            "user": os.getenv("USER_DB_USER", "user_service"),
            "password": os.getenv("USER_DB_PASSWORD", "password"),
            "database": os.getenv("USER_DB_NAME", "system_users")
        }
        self.initialized = False
        logger.info("UserRepository initialized with configuration for system_users database")
        
    async def initialize(self):
        """Initialize the database connection pool."""
        if self.initialized:
            return
            
        try:
            self.pool = await asyncpg.create_pool(**self.db_config)
            self.initialized = True
            logger.info("Successfully connected to system_users database")
        except Exception as e:
            logger.error(f"Failed to initialize system_users database connection: {str(e)}")
            raise
            
    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            self.initialized = False
            logger.info("Closed connection to system_users database")
            
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User entity or None if not found
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, username, email, metadata
                    FROM users
                    WHERE id = $1
                    """,
                    user_id
                )
                
                if not row:
                    return None
                    
                return User(
                    id=row['id'],
                    name=row['username'],
                    email=row['email'],
                    metadata=row['metadata'] if row['metadata'] else {}
                )
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            return None
            
    async def validate_user_exists(self, user_id: str) -> bool:
        """
        Validate that a user exists.
        
        Args:
            user_id: User ID
            
        Returns:
            True if user exists, False otherwise
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)
                    """,
                    user_id
                )
                return bool(result)
        except Exception as e:
            logger.error(f"Error validating user {user_id}: {str(e)}")
            return False
            
    async def get_user_tenant(self, user_id: str) -> Optional[str]:
        """
        Get the tenant ID for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Tenant ID or None if not found
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    """
                    SELECT tenant_id 
                    FROM user_tenants
                    WHERE user_id = $1
                    LIMIT 1
                    """,
                    user_id
                )
        except Exception as e:
            logger.error(f"Error retrieving tenant for user {user_id}: {str(e)}")
            return None
            
    async def get_users_by_ids(self, user_ids: List[str]) -> List[User]:
        """
        Get multiple users by their IDs.
        
        Args:
            user_ids: List of user IDs
            
        Returns:
            List of User entities
        """
        if not self.initialized:
            await self.initialize()
            
        if not user_ids:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, username, email, metadata
                    FROM users
                    WHERE id = ANY($1)
                    """,
                    user_ids
                )
                
                return [
                    User(
                        id=row['id'],
                        name=row['username'],
                        email=row['email'],
                        metadata=row['metadata'] if row['metadata'] else {}
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error retrieving users by IDs: {str(e)}")
            return []
            
    async def check_user_permission(self, user_id: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if not self.initialized:
            await self.initialize()
            
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 
                        FROM user_permissions up
                        JOIN permissions p ON up.permission_id = p.id
                        WHERE up.user_id = $1 AND p.name = $2
                    )
                    """,
                    user_id,
                    permission
                )
                return bool(result)
        except Exception as e:
            logger.error(f"Error checking permission for user {user_id}: {str(e)}")
            return False 