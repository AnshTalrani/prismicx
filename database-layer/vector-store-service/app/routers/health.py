"""
Health check endpoints for the vector store service.
"""

from fastapi import APIRouter, Depends
from pymongo.database import Database
from dependencies import get_mongodb
import platform
import os
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: Database = Depends(get_mongodb)):
    """
    Check the health of the vector store service.
    
    Performs basic health checks:
    - Verifies the database connection
    - Returns system information
    - Reports service uptime
    
    Returns:
        Health status information
    """
    # Check database connection
    try:
        db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    # Get system information
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor()
    }
    
    # Get service information
    service_start_time = getattr(health_check, "start_time", time.time())
    if not hasattr(health_check, "start_time"):
        health_check.start_time = service_start_time
    
    uptime_seconds = int(time.time() - service_start_time)
    
    # Get environment information
    vector_store_dir = os.getenv("VECTOR_STORE_DIR", "./data/vector_stores")
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "time": time.time(),
        "database": {
            "status": db_status,
        },
        "system": system_info,
        "service": {
            "name": "vector-store-service",
            "uptime_seconds": uptime_seconds,
            "vector_store_dir": vector_store_dir,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    }

@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancers and monitoring.
    
    Returns:
        Simple pong response for liveness checks
    """
    return {"ping": "pong", "time": time.time()} 