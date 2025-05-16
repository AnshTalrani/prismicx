"""
Tenant middleware for management systems.

This module provides middleware for handling tenant context in incoming requests
and a context variable for tenant ID that can be used throughout the application.
"""
import logging
from contextvars import ContextVar
from typing import Optional, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Context variable to store tenant ID
tenant_id_var = ContextVar('tenant_id', default=None)

class TenantContext:
    """Manages tenant context throughout request lifecycle."""
    
    @staticmethod
    def set_tenant_id(tenant_id: Optional[str]) -> None:
        """
        Set the current tenant ID in context.
        
        Args:
            tenant_id: Tenant ID to set, or None to clear
        """
        tenant_id_var.set(tenant_id)
        if tenant_id:
            logger.debug(f"Set tenant context: {tenant_id}")
        else:
            logger.debug("Cleared tenant context")
    
    @staticmethod
    def get_tenant_id() -> Optional[str]:
        """
        Get the current tenant ID from context.
        
        Returns:
            The current tenant ID or None if not set
        """
        return tenant_id_var.get()


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant ID from request headers and set tenant context.
    
    This middleware extracts tenant information from request headers and sets up
    the tenant context for the duration of the request.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        tenant_header: str = "X-Tenant-ID",
        exclude_paths: list = None
    ):
        """
        Initialize the tenant middleware.
        
        Args:
            app: The ASGI application
            tenant_header: The header name for tenant ID
            exclude_paths: List of paths to exclude from tenant context
        """
        super().__init__(app)
        self.tenant_header = tenant_header
        self.exclude_paths = exclude_paths or [
            "/health", 
            "/health/live",
            "/health/ready",
            "/",
            "/docs", 
            "/openapi.json",
            "/redoc"
        ]
        logger.info(f"Initialized TenantMiddleware with header: {tenant_header}")
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process the request and handle tenant context.
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
            
        Returns:
            The response from the next middleware or endpoint
        """
        # Skip tenant context for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Extract tenant ID from header
        tenant_id = request.headers.get(self.tenant_header)
        
        try:
            # Set tenant context
            TenantContext.set_tenant_id(tenant_id)
            
            if tenant_id:
                logger.debug(f"Request for tenant: {tenant_id}")
            else:
                logger.debug("No tenant ID in request")
            
            # Process the request
            response = await call_next(request)
            
            return response
        finally:
            # Always clear tenant context
            TenantContext.set_tenant_id(None) 