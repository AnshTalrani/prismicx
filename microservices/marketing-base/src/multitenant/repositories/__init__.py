"""
Tenant repository package.

Provides repository interfaces and implementations for tenant data access.
"""

from .tenant_repository import TenantRepository
from .tenant_repository_impl import TenantRepositoryImpl

__all__ = [
    'TenantRepository',
    'TenantRepositoryImpl'
] 