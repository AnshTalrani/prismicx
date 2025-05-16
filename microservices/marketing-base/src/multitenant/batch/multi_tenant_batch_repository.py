"""
Multi-Tenant Batch Repository Module.

This module provides repository functionality for storing and retrieving
multi-tenant campaign batch data.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from ...config.app_config import get_config
from ...config.logging_config import get_logger
from .multi_tenant_batch import (
    MultiTenantCampaignBatch,
    MultiTenantBatchStatus,
    TenantExecutionResult,
    TenantExecutionStatus
)
from ...infrastructure.database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)


class MultiTenantBatchRepository:
    """Repository for multi-tenant campaign batch operations."""
    
    def __init__(self, collection_name: str = "multi_tenant_batches"):
        """
        Initialize the multi-tenant batch repository.
        
        Args:
            collection_name: Name of the MongoDB collection for multi-tenant batches
        """
        config = get_config()
        self.client = MongoClient(config.mongodb_uri)
        self.db = self.client[config.mongodb_database]
        self.collection_name = collection_name
        self._collection = self.db[collection_name]
        
        # Ensure indexes for efficient querying
        self._ensure_indexes()
        
    def _ensure_indexes(self):
        """Create necessary indexes on the collection."""
        try:
            self._collection.create_index("status")
            self._collection.create_index("created_at")
            self._collection.create_index("tenant_ids")
            logger.info(f"Created indexes for {self.collection_name} collection")
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
    
    async def close(self):
        """Close MongoDB connection and free resources."""
        try:
            if hasattr(self, 'client') and self.client:
                self.client.close()
                logger.info("Closed MongoDB connection for multi-tenant batch repository")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
    
    async def save(self, batch: MultiTenantCampaignBatch) -> str:
        """
        Save a multi-tenant campaign batch.
        
        Args:
            batch: The batch to save
            
        Returns:
            The batch ID
        """
        if not batch:
            logger.error("Cannot save None batch")
            raise ValueError("Batch cannot be None")
            
        # Convert to dictionary
        batch_dict = self._to_dict(batch)
        
        try:
            # Handle update or insert
            if "_id" in batch_dict:
                # Update existing batch
                result = self._collection.update_one(
                    {"_id": batch_dict["_id"]},
                    {"$set": batch_dict}
                )
                
                if result.modified_count > 0:
                    logger.debug(f"Updated batch {batch.id}")
                else:
                    logger.warning(f"Failed to update batch {batch.id}")
            else:
                # Insert new batch
                result = self._collection.insert_one(batch_dict)
                batch.id = str(result.inserted_id)
                logger.debug(f"Inserted new batch {batch.id}")
            
            return batch.id
        except Exception as e:
            logger.error(f"Error saving batch: {str(e)}")
            raise
    
    async def get_by_id(self, batch_id: str) -> Optional[MultiTenantCampaignBatch]:
        """
        Get a multi-tenant campaign batch by ID.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            The batch or None if not found
        """
        if not batch_id:
            logger.error("Cannot get batch with None ID")
            return None
            
        try:
            # Convert string ID to ObjectId if needed
            query_id = batch_id
            if not isinstance(batch_id, ObjectId) and ObjectId.is_valid(batch_id):
                query_id = ObjectId(batch_id)
                
            batch_dict = self._collection.find_one({"_id": query_id})
            
            if not batch_dict:
                logger.debug(f"Batch {batch_id} not found")
                return None
                
            return self._from_dict(batch_dict)
        except Exception as e:
            logger.error(f"Error getting batch {batch_id}: {str(e)}")
            return None
    
    async def get_pending_batches(self, limit: int = 5) -> List[MultiTenantCampaignBatch]:
        """
        Get pending multi-tenant campaign batches.
        
        Args:
            limit: Maximum number of batches to retrieve
            
        Returns:
            List of pending batches
        """
        try:
            pending_batches = []
            
            cursor = self._collection.find({
                "status": {"$in": ["created", "queued"]}
            }).sort("created_at", 1).limit(limit)
            
            for batch_dict in cursor:
                pending_batches.append(self._from_dict(batch_dict))
                
            logger.debug(f"Retrieved {len(pending_batches)} pending batches")
            return pending_batches
        except Exception as e:
            logger.error(f"Error getting pending batches: {str(e)}")
            return []
    
    async def update_batch_status(
        self, 
        batch_id: str, 
        new_status: MultiTenantBatchStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the status of a multi-tenant campaign batch.
        
        Args:
            batch_id: The batch ID
            new_status: The new status
            error_message: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        if not batch_id:
            logger.error("Cannot update status for None batch ID")
            return False
            
        try:
            # Convert string ID to ObjectId if needed
            query_id = batch_id
            if not isinstance(batch_id, ObjectId) and ObjectId.is_valid(batch_id):
                query_id = ObjectId(batch_id)
            
            update_data = {
                "status": new_status.value,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add timestamps based on status
            if new_status == MultiTenantBatchStatus.PROCESSING:
                update_data["started_at"] = datetime.utcnow().isoformat()
                
            if new_status in (
                MultiTenantBatchStatus.COMPLETED, 
                MultiTenantBatchStatus.FAILED, 
                MultiTenantBatchStatus.CANCELLED
            ):
                update_data["completed_at"] = datetime.utcnow().isoformat()
            
            # Add error message if provided
            if error_message and new_status == MultiTenantBatchStatus.FAILED:
                update_data["last_error"] = error_message
                update_data["error_count"] = 1  # Will be incremented by MongoDB
            
            result = self._collection.update_one(
                {"_id": query_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.debug(f"Updated batch {batch_id} status to {new_status.value}")
            else:
                logger.warning(f"Failed to update batch {batch_id} status")
                
            return success
        except Exception as e:
            logger.error(f"Error updating batch status: {str(e)}")
            return False
    
    async def update_tenant_result(
        self, 
        batch_id: str, 
        tenant_id: str, 
        result: TenantExecutionResult
    ) -> bool:
        """
        Update the result for a specific tenant in a batch.
        
        Args:
            batch_id: The batch ID
            tenant_id: The tenant ID
            result: The execution result
            
        Returns:
            True if successful, False otherwise
        """
        if not batch_id or not tenant_id or not result:
            logger.error("Missing required parameters for updating tenant result")
            return False
            
        try:
            # Convert string ID to ObjectId if needed
            query_id = batch_id
            if not isinstance(batch_id, ObjectId) and ObjectId.is_valid(batch_id):
                query_id = ObjectId(batch_id)
            
            # Convert result to dictionary
            result_dict = {
                "status": result.status.value,
                "processed_count": result.processed_count,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if result.campaign_id:
                result_dict["campaign_id"] = result.campaign_id
                
            if result.error_message:
                result_dict["error_message"] = result.error_message
                
            if result.started_at:
                result_dict["started_at"] = result.started_at.isoformat()
                
            if result.completed_at:
                result_dict["completed_at"] = result.completed_at.isoformat()
            
            # Add custom attributes if present
            if result.custom_attributes:
                result_dict["custom_attributes"] = result.custom_attributes
            
            # Update the tenant result
            update_result = self._collection.update_one(
                {"_id": query_id},
                {
                    "$set": {
                        f"tenant_results.{tenant_id}": result_dict,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            success = update_result.modified_count > 0
            if success:
                logger.debug(f"Updated tenant {tenant_id} result for batch {batch_id}")
            else:
                logger.warning(f"Failed to update tenant {tenant_id} result for batch {batch_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error updating tenant result: {str(e)}")
            return False
    
    async def delete(self, batch_id: str) -> bool:
        """
        Delete a multi-tenant campaign batch.
        
        Args:
            batch_id: The batch ID
            
        Returns:
            True if successful, False otherwise
        """
        if not batch_id:
            logger.error("Cannot delete batch with None ID")
            return False
            
        try:
            # Convert string ID to ObjectId if needed
            query_id = batch_id
            if not isinstance(batch_id, ObjectId) and ObjectId.is_valid(batch_id):
                query_id = ObjectId(batch_id)
                
            result = self._collection.delete_one({"_id": query_id})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted batch {batch_id}")
            else:
                logger.warning(f"Failed to delete batch {batch_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error deleting batch {batch_id}: {str(e)}")
            return False
    
    def _to_dict(self, batch: MultiTenantCampaignBatch) -> Dict[str, Any]:
        """Convert a MultiTenantCampaignBatch to a dictionary for MongoDB storage."""
        batch_dict = {
            "name": batch.name,
            "description": batch.description,
            "campaign_template": batch.campaign_template,
            "status": batch.status.value,
            "tenant_ids": batch.tenant_ids,
            "current_tenant_index": batch.current_tenant_index,
            "error_count": batch.error_count,
            "max_retries": batch.max_retries,
            "retry_count": batch.retry_count,
            "created_at": batch.created_at.isoformat(),
            "updated_at": batch.updated_at.isoformat(),
            "tags": batch.tags,
            "custom_attributes": batch.custom_attributes
        }
        
        # Add optional fields if present
        if batch.id and ObjectId.is_valid(batch.id):
            batch_dict["_id"] = ObjectId(batch.id)
        elif batch.id:
            batch_dict["_id"] = batch.id
            
        if batch.started_at:
            batch_dict["started_at"] = batch.started_at.isoformat()
            
        if batch.completed_at:
            batch_dict["completed_at"] = batch.completed_at.isoformat()
            
        if batch.last_error:
            batch_dict["last_error"] = batch.last_error
        
        # Convert tenant results to dictionary
        tenant_results = {}
        for tenant_id, result in batch.tenant_results.items():
            tenant_results[tenant_id] = {
                "status": result.status.value,
                "processed_count": result.processed_count,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "custom_attributes": result.custom_attributes
            }
            
            if result.campaign_id:
                tenant_results[tenant_id]["campaign_id"] = result.campaign_id
                
            if result.error_message:
                tenant_results[tenant_id]["error_message"] = result.error_message
                
            if result.started_at:
                tenant_results[tenant_id]["started_at"] = result.started_at.isoformat()
                
            if result.completed_at:
                tenant_results[tenant_id]["completed_at"] = result.completed_at.isoformat()
        
        if tenant_results:
            batch_dict["tenant_results"] = tenant_results
            
        return batch_dict
    
    def _from_dict(self, batch_dict: Dict[str, Any]) -> MultiTenantCampaignBatch:
        """Convert a dictionary from MongoDB to a MultiTenantCampaignBatch."""
        # Convert _id to string
        if "_id" in batch_dict:
            batch_dict["id"] = str(batch_dict["_id"])
            del batch_dict["_id"]
            
        # Convert timestamps
        for timestamp_field in ["created_at", "updated_at", "started_at", "completed_at"]:
            if timestamp_field in batch_dict and batch_dict[timestamp_field]:
                if isinstance(batch_dict[timestamp_field], str):
                    try:
                        batch_dict[timestamp_field] = datetime.fromisoformat(batch_dict[timestamp_field])
                    except ValueError:
                        logger.warning(f"Invalid timestamp format for {timestamp_field}: {batch_dict[timestamp_field]}")
        
        # Convert tenant results
        if "tenant_results" in batch_dict:
            tenant_results = {}
            for tenant_id, result in batch_dict["tenant_results"].items():
                try:
                    result["tenant_id"] = tenant_id
                    tenant_results[tenant_id] = TenantExecutionResult.from_dict(result)
                except Exception as e:
                    logger.error(f"Error converting tenant result for {tenant_id}: {str(e)}")
            batch_dict["tenant_results"] = tenant_results
        
        try:
            return MultiTenantCampaignBatch.from_dict(batch_dict)
        except Exception as e:
            logger.error(f"Error creating MultiTenantCampaignBatch from dict: {str(e)}")
            # Create a minimal valid batch to avoid returning None
            return MultiTenantCampaignBatch(
                id=batch_dict.get("id", str(uuid.uuid4())),
                name=batch_dict.get("name", "Error Batch")
            ) 