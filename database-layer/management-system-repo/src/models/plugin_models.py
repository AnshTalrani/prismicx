"""
Plugin Repository Models

This module defines the data models for the Plugin Repository Service.
These models represent plugins, plugin versions, tenant plugin installations,
and schema migrations.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Plugin(BaseModel):
    """Plugin model representing a management system plugin."""
    
    plugin_id: str = Field(default_factory=lambda: f"plugin_{uuid4().hex[:8]}")
    name: str
    description: Optional[str] = None
    type: str  # "crm", "sales", "marketing", "support", etc.
    vendor: Optional[str] = None
    status: str = "active"  # "active", "deprecated", "inactive", "beta"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "plugin_id": "plugin_a1b2c3d4",
                "name": "CRM System",
                "description": "Customer Relationship Management system for tracking customers and interactions",
                "type": "crm",
                "vendor": "PrismicX",
                "status": "active",
                "metadata": {
                    "icon": "crm_icon.svg",
                    "categories": ["business", "customer-management"],
                    "website": "https://prismicx.io/plugins/crm"
                }
            }
        }


class PluginVersion(BaseModel):
    """Plugin version model representing a specific version of a plugin."""
    
    version_id: str = Field(default_factory=lambda: f"ver_{uuid4().hex[:8]}")
    plugin_id: str
    version: str  # Semantic version: "1.0.0"
    release_notes: Optional[str] = None
    schema_version: int
    is_latest: bool = False
    release_date: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, str] = Field(default_factory=dict)  # {"plugin_id": "min_version"}
    compatibility: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "version_id": "ver_a1b2c3d4",
                "plugin_id": "plugin_a1b2c3d4",
                "version": "2.1.0",
                "release_notes": "Added support for custom fields and improved performance",
                "schema_version": 5,
                "is_latest": True,
                "release_date": "2023-06-15T00:00:00Z",
                "dependencies": {
                    "plugin_user_data": "1.5.0"
                },
                "compatibility": {
                    "min_platform_version": "3.2.0",
                    "max_platform_version": "4.0.0"
                }
            }
        }


class TenantPlugin(BaseModel):
    """Tenant plugin model representing a plugin installed for a specific tenant."""
    
    tenant_id: str
    plugin_id: str
    version_id: str
    status: str = "active"  # "active", "installing", "upgrading", "error", "inactive"
    installed_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    configurations: Dict[str, Any] = Field(default_factory=dict)
    features_enabled: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "tenant_id": "tenant-001",
                "plugin_id": "plugin_a1b2c3d4",
                "version_id": "ver_a1b2c3d4",
                "status": "active",
                "installed_at": "2023-06-20T14:30:00Z",
                "configurations": {
                    "data_retention_days": 365,
                    "enable_ai_suggestions": True
                },
                "features_enabled": ["basic", "advanced", "reporting"]
            }
        }


class SchemaMigration(BaseModel):
    """Schema migration model representing a database schema change for a plugin version."""
    
    migration_id: str = Field(default_factory=lambda: f"mig_{uuid4().hex[:8]}")
    plugin_id: str
    version_from: str  # "1.0.0"
    version_to: str  # "1.1.0"
    schema_version_from: int
    schema_version_to: int
    migration_sql: str
    rollback_sql: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "migration_id": "mig_a1b2c3d4",
                "plugin_id": "plugin_a1b2c3d4",
                "version_from": "2.0.0",
                "version_to": "2.1.0",
                "schema_version_from": 4,
                "schema_version_to": 5,
                "migration_sql": "ALTER TABLE customers ADD COLUMN custom_fields JSONB DEFAULT '{}'::jsonb;",
                "rollback_sql": "ALTER TABLE customers DROP COLUMN custom_fields;",
                "description": "Add custom fields support to customers table"
            }
        }


class PluginInstallRequest(BaseModel):
    """Plugin installation request model."""
    
    tenant_id: str
    plugin_id: str
    version_id: Optional[str] = None  # If None, use the latest version
    configurations: Dict[str, Any] = Field(default_factory=dict)
    features_to_enable: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "tenant_id": "tenant-001",
                "plugin_id": "plugin_a1b2c3d4",
                "configurations": {
                    "data_retention_days": 365,
                    "enable_ai_suggestions": True
                },
                "features_to_enable": ["basic", "advanced", "reporting"]
            }
        }


class PluginUpdateRequest(BaseModel):
    """Plugin update request model."""
    
    tenant_id: str
    plugin_id: str
    version_id: str
    configurations: Optional[Dict[str, Any]] = None
    features_to_enable: Optional[List[str]] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "tenant_id": "tenant-001",
                "plugin_id": "plugin_a1b2c3d4",
                "version_id": "ver_b2c3d4e5",
                "configurations": {
                    "data_retention_days": 730,
                    "enable_ai_suggestions": True
                }
            }
        }


class PluginConfigUpdateRequest(BaseModel):
    """Plugin configuration update request model."""
    
    configurations: Dict[str, Any]
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "configurations": {
                    "data_retention_days": 730,
                    "enable_ai_suggestions": True,
                    "default_currency": "EUR"
                }
            }
        } 