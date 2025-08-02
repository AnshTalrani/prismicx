"""
PostgreSQL Configuration Module.

This module provides configuration settings for PostgreSQL database connections,
supporting the multi-tenant architecture described in the project documentation.
It follows the MACH architecture principles by maintaining a clean separation
between domains and providing configuration for microservices.
"""

import os
from typing import Dict, Optional, Any
from pydantic import BaseSettings, Field


class PostgresSettings(BaseSettings):
    """
    PostgreSQL connection settings loaded from environment variables.
    
    This class provides a standardized way to configure PostgreSQL connections
    across all microservices in the MACH architecture.
    """
    
    # PostgreSQL connection settings
    PG_HOST: str = Field(
        default="postgres-system",
        env="PG_HOST",
        description="PostgreSQL host"
    )
    PG_PORT: int = Field(
        default=5432,
        env="PG_PORT",
        description="PostgreSQL port"
    )
    PG_USER: str = Field(
        default="postgres",
        env="PG_USER",
        description="PostgreSQL username"
    )
    PG_PASSWORD: str = Field(
        env="PG_PASSWORD",
        description="PostgreSQL password"
    )
    PG_DATABASE: str = Field(
        env="PG_DATABASE",
        description="PostgreSQL database name"
    )
    
    # Connection pool settings
    PG_MIN_POOL_SIZE: int = Field(
        default=5,
        env="PG_MIN_POOL_SIZE",
        description="Minimum connection pool size"
    )
    PG_MAX_POOL_SIZE: int = Field(
        default=20,
        env="PG_MAX_POOL_SIZE",
        description="Maximum connection pool size"
    )
    PG_CONNECTION_TIMEOUT: int = Field(
        default=30,
        env="PG_CONNECTION_TIMEOUT",
        description="Connection timeout in seconds"
    )
    
    # Tenant settings
    PG_TENANT_AWARE: bool = Field(
        default=True,
        env="PG_TENANT_AWARE",
        description="Whether this database uses tenant schemas"
    )
    PG_DEFAULT_SCHEMA: str = Field(
        default="public",
        env="PG_DEFAULT_SCHEMA",
        description="Default schema to use when no tenant is specified"
    )
    
    # SSL settings
    PG_SSL_MODE: Optional[str] = Field(
        default=None,
        env="PG_SSL_MODE",
        description="SSL mode (disable, allow, prefer, require, verify-ca, verify-full)"
    )
    PG_SSL_ROOT_CERT: Optional[str] = Field(
        default=None,
        env="PG_SSL_ROOT_CERT",
        description="Path to SSL root certificate"
    )
    
    # Application settings
    PG_APPLICATION_NAME: str = Field(
        default="prismicx-app",
        env="PG_APPLICATION_NAME",
        description="Application name for connection identification"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


class PostgresConfig:
    """
    PostgreSQL configuration manager.
    
    This class provides methods to get PostgreSQL connection configurations
    for different services in the MACH architecture.
    """
    
    _instances: Dict[str, PostgresSettings] = {}
    
    @classmethod
    def get_settings(cls, service_name: str = "default") -> PostgresSettings:
        """
        Get PostgreSQL settings for a specific service.
        
        Args:
            service_name: The name of the service (used for env var prefixing).
            
        Returns:
            PostgresSettings object with database configuration.
        """
        if service_name not in cls._instances:
            # Dynamically create settings with environment variable prefixes
            class ServiceSpecificSettings(PostgresSettings):
                """Service-specific PostgreSQL settings with prefixed env vars."""
                
                class Config:
                    """Pydantic config with environment variable prefix."""
                    env_prefix = f"{service_name.upper()}_" if service_name != "default" else ""
                    env_file = ".env"
                    case_sensitive = True
            
            # Create and cache the settings instance
            cls._instances[service_name] = ServiceSpecificSettings()
        
        return cls._instances[service_name]
    
    @classmethod
    def get_connection_string(cls, service_name: str = "default") -> str:
        """
        Get a PostgreSQL connection string for a specific service.
        
        Args:
            service_name: The name of the service.
            
        Returns:
            PostgreSQL connection string.
        """
        settings = cls.get_settings(service_name)
        
        # Build base connection string
        conn_string = (
            f"postgresql://{settings.PG_USER}:{settings.PG_PASSWORD}"
            f"@{settings.PG_HOST}:{settings.PG_PORT}/{settings.PG_DATABASE}"
        )
        
        # Add SSL parameters if configured
        params = []
        if settings.PG_SSL_MODE:
            params.append(f"sslmode={settings.PG_SSL_MODE}")
        if settings.PG_SSL_ROOT_CERT:
            params.append(f"sslrootcert={settings.PG_SSL_ROOT_CERT}")
        if settings.PG_APPLICATION_NAME:
            params.append(f"application_name={settings.PG_APPLICATION_NAME}")
        
        # Append parameters if any
        if params:
            conn_string += "?" + "&".join(params)
        
        return conn_string
    
    @classmethod
    def get_connection_params(cls, service_name: str = "default") -> Dict[str, Any]:
        """
        Get PostgreSQL connection parameters as a dictionary.
        
        Args:
            service_name: The name of the service.
            
        Returns:
            Dictionary with connection parameters.
        """
        settings = cls.get_settings(service_name)
        
        return {
            "host": settings.PG_HOST,
            "port": settings.PG_PORT,
            "user": settings.PG_USER,
            "password": settings.PG_PASSWORD,
            "database": settings.PG_DATABASE,
            "min_size": settings.PG_MIN_POOL_SIZE,
            "max_size": settings.PG_MAX_POOL_SIZE,
            "command_timeout": settings.PG_CONNECTION_TIMEOUT,
            "ssl": settings.PG_SSL_MODE not in (None, "disable"),
            "server_settings": {
                "application_name": settings.PG_APPLICATION_NAME
            }
        }


# Default instance for direct imports
postgres_config = PostgresConfig() 