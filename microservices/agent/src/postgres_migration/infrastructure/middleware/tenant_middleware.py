"""
Tenant Middleware for FastAPI.

Extracts tenant information from incoming requests and manages tenant context throughout the request lifecycle.
"""
import logging
from typing import Callable, Dict, Any, Optional
import asyncio

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.postgres_migration.utils.tenant_context import (
    set_current_tenant_id, set_current_tenant_info, clear_tenant_context
)
from src.postgres_migration.infrastructure.clients.tenant_mgmt_client import (
    validate_tenant, get_tenant_info
)

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for handling tenant context in requests."""
    
    def __init__(self, app: ASGIApp, header_name: str = "X-Tenant-ID"):
        """
        Initialize the tenant middleware.
        
        Args:
            app: FastAPI application
            header_name: Name of the header containing the tenant ID
        """
        super().__init__(app)
        self.header_name = header_name
        logger.info(f"Initialized TenantMiddleware with header name: {header_name}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request to extract and set tenant context.
        
        Args:
            request: FastAPI request
            call_next: Next middleware handler
            
        Returns:
            FastAPI response
        """
        # Clear any previous tenant context
        clear_tenant_context()
        
        # Try to extract tenant ID from header
        tenant_id = request.headers.get(self.header_name)
        
        # If no tenant ID in header, try other methods
        if not tenant_id:
            # Check for tenant ID in path
            if "tenant_id" in request.path_params:
                tenant_id = request.path_params.get("tenant_id")
                logger.debug(f"Extracted tenant ID from path: {tenant_id}")
            # Check for tenant ID in query params
            elif request.query_params.get("tenant_id"):
                tenant_id = request.query_params.get("tenant_id")
                logger.debug(f"Extracted tenant ID from query: {tenant_id}")
            # Check if there's a subdomain that indicates the tenant
            else:
                host = request.headers.get("host", "")
                parts = host.split(".")
                if len(parts) > 2 and parts[0] != "www":
                    tenant_id = parts[0]
                    logger.debug(f"Extracted tenant ID from subdomain: {tenant_id}")
        
        # Set tenant context if tenant ID found
        if tenant_id:
            # Validate tenant with the tenant management service
            is_valid = await validate_tenant(tenant_id)
            
            if is_valid:
                # Set tenant ID in context
                set_current_tenant_id(tenant_id)
                
                # Get detailed tenant info
                tenant_info = await get_tenant_info(tenant_id)
                if tenant_info:
                    set_current_tenant_info(tenant_info)
                    logger.info(f"Tenant context set for tenant: {tenant_id}")
                else:
                    logger.warning(f"Failed to get tenant information for {tenant_id}")
            else:
                logger.warning(f"Invalid tenant ID: {tenant_id}")
                # Return 401 Unauthorized for invalid tenant
                return Response(
                    content={"detail": "Invalid tenant ID"},
                    status_code=401,
                    media_type="application/json"
                )
        else:
            logger.debug("No tenant ID found in request")
        
        try:
            # Process the request
            response = await call_next(request)
            return response
        finally:
            # Always clear tenant context after request completes
            clear_tenant_context()

class TenantRoute(APIRoute):
    """Custom API route that ensures tenant context is properly handled."""
    
    async def handle(self, request: Request) -> Response:
        """
        Handle the request and maintain tenant context.
        
        Args:
            request: FastAPI request
            
        Returns:
            FastAPI response
        """
        # Get tenant ID from context (should be set by middleware)
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Execute original route handler
        response = await super().handle(request)
        
        return response 