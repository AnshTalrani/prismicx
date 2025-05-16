"""
Multitenant API package.

Provides API endpoints for multitenant functionality.
"""

from .tenant_routes import router as tenant_router

__all__ = ['tenant_router'] 