"""
Database client wrapper for integrating with the database-layer.

This module provides a standardized way to access database functionality from the database-layer
through HTTP API calls instead of direct database connections, following the MACH architecture.
"""
import logging
import os
from typing import Any, Dict, Optional

from ..clients.management_system_repo_client import ManagementSystemRepoClient
from ..clients.config_db_client import ConfigDBClient

logger = logging.getLogger(__name__)

class DatabaseClientError(Exception):
    """Base class for database client errors."""
    pass

class TenantDatabaseError(DatabaseClientError):
    """Error related to tenant database operations."""
    pass

class ConfigDatabaseError(DatabaseClientError):
    """Error related to configuration database operations."""
    pass

class DatabaseClientWrapper:
    """
    Wrapper for accessing database-layer services through HTTP APIs.
    
    This wrapper uses HTTP clients to communicate with the database layer,
    following the MACH architecture principles of using API calls instead
    of direct database connections.
    """
    
    def __init__(self):
        """Initialize the database client wrapper."""
        self._initialized = False
        self._config_db_client = None
        self._management_repo_client = None
        logger.info("DatabaseClientWrapper initialized")
    
    async def initialize(self):
        """Initialize the database client wrapper."""
        if self._initialized:
            return
            
        try:
            # Initialize config DB client
            config_db_url = os.getenv("MANAGEMENT_SYSTEM_REPO_URL", "http://management-system-repo:8080")
            config_db_api_key = os.getenv("MANAGEMENT_SYSTEM_REPO_API_KEY", "dev_api_key")
            
            self._config_db_client = ConfigDBClient(config_db_url, config_db_api_key)
            await self._config_db_client.initialize()
            
            # Initialize management repo client
            repo_url = os.getenv("MANAGEMENT_SYSTEM_REPO_URL", "http://management-system-repo:8080")
            repo_api_key = os.getenv("MANAGEMENT_SYSTEM_REPO_API_KEY", "dev_api_key")
            
            self._management_repo_client = ManagementSystemRepoClient(repo_url, repo_api_key)
            await self._management_repo_client.initialize()
            
            self._initialized = True
            logger.info("DatabaseClientWrapper initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize database client wrapper: {str(e)}"
            logger.error(error_msg)
            raise DatabaseClientError(error_msg) from e
    
    async def close(self):
        """Close all database client connections."""
        if self._config_db_client:
            await self._config_db_client.close()
            
        if self._management_repo_client:
            await self._management_repo_client.close()
            
        self._initialized = False
        logger.info("DatabaseClientWrapper closed")
    
    async def ensure_collection(self, tenant_id: str, collection_name: str) -> bool:
        """
        Ensure that a collection exists in the tenant database.
        
        Args:
            tenant_id: The unique identifier for the tenant
            collection_name: The name of the collection to ensure
            
        Returns:
            True if the collection was created or already exists, False otherwise
            
        Raises:
            TenantDatabaseError: If there's an error creating the collection
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Call the management system repo API to ensure collection
            url = f"{self._management_repo_client.base_url}/api/v1/tenants/{tenant_id}/collections/{collection_name}"
            response = await self._management_repo_client.http_client.put(url)
            
            if response.status_code not in (200, 201):
                error_msg = f"Failed to ensure collection {collection_name} for tenant {tenant_id}: {response.text}"
                logger.error(error_msg)
                raise TenantDatabaseError(error_msg)
                
            logger.info(f"Ensured collection {collection_name} for tenant {tenant_id}")
            return True
        except Exception as e:
            error_msg = f"Failed to ensure collection {collection_name} for tenant {tenant_id}: {str(e)}"
            logger.error(error_msg)
            raise TenantDatabaseError(error_msg) from e
    
    @property
    def config_db_client(self) -> ConfigDBClient:
        """Get the config DB client."""
        if not self._initialized:
            raise DatabaseClientError("Database client wrapper not initialized")
            
        return self._config_db_client
    
    @property
    def management_repo_client(self) -> ManagementSystemRepoClient:
        """Get the management system repo client."""
        if not self._initialized:
            raise DatabaseClientError("Database client wrapper not initialized")
            
        return self._management_repo_client

# Global database client instance
db_client = DatabaseClientWrapper() 