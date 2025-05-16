"""
Middleware for the User Data Service.

This module provides middleware components for the User Data Service,
including tenant context management for multi-tenant support.
"""

import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts the tenant ID from request headers and sets it in PostgreSQL session.
    
    This allows row-level security policies to correctly filter data by tenant.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process an incoming request.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response from the next middleware or route handler.
        """
        # Extract tenant ID from headers
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # If no tenant ID, check query parameters
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id")
        
        # Store tenant ID in request state
        request.state.tenant_id = tenant_id or ""
        
        # Log tenant context
        logger.debug(f"Request for tenant: {tenant_id or 'default'}")
        
        # Set PostgreSQL session variable for tenant ID
        # This will be used by RLS policies
        async with request.app.state.db_pool.acquire() as conn:
            await conn.execute(f"SET app.current_tenant_id = '{tenant_id or ''}'")
        
        # Process the request
        response = await call_next(request)
        
        # Clean up
        async with request.app.state.db_pool.acquire() as conn:
            await conn.execute("RESET app.current_tenant_id")
        
        return response 