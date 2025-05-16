"""
Database factory module.

This module provides factory methods to create database connections to
different microservice databases (marketing, CRM, product, user).
"""

import logging
from typing import Dict, Optional

from ...config.app_config import get_config
from .postgres_database import PostgresDatabase

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """
    Factory for creating database connections.
    
    This class provides methods to create connections to different
    microservice databases, such as the marketing, CRM, product,
    and user databases.
    """
    
    _instances: Dict[str, PostgresDatabase] = {}
    
    @classmethod
    def get_marketing_db(cls) -> PostgresDatabase:
        """
        Get a connection to the marketing database.
        
        Returns:
            A PostgresDatabase instance for the marketing database.
        """
        if "marketing" not in cls._instances:
            config = get_config()
            cls._instances["marketing"] = PostgresDatabase(
                connection_string=config.marketing_db_uri,
                database_name=config.marketing_db_name,
                tenant_aware=True
            )
        return cls._instances["marketing"]
    
    @classmethod
    def get_crm_db(cls) -> PostgresDatabase:
        """
        Get a connection to the CRM database with read/write permissions.
        
        Returns:
            A PostgresDatabase instance for the CRM database.
        """
        if "crm" not in cls._instances:
            config = get_config()
            cls._instances["crm"] = PostgresDatabase(
                connection_string=config.crm_db_uri,
                database_name=config.crm_db_name,
                tenant_aware=True,
                read_only=False  # Read/write access
            )
        return cls._instances["crm"]
    
    @classmethod
    def get_product_db(cls) -> PostgresDatabase:
        """
        Get a connection to the product database with read/write permissions.
        
        Returns:
            A PostgresDatabase instance for the product database.
        """
        if "product" not in cls._instances:
            config = get_config()
            cls._instances["product"] = PostgresDatabase(
                connection_string=config.product_db_uri,
                database_name=config.product_db_name,
                tenant_aware=True,
                read_only=False  # Read/write access
            )
        return cls._instances["product"]
    
    @classmethod
    def get_user_db(cls) -> PostgresDatabase:
        """
        Get a connection to the user database with read-only permissions.
        
        Returns:
            A PostgresDatabase instance for the user database.
        """
        if "user" not in cls._instances:
            config = get_config()
            cls._instances["user"] = PostgresDatabase(
                connection_string=config.user_db_uri,
                database_name=config.user_db_name,
                tenant_aware=False,  # User DB is not tenant-aware
                read_only=True  # Read-only access
            )
        return cls._instances["user"]
    
    @classmethod
    async def close_all(cls) -> None:
        """
        Close all database connections.
        """
        for name, db in cls._instances.items():
            logger.info(f"Closing {name} database connection")
            await db.close()
        cls._instances.clear() 