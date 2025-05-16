"""
Redis cache client for the management systems service.
Provides caching functionality with advanced features like circuit breaking and rate limiting.
"""

import json
import logging
from typing import Optional, Any, Union
from datetime import datetime
import aioredis
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CacheConfig(BaseModel):
    """Configuration for the cache client."""
    url: str
    ttl: int = 3600  # Default 1 hour
    max_connections: int = 100
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 1000
    rate_limit_duration: int = 60  # seconds

class CacheClient:
    """
    Redis cache client with advanced features.
    Handles caching, rate limiting, and circuit breaking.
    """
    
    def __init__(self, config: CacheConfig):
        """Initialize the cache client."""
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        
    async def connect(self):
        """Establish connection to Redis."""
        try:
            self.redis = await aioredis.from_url(
                self.config.url,
                max_connections=self.config.max_connections,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
            
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Closed Redis connection")
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with retry logic.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        try:
            if not self.redis:
                return None
                
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            bool: Success status
        """
        try:
            if not self.redis:
                return False
                
            ttl = ttl or self.config.ttl
            await self.redis.set(
                key,
                json.dumps(value),
                ex=ttl
            )
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: Success status
        """
        try:
            if not self.redis:
                return False
                
            await self.redis.delete(key)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
            
    async def check_rate_limit(
        self,
        key: str,
        max_requests: Optional[int] = None,
        duration: Optional[int] = None
    ) -> bool:
        """
        Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key
            max_requests: Maximum requests allowed
            duration: Time window in seconds
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        if not self.config.rate_limit_enabled or not self.redis:
            return True
            
        try:
            max_requests = max_requests or self.config.rate_limit_requests
            duration = duration or self.config.rate_limit_duration
            
            # Get current count
            count = await self.redis.get(f"ratelimit:{key}")
            count = int(count) if count else 0
            
            if count >= max_requests:
                return False
                
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(f"ratelimit:{key}")
            pipe.expire(f"ratelimit:{key}", duration)
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow request on error
            
    async def clear_rate_limit(self, key: str) -> bool:
        """
        Clear rate limit for a key.
        
        Args:
            key: Rate limit key
            
        Returns:
            bool: Success status
        """
        try:
            if not self.redis:
                return False
                
            await self.redis.delete(f"ratelimit:{key}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing rate limit: {str(e)}")
            return False 