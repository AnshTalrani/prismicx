"""
PostgreSQL tenant repository implementation.

This module provides an implementation of the tenant repository interface
that uses the PostgreSQL user database to access tenant information.
"""

import logging
from typing import Dict, List, Optional, Any

from ...domain.repositories.tenant_repository import TenantRepository
from ..database.postgres_database import PostgresDatabase

logger = logging.getLogger(__name__)


class PostgresTenantRepository(TenantRepository):
    """
    PostgreSQL implementation of the tenant repository.
    
    This implementation uses the central user database to access tenant information.
    """
    
    def __init__(self, database: PostgresDatabase):
        """
        Initialize the repository.
        
        Args:
            database: The PostgreSQL database instance for the user database.
        """
        self.database = database
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The tenant information, or None if not found.
        """
        try:
            query = """
                SELECT id, name, schema_name, is_active, created_at, updated_at
                FROM tenants
                WHERE id = $1
            """
            return await self.database.fetch_one(query, tenant_id)
        except Exception as e:
            logger.error(f"Error retrieving tenant {tenant_id}: {str(e)}")
            return None
    
    async def get_all_tenants(self) -> List[Dict[str, Any]]:
        """
        Get all tenants.
        
        Returns:
            A list of all tenants.
        """
        try:
            query = """
                SELECT id, name, schema_name, is_active, created_at, updated_at
                FROM tenants
                WHERE is_active = true
            """
            return await self.database.execute_query(query)
        except Exception as e:
            logger.error(f"Error retrieving all tenants: {str(e)}")
            return []
    
    async def get_tenant_schema(self, tenant_id: str) -> Optional[str]:
        """
        Get the database schema name for a tenant.
        
        Args:
            tenant_id: The ID of the tenant.
            
        Returns:
            The schema name, or None if the tenant does not exist.
        """
        try:
            query = """
                SELECT schema_name
                FROM tenants
                WHERE id = $1 AND is_active = true
            """
            result = await self.database.fetch_one(query, tenant_id)
            return result["schema_name"] if result else None
        except Exception as e:
            logger.error(f"Error retrieving schema for tenant {tenant_id}: {str(e)}")
            return None 