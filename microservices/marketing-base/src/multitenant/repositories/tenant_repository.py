"""
Tenant repository interface.

This module defines the interface for tenant repository implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class TenantRepository(ABC):
    """
    Interface for tenant repository implementations.
    
    This interface defines the methods that any tenant repository
    implementation must provide.
    """
    
    @abstractmethod
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The tenant information, or None if not found.
        """
        pass
    
    @abstractmethod
    async def get_all_tenants(self) -> List[Dict[str, Any]]:
        """
        Get all tenants.
        
        Returns:
            A list of all tenants.
        """
        pass
    
    @abstractmethod
    async def get_tenant_schema(self, tenant_id: str) -> Optional[str]:
        """
        Get the database schema name for a tenant.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The schema name, or None if the tenant does not exist.
        """
        pass 