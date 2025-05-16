"""
Tenant Middleware Module

This module provides middleware for extracting tenant information from
requests and setting up the tenant context for request processing.
"""

import logging
from typing import Optional, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from .tenant_context import TenantContext

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant ID from request headers and set tenant context.
    
    This middleware automatically extracts the tenant ID from the request
    headers and sets up the tenant context for the duration of the request.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Tenant-ID",
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize the tenant middleware.
        
        Args:
            app: The ASGI application.
            header_name: The name of the header containing the tenant ID.
            exclude_paths: List of paths to exclude from tenant context.
        """
        super().__init__(app)
        self.header_name = header_name
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
            "/metrics",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request and set tenant context.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint.
            
        Returns:
            The response from the next middleware or endpoint.
        """
        # Clear any existing tenant context
        TenantContext.clear_current_tenant()
        
        # Skip tenant context for excluded paths
        if self._should_skip_tenant_context(request.url.path):
            return await call_next(request)
        
        # Extract tenant ID from header
        tenant_id = request.headers.get(self.header_name)
        
        if tenant_id:
            # Set tenant context for this request
            TenantContext.set_current_tenant(tenant_id)
            logger.debug(f"Set tenant context for tenant {tenant_id}")
        
        try:
            # Process the request with tenant context
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context after request is processed
            TenantContext.clear_current_tenant()
    
    def _should_skip_tenant_context(self, path: str) -> bool:
        """
        Check if tenant context should be skipped for this path.
        
        Args:
            path: The request path.
            
        Returns:
            True if tenant context should be skipped.
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths) 