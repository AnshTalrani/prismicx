"""
Database access module.

This module provides a database access layer for MongoDB operations.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from ...config.app_config import get_config

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database access class."""
    
    def __init__(self, connection_string: Optional[str] = None, database_name: Optional[str] = None):
        """
        Initialize the database connection.
        
        Args:
            connection_string: MongoDB connection string. If None, uses configuration.
            database_name: MongoDB database name. If None, uses configuration.
        """
        config = get_config()
        self.client = AsyncIOMotorClient(connection_string or config.mongodb_uri)
        self.db = self.client[database_name or config.mongodb_database]
    
    async def get_by_id(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            collection: Collection name.
            id: Document ID.
            
        Returns:
            Document if found, None otherwise.
        """
        try:
            result = await self.db[collection].find_one({"id": id})
            return result
        except Exception as e:
            logger.error(f"Database error in get_by_id: {str(e)}")
            raise
    
    async def find(
        self,
        collection: str,
        query: Dict[str, Any],
        limit: int = 100,
        offset: int = 0,
        sort: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents matching a query.
        
        Args:
            collection: Collection name.
            query: Query filter.
            limit: Maximum number of documents to return.
            offset: Number of documents to skip.
            sort: Sort specification.
            
        Returns:
            List of matching documents.
        """
        try:
            cursor = self.db[collection].find(query)
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
                
            cursor = cursor.skip(offset).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Database error in find: {str(e)}")
            raise
    
    async def count(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Count documents matching a query.
        
        Args:
            collection: Collection name.
            query: Query filter.
            
        Returns:
            Count of matching documents.
        """
        try:
            return await self.db[collection].count_documents(query)
        except Exception as e:
            logger.error(f"Database error in count: {str(e)}")
            raise
    
    async def insert(self, collection: str, data: Dict[str, Any]) -> str:
        """
        Insert a new document.
        
        Args:
            collection: Collection name.
            data: Document data.
            
        Returns:
            ID of the inserted document.
        """
        try:
            result = await self.db[collection].insert_one(data)
            return data.get("id")
        except Exception as e:
            logger.error(f"Database error in insert: {str(e)}")
            raise
    
    async def upsert(self, collection: str, id: str, data: Dict[str, Any]) -> bool:
        """
        Insert or update a document by ID.
        
        Args:
            collection: Collection name.
            id: Document ID.
            data: Document data.
            
        Returns:
            True if successful.
        """
        try:
            result = await self.db[collection].replace_one(
                {"id": id},
                data,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Database error in upsert: {str(e)}")
            raise
    
    async def update(self, collection: str, id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in a document.
        
        Args:
            collection: Collection name.
            id: Document ID.
            updates: Fields to update.
            
        Returns:
            True if document was updated, False if not found.
        """
        try:
            result = await self.db[collection].update_one(
                {"id": id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Database error in update: {str(e)}")
            raise
    
    async def update_array_element(
        self,
        collection: str,
        id: str,
        array_field: str,
        element_query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """
        Update a specific element within an array field.
        
        Args:
            collection: Collection name.
            id: Document ID.
            array_field: Name of the array field.
            element_query: Query to match the array element.
            update: Update operations.
            
        Returns:
            True if document was updated, False if not found.
        """
        try:
            # Build the query
            query = {
                "id": id,
                f"{array_field}": {"$elemMatch": element_query}
            }
            
            result = await self.db[collection].update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Database error in update_array_element: {str(e)}")
            raise
    
    async def delete(self, collection: str, id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            collection: Collection name.
            id: Document ID.
            
        Returns:
            True if document was deleted, False if not found.
        """
        try:
            result = await self.db[collection].delete_one({"id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Database error in delete: {str(e)}")
            raise 