"""
Tenant Middleware Module

This module provides middleware for handling tenant context in requests.
"""

import structlog
from typing import Optional, Dict, Any

# Import the tenant context
from ..context.tenant_context import TenantContext
from .client import tenant_client

# Configure structured logging
logger = structlog.get_logger(__name__)


class TenantContextMiddleware:
    """
    Middleware factory for FastAPI to handle tenant context.
    
    This middleware extracts tenant information from requests and
    sets up the tenant context for the duration of the request.
    """
    
    def __init__(self, app):
        """Initialize the middleware with the app."""
        self.app = app
        logger.info("Initialized TenantContextMiddleware")
    
    async def __call__(self, scope, receive, send):
        """
        Process an ASGI request/response cycle.
        
        Args:
            scope: ASGI scope
            receive: ASGI receive function
            send: ASGI send function
        """
        # Only process HTTP requests
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Extract tenant ID from headers
        headers = dict(scope.get("headers", []))
        tenant_id = None
        
        # Try to get tenant from X-Tenant-ID header (convert from bytes)
        tenant_header = headers.get(b"x-tenant-id")
        if tenant_header:
            tenant_id = tenant_header.decode("utf-8")
            logger.debug(f"Extracted tenant ID from header: {tenant_id}")
        
        # If no tenant ID in headers, try to extract from host (subdomain)
        if not tenant_id:
            host_header = headers.get(b"host")
            if host_header:
                host = host_header.decode("utf-8").split(":")[0]  # Remove port if present
                # Extract tenant from subdomain (e.g., tenant-name.example.com)
                parts = host.split(".")
                if len(parts) >= 3:  # At least tenant.example.com
                    tenant_id = f"tenant_{parts[0]}"  # Prefix with tenant_ for safety
                    logger.debug(f"Extracted tenant ID from subdomain: {tenant_id}")
        
        # If tenant ID found, validate and set it in context
        if tenant_id:
            # Optional: Validate tenant with tenant management service
            # This could be enabled in production for additional security
            # is_valid = await tenant_client.validate_tenant(tenant_id)
            # if not is_valid:
            #     logger.warning(f"Invalid tenant ID: {tenant_id}")
            #     # Return 401 response for invalid tenant
            #     return Response(status_code=401, content=b"Invalid tenant ID")
            
            # Set tenant context
            TenantContext.set_tenant_id(tenant_id)
            
            # Schema is typically derived from tenant ID
            TenantContext.set_tenant_schema(tenant_id)
            
            # Get tenant info if possible
            try:
                tenant_info = await tenant_client.get_tenant_info(tenant_id)
                if tenant_info:
                    TenantContext.set_tenant_info(tenant_info)
                else:
                    # Set basic info if tenant service couldn't be reached
                    TenantContext.set_tenant_info({
                        "tenant_id": tenant_id,
                        "schema": tenant_id,
                        "status": "active"
                    })
            except Exception as e:
                logger.error(f"Error getting tenant info: {str(e)}")
                # Set basic info on error
                TenantContext.set_tenant_info({
                    "tenant_id": tenant_id,
                    "schema": tenant_id,
                    "status": "active"
                })
        
        try:
            # Process the request with tenant context
            return await self.app(scope, receive, send)
        finally:
            # Clear tenant context after request completes
            TenantContext.clear() 