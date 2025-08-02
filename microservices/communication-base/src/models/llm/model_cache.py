"""
Model caching system for improving LLM performance.

This module provides caching mechanisms for LLM models to avoid
repeated loading of the same models and improve response times.
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple
from threading import Lock

class ModelCache:
    """
    Cache for LLM models with time-based expiration.
    
    This cache stores loaded models and handles expiration to manage memory usage.
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ModelCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_cache_size=5, expiration_time=3600):
        """
        Initialize the model cache.
        
        Args:
            max_cache_size: Maximum number of models to keep in cache
            expiration_time: Expiration time in seconds
        """
        if self._initialized:
            return
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_cache_size = max_cache_size
        self.expiration_time = expiration_time
        self.cache: Dict[str, Tuple[Any, float]] = {}  # model_id -> (model, timestamp)
        self.cache_lock = Lock()
        self._initialized = True
        self.logger.info(f"Model cache initialized with max size: {max_cache_size}, expiration: {expiration_time}s")
    
    def get(self, model_id: str) -> Optional[Any]:
        """
        Get a model from cache if available and not expired.
        
        Args:
            model_id: The ID of the model to retrieve
            
        Returns:
            The cached model if available and not expired, None otherwise
        """
        with self.cache_lock:
            if model_id not in self.cache:
                return None
            
            model, timestamp = self.cache[model_id]
            current_time = time.time()
            
            # Check if expired
            if current_time - timestamp > self.expiration_time:
                self.logger.info(f"Model {model_id} expired from cache")
                del self.cache[model_id]
                return None
            
            # Update timestamp on access
            self.cache[model_id] = (model, current_time)
            self.logger.debug(f"Cache hit for model: {model_id}")
            return model
    
    def put(self, model_id: str, model: Any) -> None:
        """
        Add a model to the cache.
        
        Args:
            model_id: The ID to use for the model
            model: The model to cache
        """
        with self.cache_lock:
            # Check if cache is full and evict oldest entry if needed
            if len(self.cache) >= self.max_cache_size and model_id not in self.cache:
                self._evict_oldest()
            
            # Add or update model in cache
            self.cache[model_id] = (model, time.time())
            self.logger.info(f"Added model to cache: {model_id}")
    
    def _evict_oldest(self) -> None:
        """Evict the oldest model from the cache."""
        if not self.cache:
            return
            
        oldest_id = None
        oldest_time = float('inf')
        
        for model_id, (_, timestamp) in self.cache.items():
            if timestamp < oldest_time:
                oldest_time = timestamp
                oldest_id = model_id
        
        if oldest_id:
            self.logger.info(f"Evicting oldest model from cache: {oldest_id}")
            del self.cache[oldest_id]
    
    def clear(self) -> None:
        """Clear all models from the cache."""
        with self.cache_lock:
            self.cache.clear()
            self.logger.info("Cache cleared")
    
    def remove(self, model_id: str) -> None:
        """
        Remove a specific model from the cache.
        
        Args:
            model_id: ID of the model to remove
        """
        with self.cache_lock:
            if model_id in self.cache:
                del self.cache[model_id]
                self.logger.info(f"Removed model from cache: {model_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self.cache_lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_cache_size,
                "expiration_time": self.expiration_time,
                "models": list(self.cache.keys())
            } 