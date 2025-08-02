"""
Application configuration.

This module provides configuration settings for the marketing service.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration settings."""
    
    # MongoDB settings
    mongodb_uri: str
    mongodb_database: str
    
    # Redis settings
    redis_uri: str
    
    # SMTP settings
    smtp_host: str
    smtp_port: int
    smtp_username: Optional[str]
    smtp_password: Optional[str]
    smtp_from_email: str
    smtp_use_tls: bool = False
    smtp_use_starttls: bool = False
    smtp_timeout: int = 30
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    api_key: str = "default-api-key"
    
    # Processing settings
    batch_size: int = 100
    batch_processing_enabled: bool = True
    worker_id: str = "marketing-worker-1"
    
    # External database connections
    # User database (read access only)
    user_db_uri: str = "postgresql://user_readonly:password@postgres-system:5432/user_db"
    user_db_name: str = "user_db"
    
    # CRM database (read/write access)
    crm_db_uri: str = "postgresql://crm_readwrite:password@postgres-system:5432/crm_db"
    crm_db_name: str = "crm_db"
    
    # Product database (read/write access)
    product_db_uri: str = "postgresql://product_readwrite:password@postgres-system:5432/product_db"
    product_db_name: str = "product_db"
    
    # Marketing database (this service's own database)
    marketing_db_uri: str = "postgresql://marketing_admin:password@postgres-system:5432/marketing_db"
    marketing_db_name: str = "marketing_db"
    
    # Tenant Management Service
    tenant_management_url: str = "http://tenant-mgmt-service:8501"
    tenant_management_timeout_ms: int = 5000
    
    # Tenant Context Settings
    tenant_header: str = "X-Tenant-ID"
    tenant_subdomain_enabled: bool = True
    tenant_path_enabled: bool = True


def get_config() -> Config:
    """
    Get application configuration.
    
    Loads configuration from environment variables with defaults.
    
    Returns:
        Config object with application settings.
    """
    return Config(
        # MongoDB settings
        mongodb_uri=os.getenv("MARKETING_MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_database=os.getenv("MARKETING_MONGODB_DATABASE", "marketing_db"),
        
        # Redis settings
        redis_uri=os.getenv("MARKETING_REDIS_URI", "redis://localhost:6379/0"),
        
        # SMTP settings
        smtp_host=os.getenv("MARKETING_SMTP_HOST", "localhost"),
        smtp_port=int(os.getenv("MARKETING_SMTP_PORT", "25")),
        smtp_username=os.getenv("MARKETING_SMTP_USERNAME"),
        smtp_password=os.getenv("MARKETING_SMTP_PASSWORD"),
        smtp_from_email=os.getenv("MARKETING_SMTP_FROM_EMAIL", "noreply@example.com"),
        smtp_use_tls=os.getenv("MARKETING_SMTP_USE_TLS", "false").lower() == "true",
        smtp_use_starttls=os.getenv("MARKETING_SMTP_USE_STARTTLS", "false").lower() == "true",
        smtp_timeout=int(os.getenv("MARKETING_SMTP_TIMEOUT", "30")),
        
        # API settings
        host=os.getenv("MARKETING_HOST", "0.0.0.0"),
        port=int(os.getenv("MARKETING_PORT", "8020")),
        debug=os.getenv("MARKETING_DEBUG", "false").lower() == "true",
        api_key=os.getenv("MARKETING_API_KEY", "default-api-key"),
        
        # Processing settings
        batch_size=int(os.getenv("MARKETING_BATCH_SIZE", "100")),
        batch_processing_enabled=os.getenv("MARKETING_BATCH_PROCESSING_ENABLED", "true").lower() == "true",
        worker_id=os.getenv("MARKETING_WORKER_ID", "marketing-worker-1"),
        
        # External database connections
        # User database (read access only)
        user_db_uri=os.getenv("USER_DB_URI", "postgresql://user_readonly:password@postgres-system:5432/user_db"),
        user_db_name=os.getenv("USER_DB_NAME", "user_db"),
        
        # CRM database (read/write access)
        crm_db_uri=os.getenv("CRM_DB_URI", "postgresql://crm_readwrite:password@postgres-system:5432/crm_db"),
        crm_db_name=os.getenv("CRM_DB_NAME", "crm_db"),
        
        # Product database (read/write access)
        product_db_uri=os.getenv("PRODUCT_DB_URI", "postgresql://product_readwrite:password@postgres-system:5432/product_db"),
        product_db_name=os.getenv("PRODUCT_DB_NAME", "product_db"),
        
        # Marketing database (this service's own database)
        marketing_db_uri=os.getenv("MARKETING_DB_URI", "postgresql://marketing_admin:password@postgres-system:5432/marketing_db"),
        marketing_db_name=os.getenv("MARKETING_DB_NAME", "marketing_db"),
        
        # Tenant Management Service
        tenant_management_url=os.getenv("TENANT_MGMT_URL", "http://tenant-mgmt-service:8501"),
        tenant_management_timeout_ms=int(os.getenv("TENANT_MGMT_TIMEOUT_MS", "5000")),
        
        # Tenant Context Settings
        tenant_header=os.getenv("TENANT_HEADER", "X-Tenant-ID"),
        tenant_subdomain_enabled=os.getenv("TENANT_SUBDOMAIN_ENABLED", "true").lower() == "true",
        tenant_path_enabled=os.getenv("TENANT_PATH_ENABLED", "true").lower() == "true"
    ) 