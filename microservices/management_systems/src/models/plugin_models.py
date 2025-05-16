"""
Plugin models for the Management Systems microservice.

These models define the data structures for plugins and related entities.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class Plugin(BaseModel):
    """Plugin model representing a business system plugin."""
    
    plugin_id: str
    name: str
    description: str
    type: str
    vendor: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PluginVersion(BaseModel):
    """Plugin version model representing a specific version of a plugin."""
    
    version_id: str
    plugin_id: str
    version: str
    release_notes: Optional[str] = None
    schema_version: str
    is_latest: bool
    release_date: datetime
    created_at: datetime
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    compatibility: Dict[str, Any] = Field(default_factory=dict)

class TenantPlugin(BaseModel):
    """Tenant plugin model representing a plugin installed for a tenant."""
    
    tenant_id: str
    plugin_id: str
    version_id: str
    status: str
    installed_at: datetime
    updated_at: datetime
    configurations: Dict[str, Any] = Field(default_factory=dict)
    features_enabled: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

class SchemaMigration(BaseModel):
    """Schema migration model representing a database migration for a plugin."""
    
    migration_id: str
    plugin_id: str
    version_from: str
    version_to: str
    schema_version_from: str
    schema_version_to: str
    migration_sql: str
    rollback_sql: Optional[str] = None
    description: str
    created_at: datetime

class PluginInstallRequest(BaseModel):
    """Request model for installing a plugin for a tenant."""
    
    plugin_id: str
    version_id: str
    configurations: Optional[Dict[str, Any]] = Field(default_factory=dict)
    features_enabled: Optional[List[str]] = Field(default_factory=list)

class PluginUpdateRequest(BaseModel):
    """Request model for updating a tenant plugin."""
    
    status: Optional[str] = None
    version_id: Optional[str] = None
    configurations: Optional[Dict[str, Any]] = None
    features_enabled: Optional[List[str]] = None 