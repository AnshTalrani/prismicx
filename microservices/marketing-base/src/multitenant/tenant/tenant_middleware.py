"""
Middleware for handling tenant context in requests.

This module provides middleware for extracting tenant information from requests
and setting it in the tenant context for downstream handlers.
"""

import re
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

from ...config.app_config import get_config
from ...domain.repositories.tenant_repository import TenantRepository
from ...config.logging_config import get_logger
from ..context.tenant_context import TenantContext


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract tenant information from requests."""
    
    def __init__(self, app, tenant_repository: TenantRepository):
        """Initialize middleware with tenant repository."""
        super().__init__(app)
        self.tenant_repository = tenant_repository
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.tenant_header = self.config.tenant_header
        self.subdomain_enabled = self.config.tenant_subdomain_enabled
        self.path_enabled = self.config.tenant_path_enabled
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request to extract and validate tenant information."""
        # Clear tenant context at the beginning of the request
        TenantContext.clear()
        
        # Skip tenant extraction for health and docs endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        tenant_id = await self._extract_tenant_id(request)
        
        if not tenant_id:
            self.logger.warning("No tenant ID found in request")
            return Response(
                content="Tenant ID is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="text/plain"
            )
        
        # Validate tenant exists
        tenant = await self.tenant_repository.get_tenant_by_id(tenant_id)
        if not tenant:
            self.logger.warning(f"Invalid tenant ID: {tenant_id}")
            return Response(
                content="Invalid tenant ID",
                status_code=status.HTTP_403_FORBIDDEN,
                media_type="text/plain"
            )
        
        # Set tenant in context for this request
        TenantContext.set_tenant_id(tenant_id)
        self.logger.debug(f"Tenant context set: {tenant_id}")
        
        # Process the request with tenant context set
        try:
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context at the end of the request
            TenantContext.clear()
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if the path is a public endpoint that doesn't require tenant context."""
        public_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        return any(path.startswith(public_path) for public_path in public_paths)
    
    async def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request using configured methods."""
        # Try to get tenant from header
        tenant_id = request.headers.get(self.tenant_header)
        if tenant_id:
            return tenant_id
        
        # Try to get tenant from subdomain if enabled
        if self.subdomain_enabled:
            tenant_id = self._extract_tenant_from_subdomain(request)
            if tenant_id:
                return tenant_id
        
        # Try to get tenant from path if enabled
        if self.path_enabled:
            tenant_id = self._extract_tenant_from_path(request)
            if tenant_id:
                return tenant_id
        
        return None
    
    def _extract_tenant_from_subdomain(self, request: Request) -> Optional[str]:
        """Extract tenant ID from subdomain."""
        host = request.headers.get("host", "")
        # Pattern to match subdomain.domain.com
        subdomain_pattern = r"^([a-zA-Z0-9-]+)\."
        match = re.match(subdomain_pattern, host)
        if match:
            return match.group(1)
        return None
    
    def _extract_tenant_from_path(self, request: Request) -> Optional[str]:
        """Extract tenant ID from URL path."""
        # Pattern to match /tenants/{tenant_id}/...
        path_pattern = r"/tenants/([a-zA-Z0-9-]+)/"
        match = re.search(path_pattern, request.url.path)
        if match:
            return match.group(1)
        return None 