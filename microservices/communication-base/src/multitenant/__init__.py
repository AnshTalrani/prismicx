"""
Multitenant Package for Communication Base Microservice

This package contains all components related to multi-tenancy in the communication microservice.
It provides tools for tenant identification, isolation, and context management.
"""

from .tenant_context import TenantContext, TenantContextManager, with_tenant
from .tenant_middleware import TenantMiddleware
from .tenant_service import TenantService
from .tenant_resolver import TenantResolver
from .tenant_config import TenantConfig

__all__ = [
    'TenantContext',
    'TenantContextManager',
    'TenantMiddleware',
    'TenantService',
    'TenantResolver',
    'TenantConfig',
    'with_tenant'
] 