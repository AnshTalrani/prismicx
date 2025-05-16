"""
Service for managing business systems and their data through the Management System Repository.

This service provides access to management system repository functionality
through HTTP API calls to the database layer service.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import lru_cache
import uuid

from ..clients.management_system_repo_client import ManagementSystemRepoClient
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

logger = logging.getLogger(__name__)

class ManagementSystemRepoError(Exception):
    """Base exception for management system repository errors."""
    pass

class TemplateNotFoundError(ManagementSystemRepoError):
    """Exception raised when a template is not found."""
    pass

class SystemNotFoundError(ManagementSystemRepoError):
    """Exception raised when a system is not found."""
    pass

class InstanceNotFoundError(ManagementSystemRepoError):
    """Exception raised when a system instance is not found."""
    pass

class ManagementSystemRepoService:
    """Service for managing business systems and their data through the Management System Repository."""
    
    def __init__(self, client: ManagementSystemRepoClient):
        """
        Initialize the management system repository service.
        
        Args:
            client: Client for interacting with the management-system-repo
        """
        self.client = client
        self._initialized = False
        logger.info("ManagementSystemRepoService initialized")
    
    async def initialize(self) -> None:
        """
        Initialize service connections and ensure system templates exist.
        
        Raises:
            ManagementSystemRepoError: If initialization fails
        """
        if self._initialized:
            return
            
        try:
            # Initialize the HTTP client
            await self.client.initialize()
            
            # Ensure system templates are loaded in the repository
            await self._ensure_system_templates()
            
            self._initialized = True
            logger.info("ManagementSystemRepoService initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize management system repository service: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def _ensure_system_templates(self) -> None:
        """
        Initialize default system templates if they don't exist.
        
        Raises:
            ManagementSystemRepoError: If template initialization fails
        """
        try:
            # Check if we have any templates defined
            template_count = await self.client.count_system_templates()
            
            if template_count == 0:
                logger.info("No management system templates found. Creating default templates.")
                templates = get_all_system_templates()
                
                # Create each template
                for template_data in templates:
                    # Create a ManagementSystem object to validate the data
                    template = ManagementSystem(**template_data)
                    template.is_template = True
                    
                    # Create the template in the repository
                    await self.client.create_system_template(template.dict())
                
                logger.info(f"Created {len(templates)} system templates")
                
                # Invalidate cache
                await cache.delete("systems:templates")
                logger.debug("Cache invalidated for systems:templates")
        except Exception as e:
            error_msg = f"Error ensuring system templates: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def get_management_systems(self) -> List[ManagementSystem]:
        """
        Get all available management systems.
        
        Returns:
            List of management system definitions
            
        Raises:
            ManagementSystemRepoError: If retrieval fails
        """
        cache_key = "systems:all"
        cached = await cache.get(cache_key)
        if cached:
            logger.debug("Returning cached management systems")
            return [ManagementSystem(**system) for system in cached]
            
        try:
            # Get systems from repository
            systems = await self.client.get_management_systems()
            
            # Convert to model objects for validation
            system_models = [ManagementSystem(**system) for system in systems]
            
            # Cache the raw dictionaries
            await cache.set(cache_key, systems, CacheConfig.SYSTEM_DEF_TTL)
            
            logger.debug(f"Retrieved and cached {len(systems)} management systems")
            return system_models
        except Exception as e:
            error_msg = f"Error retrieving management systems: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def get_management_system(self, system_id: str) -> Optional[ManagementSystem]:
        """
        Get a specific management system.
        
        Args:
            system_id: System identifier
            
        Returns:
            ManagementSystem or None if not found
            
        Raises:
            ManagementSystemRepoError: If retrieval fails
        """
        cache_key = f"systems:{system_id}"
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Returning cached management system: {system_id}")
            return ManagementSystem(**cached)
            
        try:
            system_data = await self.client.get_management_system(system_id)
            if not system_data:
                logger.debug(f"Management system not found: {system_id}")
                return None
                
            system = ManagementSystem(**system_data)
            await cache.set(cache_key, system_data, CacheConfig.SYSTEM_DEF_TTL)
            
            logger.debug(f"Retrieved and cached management system: {system_id}")
            return system
        except Exception as e:
            error_msg = f"Error retrieving management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def create_management_system(self, system_data: Dict[str, Any]) -> ManagementSystem:
        """
        Create a new management system.
        
        Args:
            system_data: System definition data
            
        Returns:
            Created ManagementSystem
            
        Raises:
            ManagementSystemRepoError: If creation fails
        """
        try:
            # Generate an ID if not provided
            if "id" not in system_data:
                system_data["id"] = str(uuid.uuid4())
            
            # Create a ManagementSystem object to validate the data
            system = ManagementSystem(**system_data)
            
            # Create the system in the repository
            result = await self.client.create_management_system(system.dict())
            
            if not result:
                raise ManagementSystemRepoError(f"Failed to create management system")
                
            # Invalidate cache
            await cache.delete("systems:all")
            
            # Return the created system
            return ManagementSystem(**result)
        except Exception as e:
            error_msg = f"Error creating management system: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
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
            ManagementSystemRepoError: If system creation fails
        """
        try:
            # Get the template
            template = get_system_template(template_id)
            if not template:
                raise TemplateNotFoundError(f"Template {template_id} not found")
                
            # Apply customizations if provided
            if custom_data:
                template.update(custom_data)
                
            # Ensure we don't use the template ID for the new system
            template["id"] = str(uuid.uuid4())
            template["is_template"] = False
            template["template_id"] = template_id
            
            # Create the system
            return await self.create_management_system(template)
        except TemplateNotFoundError:
            # Re-raise template errors
            raise
        except Exception as e:
            error_msg = f"Error creating system from template {template_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
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
            ManagementSystemRepoError: If update fails
        """
        try:
            # Update the system in the repository
            success = await self.client.update_management_system(system_id, updates)
            
            if success:
                # Invalidate caches
                await cache.delete(f"systems:{system_id}")
                await cache.delete("systems:all")
                logger.debug(f"Cache invalidated for system {system_id}")
                
            return success
        except Exception as e:
            error_msg = f"Error updating management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def delete_management_system(self, system_id: str) -> bool:
        """
        Delete a management system.
        
        Args:
            system_id: System identifier
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ManagementSystemRepoError: If deletion fails
        """
        try:
            # Delete the system from the repository
            success = await self.client.delete_management_system(system_id)
            
            if success:
                # Invalidate caches
                await cache.delete(f"systems:{system_id}")
                await cache.delete("systems:all")
                logger.debug(f"Cache invalidated for system {system_id}")
                
            return success
        except Exception as e:
            error_msg = f"Error deleting management system {system_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def get_tenant_systems(self, tenant_id: str) -> List[SystemInstance]:
        """
        Get all system instances for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            List of system instances
            
        Raises:
            ManagementSystemRepoError: If retrieval fails
        """
        cache_key = f"tenant:{tenant_id}:systems"
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Returning cached tenant systems for tenant {tenant_id}")
            return [SystemInstance(**instance) for instance in cached]
            
        try:
            # Get instances from repository
            instances = await self.client.get_tenant_systems(tenant_id)
            
            # Convert to model objects for validation
            instance_models = [SystemInstance(**instance) for instance in instances]
            
            # Cache the raw dictionaries
            await cache.set(cache_key, instances, CacheConfig.INSTANCE_TTL)
            
            logger.debug(f"Retrieved and cached {len(instances)} tenant systems for tenant {tenant_id}")
            return instance_models
        except Exception as e:
            error_msg = f"Error retrieving tenant systems for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def get_system_instance(self, tenant_id: str, instance_id: str) -> Optional[SystemInstance]:
        """
        Get a specific system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            
        Returns:
            SystemInstance or None if not found
            
        Raises:
            ManagementSystemRepoError: If retrieval fails
        """
        cache_key = f"tenant:{tenant_id}:instance:{instance_id}"
        cached = await cache.get(cache_key)
        if cached:
            logger.debug(f"Returning cached instance {instance_id} for tenant {tenant_id}")
            return SystemInstance(**cached)
            
        try:
            # Get instance from repository
            instance_data = await self.client.get_system_instance(tenant_id, instance_id)
            
            if not instance_data:
                logger.debug(f"System instance {instance_id} not found for tenant {tenant_id}")
                return None
                
            # Convert to model object for validation
            instance = SystemInstance(**instance_data)
            
            # Cache the raw dictionary
            await cache.set(cache_key, instance_data, CacheConfig.INSTANCE_TTL)
            
            logger.debug(f"Retrieved and cached instance {instance_id} for tenant {tenant_id}")
            return instance
        except Exception as e:
            error_msg = f"Error retrieving system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
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
            ManagementSystemRepoError: If creation fails
        """
        try:
            # Create the instance in the repository
            instance_data = await self.client.create_system_instance(
                tenant_id=tenant_id,
                system_id=system_id,
                name=name,
                settings=settings
            )
            
            if not instance_data:
                raise ManagementSystemRepoError(f"Failed to create system instance for tenant {tenant_id}")
                
            # Convert to model object for validation
            instance = SystemInstance(**instance_data)
            
            # Invalidate cache
            await cache.delete(f"tenant:{tenant_id}:systems")
            
            logger.debug(f"Created system instance {instance.id} for tenant {tenant_id}")
            return instance
        except Exception as e:
            error_msg = f"Error creating system instance for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
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
            ManagementSystemRepoError: If update fails
        """
        try:
            # Update the instance in the repository
            success = await self.client.update_system_instance(tenant_id, instance_id, updates)
            
            if success:
                # Invalidate caches
                await cache.delete(f"tenant:{tenant_id}:instance:{instance_id}")
                await cache.delete(f"tenant:{tenant_id}:systems")
                logger.debug(f"Cache invalidated for instance {instance_id}, tenant {tenant_id}")
                
            return success
        except Exception as e:
            error_msg = f"Error updating system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
    async def delete_system_instance(self, tenant_id: str, instance_id: str) -> bool:
        """
        Delete a system instance.
        
        Args:
            tenant_id: Tenant identifier
            instance_id: System instance identifier
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ManagementSystemRepoError: If deletion fails
        """
        try:
            # Delete the instance from the repository
            success = await self.client.delete_system_instance(tenant_id, instance_id)
            
            if success:
                # Invalidate caches
                await cache.delete(f"tenant:{tenant_id}:instance:{instance_id}")
                await cache.delete(f"tenant:{tenant_id}:systems")
                logger.debug(f"Cache invalidated for instance {instance_id}, tenant {tenant_id}")
                
            return success
        except Exception as e:
            error_msg = f"Error deleting system instance {instance_id} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
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
            ManagementSystemRepoError: If retrieval fails
        """
        try:
            # Get data from repository
            data = await self.client.get_system_data(
                tenant_id=tenant_id,
                instance_id=instance_id,
                view_id=view_id,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            if not data:
                raise InstanceNotFoundError(f"System instance {instance_id} not found for tenant {tenant_id}")
                
            # Convert to PaginatedResponse
            paginated_response = PaginatedResponse(
                items=data.get("items", []),
                total=data.get("total", 0),
                page=data.get("page", page),
                page_size=data.get("page_size", page_size),
                total_pages=data.get("total_pages", 0)
            )
            
            logger.debug(f"Retrieved {len(paginated_response.items)} data items for instance {instance_id}, tenant {tenant_id}")
            return paginated_response
        except Exception as e:
            error_msg = f"Error retrieving system data for instance {instance_id}, tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e
    
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
            ManagementSystemRepoError: If creation fails
        """
        try:
            # Create the item in the repository
            item_data = await self.client.create_data_item(tenant_id, instance_id, data)
            
            if not item_data:
                raise ManagementSystemRepoError(f"Failed to create data item for instance {instance_id}, tenant {tenant_id}")
                
            logger.debug(f"Created data item for instance {instance_id}, tenant {tenant_id}")
            return item_data
        except Exception as e:
            error_msg = f"Error creating data item for instance {instance_id}, tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise ManagementSystemRepoError(error_msg) from e

@lru_cache()
def get_management_system_repo_service() -> ManagementSystemRepoService:
    """
    Get a cached instance of the management system repository service.
    
    Returns:
        ManagementSystemRepoService instance
    """
    base_url = os.getenv("MANAGEMENT_SYSTEM_REPO_URL", "http://management-system-repo:8080")
    api_key = os.getenv("MANAGEMENT_SYSTEM_REPO_API_KEY", "dev_api_key")
    
    client = ManagementSystemRepoClient(base_url, api_key)
    return ManagementSystemRepoService(client) 