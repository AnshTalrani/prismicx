"""
Common database client module for all services.

This module provides database connection clients and utilities
that can be used across all microservices.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import motor.motor_asyncio
import asyncpg
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseClient:
    """Database client for connecting to both MongoDB and PostgreSQL databases."""
    
    def __init__(self):
        self.config_db = None
        self.tenant_pools: Dict[str, asyncpg.Pool] = {}
        self._mongo_client = None
        
    async def init_config_db(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str
    ) -> None:
        """Initialize connection to the configuration database.
        
        Args:
            host: MongoDB host
            port: MongoDB port
            user: Database user
            password: Database password
            db_name: Database name
        """
        try:
            uri = f"mongodb://{user}:{password}@{host}:{port}/{db_name}"
            self._mongo_client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self.config_db = self._mongo_client[db_name]
            
            # Test connection
            await self.config_db.command("ping")
            logger.info("Successfully connected to configuration database")
            
        except Exception as e:
            logger.error(f"Failed to connect to configuration database: {str(e)}")
            raise
            
    async def init_tenant_db(
        self,
        tenant_id: str,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str
    ) -> None:
        """Initialize connection pool for a tenant database.
        
        Args:
            tenant_id: Tenant identifier
            host: PostgreSQL host
            port: PostgreSQL port
            user: Database user
            password: Database password
            db_name: Database name
        """
        try:
            if tenant_id in self.tenant_pools:
                return
                
            dsn = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
            pool = await asyncpg.create_pool(
                dsn,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            self.tenant_pools[tenant_id] = pool
            logger.info(f"Successfully connected to tenant database: {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect to tenant database {tenant_id}: {str(e)}")
            raise
            
    @asynccontextmanager
    async def tenant_connection(self, tenant_id: str):
        """Get a connection from the tenant's connection pool.
        
        Args:
            tenant_id: Tenant identifier
            
        Yields:
            asyncpg.Connection: Database connection
        """
        if tenant_id not in self.tenant_pools:
            raise ValueError(f"No connection pool for tenant: {tenant_id}")
            
        async with self.tenant_pools[tenant_id].acquire() as conn:
            yield conn
            
    async def close(self):
        """Close all database connections."""
        if self._mongo_client:
            self._mongo_client.close()
            
        for pool in self.tenant_pools.values():
            await pool.close()
            
        logger.info("Closed all database connections")

# Global database client instance
db_client = DatabaseClient() 