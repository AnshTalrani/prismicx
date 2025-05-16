"""
Tenant Context Management.

Provides thread-local storage for tenant context throughout the request lifecycle.
"""
import logging
import contextvars
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Context variable to store tenant information throughout the request
current_tenant_id = contextvars.ContextVar('current_tenant_id', default=None)
current_tenant_info = contextvars.ContextVar('current_tenant_info', default=None)

def get_current_tenant_id() -> Optional[str]:
    """
    Get the current tenant ID from the context.
    
    Returns:
        Tenant ID or None if not set
    """
    return current_tenant_id.get()

def set_current_tenant_id(tenant_id: str) -> None:
    """
    Set the current tenant ID in the context.
    
    Args:
        tenant_id: Tenant identifier
    """
    if not tenant_id:
        logger.warning("Attempted to set empty tenant ID")
        return
        
    logger.debug(f"Setting current tenant ID: {tenant_id}")
    current_tenant_id.set(tenant_id)

def get_current_tenant_info() -> Optional[Dict[str, Any]]:
    """
    Get the current tenant information from the context.
    
    Returns:
        Tenant information dictionary or None if not set
    """
    return current_tenant_info.get()

def set_current_tenant_info(info: Dict[str, Any]) -> None:
    """
    Set the current tenant information in the context.
    
    Args:
        info: Tenant information
    """
    if not info:
        logger.warning("Attempted to set empty tenant info")
        return
        
    logger.debug(f"Setting current tenant info: {info}")
    current_tenant_info.set(info)

def get_tenant_schema() -> str:
    """
    Get the PostgreSQL schema name for the current tenant.
    
    Returns:
        Schema name for the current tenant or default schema if not available
    """
    from src.postgres_migration.config.postgres_config import DEFAULT_SCHEMA
    
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        logger.warning("No tenant context found, using default schema")
        return DEFAULT_SCHEMA
    
    # Convert tenant ID to schema name format
    # Typically: tenant_id -> tenant_<id>
    schema_name = f"tenant_{tenant_id}"
    
    return schema_name

def clear_tenant_context() -> None:
    """Clear all tenant context variables."""
    try:
        current_tenant_id.set(None)
        current_tenant_info.set(None)
        logger.debug("Tenant context cleared")
    except Exception as e:
        logger.error(f"Error clearing tenant context: {str(e)}") 