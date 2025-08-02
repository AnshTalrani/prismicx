"""
Dependencies for the User Data Service

This module provides dependency injection helpers for the User Data Service.
"""

import logging
from fastapi import Depends, Request
from typing import Optional

from .database import get_db, get_db_sync, get_mongo_client, get_mongo_client_sync, TenantAwareCollection
from app.config import settings
from app.services.user_extension_service import UserExtensionService
from .services.user_context_service import UserContextService

logger = logging.getLogger(__name__)

async def get_user_db():
    """
    Get the user database instance.
    
    Returns:
        Database: The user database instance
    """
    return await get_db()

def get_user_db_sync():
    """
    Get the synchronous user database instance.
    
    Returns:
        Database: The user database instance
    """
    return get_db_sync()

async def get_tenant_aware_collection(collection_prefix: str, request: Request):
    """
    Get a tenant-aware collection.
    
    Args:
        collection_prefix: The base name of the collection
        request: The FastAPI request object
        
    Returns:
        TenantAwareCollection: A tenant-specific view of the collection
    """
    db = await get_db()
    tenant_id = request.state.tenant_id
    if not tenant_id:
        # If no tenant ID, default to a standard collection name
        return db[collection_prefix]
    
    return TenantAwareCollection(db, collection_prefix, tenant_id)

def get_tenant_aware_collection_sync(collection_prefix: str, tenant_id: str):
    """
    Get a synchronous tenant-aware collection.
    
    Args:
        collection_prefix: The base name of the collection
        tenant_id: The tenant ID
        
    Returns:
        TenantAwareCollection: A tenant-specific view of the collection
    """
    db = get_db_sync()
    if not tenant_id:
        # If no tenant ID, default to a standard collection name
        return db[collection_prefix]
    
    return TenantAwareCollection(db, collection_prefix, tenant_id)

async def get_extensions_collection(request: Request):
    """
    Get the user extensions collection for the tenant in the request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        Collection: The user extensions collection
    """
    return await get_tenant_aware_collection("user_extensions", request)

def get_extensions_collection_sync(tenant_id: str):
    """
    Get the synchronous user extensions collection for a tenant.
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        Collection: The user extensions collection
    """
    return get_tenant_aware_collection_sync("user_extensions", tenant_id)

async def get_insights_collection(request: Request):
    """
    Get the user insights collection for the tenant in the request.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        Collection: The user insights collection
    """
    return await get_tenant_aware_collection("user_insights", request)

def get_insights_collection_sync(tenant_id: str):
    """
    Get the synchronous user insights collection for a tenant.
    
    Args:
        tenant_id: The tenant ID
        
    Returns:
        Collection: The user insights collection
    """
    return get_tenant_aware_collection_sync("user_insights", tenant_id)

def get_tenant_id_from_request(request: Request) -> str:
    """
    Extract tenant ID from the request state.
    
    Args:
        request: FastAPI request
        
    Returns:
        str: Tenant ID
    """
    return request.state.tenant_id 

# MongoDB client instance
_mongo_client = None

def get_mongo_client():
    """
    Get or create a MongoDB client.
    
    Returns:
        MongoDB client instance
    """
    global _mongo_client
    if _mongo_client is None:
        connection_string = settings.MONGODB_CONNECTION_STRING
        _mongo_client = MongoClient(connection_string)
        logger.info("MongoDB client initialized")
    return _mongo_client

def get_database():
    """
    Get the MongoDB database instance.
    
    Returns:
        MongoDB database instance
    """
    client = get_mongo_client()
    database = client[settings.MONGODB_DATABASE]
    return database

def get_user_extension_collection(
    tenant_id: str = Depends(get_tenant_id_from_request),
    db = Depends(get_database)
):
    """
    Get the tenant-specific user extension collection.
    
    Args:
        tenant_id: Tenant identifier
        db: MongoDB database instance
    
    Returns:
        MongoDB collection for user extensions
    """
    # Use tenant ID as part of collection name for isolation
    collection_name = f"user_extensions_{tenant_id}"
    return db[collection_name]

def get_extension_service(
    collection: Collection = Depends(get_user_extension_collection),
    db = Depends(get_database)
):
    """
    Get an initialized user extension service.
    
    Args:
        collection: MongoDB collection for user extensions
        db: MongoDB database instance
    
    Returns:
        Initialized UserExtensionService
    """
    service = UserExtensionService(db=db, collection=collection)
    service.initialize(collection=collection)
    return service 

# Global instance of UserContextService
_user_context_service: Optional[UserContextService] = None

async def get_user_context_service() -> UserContextService:
    """
    Get the UserContextService instance.
    
    Returns:
        UserContextService: The UserContextService instance
    """
    global _user_context_service
    
    if _user_context_service is None:
        # Initialize the service if not already done
        _user_context_service = UserContextService()
        mongo_client = await get_mongo_client()
        await _user_context_service.initialize(mongo_client)
        
    return _user_context_service

# Update shutdown event to include _user_context_service
async def on_shutdown():
    """Clean up resources on application shutdown."""
    global _user_extension_service, _user_insight_service, _user_context_service
    
    if _user_insight_service:
        await _user_insight_service.close()
        _user_insight_service = None
        
    if _user_extension_service:
        await _user_extension_service.close()
        _user_extension_service = None
        
    if _user_context_service:
        await _user_context_service.close()
        _user_context_service = None 