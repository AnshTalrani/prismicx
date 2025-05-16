"""
Middleware components for the Vector Store Service.
Provides tenant context management and request logging.
"""

import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("vector-store-service")

# Thread-local storage for tenant context
from contextvars import ContextVar

tenant_context_var: ContextVar[str] = ContextVar("tenant_id", default="")

def get_current_tenant_id() -> str:
    """Get the current tenant ID from the context variable."""
    return tenant_context_var.get()

def set_current_tenant_id(tenant_id: str) -> None:
    """Set the current tenant ID in the context variable."""
    tenant_context_var.set(tenant_id)

async def tenant_header_middleware(request: Request, call_next):
    """
    Extract tenant ID from headers and set in context.
    
    This middleware looks for the X-Tenant-ID header and sets
    it in the request state and context variable for the duration
    of the request.
    """
    tenant_id = request.headers.get("X-Tenant-ID", "")
    token = None
    
    if tenant_id:
        logger.debug(f"Request for tenant: {tenant_id}")
        # Set in context var for thread-local access
        token = tenant_context_var.set(tenant_id)
        # Also add to request state for dependency injection
        request.state.tenant_id = tenant_id
    
    try:
        response = await call_next(request)
        return response
    finally:
        # Clear the context after request is processed
        if token:
            tenant_context_var.reset(token)

async def log_request_middleware(request: Request, call_next):
    """
    Log request details and timing.
    
    This middleware logs information about each request including
    path, method, and execution time.
    """
    start_time = time.time()
    
    method = request.method
    path = request.url.path
    query = request.url.query
    
    logger.info(f"Request: {method} {path}?{query}")
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Response: {method} {path} - Status: {response.status_code} - Time: {process_time:.4f}s")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Error: {method} {path} - Error: {str(e)} - Time: {process_time:.4f}s")
        raise 