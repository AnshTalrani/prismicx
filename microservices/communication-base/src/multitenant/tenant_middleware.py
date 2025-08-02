"""
Tenant Middleware Module

This module provides middleware for extracting tenant information from HTTP requests
and establishing tenant context for the duration of request processing.
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send

from .tenant_context import TenantContext
from .tenant_service import TenantService

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware for extracting tenant information from HTTP requests.
    
    This middleware extracts tenant information from request headers or other sources
    and establishes tenant context for the duration of request processing.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_header: str = "X-Tenant-ID",
        tenant_service: Optional[TenantService] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize the tenant middleware.
        
        Args:
            app: The ASGI application.
            tenant_header: The header name for tenant ID extraction.
            tenant_service: Optional tenant service for retrieving tenant details.
            exclude_paths: Optional list of paths to exclude from tenant extraction.
        """
        super().__init__(app)
        self.tenant_header = tenant_header
        self.tenant_service = tenant_service or TenantService()
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request and set tenant context.
        
        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or endpoint in the chain.
            
        Returns:
            The HTTP response.
        """
        # Clear any existing tenant context
        TenantContext.clear_current_tenant()
        
        # Check if path should be excluded
        if self._should_skip_tenant_extraction(request.url.path):
            return await call_next(request)
        
        # Extract tenant ID from header
        tenant_id = request.headers.get(self.tenant_header)
        
        if not tenant_id:
            # Try to extract from query parameters
            tenant_id = request.query_params.get("tenant_id")
            
        if not tenant_id:
            # Try to extract from path parameters
            path_params = getattr(request, "path_params", {})
            tenant_id = path_params.get("tenant_id")
        
        if tenant_id:
            try:
                # Get tenant metadata if available
                tenant_metadata = await self._get_tenant_metadata(tenant_id)
                
                # Set tenant context
                TenantContext.set_current_tenant(tenant_id, tenant_metadata)
                logger.debug(f"Set tenant context for request: {tenant_id}")
                
                # Process request with tenant context
                response = await call_next(request)
                
                # Clear tenant context
                TenantContext.clear_current_tenant()
                return response
                
            except Exception as e:
                logger.error(f"Error setting tenant context: {str(e)}")
                # Continue without tenant context
        
        # Process request without tenant context
        return await call_next(request)
    
    def _should_skip_tenant_extraction(self, path: str) -> bool:
        """
        Check if tenant extraction should be skipped for a path.
        
        Args:
            path: The request path.
            
        Returns:
            True if tenant extraction should be skipped, False otherwise.
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def _get_tenant_metadata(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant metadata from the tenant service.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            Tenant metadata if available, None otherwise.
        """
        try:
            tenant_info = await self.tenant_service.get_tenant_info(tenant_id)
            return tenant_info or {"tenant_id": tenant_id}
        except Exception as e:
            logger.error(f"Error getting tenant metadata: {str(e)}")
            return {"tenant_id": tenant_id}


class TenantAsgiMiddleware:
    """
    ASGI middleware for tenant context management.
    
    This version works at the ASGI level for more granular control and better
    compatibility with different async web frameworks.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_header: str = "X-Tenant-ID",
        tenant_service: Optional[TenantService] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
        Initialize the ASGI tenant middleware.
        
        Args:
            app: The ASGI application.
            tenant_header: The header name for tenant ID extraction.
            tenant_service: Optional tenant service for retrieving tenant details.
            exclude_paths: Optional list of paths to exclude from tenant extraction.
        """
        self.app = app
        self.tenant_header = tenant_header
        self.tenant_service = tenant_service or TenantService()
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Process an ASGI request.
        
        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive function.
            send: The ASGI send function.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract path from scope
        path = scope.get("path", "")
        
        # Check if path should be excluded
        if self._should_skip_tenant_extraction(path):
            await self.app(scope, receive, send)
            return
        
        # Extract tenant ID from headers
        headers = scope.get("headers", [])
        tenant_id = None
        
        for name, value in headers:
            if name.decode("latin1").lower() == self.tenant_header.lower():
                tenant_id = value.decode("latin1")
                break
        
        # Try to extract from query parameters if not found in headers
        if not tenant_id:
            query_string = scope.get("query_string", b"").decode("latin1")
            for param in query_string.split("&"):
                if param.startswith("tenant_id="):
                    tenant_id = param.split("=", 1)[1]
                    break
        
        if tenant_id:
            try:
                # Get tenant metadata if available
                tenant_metadata = await self._get_tenant_metadata(tenant_id)
                
                # Set tenant context
                TenantContext.set_current_tenant(tenant_id, tenant_metadata)
                logger.debug(f"Set tenant context for request: {tenant_id}")
                
                # Process request with tenant context
                await self.app(scope, receive, send)
                
                # Clear tenant context
                TenantContext.clear_current_tenant()
                return
                
            except Exception as e:
                logger.error(f"Error setting tenant context: {str(e)}")
                # Continue without tenant context
        
        # Process request without tenant context
        await self.app(scope, receive, send)
    
    def _should_skip_tenant_extraction(self, path: str) -> bool:
        """
        Check if tenant extraction should be skipped for a path.
        
        Args:
            path: The request path.
            
        Returns:
            True if tenant extraction should be skipped, False otherwise.
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def _get_tenant_metadata(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant metadata from the tenant service.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            Tenant metadata if available, None otherwise.
        """
        try:
            tenant_info = await self.tenant_service.get_tenant_info(tenant_id)
            return tenant_info or {"tenant_id": tenant_id}
        except Exception as e:
            logger.error(f"Error getting tenant metadata: {str(e)}")
            return {"tenant_id": tenant_id} 