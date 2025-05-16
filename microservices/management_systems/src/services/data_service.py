"""
Service for handling data operations for management systems.
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from bson.objectid import ObjectId

from ..common.db_client_wrapper import db_client, TenantDatabaseError
from ..models.management_system import DataItem, PaginatedResponse
from ..services.management_service import (
    management_service,
    ManagementServiceError,
    InstanceNotFoundError,
    SystemNotFoundError
)
from ..cache.redis_cache import cache

logger = logging.getLogger(__name__)

class DataServiceError(Exception):
    """Base exception for data service errors."""
    pass

class DataValidationError(DataServiceError):
    """Exception raised when data validation fails."""
    pass

class DataItemNotFoundError(DataServiceError):
    """Exception raised when a data item is not found."""
    pass

class DataService:
    """Service for data operations in management systems."""
    
    async def validate_data(self, system_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate data against system field definitions.
        
        Args:
            system_id: System identifier
            data: Data to validate
            
        Returns:
            Dictionary of validation errors, empty if valid
            
        Raises:
            SystemNotFoundError: If system is not found
            ManagementServiceError: If system retrieval fails
        """
        errors = {}
        
        try:
            # Get system definition
            system = await management_service.get_management_system(system_id)
            if not system:
                raise SystemNotFoundError(f"System {system_id} not found")
            
            # Check required fields
            for field in system.fields:
                if field.required and field.id not in data:
                    errors[field.id] = "This field is required"
                    continue
                
                # Skip validation if field is not present and not required
                if field.id not in data:
                    continue
                    
                value = data[field.id]
                
                # Type validation
                if field.type == "string" and not isinstance(value, str):
                    errors[field.id] = "Must be a string"
                elif field.type == "number" and not isinstance(value, (int, float)):
                    errors[field.id] = "Must be a number"
                elif field.type == "boolean" and not isinstance(value, bool):
                    errors[field.id] = "Must be a boolean"
                elif field.type == "date" and not isinstance(value, (datetime, str)):
                    errors[field.id] = "Must be a valid date"
                elif field.type == "object" and not isinstance(value, dict):
                    errors[field.id] = "Must be an object"
                elif field.type == "array" and not isinstance(value, list):
                    errors[field.id] = "Must be an array"
            
            return errors
        except SystemNotFoundError:
            # Re-raise system not found error
            raise
        except ManagementServiceError as e:
            logger.error(f"Error retrieving system {system_id} for validation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error validating data for system {system_id}: {str(e)}")
            errors["_general"] = f"Validation error: {str(e)}"
            return errors
    
    async def get_data_items(
        self,
        tenant_id: str,
        instance_id: str,
        view_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedResponse:
        """
        Get data items for a system instance.
        
        This is a wrapper around management_service.get_system_data
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            view_id: Optional view identifier to use
            filters: Additional filters to apply
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse with data items
            
        Raises:
            InstanceNotFoundError: If instance is not found
            SystemNotFoundError: If system is not found
            TenantDatabaseError: If tenant database operations fail
            DataServiceError: If other errors occur
        """
        try:
            return await management_service.get_system_data(
                tenant_id,
                instance_id,
                view_id=view_id,
                filters=filters,
                page=page,
                page_size=page_size
            )
        except (InstanceNotFoundError, SystemNotFoundError, TenantDatabaseError) as e:
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Error retrieving data for instance {instance_id}: {str(e)}"
            logger.error(error_msg)
            raise DataServiceError(error_msg) from e
    
    async def get_data_item(
        self,
        tenant_id: str,
        instance_id: str,
        item_id: str
    ) -> DataItem:
        """
        Get a specific data item.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            item_id: Item identifier
            
        Returns:
            DataItem
            
        Raises:
            InstanceNotFoundError: If instance is not found
            SystemNotFoundError: If system is not found
            DataItemNotFoundError: If item is not found
            TenantDatabaseError: If tenant database operations fail
            DataServiceError: If other errors occur
        """
        try:
            # Get system instance
            instance = await management_service.get_system_instance(tenant_id, instance_id)
            if not instance:
                raise InstanceNotFoundError(f"System instance {instance_id} not found for tenant {tenant_id}")
                
            # Get system definition
            system = await management_service.get_management_system(instance.system_id)
            if not system:
                raise SystemNotFoundError(f"System definition {instance.system_id} not found")
            
            # Connect to tenant database
            try:
                tenant_db = await db_client.get_tenant_db(tenant_id)
            except TenantDatabaseError as e:
                logger.error(f"Failed to connect to tenant database for {tenant_id}: {str(e)}")
                raise
            
            # Get collection
            collection_name = f"system_{system.id}"
            collection = tenant_db[collection_name]
            
            # Convert string ID to ObjectId for MongoDB
            try:
                object_id = ObjectId(item_id)
            except:
                raise DataItemNotFoundError(f"Invalid item ID format: {item_id}")
            
            # Get item
            item_data = await collection.find_one({"_id": object_id})
            if not item_data:
                raise DataItemNotFoundError(f"Item {item_id} not found in {instance_id}")
            
            # Convert to DataItem
            item_id = str(item_data.pop("_id"))
            created_at = item_data.pop("created_at", datetime.utcnow())
            updated_at = item_data.pop("updated_at", None)
            
            return DataItem(
                id=item_id,
                data=item_data,
                created_at=created_at,
                updated_at=updated_at
            )
        except (InstanceNotFoundError, SystemNotFoundError, DataItemNotFoundError, TenantDatabaseError):
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Error retrieving data item {item_id}: {str(e)}"
            logger.error(error_msg)
            raise DataServiceError(error_msg) from e
    
    async def create_data_item(
        self,
        tenant_id: str,
        instance_id: str,
        data: Dict[str, Any]
    ) -> DataItem:
        """
        Create a new data item.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            data: Item data
            
        Returns:
            Created DataItem
            
        Raises:
            InstanceNotFoundError: If instance is not found
            SystemNotFoundError: If system is not found
            DataValidationError: If data validation fails
            TenantDatabaseError: If tenant database operations fail
            DataServiceError: If other errors occur
        """
        try:
            # Get system instance
            instance = await management_service.get_system_instance(tenant_id, instance_id)
            if not instance:
                raise InstanceNotFoundError(f"System instance {instance_id} not found for tenant {tenant_id}")
                
            # Get system definition
            system = await management_service.get_management_system(instance.system_id)
            if not system:
                raise SystemNotFoundError(f"System definition {instance.system_id} not found")
            
            # Validate data
            validation_errors = await self.validate_data(system.id, data)
            if validation_errors:
                raise DataValidationError(f"Data validation failed: {validation_errors}")
            
            # Apply default values for missing fields
            for field in system.fields:
                if field.id not in data and field.default is not None:
                    data[field.id] = field.default
            
            # Connect to tenant database
            try:
                tenant_db = await db_client.get_tenant_db(tenant_id)
            except TenantDatabaseError as e:
                logger.error(f"Failed to connect to tenant database for {tenant_id}: {str(e)}")
                raise
            
            # Add metadata
            now = datetime.utcnow()
            item_data = {
                **data,
                "created_at": now,
                "updated_at": now
            }
            
            # Insert into collection
            collection_name = f"system_{system.id}"
            collection = tenant_db[collection_name]
            result = await collection.insert_one(item_data)
            
            if not result.inserted_id:
                raise DataServiceError("Failed to insert data item")
            
            # Clear cache for this instance's data
            await cache.clear_pattern(f"data:{tenant_id}:{instance_id}:*")
            
            # Return created item
            return DataItem(
                id=str(result.inserted_id),
                data=data,
                created_at=now,
                updated_at=now
            )
        except (InstanceNotFoundError, SystemNotFoundError, DataValidationError, TenantDatabaseError):
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Error creating data item: {str(e)}"
            logger.error(error_msg)
            raise DataServiceError(error_msg) from e
    
    async def update_data_item(
        self,
        tenant_id: str,
        instance_id: str,
        item_id: str,
        updates: Dict[str, Any]
    ) -> DataItem:
        """
        Update a data item.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            item_id: Item identifier
            updates: Fields to update
            
        Returns:
            Updated DataItem
            
        Raises:
            InstanceNotFoundError: If instance is not found
            SystemNotFoundError: If system is not found
            DataItemNotFoundError: If item is not found
            DataValidationError: If data validation fails
            TenantDatabaseError: If tenant database operations fail
            DataServiceError: If other errors occur
        """
        try:
            # Get system instance
            instance = await management_service.get_system_instance(tenant_id, instance_id)
            if not instance:
                raise InstanceNotFoundError(f"System instance {instance_id} not found for tenant {tenant_id}")
                
            # Get system definition
            system = await management_service.get_management_system(instance.system_id)
            if not system:
                raise SystemNotFoundError(f"System definition {instance.system_id} not found")
            
            # Get current item to merge with updates
            current_item = await self.get_data_item(tenant_id, instance_id, item_id)
            
            # Merge updates with current data
            merged_data = {**current_item.data, **updates}
            
            # Validate merged data
            validation_errors = await self.validate_data(system.id, merged_data)
            if validation_errors:
                raise DataValidationError(f"Data validation failed: {validation_errors}")
            
            # Connect to tenant database
            try:
                tenant_db = await db_client.get_tenant_db(tenant_id)
            except TenantDatabaseError as e:
                logger.error(f"Failed to connect to tenant database for {tenant_id}: {str(e)}")
                raise
            
            # Add updated timestamp
            now = datetime.utcnow()
            updates["updated_at"] = now
            
            # Update item
            collection_name = f"system_{system.id}"
            collection = tenant_db[collection_name]
            
            # Convert string ID to ObjectId for MongoDB
            try:
                object_id = ObjectId(item_id)
            except:
                raise DataItemNotFoundError(f"Invalid item ID format: {item_id}")
            
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                # Check if item exists
                if await collection.count_documents({"_id": object_id}) == 0:
                    raise DataItemNotFoundError(f"Item {item_id} not found")
                # Item exists but wasn't modified (no changes)
                logger.debug(f"Item {item_id} not modified (no changes)")
            
            # Clear cache for this instance's data
            await cache.clear_pattern(f"data:{tenant_id}:{instance_id}:*")
            
            # Return updated item
            return DataItem(
                id=item_id,
                data=merged_data,
                created_at=current_item.created_at,
                updated_at=now
            )
        except (InstanceNotFoundError, SystemNotFoundError, DataItemNotFoundError, 
                DataValidationError, TenantDatabaseError):
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Error updating data item {item_id}: {str(e)}"
            logger.error(error_msg)
            raise DataServiceError(error_msg) from e
    
    async def delete_data_item(
        self,
        tenant_id: str,
        instance_id: str,
        item_id: str
    ) -> bool:
        """
        Delete a data item.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            item_id: Item identifier
            
        Returns:
            True if deleted
            
        Raises:
            InstanceNotFoundError: If instance is not found
            SystemNotFoundError: If system is not found
            DataItemNotFoundError: If item is not found
            TenantDatabaseError: If tenant database operations fail
            DataServiceError: If other errors occur
        """
        try:
            # Get system instance
            instance = await management_service.get_system_instance(tenant_id, instance_id)
            if not instance:
                raise InstanceNotFoundError(f"System instance {instance_id} not found for tenant {tenant_id}")
                
            # Get system definition
            system = await management_service.get_management_system(instance.system_id)
            if not system:
                raise SystemNotFoundError(f"System definition {instance.system_id} not found")
            
            # Connect to tenant database
            try:
                tenant_db = await db_client.get_tenant_db(tenant_id)
            except TenantDatabaseError as e:
                logger.error(f"Failed to connect to tenant database for {tenant_id}: {str(e)}")
                raise
            
            # Delete item
            collection_name = f"system_{system.id}"
            collection = tenant_db[collection_name]
            
            # Convert string ID to ObjectId for MongoDB
            try:
                object_id = ObjectId(item_id)
            except:
                raise DataItemNotFoundError(f"Invalid item ID format: {item_id}")
            
            result = await collection.delete_one({"_id": object_id})
            
            if result.deleted_count == 0:
                raise DataItemNotFoundError(f"Item {item_id} not found")
            
            # Clear cache for this instance's data
            await cache.clear_pattern(f"data:{tenant_id}:{instance_id}:*")
            
            logger.info(f"Deleted data item {item_id} from instance {instance_id}")
            return True
        except (InstanceNotFoundError, SystemNotFoundError, DataItemNotFoundError, TenantDatabaseError):
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Error deleting data item {item_id}: {str(e)}"
            logger.error(error_msg)
            raise DataServiceError(error_msg) from e
    
    async def bulk_import_data(
        self,
        tenant_id: str,
        instance_id: str,
        items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk import data items.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            items: List of data items to import
            
        Returns:
            Dict with import results
            
        Raises:
            InstanceNotFoundError: If instance is not found
            SystemNotFoundError: If system is not found
            DataValidationError: If data validation fails
            TenantDatabaseError: If tenant database operations fail
            DataServiceError: If other errors occur
        """
        validation_errors = []
        
        try:
            # Get system instance
            instance = await management_service.get_system_instance(tenant_id, instance_id)
            if not instance:
                raise InstanceNotFoundError(f"System instance {instance_id} not found for tenant {tenant_id}")
                
            # Get system definition
            system = await management_service.get_management_system(instance.system_id)
            if not system:
                raise SystemNotFoundError(f"System definition {instance.system_id} not found")
            
            # Validate all items
            for i, item_data in enumerate(items):
                errors = await self.validate_data(system.id, item_data)
                if errors:
                    validation_errors.append({
                        "index": i,
                        "errors": errors
                    })
            
            # If validation errors, return them
            if validation_errors:
                return {
                    "success": False,
                    "errors": validation_errors,
                    "message": "Validation failed for some items"
                }
            
            # Prepare items for insert
            now = datetime.utcnow()
            items_to_insert = []
            
            for item_data in items:
                # Apply default values for missing fields
                for field in system.fields:
                    if field.id not in item_data and field.default is not None:
                        item_data[field.id] = field.default
                
                # Add metadata
                item_data["created_at"] = now
                item_data["updated_at"] = now
                items_to_insert.append(item_data)
            
            # Connect to tenant database
            try:
                tenant_db = await db_client.get_tenant_db(tenant_id)
            except TenantDatabaseError as e:
                logger.error(f"Failed to connect to tenant database for {tenant_id}: {str(e)}")
                raise
            
            # Insert into collection
            collection_name = f"system_{system.id}"
            collection = tenant_db[collection_name]
            result = await collection.insert_many(items_to_insert)
            
            # Clear cache for this instance's data
            await cache.clear_pattern(f"data:{tenant_id}:{instance_id}:*")
            
            logger.info(f"Bulk imported {len(result.inserted_ids)} items for instance {instance_id}")
            
            return {
                "success": True,
                "imported_count": len(result.inserted_ids),
                "total_items": len(items)
            }
        except (InstanceNotFoundError, SystemNotFoundError, TenantDatabaseError):
            # Re-raise known errors
            raise
        except Exception as e:
            error_msg = f"Error bulk importing data: {str(e)}"
            logger.error(error_msg)
            raise DataServiceError(error_msg) from e

# Global service instance
data_service = DataService() 