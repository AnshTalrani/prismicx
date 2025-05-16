"""
Schema Manager for Plugin Repository Service.

This module provides functionality to manage tenant-specific database schemas,
including creation, migration, and cross-schema relationships.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.sql import text
import asyncio

from .database import DatabaseClient
from ..models.plugin_models import SchemaMigration, Plugin, PluginVersion

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schemas for tenant plugins."""
    
    def __init__(
        self,
        db_host: str,
        db_port: int,
        db_user: str,
        db_password: str,
        db_name: str,
        min_pool_size: int = 5,
        max_pool_size: int = 20
    ):
        """
        Initialize the schema manager.
        
        Args:
            db_host: Database host
            db_port: Database port
            db_user: Database user
            db_password: Database password
            db_name: Database name
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        self.db_client = DatabaseClient(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            min_pool_size=min_pool_size,
            max_pool_size=max_pool_size
        )
    
    async def initialize(self) -> None:
        """Initialize the schema manager and database connection."""
        await self.db_client.initialize()
    
    async def close(self) -> None:
        """Close the database connection."""
        await self.db_client.close()
    
    async def create_tenant_plugin_schema(
        self, 
        tenant_id: str, 
        plugin_id: str, 
        plugin_type: str
    ) -> bool:
        """
        Create a tenant-specific schema for a plugin.
        
        Args:
            tenant_id: Tenant ID
            plugin_id: Plugin ID
            plugin_type: Plugin type ('crm', 'sales', etc.)
            
        Returns:
            bool: True if schema was created successfully, False otherwise
        """
        try:
            schema_name = f"tenant_{tenant_id.replace('-', '_')}_{plugin_type}_plugin"
            
            # Create schema SQL
            create_schema_sql = f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'
            
            # Execute schema creation
            async with self.db_client.session() as session:
                await session.execute(text(create_schema_sql))
                await session.commit()
                
                logger.info(f"Created schema {schema_name} for tenant {tenant_id} and plugin {plugin_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create schema for tenant {tenant_id} and plugin {plugin_id}: {str(e)}")
            return False
    
    async def apply_schema_migration(
        self, 
        tenant_id: str, 
        plugin_id: str, 
        version_from: str, 
        version_to: str,
        schema_name: Optional[str] = None
    ) -> bool:
        """
        Apply a schema migration for a tenant plugin.
        
        Args:
            tenant_id: Tenant ID
            plugin_id: Plugin ID
            version_from: Current version
            version_to: Target version
            schema_name: Optional schema name override
            
        Returns:
            bool: True if migration was applied successfully, False otherwise
        """
        try:
            # Get plugin type if schema_name is not provided
            if not schema_name:
                async with self.db_client.session() as session:
                    plugin_query = """
                    SELECT type FROM plugins WHERE plugin_id = :plugin_id
                    """
                    result = await session.execute(text(plugin_query), {"plugin_id": plugin_id})
                    plugin_type = result.scalar()
                    
                    if not plugin_type:
                        logger.error(f"Plugin {plugin_id} not found")
                        return False
                    
                    schema_name = f"tenant_{tenant_id.replace('-', '_')}_{plugin_type}_plugin"
            
            # Get migration SQL
            async with self.db_client.session() as session:
                migration_query = """
                SELECT migration_sql FROM schema_migrations 
                WHERE plugin_id = :plugin_id 
                AND version_from = :version_from 
                AND version_to = :version_to
                """
                result = await session.execute(
                    text(migration_query), 
                    {
                        "plugin_id": plugin_id, 
                        "version_from": version_from, 
                        "version_to": version_to
                    }
                )
                migration_sql = result.scalar()
                
                if not migration_sql:
                    logger.error(
                        f"Migration not found for plugin {plugin_id} from version {version_from} to {version_to}"
                    )
                    return False
                
                # Replace schema placeholder with actual schema name
                migration_sql = migration_sql.replace("{{schema_name}}", schema_name)
                
                # Execute migration within a transaction
                async with session.begin():
                    await session.execute(text(migration_sql))
                
                logger.info(
                    f"Applied migration for tenant {tenant_id}, plugin {plugin_id} "
                    f"from version {version_from} to {version_to}"
                )
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to apply migration for tenant {tenant_id}, plugin {plugin_id}: {str(e)}"
            )
            return False
    
    async def drop_tenant_plugin_schema(self, tenant_id: str, plugin_type: str) -> bool:
        """
        Drop a tenant-specific plugin schema.
        
        Args:
            tenant_id: Tenant ID
            plugin_type: Plugin type ('crm', 'sales', etc.)
            
        Returns:
            bool: True if schema was dropped successfully, False otherwise
        """
        try:
            schema_name = f"tenant_{tenant_id.replace('-', '_')}_{plugin_type}_plugin"
            
            # Drop schema SQL - CASCADE to remove all objects in the schema
            drop_schema_sql = f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'
            
            # Execute schema drop
            async with self.db_client.session() as session:
                await session.execute(text(drop_schema_sql))
                await session.commit()
                
                logger.info(f"Dropped schema {schema_name} for tenant {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to drop schema for tenant {tenant_id} and plugin type {plugin_type}: {str(e)}")
            return False
    
    async def create_cross_schema_references(
        self, 
        tenant_id: str, 
        source_plugin_type: str, 
        target_plugin_type: str,
        reference_sql: str
    ) -> bool:
        """
        Create cross-schema references between tenant plugin schemas.
        
        Args:
            tenant_id: Tenant ID
            source_plugin_type: Source plugin type ('crm', 'sales', etc.)
            target_plugin_type: Target plugin type ('crm', 'sales', etc.)
            reference_sql: SQL to create the reference (with {{schema_name}} placeholders)
            
        Returns:
            bool: True if references were created successfully, False otherwise
        """
        try:
            source_schema = f"tenant_{tenant_id.replace('-', '_')}_{source_plugin_type}_plugin"
            target_schema = f"tenant_{tenant_id.replace('-', '_')}_{target_plugin_type}_plugin"
            
            # Replace placeholders with actual schema names
            reference_sql = (
                reference_sql
                .replace("{{source_schema}}", source_schema)
                .replace("{{target_schema}}", target_schema)
            )
            
            # Execute reference creation
            async with self.db_client.session() as session:
                await session.execute(text(reference_sql))
                await session.commit()
                
                logger.info(
                    f"Created cross-schema reference from {source_schema} to {target_schema} for tenant {tenant_id}"
                )
                return True
                
        except Exception as e:
            logger.error(
                f"Failed to create cross-schema reference for tenant {tenant_id}: {str(e)}"
            )
            return False
    
    async def create_cross_schema_view(
        self,
        tenant_id: str,
        view_name: str,
        view_sql: str,
        target_schema_type: str
    ) -> bool:
        """
        Create a cross-schema view.
        
        Args:
            tenant_id: Tenant ID
            view_name: Name of the view to create
            view_sql: SQL to create the view (with {{schema_name}} placeholders)
            target_schema_type: Schema type where the view will be created
            
        Returns:
            bool: True if view was created successfully, False otherwise
        """
        try:
            # Generate schema names for all common plugin types
            schemas = {
                "crm": f"tenant_{tenant_id.replace('-', '_')}_crm_plugin",
                "sales": f"tenant_{tenant_id.replace('-', '_')}_sales_automation_plugin",
                "marketing": f"tenant_{tenant_id.replace('-', '_')}_marketing_plugin",
                "support": f"tenant_{tenant_id.replace('-', '_')}_customer_support_plugin"
            }
            
            # Replace all schema placeholders
            for plugin_type, schema_name in schemas.items():
                view_sql = view_sql.replace(f"{{{{schema_{plugin_type}}}}}", schema_name)
            
            # Set target schema
            target_schema = schemas.get(target_schema_type)
            if not target_schema:
                logger.error(f"Unknown schema type: {target_schema_type}")
                return False
            
            # Create view SQL
            create_view_sql = f'CREATE OR REPLACE VIEW "{target_schema}"."{view_name}" AS {view_sql}'
            
            # Execute view creation
            async with self.db_client.session() as session:
                await session.execute(text(create_view_sql))
                await session.commit()
                
                logger.info(f"Created cross-schema view {view_name} in {target_schema} for tenant {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create cross-schema view for tenant {tenant_id}: {str(e)}")
            return False
    
    async def execute_schema_sql(self, schema_name: str, sql: str) -> bool:
        """
        Execute arbitrary SQL in a specific schema.
        
        Args:
            schema_name: Schema name
            sql: SQL to execute
            
        Returns:
            bool: True if SQL was executed successfully, False otherwise
        """
        try:
            # Set search path to the schema
            set_schema_sql = f'SET search_path TO "{schema_name}"'
            
            # Execute SQL in the schema
            async with self.db_client.session() as session:
                async with session.begin():
                    await session.execute(text(set_schema_sql))
                    await session.execute(text(sql))
                
                logger.info(f"Executed SQL in schema {schema_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to execute SQL in schema {schema_name}: {str(e)}")
            return False
    
    async def create_initial_schema_from_template(
        self,
        tenant_id: str,
        plugin_id: str,
        plugin_type: str,
        schema_template_sql: str
    ) -> bool:
        """
        Create an initial schema for a tenant plugin using a template.
        
        Args:
            tenant_id: Tenant ID
            plugin_id: Plugin ID
            plugin_type: Plugin type ('crm', 'sales', etc.)
            schema_template_sql: SQL template for creating schema objects
            
        Returns:
            bool: True if schema was created successfully, False otherwise
        """
        try:
            schema_name = f"tenant_{tenant_id.replace('-', '_')}_{plugin_type}_plugin"
            
            # First, create the schema
            schema_created = await self.create_tenant_plugin_schema(tenant_id, plugin_id, plugin_type)
            if not schema_created:
                return False
            
            # Replace schema placeholder
            schema_template_sql = schema_template_sql.replace("{{schema_name}}", schema_name)
            
            # Execute template SQL
            return await self.execute_schema_sql(schema_name, schema_template_sql)
            
        except Exception as e:
            logger.error(
                f"Failed to create initial schema for tenant {tenant_id} and plugin {plugin_id}: {str(e)}"
            )
            return False 