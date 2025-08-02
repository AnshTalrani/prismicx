"""
Tenant context module for maintaining tenant-specific information throughout request lifecycle.
"""
from contextvars import ContextVar
from typing import Optional, Dict, Any
from pydantic import BaseModel


class TenantInfo(BaseModel):
    """Model representing essential tenant information."""
    tenant_id: str
    schema_name: str
    database_url: Optional[str] = None
    config: Dict[str, Any] = {}
    is_active: bool = True


# Global context variable to store the current tenant information
tenant_context_var: ContextVar[Optional[TenantInfo]] = ContextVar('tenant_context', default=None)


class TenantContext:
    """
    Manages tenant context throughout request lifecycle.
    
    This class provides methods to set and get the current tenant information
    using Python's ContextVar for async-safe context management.
    """
    
    @staticmethod
    def get_current_tenant() -> Optional[TenantInfo]:
        """
        Get the current tenant information from context.
        
        Returns:
            Optional[TenantInfo]: The current tenant information or None if not set
        """
        return tenant_context_var.get()
    
    @staticmethod
    def set_tenant(tenant_info: TenantInfo) -> None:
        """
        Set the current tenant information in context.
        
        Args:
            tenant_info (TenantInfo): Tenant information to set
        """
        tenant_context_var.set(tenant_info)
    
    @staticmethod
    def clear_tenant() -> None:
        """Remove the current tenant information from context."""
        tenant_context_var.set(None)
    
    @staticmethod
    def get_tenant_id() -> Optional[str]:
        """
        Get the current tenant ID from context.
        
        Returns:
            Optional[str]: The current tenant ID or None if not set
        """
        tenant = tenant_context_var.get()
        return tenant.tenant_id if tenant else None
    
    @staticmethod
    def get_schema_name() -> Optional[str]:
        """
        Get the current tenant's schema name from context.
        
        Returns:
            Optional[str]: The current tenant's schema name or None if not set
        """
        tenant = tenant_context_var.get()
        return tenant.schema_name if tenant else None 