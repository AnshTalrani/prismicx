"""
Tenant context module - simplified version without schema switching.
"""
from contextvars import ContextVar
from typing import Optional

# Global context variable to store current tenant ID
tenant_context: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)

def get_current_tenant_id() -> Optional[str]:
    """
    Get the current tenant ID from context.
    Returns None if no tenant is set.
    """
    return tenant_context.get()

def set_tenant_context(tenant_id: Optional[str]) -> None:
    """
    Set the current tenant ID in context.
    Args:
        tenant_id: The tenant ID to set, or None to clear
    """
    tenant_context.set(tenant_id) 