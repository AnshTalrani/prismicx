"""
Database and Batch Context Package

This package provides database context management without tenant schema switching.
It maintains compatibility with existing code by providing equivalent interfaces.
"""

# Legacy tenant context imports maintained for compatibility
from .tenant.tenant_context import TenantContext, TenantContextManager, with_tenant
from .tenant.tenant_middleware import TenantMiddleware
from .tenant.tenant_service import TenantServiceClient

# Updated context managers without schema switching
from .context.tenant_db_context import get_db_session_with_batch, get_tenant_db_session, DatabaseContext
from .context.db_session import get_db_session, get_engine, get_session_factory, close_db_connections

__all__ = [
    # Legacy tenant context classes maintained for compatibility
    'TenantContext',
    'TenantContextManager',
    'TenantMiddleware',
    'TenantServiceClient',
    
    # Updated context classes without schema switching
    'DatabaseContext',
    'get_db_session_with_batch',
    'get_tenant_db_session',
    'get_db_session',
    'get_engine',
    'get_session_factory',
    'close_db_connections',
    'with_tenant',
] 