"""
Tenant Context Module

This module provides context management for multi-tenant operations.
It allows setting and retrieving the current tenant ID for database operations.
"""

import logging
import contextvars
from typing import Optional

logger = logging.getLogger(__name__)

# Context variable to store the current tenant ID
current_tenant = contextvars.ContextVar('current_tenant', default=None)


class TenantContext:
    """
    Tenant context manager for multi-tenant operations.
    
    This class provides static methods to get and set the current tenant ID
    for database operations. It uses contextvars to ensure isolation in
    asynchronous code.
    """
    
    @staticmethod
    def set_current_tenant(tenant_id: str) -> None:
        """
        Set the current tenant ID in the context.
        
        Args:
            tenant_id: The tenant ID to set.
        """
        current_tenant.set(tenant_id)
        logger.debug(f"Set current tenant to: {tenant_id}")
    
    @staticmethod
    def get_current_tenant() -> Optional[str]:
        """
        Get the current tenant ID from the context.
        
        Returns:
            The current tenant ID or None if not set.
        """
        return current_tenant.get()
    
    @staticmethod
    def clear_current_tenant() -> None:
        """Clear the current tenant ID from the context."""
        current_tenant.set(None)
        logger.debug("Cleared current tenant")


class TenantContextManager:
    """
    Context manager for tenant operations.
    
    This class provides a context manager interface for setting and clearing
    the current tenant ID for a block of code.
    """
    
    def __init__(self, tenant_id: str):
        """
        Initialize the tenant context manager.
        
        Args:
            tenant_id: The tenant ID to use in the context.
        """
        self.tenant_id = tenant_id
        self.token = None
    
    async def __aenter__(self):
        """
        Set the tenant ID when entering the context.
        
        Returns:
            The tenant ID.
        """
        self.token = current_tenant.set(self.tenant_id)
        logger.debug(f"Entered tenant context: {self.tenant_id}")
        return self.tenant_id
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Reset the tenant ID when exiting the context."""
        current_tenant.reset(self.token)
        logger.debug(f"Exited tenant context: {self.tenant_id}")
    
    def __enter__(self):
        """
        Set the tenant ID when entering the context.
        
        Returns:
            The tenant ID.
        """
        self.token = current_tenant.set(self.tenant_id)
        logger.debug(f"Entered tenant context: {self.tenant_id}")
        return self.tenant_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset the tenant ID when exiting the context."""
        current_tenant.reset(self.token)
        logger.debug(f"Exited tenant context: {self.tenant_id}")


def with_tenant(tenant_id: str):
    """
    Decorator for functions that need to run in a tenant context.
    
    Args:
        tenant_id: The tenant ID to use.
        
    Returns:
        Decorated function that runs in the specified tenant context.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with TenantContextManager(tenant_id):
                return await func(*args, **kwargs)
        return wrapper
    return decorator 