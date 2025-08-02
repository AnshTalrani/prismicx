"""
Database Service for the Tenant Management Service.

This module provides business logic for tenant database management operations,
including provisioning, monitoring, and tenant assignment.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models import TenantDatabaseCreate, TenantDatabaseUpdate, DatabaseStatus

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for tenant database management operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the database service.
        
        Args:
            db: The database connection.
        """
        self.db = db
        self.collection = db.tenant_databases
    
    async def create_database(self, database: TenantDatabaseCreate) -> Dict[str, Any]:
        """
        Create a new tenant database.
        
        Args:
            database: The database configuration to create.
            
        Returns:
            The created database.
        """
        # Prepare database document
        database_doc = {
            "database_name": database.database_name,
            "type": database.type,
            "tenants": database.tenants or [],
            "status": DatabaseStatus.PROVISIONING,
            "created_at": datetime.utcnow(),
            "server": database.server,
            "region": database.region
        }
        
        # Insert database
        await self.collection.insert_one(database_doc)
        
        # Fetch the created database
        created_db = await self.collection.find_one({"database_name": database.database_name})
        logger.info(f"Created database: {database.database_name}")
        
        # In a real implementation, you would:
        # 1. Provision the actual database on the server
        # 2. Create initial schema/collections
        # 3. Set up access controls
        # Then update the status once provisioning is complete
        
        # For this example, we'll just update the status
        await self.collection.update_one(
            {"database_name": database.database_name},
            {"$set": {"status": DatabaseStatus.ACTIVE}}
        )
        
        # Return the updated database
        return await self.collection.find_one({"database_name": database.database_name})
    
    async def get_database(self, database_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a database by name.
        
        Args:
            database_name: The database name.
            
        Returns:
            The database if found, None otherwise.
        """
        database = await self.collection.find_one({"database_name": database_name})
        return database
    
    async def list_databases(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List tenant databases with optional filtering.
        
        Args:
            filters: Optional filters to apply.
            skip: Number of databases to skip.
            limit: Maximum number of databases to return.
            
        Returns:
            List of databases.
        """
        cursor = self.collection.find(filters or {}).skip(skip).limit(limit)
        databases = await cursor.to_list(length=limit)
        return databases
    
    async def update_database(self, database_name: str, database_update: TenantDatabaseUpdate) -> Dict[str, Any]:
        """
        Update a database.
        
        Args:
            database_name: The database name.
            database_update: The database update data.
            
        Returns:
            The updated database.
        """
        # Prepare update document
        update_doc = {}
        
        # Add fields from database_update
        if database_update.tenants is not None:
            update_doc["tenants"] = database_update.tenants
        
        if database_update.status is not None:
            update_doc["status"] = database_update.status
        
        if database_update.server is not None:
            update_doc["server"] = database_update.server
        
        if database_update.region is not None:
            update_doc["region"] = database_update.region
        
        # Update database
        if update_doc:
            await self.collection.update_one(
                {"database_name": database_name},
                {"$set": update_doc}
            )
        
        # Fetch the updated database
        updated_database = await self.collection.find_one({"database_name": database_name})
        logger.info(f"Updated database: {database_name}")
        
        return updated_database
    
    async def mark_database_for_decommissioning(self, database_name: str) -> bool:
        """
        Mark a database for decommissioning.
        
        Args:
            database_name: The database name.
            
        Returns:
            True if marked, False otherwise.
        """
        # Update database status
        result = await self.collection.update_one(
            {"database_name": database_name},
            {"$set": {"status": DatabaseStatus.DECOMMISSIONING}}
        )
        
        success = result.modified_count > 0
        
        if success:
            logger.info(f"Marked database for decommissioning: {database_name}")
        else:
            logger.warning(f"Failed to mark database for decommissioning: {database_name}")
        
        # In a real implementation, you would:
        # 1. Schedule the database for decommissioning
        # 2. Archive data
        # 3. Clean up resources
        
        return success
    
    async def add_tenant_to_database(self, database_name: str, tenant_id: str) -> bool:
        """
        Add a tenant to a database.
        
        Args:
            database_name: The database name.
            tenant_id: The tenant ID to add.
            
        Returns:
            True if added, False otherwise.
        """
        # Add tenant to database
        result = await self.collection.update_one(
            {"database_name": database_name},
            {"$addToSet": {"tenants": tenant_id}}
        )
        
        success = result.modified_count > 0
        
        if success:
            logger.info(f"Added tenant {tenant_id} to database {database_name}")
        else:
            logger.warning(f"Failed to add tenant {tenant_id} to database {database_name}")
        
        # In a real implementation, you would:
        # 1. Provision the tenant schema/collections in the database
        # 2. Set up access controls
        # 3. Initialize default data
        
        return success
    
    async def remove_tenant_from_database(self, database_name: str, tenant_id: str) -> bool:
        """
        Remove a tenant from a database.
        
        Args:
            database_name: The database name.
            tenant_id: The tenant ID to remove.
            
        Returns:
            True if removed, False otherwise.
        """
        # Remove tenant from database
        result = await self.collection.update_one(
            {"database_name": database_name},
            {"$pull": {"tenants": tenant_id}}
        )
        
        success = result.modified_count > 0
        
        if success:
            logger.info(f"Removed tenant {tenant_id} from database {database_name}")
        else:
            logger.warning(f"Failed to remove tenant {tenant_id} from database {database_name}")
        
        # In a real implementation, you would:
        # 1. Archive tenant data
        # 2. Clean up tenant schema/collections
        # 3. Remove access controls
        
        return success 