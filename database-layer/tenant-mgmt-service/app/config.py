"""
Configuration settings for the Tenant Management Service.

This module loads configuration from environment variables and provides
settings for database connections, service behavior, and other parameters.
"""

import os
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service configuration
    SERVICE_HOST: str = Field(
        default="0.0.0.0", 
        env="TENANT_SERVICE_HOST", 
        description="Host to bind the service to"
    )
    SERVICE_PORT: int = Field(
        default=8501, 
        env="TENANT_SERVICE_PORT", 
        description="Port to bind the service to"
    )
    LOG_LEVEL: str = Field(
        default="INFO", 
        env="TENANT_SERVICE_LOG_LEVEL", 
        description="Logging level"
    )
    
    # MongoDB connection for tenant registry
    MONGODB_URI: str = Field(
        env="TENANT_MONGODB_URI", 
        description="MongoDB connection URI for tenant registry"
    )
    MONGODB_DB: str = Field(
        default="tenant_registry", 
        env="TENANT_REGISTRY_DB", 
        description="MongoDB database name for tenant registry"
    )
    
    # Redis configuration for caching (optional)
    REDIS_URI: str = Field(
        default=None, 
        env="TENANT_REDIS_URI", 
        description="Redis connection URI for caching"
    )
    
    # Security settings
    API_KEY_HEADER: str = Field(
        default="X-API-Key", 
        env="TENANT_API_KEY_HEADER", 
        description="Header name for API key authentication"
    )
    API_KEY: str = Field(
        default=None, 
        env="TENANT_API_KEY", 
        description="API key for service authentication"
    )
    
    # Tenant database settings
    DEFAULT_TENANT_DB_HOST: str = Field(
        default="mongodb-tenant", 
        env="DEFAULT_TENANT_DB_HOST", 
        description="Default host for tenant databases"
    )
    DEFAULT_TENANT_DB_PORT: int = Field(
        default=27017, 
        env="DEFAULT_TENANT_DB_PORT", 
        description="Default port for tenant databases"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings() 