"""
Repository Module

This module provides the data repository adapter for MongoDB.
It handles all database interactions for the application.
"""

import asyncio
import structlog
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson.objectid import ObjectId
import redis.asyncio as redis

# Configure structured logging
logger = structlog.get_logger(__name__)

class Repository:
    """
    Repository for database interactions.
    
    This class handles all database operations including:
    - Connecting to and querying MongoDB
    - CRUD operations for contexts
    - Managing indexes and collections
    - Handling distributed locks via Redis
    """
    
    def __init__(self, mongodb_url: str, database_name: str, redis_client: Optional[redis.Redis] = None, settings: Any = None):
        """
        Initialize the repository.
        
        Args:
            mongodb_url: MongoDB connection URL
            database_name: Database name
            redis_client: Optional Redis client for distributed locking
            settings: Application settings
        """
        self.mongodb_url = mongodb_url
        self.database_name = database_name
        self.client = None
        self.db = None
        self.redis = redis_client
        self.settings = settings
        
        # Collections
        self.contexts_collection = None
        self.templates_collection = None
        
        logger.info(
            "Repository initialized",
            database=database_name
        )
    
    async def connect(self):
        """
        Connect to MongoDB and initialize collections.
        """
        try:
            # Set up connection
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.contexts_collection = self.db.contexts
            self.templates_collection = self.db.templates
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("Repository connected to database")
            return True
            
        except Exception as e:
            logger.error(
                "Failed to connect to database",
                error=str(e),
                exc_info=True
            )
            return False
    
    async def close(self):
        """
        Close the database connection.
        """
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Repository disconnected from database")
    
    def is_connected(self) -> bool:
        """
        Check if the repository is connected to the database.
        
        Returns:
            True if connected, False otherwise
        """
        return self.client is not None and self.db is not None
    
    async def _create_indexes(self):
        """
        Create necessary indexes on collections.
        """
        # Contexts collection indexes
        indexes = [
            [("status", 1), ("service_type", 1), ("created_at", 1)],
            [("template_id", 1), ("status", 1)],
            [("organization_id", 1), ("status", 1)],
            [("tags", 1)],
            [("batch_id", 1)],
            [("metadata.priority", 1), ("status", 1), ("created_at", 1)]
        ]
        
        for index in indexes:
            await self.contexts_collection.create_index(index)
        
        # Templates collection indexes
        await self.templates_collection.create_index("template_id", unique=True)
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a context by ID.
        
        Args:
            context_id: Context ID
            
        Returns:
            Context document or None if not found
        """
        if not self.is_connected():
            logger.error("Cannot get context: not connected to database")
            return None
        
        try:
            # Convert string ID to ObjectId if needed
            _id = ObjectId(context_id) if not isinstance(context_id, ObjectId) else context_id
            
            context = await self.contexts_collection.find_one({"_id": _id})
            
            if context:
                # Ensure context has an ID as string
                context["_id"] = str(context["_id"])
            
            return context
            
        except Exception as e:
            logger.error(
                "Failed to get context",
                context_id=context_id,
                error=str(e)
            )
            return None
    
    async def get_next_pending_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the next pending context for processing.
        
        This method uses optimistic locking with Redis to prevent
        multiple workers from processing the same context.
        
        Returns:
            The next pending context, or None if no pending contexts
        """
        if not self.is_connected():
            logger.error("Cannot get pending context: not connected to database")
            return None
            
        query = {
            "status": "pending",
            "$or": [
                {"retry_metadata.next_retry_at": {"$lte": datetime.utcnow().isoformat()}},
                {"retry_metadata.next_retry_at": {"$exists": False}}
            ]
        }
        
        # Sort by priority (if exists) and then by creation time
        sort = [
            ("metadata.priority", 1),  # Lower number = higher priority
            ("created_at", 1)  # Oldest first
        ]
        
        # Find and get a pending context
        context = await self.contexts_collection.find_one(query, sort=sort)
        
        if not context:
            return None
        
        # Convert ObjectId to string
        context["_id"] = str(context["_id"])
        
        # If Redis is available, try to acquire a lock
        if self.redis and self.settings:
            # Try to acquire a lock to prevent other workers from processing the same context
            lock_key = f"generative:lock:{context['_id']}"
            worker_id = getattr(self.settings, 'worker_id', 'unknown-worker')
            lock_expiry = getattr(self.settings, 'lock_expiry_seconds', 300)
            
            lock_acquired = await self.redis.set(
                lock_key, 
                worker_id,
                nx=True,  # Only set if the key doesn't exist
                ex=lock_expiry
            )
            
            if not lock_acquired:
                logger.debug(
                    "Context is being processed by another worker", 
                    context_id=context["_id"]
                )
                return None
        
        return context
    
    async def get_pending_contexts_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Get a batch of pending contexts for processing.
        
        Args:
            batch_size: Maximum number of contexts to retrieve
            
        Returns:
            List of pending contexts, may be empty
        """
        if not self.is_connected():
            logger.error("Cannot get pending contexts: not connected to database")
            return []
            
        query = {
            "status": "pending",
            "$or": [
                {"retry_metadata.next_retry_at": {"$lte": datetime.utcnow().isoformat()}},
                {"retry_metadata.next_retry_at": {"$exists": False}}
            ]
        }
        
        # Sort by priority (if exists) and then by creation time
        sort = [
            ("metadata.priority", 1),  # Lower number = higher priority
            ("created_at", 1)  # Oldest first
        ]
        
        contexts = []
        
        # Find pending contexts
        cursor = self.contexts_collection.find(query).sort(sort).limit(batch_size * 2)  # Get more than needed in case some are locked
        
        async for context in cursor:
            if len(contexts) >= batch_size:
                break
                
            # Convert ObjectId to string
            context["_id"] = str(context["_id"])
            
            # If Redis is available, try to acquire locks
            if self.redis and self.settings:
                # Try to acquire a lock
                lock_key = f"generative:lock:{context['_id']}"
                worker_id = getattr(self.settings, 'worker_id', 'unknown-worker')
                lock_expiry = getattr(self.settings, 'lock_expiry_seconds', 300)
                
                lock_acquired = await self.redis.set(
                    lock_key, 
                    worker_id,
                    nx=True,
                    ex=lock_expiry
                )
                
                if lock_acquired:
                    contexts.append(context)
            else:
                contexts.append(context)
        
        return contexts
    
    async def update_context_status(
        self, 
        context_id: str, 
        status: str, 
        error: Optional[Dict[str, Any]] = None,
        retry_metadata: Optional[Dict[str, Any]] = None,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the status of a context.
        
        Args:
            context_id: ID of the context
            status: New status
            error: Optional error information
            retry_metadata: Optional retry information
            processing_metadata: Optional processing information
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot update context: not connected to database")
            return False
            
        try:
            now = datetime.utcnow().isoformat()
            update = {"$set": {"status": status, "updated_at": now}}
            
            if error:
                update["$set"]["error"] = error
                
            if retry_metadata:
                update["$set"]["retry_metadata"] = retry_metadata
                
            if processing_metadata:
                update["$set"]["processing_metadata"] = processing_metadata
                
            result = await self.contexts_collection.update_one(
                {"_id": ObjectId(context_id)},
                update
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(
                "Failed to update context status",
                context_id=context_id,
                status=status,
                error=str(e)
            )
            return False
    
    async def update_context_result(
        self, 
        context_id: str, 
        status: str, 
        result: Dict[str, Any],
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a context with processing results.
        
        Args:
            context_id: ID of the context
            status: New status (usually 'completed')
            result: Processing results
            processing_metadata: Optional processing information
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot update context result: not connected to database")
            return False
            
        try:
            now = datetime.utcnow().isoformat()
            
            update = {
                "$set": {
                    "status": status,
                    "updated_at": now,
                    "result": result,
                    "completed_at": now
                }
            }
            
            if processing_metadata:
                update["$set"]["processing_metadata"] = processing_metadata
                
            result = await self.contexts_collection.update_one(
                {"_id": ObjectId(context_id)},
                update
            )
            
            # Release lock if Redis is available
            if self.redis and self.settings:
                lock_key = f"generative:lock:{context_id}"
                worker_id = getattr(self.settings, 'worker_id', 'unknown-worker')
                
                await self.redis.eval(
                    """
                    if redis.call('get', KEYS[1]) == ARGV[1] then
                        return redis.call('del', KEYS[1])
                    else
                        return 0
                    end
                    """,
                    1,
                    lock_key,
                    worker_id
                )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(
                "Failed to update context result",
                context_id=context_id,
                error=str(e)
            )
            return False
    
    async def create_context(self, context_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new context.
        
        Args:
            context_data: Context data
            
        Returns:
            ID of the created context or None if creation failed
        """
        if not self.is_connected():
            logger.error("Cannot create context: not connected to database")
            return None
            
        try:
            now = datetime.utcnow().isoformat()
            
            # Ensure required fields
            if "status" not in context_data:
                context_data["status"] = "pending"
                
            context_data["created_at"] = now
            context_data["updated_at"] = now
            
            result = await self.contexts_collection.insert_one(context_data)
            context_id = str(result.inserted_id)
            
            logger.info("Created new context", context_id=context_id)
            return context_id
            
        except Exception as e:
            logger.error(
                "Failed to create context",
                error=str(e)
            )
            return None
    
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template document or None if not found
        """
        if not self.is_connected():
            logger.error("Cannot get template: not connected to database")
            return None
            
        try:
            template = await self.templates_collection.find_one({"template_id": template_id})
            
            if template:
                # Ensure template has an ID as string
                template["_id"] = str(template["_id"])
                
            return template
            
        except Exception as e:
            logger.error(
                "Failed to get template",
                template_id=template_id,
                error=str(e)
            )
            return None
    
    async def update_context_tags(self, context_id: str, tags: List[str]) -> bool:
        """
        Update the tags for a context.
        
        Args:
            context_id: ID of the context
            tags: New tags to add
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot update context tags: not connected to database")
            return False
            
        try:
            result = await self.contexts_collection.update_one(
                {"_id": ObjectId(context_id)},
                {"$addToSet": {"tags": {"$each": tags}}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(
                "Failed to update context tags",
                context_id=context_id,
                error=str(e)
            )
            return False
    
    async def schedule_context_retry(
        self, 
        context_id: str, 
        retry_count: int,
        next_retry: datetime
    ) -> bool:
        """
        Schedule a context for retry.
        
        Args:
            context_id: ID of the context
            retry_count: Current retry count
            next_retry: Time for the next retry
            
        Returns:
            True if scheduling was successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot schedule retry: not connected to database")
            return False
            
        try:
            result = await self.contexts_collection.update_one(
                {"_id": ObjectId(context_id)},
                {
                    "$set": {
                        "status": "pending",
                        "retry_metadata.retry_count": retry_count,
                        "retry_metadata.next_retry_at": next_retry.isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(
                "Failed to schedule context retry",
                context_id=context_id,
                error=str(e)
            )
            return False
            
    # Added from analysis-base for batch operations
    async def update_batch_status(
        self, 
        context_ids: List[str], 
        status: str,
        processing_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Update the status of multiple contexts.
        
        Args:
            context_ids: List of context IDs
            status: New status
            processing_metadata: Optional processing information
            
        Returns:
            Number of contexts updated
        """
        if not self.is_connected():
            logger.error("Cannot update batch: not connected to database")
            return 0
            
        try:
            now = datetime.utcnow().isoformat()
            object_ids = [ObjectId(cid) for cid in context_ids]
            
            update = {"$set": {"status": status, "updated_at": now}}
            
            if processing_metadata:
                update["$set"]["processing_metadata"] = processing_metadata
                
            result = await self.contexts_collection.update_many(
                {"_id": {"$in": object_ids}},
                update
            )
            
            return result.modified_count
            
        except Exception as e:
            logger.error(
                "Failed to update batch status",
                context_count=len(context_ids),
                error=str(e)
            )
            return 0
            
    async def find_one_and_update_context(
        self,
        query_filter: Dict[str, Any],
        update: Dict[str, Any],
        sort: List[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find one context matching the filter, update it, and return the original.
        
        Args:
            query_filter: Query filter
            update: Update operation
            sort: Optional sort criteria
            
        Returns:
            Original context document or None if not found
        """
        if not self.is_connected():
            logger.error("Cannot find and update context: not connected to database")
            return None
        
        try:
            result = await self.contexts_collection.find_one_and_update(
                filter=query_filter,
                update=update,
                sort=sort if sort else None,
                return_document=False  # Return original document
            )
            
            if result:
                # Ensure result has an ID as string
                result["_id"] = str(result["_id"])
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to find and update context",
                error=str(e),
                filter=query_filter
            )
            return None


