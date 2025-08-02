"""
API Router Module

This module provides the main router for API v1 endpoints, consolidating all
routes from various components of the communication base service.
"""

from fastapi import APIRouter

from src.api.v1.routes.campaigns import router as campaigns_router
from src.api.v1.routes.conversations import router as conversations_router
from src.api.v1.routes.health import router as health_router
from src.api.v1.routes.metrics import router as metrics_router

# Create API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(metrics_router, prefix="/metrics", tags=["metrics"]) 