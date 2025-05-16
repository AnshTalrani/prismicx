"""
System Users Conversation

Repository for managing system users conversation data. Works with the existing system_users database.
This repository handles permanent users with active subscriptions.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import asyncpg

logger = logging.getLogger(__name__)


class SystemUsersConversation:
    """Repository for managing conversation data for permanent system users. Interfaces with system_users database."""

    def __init__(self, mongo_client: AsyncIOMotorClient = None, db_name: str = "system_users"):
        """
        Initialize the repository with MongoDB connection.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
            db_name: Database name (defaults to system_users)
        """
        self.client = mongo_client
        self.db_name = db_name
        self.db = None
        self.postgres_pool = None
        self.postgres_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres-system"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "user_service"),
            "password": os.getenv("POSTGRES_PASSWORD", "password"),
            "database": "system_users"
        }
    
    async def initialize(self, mongo_client: AsyncIOMotorClient = None):
        """
        Initialize the repository with the MongoDB client and PostgreSQL connection.
        
        Args:
            mongo_client: AsyncIOMotorClient instance
        """
        if mongo_client:
            self.client = mongo_client
        
        if self.client:
            self.db = self.client[self.db_name]
            logger.info(f"SystemUsersConversation initialized with MongoDB database {self.db_name}")
        else:
            logger.error("No MongoDB client provided for SystemUsersConversation")
            raise ValueError("MongoDB client is required")
        
        # Initialize PostgreSQL connection pool for system_users database
        try:
            self.postgres_pool = await asyncpg.create_pool(**self.postgres_config)
            logger.info("Connected to PostgreSQL system_users database")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _get_collection(self, tenant_id: str) -> AsyncIOMotorCollection:
        """
        Get the collection for the tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            AsyncIOMotorCollection for the tenant
        """
        # Using tenant_id to create separate collections for each tenant
        collection_name = f'system_users_conversation_{tenant_id}'
        return self.db[collection_name]
    
    async def find_by_id(self, user_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a system user by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            User dict if found, None otherwise
        """
        collection = self._get_collection(tenant_id)
        data = await collection.find_one({"user_id": user_id})
        
        if not data:
            # Try to find user in PostgreSQL system_users database
            try:
                async with self.postgres_pool.acquire() as conn:
                    query = """
                    SELECT id, tenant_id, username, email, first_name, last_name, 
                           role, status, created_at, updated_at, last_login_at, metadata
                    FROM user_data.users
                    WHERE id = $1 AND tenant_id = $2
                    """
                    row = await conn.fetchrow(query, user_id, tenant_id)
                    
                    if row:
                        # Convert to dict and return
                        return dict(row)
            except Exception as e:
                logger.error(f"Error querying PostgreSQL: {e}")
        
        return data
    
    async def is_system_user(self, user_id: str) -> bool:
        """
        Check if a user is a system user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if the user is a system user, False otherwise
        """
        try:
            async with self.postgres_pool.acquire() as conn:
                query = "SELECT 1 FROM user_data.users WHERE id = $1"
                exists = await conn.fetchval(query, user_id)
                return exists is not None
        except Exception as e:
            logger.error(f"Error checking system user: {e}")
            return False
    
    async def find_all_by_tenant(
        self, 
        tenant_id: str,
        page: int = 1, 
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find all system users for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            page: Page number
            page_size: Page size
            
        Returns:
            List of user dicts
        """
        collection = self._get_collection(tenant_id)
        skip = (page - 1) * page_size
        
        cursor = collection.find({"tenant_id": tenant_id}).skip(skip).limit(page_size)
        users = await cursor.to_list(length=page_size)
        
        # Combine with PostgreSQL users
        try:
            async with self.postgres_pool.acquire() as conn:
                query = """
                SELECT id, tenant_id, username, email, first_name, last_name, 
                       role, status, created_at, updated_at, last_login_at, metadata
                FROM user_data.users
                WHERE tenant_id = $1
                LIMIT $2 OFFSET $3
                """
                rows = await conn.fetch(query, tenant_id, page_size, skip)
                
                # Add PostgreSQL users to the list
                for row in rows:
                    users.append(dict(row))
        except Exception as e:
            logger.error(f"Error querying PostgreSQL: {e}")
        
        return users
    
    async def save(self, user_data: Dict[str, Any]) -> str:
        """
        Save a system user.
        
        Args:
            user_data: User data to save
            
        Returns:
            The user ID
        """
        if not user_data.get("tenant_id"):
            raise ValueError("tenant_id is required")
        
        user_id = user_data.get("user_id", str(uuid4()))
        user_data["user_id"] = user_id
        
        # Set timestamps
        now = datetime.utcnow()
        if "created_at" not in user_data:
            user_data["created_at"] = now
        user_data["updated_at"] = now
        
        collection = self._get_collection(user_data["tenant_id"])
        
        # Check if user exists in PostgreSQL
        is_system = await self.is_system_user(user_id)
        
        # If not a system user in PostgreSQL, save to MongoDB
        if not is_system:
            await collection.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            logger.info(f"Saved system user {user_id} to MongoDB")
        
        return user_id
    
    async def delete(self, user_id: str, tenant_id: str) -> bool:
        """
        Delete a system user by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            
        Returns:
            True if deleted, False otherwise
        """
        collection = self._get_collection(tenant_id)
        
        try:
            result = await collection.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted system user {user_id} from MongoDB")
                return True
        except Exception as e:
            logger.error(f"Error deleting from MongoDB: {e}")
        
        # We don't delete from PostgreSQL as system users are managed elsewhere
        return False
    
    async def update(self, user_id: str, tenant_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a system user by user ID.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            update_data: Data to update
            
        Returns:
            True if updated, False otherwise
        """
        collection = self._get_collection(tenant_id)
        
        # Set updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Check if user exists in PostgreSQL
        is_system = await self.is_system_user(user_id)
        
        # If not a system user in PostgreSQL, update in MongoDB
        if not is_system:
            try:
                result = await collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data}
                )
                if result.modified_count > 0:
                    logger.info(f"Updated system user {user_id} in MongoDB")
                    return True
                elif result.matched_count > 0:
                    # Document matched but not modified
                    return True
            except Exception as e:
                logger.error(f"Error updating in MongoDB: {e}")
        
        return False
    
    async def close(self):
        """Close database connections."""
        if self.postgres_pool:
            await self.postgres_pool.close()
            logger.info("Closed PostgreSQL connection pool") 