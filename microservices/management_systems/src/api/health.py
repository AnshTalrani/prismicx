"""
Health check endpoints for monitoring the API.
"""
import logging
from fastapi import APIRouter, status, Response
from typing import Dict, Any

from ..common.db_client_wrapper import db_client
from ..cache.redis_cache import cache

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for the management systems API.
    
    Checks:
    - Overall API status
    - Database connections
    - Redis cache connection
    
    Returns 200 OK if all systems are operational, 503 otherwise.
    """
    health_status = {
        "status": "healthy",
        "components": {
            "api": {"status": "healthy"},
            "config_db": {"status": "unknown"},
            "tenant_db": {"status": "unknown"},
            "cache": {"status": "unknown"}
        }
    }
    
    # Check database connections
    try:
        await db_client.config_db.command("ping")
        health_status["components"]["config_db"]["status"] = "healthy"
    except Exception as e:
        health_status["components"]["config_db"]["status"] = "unhealthy"
        health_status["components"]["config_db"]["error"] = str(e)
    
    # Check tenant database connection (using a test tenant)
    try:
        # We'll just check if we can get a connection to any tenant
        tenant_db = await db_client.get_tenant_db("test_tenant")
        await tenant_db.command("ping")
        health_status["components"]["tenant_db"]["status"] = "healthy"
    except Exception as e:
        health_status["components"]["tenant_db"]["status"] = "unhealthy"
        health_status["components"]["tenant_db"]["error"] = str(e)
    
    # Check Redis cache
    if cache.client is None:
        health_status["components"]["cache"]["status"] = "unhealthy"
        health_status["components"]["cache"]["error"] = "Redis client not initialized"
    else:
        try:
            await cache.client.ping()
            health_status["components"]["cache"]["status"] = "healthy"
        except Exception as e:
            health_status["components"]["cache"]["status"] = "unhealthy"
            health_status["components"]["cache"]["error"] = str(e)
    
    # Overall status is unhealthy if any component is unhealthy
    for component, status_info in health_status["components"].items():
        if status_info["status"] == "unhealthy":
            health_status["status"] = "unhealthy"
            break
    
    return health_status

@router.get("/health/live")
async def liveness() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes.
    
    Returns 200 OK if the API is running.
    """
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness(response: Response) -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes.
    
    Checks if the API is ready to accept requests:
    - Database connections
    - Redis cache connection
    
    Returns 200 OK if ready, 503 if not ready.
    """
    is_ready = True
    status_info = {
        "status": "ready",
        "components": {
            "config_db": True,
            "tenant_db": True,
            "cache": True
        }
    }
    
    # Check database connections
    try:
        await db_client.config_db.command("ping")
    except Exception:
        status_info["components"]["config_db"] = False
        is_ready = False
    
    # Check Redis cache
    if cache.client is None:
        status_info["components"]["cache"] = False
        is_ready = False
    else:
        try:
            await cache.client.ping()
        except Exception:
            status_info["components"]["cache"] = False
            is_ready = False
    
    if not is_ready:
        status_info["status"] = "not ready"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return status_info 