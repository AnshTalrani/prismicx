"""
Tenant Service for the Tenant Management Service.

This module provides business logic for tenant management operations,
including CRUD operations, tenant provisioning, and database assignment.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models import Tenant, TenantCreate, TenantUpdate, TenantStatus, DatabaseConfig, DatabaseType

# Configure logging
logger = logging.getLogger(__name__)

class TenantService:
    """Service for tenant management operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the tenant service.
        
        Args:
            db: The database connection.
        """
        self.db = db
        self.collection = db.tenants
    
    async def create_tenant(self, tenant: TenantCreate) -> Dict[str, Any]:
        """
        Create a new tenant.
        
        Args:
            tenant: The tenant to create.
            
        Returns:
            The created tenant.
        """
        # Prepare tenant document
        tenant_doc = {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "database_config": tenant.database_config.dict() if tenant.database_config else self._generate_default_db_config(tenant.tenant_id),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": TenantStatus.PROVISIONING,
            "settings": tenant.settings or {},
            "tier": tenant.tier,
            "region": tenant.region
        }
        
        # Insert tenant
        await self.collection.insert_one(tenant_doc)
        
        # Fetch the created tenant
        created_tenant = await self.collection.find_one({"tenant_id": tenant.tenant_id})
        logger.info(f"Created tenant: {tenant.tenant_id}")
        
        return created_tenant
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            The tenant if found, None otherwise.
        """
        tenant = await self.collection.find_one({"tenant_id": tenant_id})
        return tenant
    
    async def list_tenants(
        self,
        filters: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List tenants with optional filtering.
        
        Args:
            filters: Optional filters to apply.
            skip: Number of tenants to skip.
            limit: Maximum number of tenants to return.
            
        Returns:
            List of tenants.
        """
        cursor = self.collection.find(filters or {}).skip(skip).limit(limit)
        tenants = await cursor.to_list(length=limit)
        return tenants
    
    async def update_tenant(self, tenant_id: str, tenant_update: TenantUpdate) -> Dict[str, Any]:
        """
        Update a tenant.
        
        Args:
            tenant_id: The tenant ID.
            tenant_update: The tenant update data.
            
        Returns:
            The updated tenant.
        """
        # Prepare update document
        update_doc = {
            "updated_at": datetime.utcnow()
        }
        
        # Add fields from tenant_update
        if tenant_update.name is not None:
            update_doc["name"] = tenant_update.name
        
        if tenant_update.database_config is not None:
            update_doc["database_config"] = tenant_update.database_config.dict()
        
        if tenant_update.settings is not None:
            update_doc["settings"] = tenant_update.settings
        
        if tenant_update.status is not None:
            update_doc["status"] = tenant_update.status
        
        if tenant_update.tier is not None:
            update_doc["tier"] = tenant_update.tier
        
        if tenant_update.region is not None:
            update_doc["region"] = tenant_update.region
        
        # Update tenant
        await self.collection.update_one(
            {"tenant_id": tenant_id},
            {"$set": update_doc}
        )
        
        # Fetch the updated tenant
        updated_tenant = await self.collection.find_one({"tenant_id": tenant_id})
        logger.info(f"Updated tenant: {tenant_id}")
        
        return updated_tenant
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            True if deleted, False otherwise.
        """
        result = await self.collection.delete_one({"tenant_id": tenant_id})
        success = result.deleted_count > 0
        
        if success:
            logger.info(f"Deleted tenant: {tenant_id}")
        else:
            logger.warning(f"Failed to delete tenant: {tenant_id}")
        
        return success
    
    async def provision_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """
        Provision a tenant's database resources.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            The provisioned tenant.
        """
        # In a real implementation, this would:
        # 1. Create database schema/collections for the tenant
        # 2. Set up indexes
        # 3. Initialize default data
        # 4. Configure access controls
        
        # For this example, we just update the status
        tenant = await self.get_tenant(tenant_id)
        
        if not tenant:
            logger.error(f"Tenant not found for provisioning: {tenant_id}")
            return None
        
        # Update status to active
        await self.collection.update_one(
            {"tenant_id": tenant_id},
            {
                "$set": {
                    "status": TenantStatus.ACTIVE,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Register the tenant with its database
        db_config = tenant["database_config"]
        
        # For shared databases, add this tenant to the list
        if db_config["type"] == DatabaseType.SHARED:
            await self.db.tenant_databases.update_one(
                {"database_name": db_config["database_name"]},
                {"$addToSet": {"tenants": tenant_id}}
            )
        
        logger.info(f"Provisioned tenant: {tenant_id}")
        
        # Return the updated tenant
        return await self.get_tenant(tenant_id)
    
    def _generate_default_db_config(self, tenant_id: str) -> Dict[str, Any]:
        """
        Generate a default database configuration for a tenant.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            Default database configuration.
        """
        # For this example, we'll use a shared database by default
        return {
            "type": DatabaseType.SHARED,
            "connection_string": "mongodb://admin:password@mongodb-tenant:27017",
            "database_name": "shared_tenant_db",
            "shard_key": tenant_id
        } 