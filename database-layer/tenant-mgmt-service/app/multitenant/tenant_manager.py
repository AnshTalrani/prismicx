"""
Tenant manager module for coordinating tenant operations.
"""
import logging
from typing import Optional, Dict, Any, List

from fastapi import Depends, HTTPException, status

from .tenant_service import TenantService
from .tenant_context import TenantContext, TenantInfo

logger = logging.getLogger(__name__)


class TenantManager:
    """
    Manager for coordinating tenant operations.
    
    This class serves as the main entry point for tenant management operations,
    coordinating between the tenant service, repository, and context.
    """
    
    def __init__(self, service: Optional[TenantService] = None):
        """
        Initialize the tenant manager.
        
        Args:
            service (Optional[TenantService]): Service for tenant business logic
        """
        self.service = service or TenantService()
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information by ID.
        
        Args:
            tenant_id (str): ID of tenant to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Tenant information if found, None otherwise
        """
        return await self.service.get_tenant(tenant_id)
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information by domain name.
        
        Args:
            domain (str): Domain name to look up
            
        Returns:
            Optional[Dict[str, Any]]: Tenant information if found, None otherwise
        """
        return await self.service.get_tenant_by_domain(domain)
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tenant.
        
        Args:
            tenant_data (Dict[str, Any]): Tenant data to create
            
        Returns:
            Dict[str, Any]: The created tenant
        """
        return await self.service.create_tenant(tenant_data)
    
    async def update_tenant(self, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a tenant.
        
        Args:
            tenant_id (str): ID of tenant to update
            update_data (Dict[str, Any]): Data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated tenant information if found, None otherwise
        """
        return await self.service.update_tenant(tenant_id, update_data)
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id (str): ID of tenant to delete
            
        Returns:
            bool: True if tenant was deleted, False otherwise
        """
        return await self.service.delete_tenant(tenant_id)
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List tenants with pagination.
        
        Args:
            limit (int): Maximum number of tenants to return
            offset (int): Offset for pagination
            
        Returns:
            List[Dict[str, Any]]: List of tenant information
        """
        return await self.service.list_tenants(limit, offset)
    
    async def get_connection_info(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get database connection information for a tenant.
        
        Args:
            tenant_id (str): ID of tenant to get connection info for
            
        Returns:
            Dict[str, Any]: Connection information
            
        Raises:
            HTTPException: If tenant not found or not active
        """
        tenant_info = await self.service.get_tenant_connection_info(tenant_id)
        if not tenant_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
            
        if not tenant_info.get('is_active', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant {tenant_id} is not active"
            )
            
        return tenant_info
    
    def set_tenant_context(self, tenant_info: Dict[str, Any]) -> None:
        """
        Set the current tenant context.
        
        Args:
            tenant_info (Dict[str, Any]): Tenant information
        """
        tenant_id = tenant_info.get('tenant_id')
        tenant_context = self.service.create_tenant_context(tenant_id, tenant_info)
        TenantContext.set_tenant(tenant_context)
    
    @staticmethod
    def get_current_tenant_id() -> Optional[str]:
        """
        Get the current tenant ID from context.
        
        Returns:
            Optional[str]: The current tenant ID or None if not set
        """
        return TenantContext.get_tenant_id()
    
    @staticmethod
    def get_current_tenant() -> Optional[TenantInfo]:
        """
        Get the current tenant information from context.
        
        Returns:
            Optional[TenantInfo]: The current tenant information or None if not set
        """
        return TenantContext.get_current_tenant()


# Dependency to get the tenant manager in FastAPI routes
def get_tenant_manager() -> TenantManager:
    """
    Get a tenant manager instance.
    
    Returns:
        TenantManager: A tenant manager instance
    """
    return TenantManager() 