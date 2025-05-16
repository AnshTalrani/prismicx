"""
Health Check API Routes

This module provides API endpoints for health monitoring and service status checks.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import structlog
from datetime import datetime
import platform
import os

from src.config.config_manager import get_settings
from src.config.settings import Settings
from src.clients.system_users_repository_client import SystemUsersRepositoryClient
from src.clients.campaign_users_repository_client import CampaignUsersRepositoryClient

# Create logger
logger = structlog.get_logger(__name__)

# Create router
router = APIRouter()

# Dependencies
async def get_repository_clients():
    """Dependency to get the repository client instances."""
    system_repo = SystemUsersRepositoryClient()
    campaign_repo = CampaignUsersRepositoryClient()
    
    await system_repo.initialize()
    await campaign_repo.initialize()
    
    return {"system_repo": system_repo, "campaign_repo": campaign_repo}

@router.get("/", response_model=Dict[str, Any])
async def health_check(
    repos: Dict[str, Any] = Depends(get_repository_clients),
    settings: Settings = Depends(get_settings)
):
    """
    Perform a health check of the service.
    
    Returns:
        Health status information
    """
    start_time = datetime.utcnow()
    health_data = {
        "status": "ok",
        "timestamp": start_time.isoformat(),
        "service": "communication-base",
        "version": settings.version,
        "environment": settings.environment,
        "dependencies": {}
    }
    
    # Check repository connections
    try:
        system_repo_status = await repos["system_repo"].ping()
        campaign_repo_status = await repos["campaign_repo"].ping()
        
        health_data["dependencies"]["system_repository"] = {
            "status": "ok" if system_repo_status else "error",
            "details": "Connected" if system_repo_status else "Failed to connect"
        }
        
        health_data["dependencies"]["campaign_repository"] = {
            "status": "ok" if campaign_repo_status else "error",
            "details": "Connected" if campaign_repo_status else "Failed to connect"
        }
        
        if not (system_repo_status and campaign_repo_status):
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["dependencies"]["repositories"] = {
            "status": "error",
            "details": str(e)
        }
        health_data["status"] = "degraded"
    
    # Add system information
    health_data["system"] = {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor() or "unknown"
    }
    
    # Add resource usage information
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        health_data["resources"] = {
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_rss_mb": memory_info.rss / (1024 * 1024),
            "memory_vms_mb": memory_info.vms / (1024 * 1024),
            "threads": process.num_threads()
        }
    except ImportError:
        health_data["resources"] = {
            "details": "psutil not available"
        }
    
    # Calculate response time
    end_time = datetime.utcnow()
    health_data["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
    
    # Log health check
    log_level = "info" if health_data["status"] == "ok" else "warning"
    getattr(logger, log_level)("Health check", status=health_data["status"])
    
    return health_data

@router.get("/readiness", response_model=Dict[str, Any])
async def readiness_check(
    repos: Dict[str, Any] = Depends(get_repository_clients)
):
    """
    Check if the service is ready to handle requests.
    
    Returns:
        Readiness status information
    """
    status = "ok"
    details = {}
    
    # Check repository connections
    try:
        system_repo_status = await repos["system_repo"].ping()
        campaign_repo_status = await repos["campaign_repo"].ping()
        
        details["system_repository"] = {
            "status": "ok" if system_repo_status else "error",
            "ready": system_repo_status
        }
        
        details["campaign_repository"] = {
            "status": "ok" if campaign_repo_status else "error",
            "ready": campaign_repo_status
        }
        
        if not (system_repo_status and campaign_repo_status):
            status = "not_ready"
    except Exception as e:
        details["repositories"] = {
            "status": "error",
            "ready": False,
            "details": str(e)
        }
        status = "not_ready"
    
    # Log readiness check
    log_level = "info" if status == "ok" else "warning"
    getattr(logger, log_level)("Readiness check", status=status)
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details
    }

@router.get("/liveness", response_model=Dict[str, Any])
async def liveness_check():
    """
    Check if the service is alive and running.
    
    Returns:
        Liveness status information
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": 0  # This would typically be calculated from process start time
    } 