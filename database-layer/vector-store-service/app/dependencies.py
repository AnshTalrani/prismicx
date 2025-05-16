"""
Dependencies for FastAPI dependency injection.
Provides access to databases, services, and tenant context.
"""

import os
import logging
from fastapi import Depends, HTTPException, Request, status
from pymongo import MongoClient
from typing import AsyncGenerator, Dict, List, Optional, Union
import httpx
from functools import lru_cache
from middleware import get_current_tenant_id
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logger = logging.getLogger("vector-store-service")

# Environment configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
TENANT_MGMT_URL = os.getenv("TENANT_MGMT_URL", "http://tenant-mgmt-service:8501")

class DatabaseConnections:
    """
    Manages database connections and client instances.
    """
    def __init__(self):
        self.mongodb_client = None
        self.init_mongodb()
        
    def init_mongodb(self):
        """Initialize MongoDB connection."""
        try:
            self.mongodb_client = MongoClient(MONGODB_URL)
            # Test connection
            self.mongodb_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    def get_mongodb_db(self, db_name: str):
        """Get MongoDB database by name."""
        if not self.mongodb_client:
            self.init_mongodb()
        return self.mongodb_client[db_name]
    
    def get_tenant_db(self, tenant_id: str):
        """Get tenant-specific database."""
        if not tenant_id:
            raise ValueError("Tenant ID is required")
        # Format tenant database name
        db_name = f"tenant_{tenant_id}"
        return self.get_mongodb_db(db_name)
    
    def get_system_db(self):
        """Get system-wide database."""
        return self.get_mongodb_db("vector_store_system")
    
    def close(self):
        """Close all database connections."""
        if self.mongodb_client:
            self.mongodb_client.close()

# Global database connections instance
db_connections = DatabaseConnections()

@lru_cache()
def get_http_client():
    """Create and cache an HTTP client for API calls."""
    return httpx.AsyncClient(timeout=10.0)

def get_tenant_id(request: Request) -> str:
    """
    Get tenant ID from request or context.
    
    This dependency provides tenant ID from:
    1. Request state (set by middleware)
    2. Thread-local context variable
    
    If no tenant ID is found, it returns empty string which is used
    for system-wide operations.
    """
    # First try to get from request state
    tenant_id = getattr(request.state, "tenant_id", None)
    
    # If not in request state, try context var
    if not tenant_id:
        tenant_id = get_current_tenant_id()
    
    return tenant_id or ""

def get_mongodb():
    """Get MongoDB client connection."""
    return db_connections.mongodb_client

def get_tenant_mongodb(tenant_id: str = Depends(get_tenant_id)):
    """Get tenant-specific MongoDB database."""
    if tenant_id:
        return db_connections.get_tenant_db(tenant_id)
    else:
        # For system-wide operations or default database
        return db_connections.get_system_db()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def validate_tenant(tenant_id: str, client: httpx.AsyncClient) -> bool:
    """
    Validate tenant ID with Tenant Management Service.
    
    Args:
        tenant_id: The tenant ID to validate
        client: HTTP client to use for the request
        
    Returns:
        True if tenant exists and is active, False otherwise
    """
    if not tenant_id:
        return False
        
    try:
        response = await client.get(
            f"{TENANT_MGMT_URL}/api/v1/tenants/{tenant_id}/validate",
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("exists", False) and data.get("active", False)
        return False
    except Exception as e:
        logger.error(f"Error validating tenant: {e}")
        return False

async def get_validated_tenant_id(
    tenant_id: str = Depends(get_tenant_id),
    client: httpx.AsyncClient = Depends(get_http_client)
) -> str:
    """
    Get and validate tenant ID.
    
    This dependency:
    1. Gets tenant ID from request
    2. Validates it with Tenant Management Service
    3. Returns it if valid, raises HTTPException otherwise
    
    Raises:
        HTTPException: If tenant ID is not valid
    """
    # Skip validation for system-wide operations
    if not tenant_id:
        return ""
        
    is_valid = await validate_tenant(tenant_id, client)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid tenant ID: {tenant_id}"
        )
    
    return tenant_id

# Close connections on application shutdown
def shutdown_db_clients():
    """Clean up database connections at shutdown."""
    db_connections.close() 