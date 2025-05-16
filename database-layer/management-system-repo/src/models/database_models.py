"""
SQLAlchemy database models for the Plugin Repository Service.

This module defines the SQLAlchemy ORM models for the Plugin Repository Service
database tables.
"""

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, 
    Text, JSON, UniqueConstraint, MetaData, Table, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# Define custom metadata with naming conventions for constraints
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
})

Base = declarative_base(metadata=metadata)


class Plugin(Base):
    """SQLAlchemy model for plugins table."""
    
    __tablename__ = "plugins"
    
    plugin_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # 'crm', 'sales', 'marketing', etc.
    vendor = Column(String(100))
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    metadata = Column(JSON)
    
    # Indexes
    __table_args__ = (
        Index('ix_plugins_type', 'type'),
        Index('ix_plugins_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Plugin(plugin_id='{self.plugin_id}', name='{self.name}', type='{self.type}')>"


class PluginVersion(Base):
    """SQLAlchemy model for plugin_versions table."""
    
    __tablename__ = "plugin_versions"
    
    version_id = Column(String(50), primary_key=True)
    plugin_id = Column(String(50), ForeignKey('plugins.plugin_id'), nullable=False)
    version = Column(String(20), nullable=False)
    release_notes = Column(Text)
    schema_version = Column(Integer, nullable=False)
    is_latest = Column(Boolean, default=False)
    release_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    dependencies = Column(JSON)
    compatibility = Column(JSON)
    
    # Unique constraint for plugin_id and version
    __table_args__ = (
        UniqueConstraint('plugin_id', 'version', name='uq_plugin_versions_plugin_id_version'),
    )
    
    def __repr__(self):
        return f"<PluginVersion(version_id='{self.version_id}', plugin_id='{self.plugin_id}', version='{self.version}')>"


class TenantPlugin(Base):
    """SQLAlchemy model for tenant_plugins table."""
    
    __tablename__ = "tenant_plugins"
    
    tenant_id = Column(String(50), primary_key=True)
    plugin_id = Column(String(50), ForeignKey('plugins.plugin_id'), primary_key=True)
    version_id = Column(String(50), ForeignKey('plugin_versions.version_id'), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    configurations = Column(JSON)
    features_enabled = Column(JSON)
    error_message = Column(Text)
    
    # Indexes
    __table_args__ = (
        Index('ix_tenant_plugins_status', 'status'),
    )
    
    def __repr__(self):
        return f"<TenantPlugin(tenant_id='{self.tenant_id}', plugin_id='{self.plugin_id}')>"


class SchemaMigration(Base):
    """SQLAlchemy model for schema_migrations table."""
    
    __tablename__ = "schema_migrations"
    
    migration_id = Column(String(50), primary_key=True)
    plugin_id = Column(String(50), ForeignKey('plugins.plugin_id'), nullable=False)
    version_from = Column(String(20), nullable=False)
    version_to = Column(String(20), nullable=False)
    schema_version_from = Column(Integer, nullable=False)
    schema_version_to = Column(Integer, nullable=False)
    migration_sql = Column(Text, nullable=False)
    rollback_sql = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SchemaMigration(migration_id='{self.migration_id}', plugin_id='{self.plugin_id}', version_from='{self.version_from}', version_to='{self.version_to}')>" 