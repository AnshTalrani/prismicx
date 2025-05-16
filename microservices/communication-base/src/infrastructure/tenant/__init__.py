"""
Tenant module compatibility layer

This module re-exports components from the new multitenant directory
to maintain backward compatibility with existing code that imports from
infrastructure.tenant.
"""

import warnings

# Import from the new location
from ...multitenant.tenant_context import (
    TenantContext, 
    TenantContextManager, 
    with_tenant
)

# Warn about deprecation
warnings.warn(
    "Importing from 'infrastructure.tenant' is deprecated. "
    "Use 'multitenant' package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the components
__all__ = [
    'TenantContext',
    'TenantContextManager',
    'with_tenant'
]
