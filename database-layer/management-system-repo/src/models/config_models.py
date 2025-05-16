"""
Configuration database models for the Management System Repository Service.

This module defines the database models for the central configuration database
that stores tenant-specific settings and preferences.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TenantConfig(BaseModel):
    """Configuration model for tenant-specific settings."""
    
    tenant_id: str = Field(..., description="Unique identifier for the tenant")
    config_key: str = Field(..., description="Configuration key")
    config_value: Dict[str, Any] = Field(default_factory=dict, description="Configuration value")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created the config")
    updated_by: Optional[str] = Field(None, description="User who last updated the config")
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "tenant_id": "tenant123",
                "config_key": "email_notifications",
                "config_value": {
                    "enabled": True,
                    "frequency": "daily"
                },
                "metadata": {
                    "description": "Email notification preferences",
                    "category": "notifications"
                },
                "created_by": "admin",
                "updated_by": "admin"
            }
        }


class ConfigSchema(BaseModel):
    """Schema definition for configuration keys."""
    
    key: str = Field(..., description="Configuration key")
    schema: Dict[str, Any] = Field(..., description="JSON schema for the configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    required: bool = Field(default=False, description="Whether this config is required")
    default_value: Optional[Dict[str, Any]] = Field(None, description="Default value")
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "key": "email_notifications",
                "schema": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "frequency": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"]
                        }
                    }
                },
                "metadata": {
                    "description": "Email notification preferences",
                    "category": "notifications"
                },
                "required": True,
                "default_value": {
                    "enabled": False,
                    "frequency": "weekly"
                }
            }
        }


class ConfigRequest(BaseModel):
    """Configuration request model."""
    
    config_value: Dict[str, Any] = Field(..., description="Configuration value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "config_value": {
                    "enabled": True,
                    "frequency": "daily"
                },
                "metadata": {
                    "description": "Email notification preferences",
                    "updated_reason": "User preference change"
                }
            }
        }


class ConfigResponse(BaseModel):
    """Configuration response model."""
    
    tenant_id: str
    config_key: str
    config_value: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]


class ConfigSchemaRequest(BaseModel):
    """Configuration schema request model."""
    
    schema: Dict[str, Any] = Field(..., description="JSON schema for the configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    required: Optional[bool] = Field(None, description="Whether this config is required")
    default_value: Optional[Dict[str, Any]] = Field(None, description="Default value")
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "frequency": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"]
                        }
                    }
                },
                "metadata": {
                    "description": "Email notification preferences",
                    "category": "notifications"
                },
                "required": True,
                "default_value": {
                    "enabled": False,
                    "frequency": "weekly"
                }
            }
        }


class UserPreference(BaseModel):
    """User preference model for feature configurations."""
    
    user_id: str = Field(..., description="Unique identifier for the user")
    feature_type: str = Field(..., description="Feature type")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "user_id": "user123",
                "feature_type": "notifications",
                "preferences": {
                    "email": True,
                    "push": False,
                    "sms": False
                }
            }
        }


class FeatureFrequencyGroup(BaseModel):
    """Feature frequency group model for batch processing."""
    
    feature_type: str = Field(..., description="Feature type")
    frequency: str = Field(..., description="Frequency (daily, weekly, monthly)")
    time_key: str = Field(..., description="Time key (e.g. '2023-01-01')")
    tenant_ids: List[str] = Field(default_factory=list, description="List of tenant IDs in this group")
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "feature_type": "reports",
                "frequency": "weekly",
                "time_key": "2023-W01",
                "tenant_ids": ["tenant1", "tenant2", "tenant3"]
            }
        } 