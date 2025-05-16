"""
Data models for the Tenant Management Service.

This module defines the Pydantic models for tenant and database entities
used in the service, including validation and serialization logic.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class DatabaseType(str, Enum):
    """Database isolation type for tenants."""
    DEDICATED = "dedicated"
    SHARED = "shared"


class TenantStatus(str, Enum):
    """Possible status values for tenants."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PROVISIONING = "provisioning"


class DatabaseConfig(BaseModel):
    """Database configuration for a tenant."""
    type: DatabaseType
    connection_string: str
    database_name: str
    shard_key: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "type": "dedicated",
                "connection_string": "mongodb://user:pass@host:port",
                "database_name": "tenant_001_db"
            }
        }


class TenantBase(BaseModel):
    """Base model for tenant data."""
    name: str
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tier: Optional[str] = None
    region: Optional[str] = None


class TenantCreate(TenantBase):
    """Model for creating a new tenant."""
    tenant_id: Optional[str] = None
    database_config: Optional[DatabaseConfig] = None

    @validator("tenant_id", pre=True, always=True)
    def set_tenant_id(cls, v):
        """Generate tenant_id if not provided."""
        import uuid
        return v or f"tenant-{str(uuid.uuid4())[:8]}"


class TenantUpdate(BaseModel):
    """Model for updating an existing tenant."""
    name: Optional[str] = None
    database_config: Optional[DatabaseConfig] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[TenantStatus] = None
    tier: Optional[str] = None
    region: Optional[str] = None


class Tenant(TenantBase):
    """Full tenant model including all fields."""
    tenant_id: str
    database_config: DatabaseConfig
    created_at: datetime
    updated_at: Optional[datetime] = None
    status: TenantStatus

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "tenant_id": "tenant-001",
                "name": "Acme Corporation",
                "database_config": {
                    "type": "dedicated",
                    "connection_string": "mongodb://user:pass@host:port",
                    "database_name": "tenant_001_db"
                },
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "status": "active",
                "settings": {"max_users": 100},
                "tier": "standard",
                "region": "us-east"
            }
        }


class DatabaseStatus(str, Enum):
    """Possible status values for tenant databases."""
    ACTIVE = "active"
    PROVISIONING = "provisioning"
    DECOMMISSIONING = "decommissioning"
    ARCHIVED = "archived"


class TenantDatabaseBase(BaseModel):
    """Base model for tenant database information."""
    database_name: str
    type: DatabaseType
    server: str
    region: Optional[str] = None


class TenantDatabaseCreate(TenantDatabaseBase):
    """Model for creating a new tenant database."""
    tenants: Optional[List[str]] = Field(default_factory=list)


class TenantDatabaseUpdate(BaseModel):
    """Model for updating an existing tenant database."""
    tenants: Optional[List[str]] = None
    status: Optional[DatabaseStatus] = None
    server: Optional[str] = None
    region: Optional[str] = None


class TenantDatabase(TenantDatabaseBase):
    """Full tenant database model including all fields."""
    tenants: List[str]
    status: DatabaseStatus
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "database_name": "tenant_001_db",
                "type": "dedicated",
                "tenants": ["tenant-001"],
                "status": "active",
                "created_at": "2023-01-01T00:00:00Z",
                "server": "mongodb-tenant",
                "region": "us-east"
            }
        } 