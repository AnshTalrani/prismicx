"""
Tenant service module for handling tenant-related business logic.
"""
import uuid
import logging
from typing import List, Optional, Dict, Any

from .tenant_repository import TenantRepository
from .tenant_context import TenantInfo

logger = logging.getLogger(__name__)


class TenantService:
    """
    Service for tenant-related business logic.
    
    This class implements the business logic for tenant management, including
    tenant creation, provisioning, and information retrieval.
    """
    
    def __init__(self, repository: Optional[TenantRepository] = None):
        """
        Initialize the tenant service.
        
        Args:
            repository (Optional[TenantRepository]): Repository for tenant data operations
        """
        self.repository = repository or TenantRepository()
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tenant.
        
        Args:
            tenant_data (Dict[str, Any]): Tenant data to create
            
        Returns:
            Dict[str, Any]: The created tenant
        """
        # Generate tenant ID if not provided
        if 'tenant_id' not in tenant_data:
            tenant_data['tenant_id'] = str(uuid.uuid4())
            
        # Generate schema name if not provided
        if 'schema_name' not in tenant_data:
            tenant_data['schema_name'] = f"tenant_{tenant_data['tenant_id'].replace('-', '_')}"
            
        tenant = await self.repository.create_tenant(tenant_data)
        return tenant.to_dict()
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information by ID.
        
        Args:
            tenant_id (str): ID of tenant to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Tenant information if found, None otherwise
        """
        tenant = await self.repository.get_tenant_by_id(tenant_id)
        return tenant.to_dict() if tenant else None
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information by domain name.
        
        Args:
            domain (str): Domain name to look up
            
        Returns:
            Optional[Dict[str, Any]]: Tenant information if found, None otherwise
        """
        tenant = await self.repository.get_tenant_by_domain(domain)
        return tenant.to_dict() if tenant else None
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List tenants with pagination.
        
        Args:
            limit (int): Maximum number of tenants to return
            offset (int): Offset for pagination
            
        Returns:
            List[Dict[str, Any]]: List of tenant information
        """
        tenants = await self.repository.list_tenants(limit, offset)
        return [tenant.to_dict() for tenant in tenants]
    
    async def update_tenant(self, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a tenant.
        
        Args:
            tenant_id (str): ID of tenant to update
            update_data (Dict[str, Any]): Data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated tenant information if found, None otherwise
        """
        # Prevent changing tenant_id and schema_name
        if 'tenant_id' in update_data:
            del update_data['tenant_id']
        if 'schema_name' in update_data:
            del update_data['schema_name']
            
        tenant = await self.repository.update_tenant(tenant_id, update_data)
        return tenant.to_dict() if tenant else None
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id (str): ID of tenant to delete
            
        Returns:
            bool: True if tenant was deleted, False otherwise
        """
        return await self.repository.delete_tenant(tenant_id)
    
    async def get_tenant_connection_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get database connection information for a tenant.
        
        Args:
            tenant_id (str): ID of tenant to get connection info for
            
        Returns:
            Optional[Dict[str, Any]]: Connection information if tenant found, None otherwise
        """
        tenant = await self.repository.get_tenant_by_id(tenant_id)
        if not tenant:
            return None
            
        # Create tenant info from tenant model
        tenant_info = {
            'tenant_id': tenant.tenant_id,
            'schema_name': tenant.schema_name,
            'database_url': self._get_database_url_for_tenant(tenant.to_dict()),
            'is_active': tenant.is_active
        }
        
        return tenant_info
    
    def _get_database_url_for_tenant(self, tenant: Dict[str, Any]) -> str:
        """
        Get database URL for a tenant.
        
        Args:
            tenant (Dict[str, Any]): Tenant information
            
        Returns:
            str: Database URL for tenant
        """
        from ..config import get_database_url
        base_url = get_database_url()
        
        # For schema-based isolation, return the base URL
        # The schema will be set at the connection level
        return base_url
    
    def create_tenant_context(self, tenant_id: str, tenant_info: Dict[str, Any]) -> TenantInfo:
        """
        Create a tenant context object from tenant information.
        
        Args:
            tenant_id (str): Tenant ID
            tenant_info (Dict[str, Any]): Tenant information
            
        Returns:
            TenantInfo: Tenant context object
        """
        return TenantInfo(
            tenant_id=tenant_id,
            schema_name=tenant_info.get('schema_name', f"tenant_{tenant_id.replace('-', '_')}"),
            database_url=tenant_info.get('database_url'),
            config=tenant_info.get('config', {}),
            is_active=tenant_info.get('is_active', True)
        ) 