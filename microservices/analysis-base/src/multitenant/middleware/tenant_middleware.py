"""
Tenant middleware for FastAPI applications.
"""
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..context.tenant_context import set_tenant_context

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle tenant context in requests.
    
    Extracts tenant ID from request headers and sets it in the context.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tenant_header: str = "X-Tenant-ID"
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The ASGI application
            tenant_header: Header name for tenant ID (default: X-Tenant-ID)
        """
        super().__init__(app)
        self.tenant_header = tenant_header

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request and handle tenant context.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in chain
            
        Returns:
            The response from downstream handlers
        """
        # Extract tenant ID from header
        tenant_id = request.headers.get(self.tenant_header)
        
        try:
            # Set tenant context
            set_tenant_context(tenant_id)
            
            # Process request
            response = await call_next(request)
            
            return response
            
        finally:
            # Clear tenant context
            set_tenant_context(None) 