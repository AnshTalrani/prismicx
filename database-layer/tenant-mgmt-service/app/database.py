"""
Database connection management for the Tenant Management Service.

This module initializes and manages database connections for the tenant registry
and provides utility functions for database operations.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Global database connection
_db_client = None
_db = None

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
    global _db_client, _db
    
    logger.info("Initializing database connection to %s", settings.MONGODB_URI)
    
    try:
        # Create MongoDB client
        _db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        # Ping the server to verify connection
        await _db_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Get database reference
        _db = _db_client[settings.MONGODB_DB]
        return _db
    
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error("Failed to connect to MongoDB: %s", str(e))
        raise

async def close_db():
    """Close database connections."""
    global _db_client
    if _db_client:
        logger.info("Closing database connection")
        _db_client.close()

async def get_db():
    """
    Get database connection.
    
    Returns:
        AsyncIOMotorDatabase: The database instance.
    """
    global _db
    if _db is None:
        logger.warning("Database not initialized, initializing now")
        _db = await init_db()
    return _db

class DatabaseManager:
    """Manager for tenant database connections."""
    
    def __init__(self):
        """Initialize the database manager."""
        self.tenant_connections = {}
        self.system_connection = None
    
    async def initialize(self):
        """Initialize the database manager."""
        # Initialize system database connection
        self.system_connection = await init_db()
    
    async def get_tenant_connection(self, tenant_id):
        """
        Get a database connection for a specific tenant.
        
        Args:
            tenant_id (str): The tenant ID.
            
        Returns:
            AsyncIOMotorDatabase: The tenant-specific database connection.
        """
        # If connection exists in cache, return it
        if tenant_id in self.tenant_connections:
            return self.tenant_connections[tenant_id]
        
        # Get tenant information from registry
        tenant_collection = self.system_connection.tenants
        tenant_info = await tenant_collection.find_one({"tenant_id": tenant_id})
        
        if not tenant_info:
            logger.error(f"Tenant {tenant_id} not found in registry")
            return None
        
        # Create new connection based on tenant config
        db_config = tenant_info["database_config"]
        client = AsyncIOMotorClient(db_config["connection_string"])
        
        # Store in connection cache
        db = client[db_config["database_name"]]
        self.tenant_connections[tenant_id] = db
        
        logger.info(f"Created new database connection for tenant {tenant_id}")
        return db
    
    async def close_all_connections(self):
        """Close all database connections."""
        # Close tenant connections
        for tenant_id, connection in self.tenant_connections.items():
            logger.info(f"Closing connection for tenant {tenant_id}")
            connection.client.close()
        
        # Close system connection
        if self.system_connection:
            self.system_connection.client.close()
            
        self.tenant_connections = {} 