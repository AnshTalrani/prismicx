"""
Database Client for PrismicX Microservices

This module provides a client for connecting to the Database Access Layer (DAL)
and accessing both tenant-specific and system-wide databases.
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, List, Optional, Any, Union
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseClient:
    """
    Client for accessing databases through the Database Access Layer.
    
    This client maintains connections to both tenant-specific and system-wide
    databases, and provides methods for querying data with proper tenant isolation.
    """
    
    def __init__(self, 
                 tenant_mgmt_url: str = None,
                 user_data_url: str = None,
                 redis_url: str = None,
                 service_name: str = None):
        """
        Initialize the database client.
        
        Args:
            tenant_mgmt_url: URL for the Tenant Management Service.
            user_data_url: URL for the User Data Service.
            redis_url: URL for Redis.
            service_name: Name of the calling service (for logging).
        """
        self.tenant_mgmt_url = tenant_mgmt_url or os.environ.get("TENANT_MGMT_URL", "http://tenant-mgmt-service:8501")
        self.user_data_url = user_data_url or os.environ.get("USER_DATA_URL", "http://user-data-service:8502")
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://:password@redis-cache:6379/0")
        self.service_name = service_name or os.environ.get("SERVICE_NAME", "unknown-service")
        
        # Connection pools
        self.tenant_connections = {}
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"Initialized DatabaseClient for {self.service_name}")
    
    async def close(self):
        """Close all database connections."""
        # Close MongoDB connections
        for tenant_id, conn in self.tenant_connections.items():
            logger.debug(f"Closing connection for tenant {tenant_id}")
            conn.client.close()
        
        # Close HTTP client
        await self.http_client.aclose()
        
        logger.info("Closed all database connections")
    
    async def get_tenant_connection(self, tenant_id: str):
        """
        Get a database connection for a specific tenant.
        
        Args:
            tenant_id: The tenant ID.
            
        Returns:
            A database connection for the tenant.
            
        Raises:
            ConnectionError: If the tenant database cannot be accessed.
        """
        # Check if connection exists in cache
        if tenant_id in self.tenant_connections:
            return self.tenant_connections[tenant_id]
        
        try:
            # Get tenant database information from Tenant Management Service
            headers = {"X-Tenant-ID": tenant_id}
            response = await self.http_client.get(
                f"{self.tenant_mgmt_url}/api/v1/tenant-connection",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get tenant connection: {response.text}")
                raise ConnectionError(f"Failed to get tenant connection: {response.status_code}")
            
            # Parse response
            tenant_info = response.json()
            db_config = tenant_info["database_config"]
            
            # Create MongoDB connection
            client = AsyncIOMotorClient(db_config["connection_string"])
            db = client[db_config["database_name"]]
            
            # For shared databases, we need to ensure tenant isolation
            if db_config["type"] == "shared" and "shard_key" in db_config:
                # Create a tenant-specific view of the database
                db = TenantDatabaseView(db, tenant_id, db_config["shard_key"])
            
            # Cache the connection
            self.tenant_connections[tenant_id] = db
            logger.info(f"Created database connection for tenant {tenant_id}")
            
            return db
            
        except (ConnectionError, httpx.HTTPError) as e:
            logger.error(f"Error connecting to tenant database: {str(e)}")
            raise ConnectionError(f"Error connecting to tenant database: {str(e)}")
    
    async def get_system_data(self, resource_type: str, resource_id: str, tenant_context: str = None):
        """
        Get data from a system-wide database through the appropriate service.
        
        Args:
            resource_type: The type of resource (e.g., 'users', 'preferences').
            resource_id: The resource ID.
            tenant_context: Optional tenant context for multi-tenant system data.
            
        Returns:
            The requested resource.
            
        Raises:
            ConnectionError: If the system database cannot be accessed.
        """
        try:
            # Determine the appropriate service URL based on resource type
            if resource_type in ['users', 'user']:
                service_url = f"{self.user_data_url}/api/v1/users/{resource_id}"
            elif resource_type in ['preferences', 'user_preferences']:
                service_url = f"{self.user_data_url}/api/v1/preferences/{resource_id}"
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
            
            # Set headers for tenant context if provided
            headers = {}
            if tenant_context:
                headers["X-Tenant-ID"] = tenant_context
            
            # Make request to the service
            response = await self.http_client.get(service_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get system data: {response.text}")
                raise ConnectionError(f"Failed to get system data: {response.status_code}")
            
            return response.json()
            
        except (ConnectionError, httpx.HTTPError) as e:
            logger.error(f"Error connecting to system database: {str(e)}")
            raise ConnectionError(f"Error connecting to system database: {str(e)}")


class TenantDatabaseView:
    """
    A tenant-specific view of a shared database.
    
    This class wraps a MongoDB database and automatically applies tenant filtering
    to all operations to ensure proper tenant isolation in a shared database.
    """
    
    def __init__(self, db, tenant_id: str, tenant_field: str = "tenant_id"):
        """
        Initialize the tenant database view.
        
        Args:
            db: The MongoDB database.
            tenant_id: The tenant ID.
            tenant_field: The field name used for tenant identification.
        """
        self.db = db
        self.tenant_id = tenant_id
        self.tenant_field = tenant_field
        
        # Create the tenant filter
        self.tenant_filter = {tenant_field: tenant_id}
    
    def __getattr__(self, name):
        """
        Get a tenant-filtered collection.
        
        Args:
            name: The collection name.
            
        Returns:
            A tenant-filtered collection.
        """
        # Get the original collection
        collection = getattr(self.db, name)
        
        # Return a tenant-filtered view of the collection
        return TenantCollectionView(collection, self.tenant_id, self.tenant_filter)


class TenantCollectionView:
    """
    A tenant-specific view of a shared collection.
    
    This class wraps a MongoDB collection and automatically applies tenant filtering
    to all operations to ensure proper tenant isolation.
    """
    
    def __init__(self, collection, tenant_id: str, tenant_filter: Dict[str, str]):
        """
        Initialize the tenant collection view.
        
        Args:
            collection: The MongoDB collection.
            tenant_id: The tenant ID.
            tenant_filter: The tenant filter to apply.
        """
        self.collection = collection
        self.tenant_id = tenant_id
        self.tenant_filter = tenant_filter
    
    async def find_one(self, filter: Dict = None, *args, **kwargs):
        """
        Find a single document with tenant isolation.
        
        Args:
            filter: The query filter.
            *args: Additional arguments for find_one.
            **kwargs: Additional keyword arguments for find_one.
            
        Returns:
            The found document or None.
        """
        # Add tenant filter to query
        filter = filter or {}
        tenant_filter = {**filter, **self.tenant_filter}
        
        # Execute query with tenant isolation
        return await self.collection.find_one(tenant_filter, *args, **kwargs)
    
    def find(self, filter: Dict = None, *args, **kwargs):
        """
        Find documents with tenant isolation.
        
        Args:
            filter: The query filter.
            *args: Additional arguments for find.
            **kwargs: Additional keyword arguments for find.
            
        Returns:
            A cursor for the found documents.
        """
        # Add tenant filter to query
        filter = filter or {}
        tenant_filter = {**filter, **self.tenant_filter}
        
        # Execute query with tenant isolation
        return self.collection.find(tenant_filter, *args, **kwargs)
    
    async def insert_one(self, document: Dict, *args, **kwargs):
        """
        Insert a document with tenant ID.
        
        Args:
            document: The document to insert.
            *args: Additional arguments for insert_one.
            **kwargs: Additional keyword arguments for insert_one.
            
        Returns:
            The result of the insert operation.
        """
        # Add tenant ID to document
        document = {**document, **self.tenant_filter}
        
        # Execute insert with tenant ID
        return await self.collection.insert_one(document, *args, **kwargs)
    
    async def insert_many(self, documents: List[Dict], *args, **kwargs):
        """
        Insert multiple documents with tenant ID.
        
        Args:
            documents: The documents to insert.
            *args: Additional arguments for insert_many.
            **kwargs: Additional keyword arguments for insert_many.
            
        Returns:
            The result of the insert operation.
        """
        # Add tenant ID to each document
        documents = [{**doc, **self.tenant_filter} for doc in documents]
        
        # Execute insert with tenant ID
        return await self.collection.insert_many(documents, *args, **kwargs)
    
    async def update_one(self, filter: Dict, update: Dict, *args, **kwargs):
        """
        Update a document with tenant isolation.
        
        Args:
            filter: The query filter.
            update: The update to apply.
            *args: Additional arguments for update_one.
            **kwargs: Additional keyword arguments for update_one.
            
        Returns:
            The result of the update operation.
        """
        # Add tenant filter to query
        filter = {**filter, **self.tenant_filter}
        
        # Ensure tenant ID is not modified
        if "$set" in update:
            update["$set"] = {k: v for k, v in update["$set"].items() if k != list(self.tenant_filter.keys())[0]}
        
        # Execute update with tenant isolation
        return await self.collection.update_one(filter, update, *args, **kwargs)
    
    async def update_many(self, filter: Dict, update: Dict, *args, **kwargs):
        """
        Update multiple documents with tenant isolation.
        
        Args:
            filter: The query filter.
            update: The update to apply.
            *args: Additional arguments for update_many.
            **kwargs: Additional keyword arguments for update_many.
            
        Returns:
            The result of the update operation.
        """
        # Add tenant filter to query
        filter = {**filter, **self.tenant_filter}
        
        # Ensure tenant ID is not modified
        if "$set" in update:
            update["$set"] = {k: v for k, v in update["$set"].items() if k != list(self.tenant_filter.keys())[0]}
        
        # Execute update with tenant isolation
        return await self.collection.update_many(filter, update, *args, **kwargs)
    
    async def delete_one(self, filter: Dict, *args, **kwargs):
        """
        Delete a document with tenant isolation.
        
        Args:
            filter: The query filter.
            *args: Additional arguments for delete_one.
            **kwargs: Additional keyword arguments for delete_one.
            
        Returns:
            The result of the delete operation.
        """
        # Add tenant filter to query
        filter = {**filter, **self.tenant_filter}
        
        # Execute delete with tenant isolation
        return await self.collection.delete_one(filter, *args, **kwargs)
    
    async def delete_many(self, filter: Dict, *args, **kwargs):
        """
        Delete multiple documents with tenant isolation.
        
        Args:
            filter: The query filter.
            *args: Additional arguments for delete_many.
            **kwargs: Additional keyword arguments for delete_many.
            
        Returns:
            The result of the delete operation.
        """
        # Add tenant filter to query
        filter = {**filter, **self.tenant_filter}
        
        # Execute delete with tenant isolation
        return await self.collection.delete_many(filter, *args, **kwargs)
    
    async def count_documents(self, filter: Dict = None, *args, **kwargs):
        """
        Count documents with tenant isolation.
        
        Args:
            filter: The query filter.
            *args: Additional arguments for count_documents.
            **kwargs: Additional keyword arguments for count_documents.
            
        Returns:
            The count of documents.
        """
        # Add tenant filter to query
        filter = filter or {}
        filter = {**filter, **self.tenant_filter}
        
        # Execute count with tenant isolation
        return await self.collection.count_documents(filter, *args, **kwargs)


# Singleton instance of the database client
_client = None


async def get_client() -> DatabaseClient:
    """
    Get the singleton instance of the database client.
    
    Returns:
        The database client instance.
    """
    global _client
    if _client is None:
        _client = DatabaseClient()
    return _client


async def get_tenant_connection(tenant_id: str):
    """
    Get a database connection for a specific tenant.
    
    Args:
        tenant_id: The tenant ID.
        
    Returns:
        A database connection for the tenant.
    """
    client = await get_client()
    return await client.get_tenant_connection(tenant_id)


async def get_system_data(resource_type: str, resource_id: str, tenant_context: str = None):
    """
    Get data from a system-wide database.
    
    Args:
        resource_type: The type of resource (e.g., 'users', 'preferences').
        resource_id: The resource ID.
        tenant_context: Optional tenant context for multi-tenant system data.
        
    Returns:
        The requested resource.
    """
    client = await get_client()
    return await client.get_system_data(resource_type, resource_id, tenant_context) 