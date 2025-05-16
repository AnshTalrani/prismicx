"""
Data Storage Module

This module manages data storage across different database types and caching.
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLDatabase:
    """
    Handles SQL database operations.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize SQL database connection.
        
        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string or "sqlite:///analysis.db"
        logger.info(f"SQL database initialized with connection: {self.connection_string}")
    
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Query results
        """
        try:
            logger.info(f"Executing SQL query: {query[:50]}...")
            
            # This is a placeholder for actual SQL execution
            # In a real implementation, this would use SQLAlchemy or similar
            
            # Simulate query execution
            await asyncio.sleep(0.2)
            
            # Return dummy results
            return [{"result": "dummy_data"}]
            
        except Exception as e:
            logger.error(f"SQL query execution failed: {str(e)}")
            raise
    
    async def store_data(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Store data in a SQL table.
        
        Args:
            table: Table name
            data: Data to store
            
        Returns:
            Success status
        """
        try:
            logger.info(f"Storing data in SQL table: {table}")
            
            # This is a placeholder for actual data storage
            # In a real implementation, this would use SQLAlchemy or similar
            
            # Simulate data storage
            await asyncio.sleep(0.2)
            
            return True
            
        except Exception as e:
            logger.error(f"SQL data storage failed: {str(e)}")
            raise

class NoSQLDatabase:
    """
    Handles NoSQL database operations.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize NoSQL database connection.
        
        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string or "mongodb://localhost:27017"
        logger.info(f"NoSQL database initialized with connection: {self.connection_string}")
    
    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data
        """
        try:
            logger.info(f"Getting NoSQL document: {doc_id}")
            
            # This is a placeholder for actual document retrieval
            # In a real implementation, this would use pymongo or similar
            
            # Simulate document retrieval
            await asyncio.sleep(0.2)
            
            # Return dummy document
            return {"_id": doc_id, "data": "dummy_data"}
            
        except Exception as e:
            logger.error(f"NoSQL document retrieval failed: {str(e)}")
            raise
    
    async def store_document(self, collection: str, data: Dict[str, Any]) -> str:
        """
        Store a document in a collection.
        
        Args:
            collection: Collection name
            data: Document data
            
        Returns:
            Document ID
        """
        try:
            logger.info(f"Storing document in NoSQL collection: {collection}")
            
            # This is a placeholder for actual document storage
            # In a real implementation, this would use pymongo or similar
            
            # Simulate document storage
            await asyncio.sleep(0.2)
            
            # Generate dummy ID
            doc_id = "doc_" + str(hash(json.dumps(data, sort_keys=True)) % 10000)
            
            return doc_id
            
        except Exception as e:
            logger.error(f"NoSQL document storage failed: {str(e)}")
            raise

class RedisCache:
    """
    Handles Redis cache operations.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize Redis cache connection.
        
        Args:
            connection_string: Cache connection string
        """
        self.connection_string = connection_string or "redis://localhost:6379/0"
        logger.info(f"Redis cache initialized with connection: {self.connection_string}")
    
    async def set_cache(self, key: str, value: str) -> bool:
        """
        Set a cache value.
        
        Args:
            key: Cache key
            value: Cache value
            
        Returns:
            Success status
        """
        try:
            logger.info(f"Setting cache key: {key}")
            
            # This is a placeholder for actual cache setting
            # In a real implementation, this would use redis-py or similar
            
            # Simulate cache setting
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache setting failed: {str(e)}")
            raise
    
    async def get_cache(self, key: str) -> Optional[str]:
        """
        Get a cache value.
        
        Args:
            key: Cache key
            
        Returns:
            Cache value or None if not found
        """
        try:
            logger.info(f"Getting cache key: {key}")
            
            # This is a placeholder for actual cache retrieval
            # In a real implementation, this would use redis-py or similar
            
            # Simulate cache retrieval
            await asyncio.sleep(0.1)
            
            # Return dummy value
            return f"cached_value_for_{key}"
            
        except Exception as e:
            logger.error(f"Cache retrieval failed: {str(e)}")
            return None

class DataStorage:
    """
    Manages data storage across different database types and caching.
    """
    
    def __init__(self):
        """Initialize data storage components"""
        self.sql_db = SQLDatabase()
        self.nosql_db = NoSQLDatabase()
        self.cache = RedisCache()
        logger.info("Data storage initialized")
    
    async def store_processed_data(self, data: Dict[str, Any], store_in: str = "default") -> Dict[str, Any]:
        """
        Store processed data in the appropriate storage.
        
        Args:
            data: Data to store
            store_in: Storage destination specified in template
            
        Returns:
            Storage metadata
        """
        try:
            logger.info(f"Storing processed data in {store_in}")
            
            # Generate storage ID
            storage_id = f"data_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(json.dumps(data)) % 10000}"
            
            # Determine storage type based on store_in
            storage_metadata = {
                "storage_id": storage_id,
                "timestamp": datetime.now().isoformat(),
                "store_in": store_in
            }
            
            if store_in == "sql_db" or store_in == "relational":
                # Store in SQL database
                table_name = data.get("template_id", "analysis_results").lower().replace("-", "_")
                await self.sql_db.store_data(table_name, data)
                storage_metadata["storage_type"] = "sql"
                storage_metadata["table"] = table_name
                
            elif store_in == "nosql_db" or store_in == "document":
                # Store in NoSQL database
                collection = data.get("analysis_type", "analysis_results")
                doc_id = await self.nosql_db.store_document(collection, data)
                storage_metadata["storage_type"] = "nosql"
                storage_metadata["collection"] = collection
                storage_metadata["document_id"] = doc_id
                
            elif store_in == "cache" or store_in == "temporary":
                # Store in cache
                cache_key = f"result_{storage_id}"
                await self.cache.set_cache(cache_key, json.dumps(data))
                storage_metadata["storage_type"] = "cache"
                storage_metadata["cache_key"] = cache_key
                
            elif store_in == "metadata_db":
                # Store as metadata
                # This is typically for results that enhance future analyses
                doc_id = data.get("template_id", storage_id)
                await self.nosql_db.store_document("metadata", data)
                storage_metadata["storage_type"] = "metadata"
                storage_metadata["document_id"] = doc_id
                
                # Also cache for quick access
                cache_key = f"metadata_{doc_id}"
                await self.cache.set_cache(cache_key, json.dumps(data))
                storage_metadata["cached"] = True
                
            else:
                # Default storage (combination of NoSQL and cache)
                doc_id = data.get("template_id", storage_id)
                await self.nosql_db.store_document("analysis_results", data)
                storage_metadata["storage_type"] = "default"
                storage_metadata["document_id"] = doc_id
                
                # Cache for quick access
                cache_key = f"data_{doc_id}"
                cache_value = json.dumps({"doc_id": doc_id, "timestamp": data.get("timestamp")})
                success = await self.cache.set_cache(cache_key, cache_value)
                storage_metadata["cached"] = success
            
            return storage_metadata
            
        except Exception as e:
            logger.error(f"Data storage failed: {str(e)}")
            
            # Log the error
            from ..error_handler.error_logger import error_logger
            error_id = error_logger.log_error(e, {"store_in": store_in})
            
            return {
                "storage_error": True,
                "error_id": error_id,
                "message": str(e)
            }
    
    async def retrieve_data(self, query: str) -> Dict[str, Any]:
        """
        Retrieve data based on query.
        
        Args:
            query: Query string
            
        Returns:
            Retrieved data
        """
        try:
            logger.info(f"Retrieving data with query: {query}")
            
            # Check cache first
            cache_key = f"query_{hash(query) % 10000}"
            cached_data = await self.cache.get_cache(cache_key)
            
            if cached_data:
                logger.info("Retrieved data from cache")
                return json.loads(cached_data)
            
            # Determine query type and execute
            if query.strip().upper().startswith("SELECT"):
                # SQL query
                results = await self.sql_db.execute_query(query)
                return {"source": "sql", "results": results}
            else:
                # Assume NoSQL query
                doc_id = query
                document = await self.nosql_db.get_document(doc_id)
                return {"source": "nosql", "document": document}
            
        except Exception as e:
            logger.error(f"Data retrieval failed: {str(e)}")
            raise

# Singleton instance for global access
data_storage = DataStorage() 