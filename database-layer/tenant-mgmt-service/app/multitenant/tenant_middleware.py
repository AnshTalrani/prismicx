"""
Tenant middleware for handling tenant context in incoming requests.
"""
import logging
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from .tenant_manager import TenantManager
from .tenant_context import TenantContext

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant ID from request headers and set tenant context.
    
    This middleware extracts tenant information from request headers and sets up
    the tenant context for the duration of the request.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        tenant_manager: Optional[TenantManager] = None,
        tenant_header: str = "X-Tenant-ID",
        exclude_paths: list = None
    ):
        """
        Initialize the tenant middleware.
        
        Args:
            app (ASGIApp): The ASGI application
            tenant_manager (Optional[TenantManager]): The tenant manager to use
            tenant_header (str): The header name for tenant ID
            exclude_paths (list): List of paths to exclude from tenant context
        """
        super().__init__(app)
        self.tenant_manager = tenant_manager or TenantManager()
        self.tenant_header = tenant_header
        self.exclude_paths = exclude_paths or [
            "/health", 
            "/api/v1/tenant-connection", 
            "/docs", 
            "/openapi.json"
        ]
        
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request and set tenant context.
        
        Args:
            request (Request): The incoming request
            call_next (RequestResponseEndpoint): The next middleware or endpoint
            
        Returns:
            Response: The response from the next middleware or endpoint
        """
        # Clear any existing tenant context
        TenantContext.clear_tenant()
        
        # Skip tenant context for excluded paths
        if self._should_skip_tenant_context(request.url.path):
            return await call_next(request)
        
        # Extract tenant ID from header
        tenant_id = request.headers.get(self.tenant_header)
        if not tenant_id:
            # If no tenant ID header, proceed without tenant context
            logger.debug(f"No tenant ID header ({self.tenant_header}) found in request")
            return await call_next(request)
        
        try:
            # Get tenant info from tenant manager
            tenant_info = await self.tenant_manager.get_tenant_by_id(tenant_id)
            if not tenant_info:
                logger.warning(f"Tenant ID {tenant_id} not found in database")
                return await call_next(request)
            
            # Set tenant context for this request
            self.tenant_manager.set_tenant_context(tenant_info)
            logger.debug(f"Set tenant context for tenant {tenant_id}")
            
            # Process the request with tenant context
            response = await call_next(request)
            
            # Clear tenant context after request is processed
            TenantContext.clear_tenant()
            
            return response
            
        except Exception as e:
            logger.error(f"Error setting tenant context: {str(e)}")
            # Continue without tenant context on error
            return await call_next(request)
    
    def _should_skip_tenant_context(self, path: str) -> bool:
        """
        Check if tenant context should be skipped for this path.
        
        Args:
            path (str): The request path
            
        Returns:
            bool: True if tenant context should be skipped
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths) 