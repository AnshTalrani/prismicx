"""
Rate limiter middleware for the management systems service.
"""

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ..cache.client import CacheClient

logger = logging.getLogger(__name__)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests based on tenant ID.
    Uses Redis for distributed rate limiting.
    """
    
    def __init__(self, app, cache_client: CacheClient):
        """
        Initialize the rate limiter middleware.
        
        Args:
            app: The FastAPI application
            cache_client: Redis cache client instance
        """
        super().__init__(app)
        self.cache_client = cache_client
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and apply rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler
            
        Returns:
            Response: The response from the next middleware/handler
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        # Get tenant ID from request
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id", "default")
            
        # Create rate limit key based on tenant and endpoint
        rate_limit_key = f"{tenant_id}:{request.url.path}"
        
        # Check rate limit
        within_limit = await self.cache_client.check_rate_limit(rate_limit_key)
        if not within_limit:
            logger.warning(f"Rate limit exceeded for tenant {tenant_id}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
            
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(
            self.cache_client.config.rate_limit_requests
        )
        response.headers["X-RateLimit-Window"] = str(
            self.cache_client.config.rate_limit_duration
        )
        
        return response 