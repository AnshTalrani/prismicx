"""
Plugin Repository implementation for the Plugin Repository Service.

This module provides database operations for plugin management.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import select, update, delete, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from uuid import uuid4

from ..models.database_models import Plugin, PluginVersion, TenantPlugin, SchemaMigration
from ..models.plugin_models import (
    Plugin as PluginSchema,
    PluginVersion as PluginVersionSchema,
    TenantPlugin as TenantPluginSchema,
    SchemaMigration as SchemaMigrationSchema
)
from .database import DatabaseClient

logger = logging.getLogger(__name__)


class PluginRepository:
    """Repository for plugin management database operations."""
    
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
        Initialize the plugin repository.
        
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
        """Initialize the repository and database connection."""
        await self.db_client.initialize()
    
    async def close(self) -> None:
        """Close the database connection."""
        await self.db_client.close()
    
    # Plugin CRUD operations
    
    async def get_plugins(
        self,
        offset: int = 0,
        limit: int = 100,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> Tuple[List[PluginSchema], int]:
        """
        Get plugins with pagination and optional filters.
        
        Args:
            offset: Pagination offset
            limit: Pagination limit
            type_filter: Filter by plugin type
            status_filter: Filter by plugin status
            
        Returns:
            Tuple[List[PluginSchema], int]: List of plugins and total count
        """
        async with self.db_client.session() as session:
            # Build query for plugins
            query = select(Plugin)
            
            # Apply filters if provided
            if type_filter:
                query = query.where(Plugin.type == type_filter)
            if status_filter:
                query = query.where(Plugin.status == status_filter)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await session.scalar(count_query)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            plugins = result.scalars().all()
            
            # Convert to Pydantic models
            plugin_schemas = [
                PluginSchema(
                    plugin_id=plugin.plugin_id,
                    name=plugin.name,
                    description=plugin.description,
                    type=plugin.type,
                    vendor=plugin.vendor,
                    status=plugin.status,
                    created_at=plugin.created_at,
                    updated_at=plugin.updated_at,
                    metadata=plugin.metadata or {}
                )
                for plugin in plugins
            ]
            
            return plugin_schemas, total_count
    
    async def get_plugin(self, plugin_id: str) -> Optional[PluginSchema]:
        """
        Get a specific plugin by ID.
        
        Args:
            plugin_id: Plugin ID
            
        Returns:
            Optional[PluginSchema]: Plugin if found, None otherwise
        """
        async with self.db_client.session() as session:
            query = select(Plugin).where(Plugin.plugin_id == plugin_id)
            result = await session.execute(query)
            plugin = result.scalars().first()
            
            if not plugin:
                return None
            
            return PluginSchema(
                plugin_id=plugin.plugin_id,
                name=plugin.name,
                description=plugin.description,
                type=plugin.type,
                vendor=plugin.vendor,
                status=plugin.status,
                created_at=plugin.created_at,
                updated_at=plugin.updated_at,
                metadata=plugin.metadata or {}
            )
    
    async def create_plugin(self, plugin_data: PluginSchema) -> PluginSchema:
        """
        Create a new plugin.
        
        Args:
            plugin_data: Plugin data
            
        Returns:
            PluginSchema: Created plugin
        """
        async with self.db_client.session() as session:
            # Generate plugin ID if not provided
            if not plugin_data.plugin_id:
                plugin_data.plugin_id = f"plugin_{uuid4().hex[:8]}"
            
            # Create plugin record
            plugin = Plugin(
                plugin_id=plugin_data.plugin_id,
                name=plugin_data.name,
                description=plugin_data.description,
                type=plugin_data.type,
                vendor=plugin_data.vendor,
                status=plugin_data.status,
                metadata=plugin_data.metadata
            )
            
            session.add(plugin)
            await session.commit()
            await session.refresh(plugin)
            
            return PluginSchema(
                plugin_id=plugin.plugin_id,
                name=plugin.name,
                description=plugin.description,
                type=plugin.type,
                vendor=plugin.vendor,
                status=plugin.status,
                created_at=plugin.created_at,
                updated_at=plugin.updated_at,
                metadata=plugin.metadata or {}
            )
    
    async def update_plugin(self, plugin_id: str, plugin_data: Dict[str, Any]) -> Optional[PluginSchema]:
        """
        Update an existing plugin.
        
        Args:
            plugin_id: Plugin ID
            plugin_data: Plugin data to update
            
        Returns:
            Optional[PluginSchema]: Updated plugin if found, None otherwise
        """
        async with self.db_client.session() as session:
            # Check if plugin exists
            query = select(Plugin).where(Plugin.plugin_id == plugin_id)
            result = await session.execute(query)
            plugin = result.scalars().first()
            
            if not plugin:
                return None
            
            # Update plugin
            update_stmt = (
                update(Plugin)
                .where(Plugin.plugin_id == plugin_id)
                .values(**plugin_data)
                .returning(Plugin)
            )
            
            result = await session.execute(update_stmt)
            updated_plugin = result.scalars().first()
            await session.commit()
            
            return PluginSchema(
                plugin_id=updated_plugin.plugin_id,
                name=updated_plugin.name,
                description=updated_plugin.description,
                type=updated_plugin.type,
                vendor=updated_plugin.vendor,
                status=updated_plugin.status,
                created_at=updated_plugin.created_at,
                updated_at=updated_plugin.updated_at,
                metadata=updated_plugin.metadata or {}
            )
    
    # Plugin version operations
    
    async def get_plugin_versions(
        self, 
        plugin_id: str, 
        offset: int = 0, 
        limit: int = 100
    ) -> Tuple[List[PluginVersionSchema], int]:
        """
        Get versions for a specific plugin.
        
        Args:
            plugin_id: Plugin ID
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple[List[PluginVersionSchema], int]: List of plugin versions and total count
        """
        async with self.db_client.session() as session:
            # Build query for plugin versions
            query = select(PluginVersion).where(PluginVersion.plugin_id == plugin_id)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await session.scalar(count_query)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            versions = result.scalars().all()
            
            # Convert to Pydantic models
            version_schemas = [
                PluginVersionSchema(
                    version_id=version.version_id,
                    plugin_id=version.plugin_id,
                    version=version.version,
                    release_notes=version.release_notes,
                    schema_version=version.schema_version,
                    is_latest=version.is_latest,
                    release_date=version.release_date,
                    created_at=version.created_at,
                    dependencies=version.dependencies or {},
                    compatibility=version.compatibility or {}
                )
                for version in versions
            ]
            
            return version_schemas, total_count
    
    async def get_plugin_version(self, version_id: str) -> Optional[PluginVersionSchema]:
        """
        Get a specific plugin version by ID.
        
        Args:
            version_id: Version ID
            
        Returns:
            Optional[PluginVersionSchema]: Plugin version if found, None otherwise
        """
        async with self.db_client.session() as session:
            query = select(PluginVersion).where(PluginVersion.version_id == version_id)
            result = await session.execute(query)
            version = result.scalars().first()
            
            if not version:
                return None
            
            return PluginVersionSchema(
                version_id=version.version_id,
                plugin_id=version.plugin_id,
                version=version.version,
                release_notes=version.release_notes,
                schema_version=version.schema_version,
                is_latest=version.is_latest,
                release_date=version.release_date,
                created_at=version.created_at,
                dependencies=version.dependencies or {},
                compatibility=version.compatibility or {}
            )
    
    async def create_plugin_version(self, version_data: PluginVersionSchema) -> PluginVersionSchema:
        """
        Create a new plugin version.
        
        Args:
            version_data: Plugin version data
            
        Returns:
            PluginVersionSchema: Created plugin version
        """
        async with self.db_client.session() as session:
            # Generate version ID if not provided
            if not version_data.version_id:
                version_data.version_id = f"ver_{uuid4().hex[:8]}"
            
            # If this is set as latest version, unset is_latest for other versions
            if version_data.is_latest:
                update_stmt = (
                    update(PluginVersion)
                    .where(PluginVersion.plugin_id == version_data.plugin_id)
                    .values(is_latest=False)
                )
                await session.execute(update_stmt)
            
            # Create version record
            version = PluginVersion(
                version_id=version_data.version_id,
                plugin_id=version_data.plugin_id,
                version=version_data.version,
                release_notes=version_data.release_notes,
                schema_version=version_data.schema_version,
                is_latest=version_data.is_latest,
                release_date=version_data.release_date,
                dependencies=version_data.dependencies,
                compatibility=version_data.compatibility
            )
            
            session.add(version)
            await session.commit()
            await session.refresh(version)
            
            return PluginVersionSchema(
                version_id=version.version_id,
                plugin_id=version.plugin_id,
                version=version.version,
                release_notes=version.release_notes,
                schema_version=version.schema_version,
                is_latest=version.is_latest,
                release_date=version.release_date,
                created_at=version.created_at,
                dependencies=version.dependencies or {},
                compatibility=version.compatibility or {}
            )
    
    # Tenant plugin operations
    
    async def get_tenant_plugins(
        self, 
        tenant_id: str, 
        offset: int = 0, 
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> Tuple[List[TenantPluginSchema], int]:
        """
        Get plugins installed for a specific tenant.
        
        Args:
            tenant_id: Tenant ID
            offset: Pagination offset
            limit: Pagination limit
            status_filter: Filter by plugin status
            
        Returns:
            Tuple[List[TenantPluginSchema], int]: List of tenant plugins and total count
        """
        async with self.db_client.session() as session:
            # Build query for tenant plugins
            query = select(TenantPlugin).where(TenantPlugin.tenant_id == tenant_id)
            
            # Apply status filter if provided
            if status_filter:
                query = query.where(TenantPlugin.status == status_filter)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await session.scalar(count_query)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            tenant_plugins = result.scalars().all()
            
            # Convert to Pydantic models
            tenant_plugin_schemas = [
                TenantPluginSchema(
                    tenant_id=tp.tenant_id,
                    plugin_id=tp.plugin_id,
                    version_id=tp.version_id,
                    status=tp.status,
                    installed_at=tp.installed_at,
                    updated_at=tp.updated_at,
                    configurations=tp.configurations or {},
                    features_enabled=tp.features_enabled or [],
                    error_message=tp.error_message
                )
                for tp in tenant_plugins
            ]
            
            return tenant_plugin_schemas, total_count
    
    async def get_tenant_plugin(self, tenant_id: str, plugin_id: str) -> Optional[TenantPluginSchema]:
        """
        Get a specific tenant plugin.
        
        Args:
            tenant_id: Tenant ID
            plugin_id: Plugin ID
            
        Returns:
            Optional[TenantPluginSchema]: Tenant plugin if found, None otherwise
        """
        async with self.db_client.session() as session:
            query = select(TenantPlugin).where(
                (TenantPlugin.tenant_id == tenant_id) & 
                (TenantPlugin.plugin_id == plugin_id)
            )
            result = await session.execute(query)
            tenant_plugin = result.scalars().first()
            
            if not tenant_plugin:
                return None
            
            return TenantPluginSchema(
                tenant_id=tenant_plugin.tenant_id,
                plugin_id=tenant_plugin.plugin_id,
                version_id=tenant_plugin.version_id,
                status=tenant_plugin.status,
                installed_at=tenant_plugin.installed_at,
                updated_at=tenant_plugin.updated_at,
                configurations=tenant_plugin.configurations or {},
                features_enabled=tenant_plugin.features_enabled or [],
                error_message=tenant_plugin.error_message
            )
    
    async def install_tenant_plugin(self, tenant_plugin_data: TenantPluginSchema) -> TenantPluginSchema:
        """
        Install a plugin for a tenant.
        
        Args:
            tenant_plugin_data: Tenant plugin data
            
        Returns:
            TenantPluginSchema: Installed tenant plugin
        """
        async with self.db_client.session() as session:
            # Check if plugin already installed for tenant
            query = select(TenantPlugin).where(
                (TenantPlugin.tenant_id == tenant_plugin_data.tenant_id) & 
                (TenantPlugin.plugin_id == tenant_plugin_data.plugin_id)
            )
            result = await session.execute(query)
            existing_plugin = result.scalars().first()
            
            if existing_plugin:
                # Update existing tenant plugin
                update_stmt = (
                    update(TenantPlugin)
                    .where(
                        (TenantPlugin.tenant_id == tenant_plugin_data.tenant_id) & 
                        (TenantPlugin.plugin_id == tenant_plugin_data.plugin_id)
                    )
                    .values(
                        version_id=tenant_plugin_data.version_id,
                        status=tenant_plugin_data.status,
                        configurations=tenant_plugin_data.configurations,
                        features_enabled=tenant_plugin_data.features_enabled,
                        error_message=tenant_plugin_data.error_message
                    )
                    .returning(TenantPlugin)
                )
                result = await session.execute(update_stmt)
                tenant_plugin = result.scalars().first()
            else:
                # Create new tenant plugin
                tenant_plugin = TenantPlugin(
                    tenant_id=tenant_plugin_data.tenant_id,
                    plugin_id=tenant_plugin_data.plugin_id,
                    version_id=tenant_plugin_data.version_id,
                    status=tenant_plugin_data.status,
                    configurations=tenant_plugin_data.configurations,
                    features_enabled=tenant_plugin_data.features_enabled,
                    error_message=tenant_plugin_data.error_message
                )
                session.add(tenant_plugin)
            
            await session.commit()
            
            if not existing_plugin:
                await session.refresh(tenant_plugin)
            
            return TenantPluginSchema(
                tenant_id=tenant_plugin.tenant_id,
                plugin_id=tenant_plugin.plugin_id,
                version_id=tenant_plugin.version_id,
                status=tenant_plugin.status,
                installed_at=tenant_plugin.installed_at,
                updated_at=tenant_plugin.updated_at,
                configurations=tenant_plugin.configurations or {},
                features_enabled=tenant_plugin.features_enabled or [],
                error_message=tenant_plugin.error_message
            )
    
    async def update_tenant_plugin(
        self, 
        tenant_id: str, 
        plugin_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[TenantPluginSchema]:
        """
        Update an installed tenant plugin.
        
        Args:
            tenant_id: Tenant ID
            plugin_id: Plugin ID
            update_data: Data to update
            
        Returns:
            Optional[TenantPluginSchema]: Updated tenant plugin if found, None otherwise
        """
        async with self.db_client.session() as session:
            # Check if plugin installed for tenant
            query = select(TenantPlugin).where(
                (TenantPlugin.tenant_id == tenant_id) & 
                (TenantPlugin.plugin_id == plugin_id)
            )
            result = await session.execute(query)
            existing_plugin = result.scalars().first()
            
            if not existing_plugin:
                return None
            
            # Update tenant plugin
            update_stmt = (
                update(TenantPlugin)
                .where(
                    (TenantPlugin.tenant_id == tenant_id) & 
                    (TenantPlugin.plugin_id == plugin_id)
                )
                .values(**update_data)
                .returning(TenantPlugin)
            )
            result = await session.execute(update_stmt)
            updated_plugin = result.scalars().first()
            await session.commit()
            
            return TenantPluginSchema(
                tenant_id=updated_plugin.tenant_id,
                plugin_id=updated_plugin.plugin_id,
                version_id=updated_plugin.version_id,
                status=updated_plugin.status,
                installed_at=updated_plugin.installed_at,
                updated_at=updated_plugin.updated_at,
                configurations=updated_plugin.configurations or {},
                features_enabled=updated_plugin.features_enabled or [],
                error_message=updated_plugin.error_message
            )
    
    async def uninstall_tenant_plugin(self, tenant_id: str, plugin_id: str) -> bool:
        """
        Uninstall a plugin for a tenant.
        
        Args:
            tenant_id: Tenant ID
            plugin_id: Plugin ID
            
        Returns:
            bool: True if plugin was uninstalled, False otherwise
        """
        async with self.db_client.session() as session:
            # Delete tenant plugin
            delete_stmt = (
                delete(TenantPlugin)
                .where(
                    (TenantPlugin.tenant_id == tenant_id) & 
                    (TenantPlugin.plugin_id == plugin_id)
                )
            )
            result = await session.execute(delete_stmt)
            await session.commit()
            
            # Check if any rows were deleted
            return result.rowcount > 0
    
    # Schema migration operations
    
    async def get_schema_migrations(
        self, 
        plugin_id: str, 
        offset: int = 0, 
        limit: int = 100
    ) -> Tuple[List[SchemaMigrationSchema], int]:
        """
        Get schema migrations for a plugin.
        
        Args:
            plugin_id: Plugin ID
            offset: Pagination offset
            limit: Pagination limit
            
        Returns:
            Tuple[List[SchemaMigrationSchema], int]: List of schema migrations and total count
        """
        async with self.db_client.session() as session:
            # Build query for schema migrations
            query = select(SchemaMigration).where(SchemaMigration.plugin_id == plugin_id)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_count = await session.scalar(count_query)
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await session.execute(query)
            migrations = result.scalars().all()
            
            # Convert to Pydantic models
            migration_schemas = [
                SchemaMigrationSchema(
                    migration_id=migration.migration_id,
                    plugin_id=migration.plugin_id,
                    version_from=migration.version_from,
                    version_to=migration.version_to,
                    schema_version_from=migration.schema_version_from,
                    schema_version_to=migration.schema_version_to,
                    migration_sql=migration.migration_sql,
                    rollback_sql=migration.rollback_sql,
                    description=migration.description,
                    created_at=migration.created_at
                )
                for migration in migrations
            ]
            
            return migration_schemas, total_count
    
    async def create_schema_migration(self, migration_data: SchemaMigrationSchema) -> SchemaMigrationSchema:
        """
        Create a new schema migration.
        
        Args:
            migration_data: Schema migration data
            
        Returns:
            SchemaMigrationSchema: Created schema migration
        """
        async with self.db_client.session() as session:
            # Generate migration ID if not provided
            if not migration_data.migration_id:
                migration_data.migration_id = f"mig_{uuid4().hex[:8]}"
            
            # Create migration record
            migration = SchemaMigration(
                migration_id=migration_data.migration_id,
                plugin_id=migration_data.plugin_id,
                version_from=migration_data.version_from,
                version_to=migration_data.version_to,
                schema_version_from=migration_data.schema_version_from,
                schema_version_to=migration_data.schema_version_to,
                migration_sql=migration_data.migration_sql,
                rollback_sql=migration_data.rollback_sql,
                description=migration_data.description
            )
            
            session.add(migration)
            await session.commit()
            await session.refresh(migration)
            
            return SchemaMigrationSchema(
                migration_id=migration.migration_id,
                plugin_id=migration.plugin_id,
                version_from=migration.version_from,
                version_to=migration.version_to,
                schema_version_from=migration.schema_version_from,
                schema_version_to=migration.schema_version_to,
                migration_sql=migration.migration_sql,
                rollback_sql=migration.rollback_sql,
                description=migration.description,
                created_at=migration.created_at
            ) 