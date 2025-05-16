"""
Settings configuration for the Category Repository Service.

This module defines the configuration settings for the service, using environment variables
with sensible defaults where appropriate.
"""
from typing import List
from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Service settings configuration."""
    # Service information
    service_name: str = "category-repository-service"
    service_version: str = "0.1.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = False
    
    # MongoDB settings
    mongodb_uri: str = Field(..., env="MONGODB_URI")
    mongodb_database: str = Field("category_repository", env="MONGODB_DATABASE")
    mongodb_categories_collection: str = "categories"
    mongodb_factors_collection: str = "factors"
    mongodb_campaigns_collection: str = "campaigns"
    mongodb_batch_as_objects_collection: str = "batch_as_objects"
    mongodb_entity_assignments_collection: str = "entity_assignments"
    
    # API settings
    api_key: str = Field(..., env="API_KEY")
    allow_cors_origins: List[str] = ["*"]
    
    # Performance settings
    cache_ttl: int = 300  # Cache TTL in seconds
    default_page_size: int = 20
    max_page_size: int = 100
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings object with configuration values
    """
    return Settings() 