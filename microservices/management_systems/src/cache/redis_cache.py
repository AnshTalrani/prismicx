"""
Redis cache module for the management systems.
"""
import logging
import json
import aioredis
from typing import Any, Optional, Dict
import os

logger = logging.getLogger(__name__)

# Redis client
redis = None

class RedisCache:
    """Redis cache implementation."""
    
    def __init__(self):
        """Initialize the Redis cache."""
        self.client = None
    
    async def initialize(self):
        """Initialize the Redis connection."""
        if self.client is not None:
            return
            
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        
        try:
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port}/{redis_db}")
            self.client = aioredis.from_url(
                f"redis://{redis_host}:{redis_port}/{redis_db}",
                password=redis_password
            )
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            # Set client to None to indicate connection failure
            self.client = None
    
    async def close(self):
        """Close the Redis connection."""
        if self.client is not None:
            await self.client.close()
            self.client = None
            logger.info("Closed Redis connection")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if self.client is None:
            return None
            
        try:
            value = await self.client.get(key)
            if value is None:
                return None
                
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Error getting cache key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
            
        try:
            serialized = json.dumps(value)
            await self.client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Error setting cache key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
            
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern to match
            
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
            
        try:
            cursor = 0
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.client.delete(*keys)
                
                if cursor == 0:
                    break
                    
            return True
        except Exception as e:
            logger.warning(f"Error clearing cache pattern {pattern}: {str(e)}")
            return False
    
    async def flush_all(self) -> bool:
        """
        Clear the entire cache.
        
        Returns:
            True if successful, False otherwise
        """
        if self.client is None:
            return False
            
        try:
            await self.client.flushdb()
            logger.info("Cache flushed")
            return True
        except Exception as e:
            logger.warning(f"Error flushing cache: {str(e)}")
            return False

# Global cache instance
cache = RedisCache()

async def initialize_cache():
    """Initialize the cache."""
    await cache.initialize()

async def close_cache():
    """Close the cache connection."""
    await cache.close() 