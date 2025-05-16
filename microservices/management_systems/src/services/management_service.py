"""
Service for managing business systems and their data.
"""
import logging
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from pathlib import Path
from bson.objectid import ObjectId

# Add database-layer to Python path
db_layer_path = Path(__file__).parent.parent.parent.parent.parent / "database-layer"
sys.path.append(str(db_layer_path))

from common.db_client import db_client
from ..models.management_system import (
    ManagementSystem,
    SystemInstance,
    DataView,
    SystemType,
    UserSystemPermission,
    CacheConfig,
    DataItem,
    PaginatedResponse
)
from ..data.system_templates import get_system_template, get_all_system_templates
from ..cache.redis_cache import cache
from ..common.db_client_wrapper import TenantDatabaseError, ConfigDatabaseError, DatabaseClientError
from .management_system_repo_service import (
    get_management_system_repo_service,
    ManagementSystemRepoError,
    TemplateNotFoundError,
    SystemNotFoundError,
    InstanceNotFoundError
)

logger = logging.getLogger(__name__)

class ManagementServiceError(Exception):
    """Base exception for management service errors."""
    pass

class ManagementService:
    """Service for business system management."""
    
    def __init__(self):
        """Initialize the management service."""
        self.repo_service = get_management_system_repo_service()
        logger.info("Management service initialized")
    
    async def initialize(self) -> None:
        """
        Initialize service connections and ensure system templates exist.
        
        Raises:
            ManagementServiceError: If initialization fails
        """
        try:
            # Initialize the repository service
            await self.repo_service.initialize()
            
            logger.info("Management service initialized successfully")
        except ManagementSystemRepoError as e:
            error_msg = f"Failed to initialize management service: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize management service: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def get_management_systems(self) -> List[ManagementSystem]:
        """
        Get all available management systems.
        
        Returns:
            List of management system definitions
            
        Raises:
            ManagementServiceError: If retrieval fails
        """
        try:
            return await self.repo_service.get_management_systems()
        except ManagementSystemRepoError as e:
            error_msg = f"Error retrieving management systems: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error retrieving management systems: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def get_management_system(self, system_id: str) -> Optional[ManagementSystem]:
        """
        Get a specific management system.
        
        Args:
            system_id: System identifier
            
        Returns:
            ManagementSystem or None if not found
            
        Raises:
            ManagementServiceError: If retrieval fails
        """
        try:
            return await self.repo_service.get_management_system(system_id)
        except ManagementSystemRepoError as e:
            error_msg = f"Error retrieving management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error retrieving management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def create_management_system(self, system_data: Dict[str, Any]) -> ManagementSystem:
        """
        Create a new management system.
        
        Args:
            system_data: System definition data
            
        Returns:
            Created ManagementSystem
            
        Raises:
            ManagementServiceError: If creation fails
        """
        try:
            return await self.repo_service.create_management_system(system_data)
        except ManagementSystemRepoError as e:
            error_msg = f"Error creating management system: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error creating management system: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def create_system_from_template(
        self, 
        template_id: str, 
        custom_data: Optional[Dict[str, Any]] = None
    ) -> ManagementSystem:
        """
        Create a new management system from a template.
        
        Args:
            template_id: System template ID
            custom_data: Custom data to override template values
            
        Returns:
            Created ManagementSystem
            
        Raises:
            TemplateNotFoundError: If template is not found
            ManagementServiceError: If system creation fails
        """
        try:
            return await self.repo_service.create_system_from_template(template_id, custom_data)
        except TemplateNotFoundError:
            # Re-raise template errors
            raise
        except ManagementSystemRepoError as e:
            error_msg = f"Error creating system from template {template_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error creating system from template {template_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def update_management_system(
        self,
        system_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a management system.
        
        Args:
            system_id: System identifier
            updates: Updates to apply
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ManagementServiceError: If update fails
        """
        try:
            return await self.repo_service.update_management_system(system_id, updates)
        except ManagementSystemRepoError as e:
            error_msg = f"Error updating management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error updating management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def delete_management_system(self, system_id: str) -> bool:
        """
        Delete a management system.
        
        Args:
            system_id: System identifier
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ManagementServiceError: If deletion fails
        """
        try:
            return await self.repo_service.delete_management_system(system_id)
        except ManagementSystemRepoError as e:
            error_msg = f"Error deleting management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error deleting management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def get_tenant_systems(self, tenant_id: str) -> List[SystemInstance]:
        """
        Get all system instances for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            List of system instances
            
        Raises:
            ManagementServiceError: If retrieval fails
        """
        try:
            return await self.repo_service.get_tenant_systems(tenant_id)
        except ManagementSystemRepoError as e:
            error_msg = f"Error retrieving tenant systems for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error retrieving tenant systems for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def get_system_instance(self, tenant_id: str, instance_id: str) -> Optional[SystemInstance]:
        """
        Get a specific system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            
        Returns:
            SystemInstance or None if not found
            
        Raises:
            ManagementServiceError: If retrieval fails
        """
        try:
            return await self.repo_service.get_system_instance(tenant_id, instance_id)
        except ManagementSystemRepoError as e:
            error_msg = f"Error retrieving system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error retrieving system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def create_system_instance(
        self,
        tenant_id: str,
        system_id: str, 
        name: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> SystemInstance:
        """
        Create a new system instance for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            system_id: System identifier
            name: Instance name
            settings: Instance settings
            
        Returns:
            Created SystemInstance
            
        Raises:
            SystemNotFoundError: If system is not found
            ManagementServiceError: If creation fails
        """
        try:
            return await self.repo_service.create_system_instance(
                tenant_id=tenant_id,
                system_id=system_id,
                name=name,
                settings=settings
            )
        except SystemNotFoundError:
            # Re-raise system errors
            raise
        except ManagementSystemRepoError as e:
            error_msg = f"Error creating system instance for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error creating system instance for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def update_system_instance(
        self,
        tenant_id: str,
        instance_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            updates: Updates to apply
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ManagementServiceError: If update fails
        """
        try:
            return await self.repo_service.update_system_instance(tenant_id, instance_id, updates)
        except ManagementSystemRepoError as e:
            error_msg = f"Error updating system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error updating system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def delete_system_instance(self, tenant_id: str, instance_id: str) -> bool:
        """
        Delete a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ManagementServiceError: If deletion fails
        """
        try:
            return await self.repo_service.delete_system_instance(tenant_id, instance_id)
        except ManagementSystemRepoError as e:
            error_msg = f"Error deleting system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error deleting system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def get_system_data(
        self,
        tenant_id: str,
        instance_id: str,
        view_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedResponse:
        """
        Get data for a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            view_id: View identifier
            filters: Data filters
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated response with data items
            
        Raises:
            InstanceNotFoundError: If instance is not found
            ManagementServiceError: If retrieval fails
        """
        try:
            return await self.repo_service.get_system_data(
                tenant_id=tenant_id,
                instance_id=instance_id,
                view_id=view_id,
                filters=filters,
                page=page,
                page_size=page_size
            )
        except InstanceNotFoundError:
            # Re-raise instance errors
            raise
        except ManagementSystemRepoError as e:
            error_msg = f"Error retrieving system data for instance {instance_id}, tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error retrieving system data for instance {instance_id}, tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
    
    async def create_data_item(
        self,
        tenant_id: str,
        instance_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new data item in a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            data: Item data
            
        Returns:
            Created item data
            
        Raises:
            InstanceNotFoundError: If instance is not found
            ManagementServiceError: If creation fails
        """
        try:
            return await self.repo_service.create_data_item(tenant_id, instance_id, data)
        except InstanceNotFoundError:
            # Re-raise instance errors
            raise
        except ManagementSystemRepoError as e:
            error_msg = f"Error creating data item for instance {instance_id}, tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error creating data item for instance {instance_id}, tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementServiceError(error_msg) from e

# Global instance of the management service
management_service = ManagementService() 