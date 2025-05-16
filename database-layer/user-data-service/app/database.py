"""
Database connection management for the User Data Service.

This module initializes and manages database connections for user-related data
and provides utility functions for database operations.
"""

import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "user_data")

# Global database connections
_async_db_client = None
_async_db = None
_sync_db_client = None
_sync_db = None

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionFailure, ServerSelectionTimeoutError)),
    reraise=True
)
async def init_db():
    """
    Initialize database connections with retry logic.
    
    Returns:
        AsyncIOMotorDatabase: The database instance.
    """
    global _async_db_client, _async_db, _sync_db_client, _sync_db
    
    logger.info("Initializing database connections to %s", MONGO_URI)
    
    try:
        # Create async MongoDB client
        _async_db_client = AsyncIOMotorClient(MONGO_URI)
        # No easy way to ping async, just log the attempt
        logger.info("Created AsyncIOMotorClient instance")
        
        # Get async database reference
        _async_db = _async_db_client[MONGO_DB_NAME]
        
        # Create sync MongoDB client
        _sync_db_client = MongoClient(MONGO_URI)
        # Ping the server to verify connection
        _sync_db_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB (sync)")
        
        # Get sync database reference
        _sync_db = _sync_db_client[MONGO_DB_NAME]
        
        return _async_db
    
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error("Failed to connect to MongoDB: %s", str(e))
        raise

async def close_db():
    """Close database connections."""
    global _async_db_client, _sync_db_client
    
    if _async_db_client:
        logger.info("Closing async database connection")
        _async_db_client.close()
    
    if _sync_db_client:
        logger.info("Closing sync database connection")
        _sync_db_client.close()

async def get_mongo_client():
    """
    Get async MongoDB client.
    
    Returns:
        AsyncIOMotorClient: The MongoDB client instance.
    """
    global _async_db_client
    if _async_db_client is None:
        logger.warning("Async database client not initialized, initializing now")
        await init_db()
    return _async_db_client

async def get_db():
    """
    Get async database connection.
    
    Returns:
        AsyncIOMotorDatabase: The database instance.
    """
    global _async_db
    if _async_db is None:
        logger.warning("Async database not initialized, initializing now")
        _async_db = await init_db()
    return _async_db

def get_mongo_client_sync():
    """
    Get sync MongoDB client.
    
    Returns:
        MongoClient: The MongoDB client instance.
    """
    global _sync_db_client
    if _sync_db_client is None:
        logger.warning("Sync database client not initialized, calling init_db is required")
        raise RuntimeError("Sync database client not initialized. Make sure init_db() is called during application startup.")
    return _sync_db_client

def get_db_sync():
    """
    Get sync database connection.
    
    Returns:
        Database: The database instance.
    """
    global _sync_db
    if _sync_db is None:
        logger.warning("Sync database not initialized, calling init_db is required")
        raise RuntimeError("Sync database not initialized. Make sure init_db() is called during application startup.")
    return _sync_db

class TenantAwareCollection:
    """
    A tenant-aware MongoDB collection wrapper.
    
    This class provides a tenant-specific view of a collection by automatically
    applying tenant filtering to all operations.
    """
    
    def __init__(self, db, collection_prefix, tenant_id):
        """
        Initialize the tenant-aware collection.
        
        Args:
            db: The MongoDB database
            collection_prefix: The base name of the collection
            tenant_id: The tenant identifier
        """
        self.db = db
        self.collection_name = f"{collection_prefix}_{tenant_id}"
        self.collection = db[self.collection_name]
    
    def __getattr__(self, name):
        """
        Forward attribute access to the underlying collection.
        
        Args:
            name: Attribute name
            
        Returns:
            The requested attribute from the collection
        """
        return getattr(self.collection, name) 