"""
Task Repository Implementation for MongoDB.

This module provides the TaskRepository class for interacting with the MongoDB task repository.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

from ..models.task import Task, TaskCreate, TaskUpdate, TaskStatus

# Configure logging
logger = logging.getLogger(__name__)


class TaskRepository:
    """
    Repository for storing and retrieving tasks from MongoDB.
    
    This class provides methods for CRUD operations on tasks in the central task repository.
    It ensures proper tenant isolation and supports various query patterns for task retrieval.
    """
    
    def __init__(self, 
                 mongodb_uri: str, 
                 database_name: str = "task_repository", 
                 collection_name: str = "tasks"):
        """
        Initialize the task repository.
        
        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name (default: task_repository)
            collection_name: Collection name (default: tasks)
        """
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.collection_name = collection_name
        
        # Initialize client to None - will connect on first use
        self.client = None
        self.db = None
        self.collection = None
        
        logger.info(f"Initialized TaskRepository with database {database_name}.{collection_name}")
    
    async def connect(self) -> bool:
        """
        Connect to the MongoDB database.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.client is not None:
            return True  # Already connected
            
        try:
            self.client = AsyncIOMotorClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Test connection
            await self.db.command("ping")
            
            logger.info(f"Connected to MongoDB {self.database_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
    
    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None
            logger.info("Closed MongoDB connection")
    
    async def ensure_connected(self):
        """Ensure the repository is connected to MongoDB."""
        if self.client is None:
            await self.connect()
    
    async def create_task(self, task: TaskCreate) -> Optional[str]:
        """
        Create a new task in the repository.
        
        Args:
            task: Task data to create
            
        Returns:
            Task ID if successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Generate ID if not provided
            task_id = task.task_id or f"task_{uuid.uuid4().hex}"
            
            now = datetime.utcnow()
            
            # Prepare task document
            task_doc = {
                "_id": ObjectId(),
                "task_id": task_id,
                "task_type": task.task_type,
                "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
                "priority": task.priority or 5,
                "created_at": now,
                "updated_at": now,
                "tenant_id": task.tenant_id,
                "batch_id": task.batch_id,
                "request": task.request.dict() if task.request else {},
                "template": task.template.dict() if task.template else {},
                "tags": task.tags.dict() if task.tags else {},
                "metadata": task.metadata or {}
            }
            
            # Insert into database
            result = await self.collection.insert_one(task_doc)
            task_obj_id = str(result.inserted_id)
            
            logger.info(f"Created task with ID {task_obj_id} and task_id {task_id}")
            return task_obj_id
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return None
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a task by its ID.
        
        Args:
            task_id: Task ID (ObjectId as string)
            
        Returns:
            Task document if found, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Get by _id (ObjectId) first
            if ObjectId.is_valid(task_id):
                task = await self.collection.find_one({"_id": ObjectId(task_id)})
                if task:
                    return task
            
            # Try finding by task_id field
            task = await self.collection.find_one({"task_id": task_id})
            if task:
                task["_id"] = str(task["_id"])  # Convert ObjectId to string
            
            return task
            
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {str(e)}")
            return None
    
    async def update_task(self, task_id: str, update_data: Union[Dict[str, Any], TaskUpdate]) -> bool:
        """
        Update a task in the repository.
        
        Args:
            task_id: Task ID
            update_data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Convert TaskUpdate to dict if needed
            if not isinstance(update_data, dict):
                update_data = update_data.dict(exclude_unset=True)
            
            # Always update the updated_at field
            update_data["updated_at"] = datetime.utcnow()
            
            # Handle status changes
            if "status" in update_data:
                status = update_data["status"]
                if isinstance(status, TaskStatus):
                    status = status.value
                
                update_data["status"] = status
                
                # Add timestamps for specific status transitions
                if status == TaskStatus.PROCESSING.value:
                    update_data["processing_started_at"] = datetime.utcnow()
                elif status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                    update_data["completed_at"] = datetime.utcnow()
            
            # Find by ObjectId or task_id
            if ObjectId.is_valid(task_id):
                filter_query = {"_id": ObjectId(task_id)}
            else:
                filter_query = {"task_id": task_id}
            
            # Update the document
            result = await self.collection.update_one(
                filter_query,
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Updated task {task_id}")
            else:
                logger.warning(f"Task {task_id} not found or not modified")
                
            return success
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {str(e)}")
            return False
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the repository.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Find by ObjectId or task_id
            if ObjectId.is_valid(task_id):
                filter_query = {"_id": ObjectId(task_id)}
            else:
                filter_query = {"task_id": task_id}
            
            # Delete the document
            result = await self.collection.delete_one(filter_query)
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted task {task_id}")
            else:
                logger.warning(f"Task {task_id} not found for deletion")
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {str(e)}")
            return False
    
    async def get_pending_tasks(self, 
                               task_type: str = None,
                               tenant_id: str = None,
                               service_tag: str = None,
                               limit: int = 10,
                               sort_by_priority: bool = True) -> List[Dict[str, Any]]:
        """
        Get pending tasks for processing.
        
        Args:
            task_type: Optional task type filter
            tenant_id: Optional tenant ID filter
            service_tag: Optional service tag filter
            limit: Maximum number of tasks to retrieve
            sort_by_priority: Whether to sort by priority (default: True)
            
        Returns:
            List of pending task documents
        """
        await self.ensure_connected()
        
        try:
            # Build query
            query = {"status": TaskStatus.PENDING.value}
            
            if task_type:
                query["task_type"] = task_type
                
            if tenant_id:
                query["tenant_id"] = tenant_id
                
            if service_tag:
                query["tags.service"] = service_tag
            
            # Build sort order
            sort_order = []
            if sort_by_priority:
                sort_order.append(("priority", 1))  # Lower priority values first
            sort_order.append(("created_at", 1))  # Oldest first
            
            # Execute query
            cursor = self.collection.find(query).sort(sort_order).limit(limit)
            
            # Convert cursor to list
            tasks = []
            async for task in cursor:
                task["_id"] = str(task["_id"])  # Convert ObjectId to string
                tasks.append(task)
            
            logger.info(f"Retrieved {len(tasks)} pending tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error retrieving pending tasks: {str(e)}")
            return []
    
    async def claim_task(self, 
                        task_id: str,
                        processor_id: str,
                        tenant_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Claim a task for processing by updating its status atomically.
        
        Args:
            task_id: Task ID
            processor_id: ID of the processor claiming the task
            tenant_id: Optional tenant ID for verification
            
        Returns:
            Updated task document if claim successful, None otherwise
        """
        await self.ensure_connected()
        
        try:
            # Find by ObjectId or task_id
            if ObjectId.is_valid(task_id):
                filter_query = {"_id": ObjectId(task_id)}
            else:
                filter_query = {"task_id": task_id}
            
            # Ensure the task is pending
            filter_query["status"] = TaskStatus.PENDING.value
            
            # Add tenant check if provided
            if tenant_id:
                filter_query["tenant_id"] = tenant_id
            
            # Update document atomically
            now = datetime.utcnow()
            update = {
                "$set": {
                    "status": TaskStatus.PROCESSING.value,
                    "processor_id": processor_id,
                    "processing_started_at": now,
                    "updated_at": now
                }
            }
            
            # Execute update and return the updated document
            result = await self.collection.find_one_and_update(
                filter_query,
                update,
                return_document=True
            )
            
            if result:
                result["_id"] = str(result["_id"])  # Convert ObjectId to string
                logger.info(f"Task {task_id} claimed by processor {processor_id}")
            else:
                logger.warning(f"Failed to claim task {task_id} by processor {processor_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error claiming task {task_id}: {str(e)}")
            return None
    
    async def mark_task_completed(self, 
                                 task_id: str,
                                 results: Dict[str, Any],
                                 processor_id: str = None) -> bool:
        """
        Mark a task as completed with results.
        
        Args:
            task_id: Task ID
            results: Task results
            processor_id: Optional processor ID for verification
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Find by ObjectId or task_id
            if ObjectId.is_valid(task_id):
                filter_query = {"_id": ObjectId(task_id)}
            else:
                filter_query = {"task_id": task_id}
            
            # Verify processor if provided
            if processor_id:
                filter_query["processor_id"] = processor_id
            
            # Update document
            now = datetime.utcnow()
            update = {
                "$set": {
                    "status": TaskStatus.COMPLETED.value,
                    "results": results,
                    "completed_at": now,
                    "updated_at": now
                }
            }
            
            # Execute update
            result = await self.collection.update_one(filter_query, update)
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked task {task_id} as completed")
            else:
                logger.warning(f"Failed to mark task {task_id} as completed")
                
            return success
            
        except Exception as e:
            logger.error(f"Error marking task {task_id} as completed: {str(e)}")
            return False
    
    async def mark_task_failed(self, 
                             task_id: str,
                             error: str,
                             processor_id: str = None) -> bool:
        """
        Mark a task as failed with error information.
        
        Args:
            task_id: Task ID
            error: Error message
            processor_id: Optional processor ID for verification
            
        Returns:
            True if successful, False otherwise
        """
        await self.ensure_connected()
        
        try:
            # Find by ObjectId or task_id
            if ObjectId.is_valid(task_id):
                filter_query = {"_id": ObjectId(task_id)}
            else:
                filter_query = {"task_id": task_id}
            
            # Verify processor if provided
            if processor_id:
                filter_query["processor_id"] = processor_id
            
            # Update document
            now = datetime.utcnow()
            update = {
                "$set": {
                    "status": TaskStatus.FAILED.value,
                    "error": error,
                    "completed_at": now,
                    "updated_at": now
                }
            }
            
            # Execute update
            result = await self.collection.update_one(filter_query, update)
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Marked task {task_id} as failed: {error}")
            else:
                logger.warning(f"Failed to mark task {task_id} as failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Error marking task {task_id} as failed: {str(e)}")
            return False 