"""
Health check API endpoints.

This module provides comprehensive health monitoring endpoints
for the outreach system, including system status, model health,
and performance metrics.
"""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ...config.settings import settings
from ...config.logging_config import get_logger
from ...services.health_service import HealthService

logger = get_logger(__name__)

router = APIRouter()


def get_health_service() -> HealthService:
    """Dependency to get health service."""
    return HealthService()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment
    }


@router.get("/detailed")
async def detailed_health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """Detailed health check with system components."""
    try:
        health_status = await health_service.get_detailed_health()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/models")
async def model_health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """Check health of all AI models."""
    try:
        model_status = await health_service.get_model_health()
        return model_status
    except Exception as e:
        logger.error(f"Model health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model health check failed: {str(e)}"
        )


@router.get("/database")
async def database_health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """Check database connectivity and health."""
    try:
        db_status = await health_service.get_database_health()
        return db_status
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/redis")
async def redis_health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """Check Redis connectivity and health."""
    try:
        redis_status = await health_service.get_redis_health()
        return redis_status
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis health check failed: {str(e)}"
        )


@router.get("/external-services")
async def external_services_health_check(
    health_service: HealthService = Depends(get_health_service)
):
    """Check health of external services (APIs, etc.)."""
    try:
        external_status = await health_service.get_external_services_health()
        return external_status
    except Exception as e:
        logger.error(f"External services health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External services health check failed: {str(e)}"
        )


@router.get("/performance")
async def performance_metrics(
    health_service: HealthService = Depends(get_health_service)
):
    """Get system performance metrics."""
    try:
        performance_metrics = await health_service.get_performance_metrics()
        return performance_metrics
    except Exception as e:
        logger.error(f"Performance metrics check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Performance metrics check failed: {str(e)}"
        )


@router.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if all critical services are ready
        health_service = HealthService()
        health_status = await health_service.get_detailed_health()
        
        # Check if all critical components are healthy
        all_healthy = all(
            component.get("status") == "healthy"
            for component in health_status.get("components", {}).values()
        )
        
        if all_healthy:
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="System not ready"
            )
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not ready"
        )


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    try:
        # Simple check to ensure the application is running
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Liveness probe failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not alive"
        )


@router.get("/info")
async def system_info():
    """Get system information and configuration."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "api_prefix": settings.api_prefix,
        "features": {
            "realtime": settings.enable_realtime,
            "analytics": settings.enable_analytics,
            "notifications": settings.enable_notifications,
            "metrics": settings.enable_metrics
        },
        "models": {
            "whisper": {
                "model_size": settings.whisper_model_size,
                "device": settings.whisper_device
            },
            "llm": {
                "provider": settings.llm_provider,
                "model": settings.openai_model if settings.llm_provider == "openai" else settings.anthropic_model
            },
            "tts": {
                "provider": "kokoro",
                "device": settings.kokoro_device
            },
            "emotion": {
                "confidence_threshold": settings.emotion_confidence_threshold
            }
        }
    } 