"""
Database Client Package for PrismicX Microservices

This package provides a client for accessing tenant-specific and system-wide
databases in the PrismicX microservices architecture.
"""

from .client import (
    DatabaseClient,
    get_client,
    get_tenant_connection,
    get_tenant_info,
    get_system_data
)

__all__ = [
    'DatabaseClient',
    'get_client',
    'get_tenant_connection',
    'get_tenant_info',
    'get_system_data'
] 