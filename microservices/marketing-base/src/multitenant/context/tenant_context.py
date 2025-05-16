"""
Tenant Context Module

This module provides the tenant context management functionality.
It allows the application to set and retrieve the current tenant context
using thread-local storage, ensuring proper tenant isolation.
"""

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class TenantContext:
    """
    Thread-local storage for tenant context.
    
    This class provides methods for setting and retrieving the current tenant ID
    using thread-local storage to ensure proper tenant isolation in a multi-threaded
    environment.
    """
    
    # Thread-local storage
    _thread_local = threading.local()
    
    @classmethod
    def set_tenant_id(cls, tenant_id: str) -> None:
        """
        Set the current tenant ID.
        
        Args:
            tenant_id: The ID of the tenant
        """
        cls._thread_local.tenant_id = tenant_id
        logger.debug(f"Set current tenant ID to: {tenant_id}")
    
    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        """
        Get the current tenant ID.
        
        Returns:
            The current tenant ID, or None if not set
        """
        return getattr(cls._thread_local, 'tenant_id', None)
    
    @classmethod
    def clear(cls) -> None:
        """Clear the current tenant ID."""
        if hasattr(cls._thread_local, 'tenant_id'):
            delattr(cls._thread_local, 'tenant_id')
            logger.debug("Cleared tenant context")
    
    @classmethod
    def with_tenant(cls, tenant_id: str):
        """
        Context manager for setting tenant context within a block.
        
        Usage:
            with TenantContext.with_tenant('tenant_123'):
                # Code that needs to run in the context of tenant_123
        
        Args:
            tenant_id: The ID of the tenant
            
        Returns:
            Context manager
        """
        class TenantContextManager:
            def __init__(self, tenant_id: str):
                self.tenant_id = tenant_id
                self.previous_tenant_id = None
                
            def __enter__(self):
                self.previous_tenant_id = cls.get_tenant_id()
                cls.set_tenant_id(self.tenant_id)
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.previous_tenant_id:
                    cls.set_tenant_id(self.previous_tenant_id)
                else:
                    cls.clear()
        
        return TenantContextManager(tenant_id) 