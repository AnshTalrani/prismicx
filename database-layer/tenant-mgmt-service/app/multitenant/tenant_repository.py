"""
Tenant repository module for handling tenant data persistence.
"""
import logging
from typing import List, Optional, Dict, Any
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from ..models import Tenant
from ..database import get_session

logger = logging.getLogger(__name__)


class TenantRepository:
    """
    Repository for tenant data operations.
    
    Handles database operations for tenant management including CRUD operations
    and schema management.
    """
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Tenant:
        """
        Create a new tenant in the database.
        
        Args:
            tenant_data (Dict[str, Any]): Tenant data to create
            
        Returns:
            Tenant: The created tenant
        """
        async with get_session() as session:
            tenant = Tenant(**tenant_data)
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            
            # Create tenant schema if tenant isolation strategy is schema-based
            await self._create_tenant_schema(tenant.schema_name)
            
            return tenant
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id (str): Tenant ID to look up
            
        Returns:
            Optional[Tenant]: The tenant if found, None otherwise
        """
        async with get_session() as session:
            result = await session.execute(
                select(Tenant).where(Tenant.tenant_id == tenant_id)
            )
            return result.scalars().first()
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """
        Get a tenant by domain name.
        
        Args:
            domain (str): Domain name to look up
            
        Returns:
            Optional[Tenant]: The tenant if found, None otherwise
        """
        async with get_session() as session:
            result = await session.execute(
                select(Tenant).where(Tenant.domain == domain)
            )
            return result.scalars().first()
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        """
        List tenants with pagination.
        
        Args:
            limit (int): Maximum number of tenants to return
            offset (int): Offset for pagination
            
        Returns:
            List[Tenant]: List of tenants
        """
        async with get_session() as session:
            result = await session.execute(
                select(Tenant).limit(limit).offset(offset)
            )
            return result.scalars().all()
    
    async def update_tenant(self, tenant_id: str, update_data: Dict[str, Any]) -> Optional[Tenant]:
        """
        Update a tenant.
        
        Args:
            tenant_id (str): ID of tenant to update
            update_data (Dict[str, Any]): Data to update
            
        Returns:
            Optional[Tenant]: Updated tenant if found, None otherwise
        """
        async with get_session() as session:
            await session.execute(
                update(Tenant)
                .where(Tenant.tenant_id == tenant_id)
                .values(**update_data)
            )
            await session.commit()
            
            result = await session.execute(
                select(Tenant).where(Tenant.tenant_id == tenant_id)
            )
            return result.scalars().first()
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id (str): ID of tenant to delete
            
        Returns:
            bool: True if tenant was deleted, False otherwise
        """
        tenant = await self.get_tenant_by_id(tenant_id)
        if not tenant:
            return False
            
        async with get_session() as session:
            await session.execute(
                delete(Tenant).where(Tenant.tenant_id == tenant_id)
            )
            await session.commit()
            
            # Drop schema if tenant isolation strategy is schema-based
            await self._drop_tenant_schema(tenant.schema_name)
            
            return True
    
    async def _create_tenant_schema(self, schema_name: str) -> None:
        """
        Create a new PostgreSQL schema for a tenant.
        
        Args:
            schema_name (str): Name of schema to create
        """
        try:
            # Get the PostgreSQL connection pool from config
            conn = await asyncpg.connect(str(self._get_db_url()))
            await conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            await conn.close()
            logger.info(f"Created schema {schema_name}")
        except Exception as e:
            logger.error(f"Error creating schema {schema_name}: {str(e)}")
            raise
    
    async def _drop_tenant_schema(self, schema_name: str) -> None:
        """
        Drop a PostgreSQL schema for a tenant.
        
        Args:
            schema_name (str): Name of schema to drop
        """
        try:
            # Get the PostgreSQL connection pool from config
            conn = await asyncpg.connect(str(self._get_db_url()))
            await conn.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            await conn.close()
            logger.info(f"Dropped schema {schema_name}")
        except Exception as e:
            logger.error(f"Error dropping schema {schema_name}: {str(e)}")
            raise
    
    def _get_db_url(self) -> str:
        """
        Get the database URL from environment.
        
        Returns:
            str: Database URL
        """
        from ..config import get_database_url
        return get_database_url() 