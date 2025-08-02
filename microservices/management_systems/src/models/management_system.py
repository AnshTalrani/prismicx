"""
Models related to management systems and instances.
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
import uuid
from bson import ObjectId
from bson.errors import InvalidId
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Table, JSON, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# SQLAlchemy Base for database models
Base = declarative_base()

# Pydantic model for ObjectId support
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class SystemType(str, Enum):
    """Types of business management systems."""
    CRM = "crm"
    SALES = "sales_automation"
    FINANCE = "finance_automation"
    SOCIAL_MEDIA = "social_media"
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    SUPPORT = "customer_support"
    CUSTOM = "custom"

class SystemPermission(str, Enum):
    """Permission types for management systems."""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"

# SQLAlchemy models
class SystemModel(Base):
    """SQLAlchemy model for management systems."""
    __tablename__ = "management_systems"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(String)
    version = Column(String, default="1.0.0")
    is_template = Column(Boolean, default=False)
    template_id = Column(String)
    fields = Column(JSON)
    views = Column(JSON)
    plugins = Column(JSON)
    dependencies = Column(JSON)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    
    # Relationships
    instances = relationship("SystemInstanceModel", back_populates="system")

class SystemInstanceModel(Base):
    """SQLAlchemy model for system instances."""
    __tablename__ = "system_instances"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    system_id = Column(String, ForeignKey("management_systems.id"), nullable=False)
    tenant_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    settings = Column(JSON)
    status = Column(String, default="active")
    error_message = Column(String)
    plugin_status = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)
    
    # Relationships
    system = relationship("SystemModel", back_populates="instances")

class UserPermissionModel(Base):
    """SQLAlchemy model for user permissions."""
    __tablename__ = "user_system_permissions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    tenant_id = Column(String, nullable=False)
    instance_id = Column(String, ForeignKey("system_instances.id"), nullable=False)
    permissions = Column(JSON) # List of permission enum values
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class DataField(BaseModel):
    """Definition of a data field in a management system."""
    id: str
    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None
    options: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Field ID must be a non-empty string')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['string', 'number', 'boolean', 'date', 'object', 'array', 'reference']
        if v not in valid_types:
            raise ValueError(f'Field type must be one of: {", ".join(valid_types)}')
        return v
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class DataView(BaseModel):
    """Definition of a data view in a management system."""
    id: str
    name: str
    description: Optional[str] = None
    fields: List[str]  # List of field IDs to include
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[List[Dict[str, str]]] = None  # e.g. [{"field": "name", "order": "asc"}]
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('View ID must be a non-empty string')
        return v
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class DataItem(BaseModel):
    """A single data item in a management system instance."""
    id: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Item ID must be a non-empty string')
        return v
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class PluginReference(BaseModel):
    """Reference to a plugin in a management system."""
    plugin_id: str
    config: Optional[Dict[str, Any]] = None
    enabled: bool = True
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class SystemDependency(BaseModel):
    """Dependency on another system."""
    system_id: str
    required: bool = True
    config: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class ManagementSystem(BaseModel):
    """Definition of a management system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    type: Optional[SystemType] = None
    version: str = "1.0.0"
    is_template: bool = False
    template_id: Optional[str] = None
    fields: List[DataField]
    views: Optional[List[DataView]] = None
    plugins: Optional[List[PluginReference]] = None
    dependencies: Optional[List[SystemDependency]] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # MongoDB specific field - not included in JSON serialization
    mongo_id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('System name must be a non-empty string')
        return v
    
    @validator('fields')
    def validate_fields(cls, v):
        if not v or len(v) == 0:
            raise ValueError('System must have at least one field defined')
        return v
    
    @validator('views')
    def validate_views(cls, v, values):
        if not v:
            return v
            
        field_ids = [f.id for f in values.get('fields', [])]
        for view in v:
            for field_id in view.fields:
                if field_id not in field_ids:
                    raise ValueError(f'View {view.id} references non-existent field {field_id}')
        return v
    
    class Config:
        json_encoders = {
            ObjectId: str
        }
        allow_population_by_field_name = True

class SystemInstance(BaseModel):
    """An instance of a management system for a specific tenant."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_id: str
    tenant_id: str
    name: str
    settings: Optional[Dict[str, Any]] = None
    status: str = "active"  # active, inactive, error
    error_message: Optional[str] = None
    plugin_status: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # MongoDB specific field - not included in JSON serialization
    mongo_id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'inactive', 'error']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v
    
    @validator('error_message')
    def validate_error_message(cls, v, values):
        if values.get('status') == 'error' and not v:
            raise ValueError('Error message is required when status is "error"')
        return v
    
    class Config:
        json_encoders = {
            ObjectId: str
        }
        allow_population_by_field_name = True
        validate_assignment = True

class SystemTemplate(ManagementSystem):
    """A template for creating management systems."""
    is_template: bool = True
    customizable_fields: Optional[List[str]] = None  # List of field paths that can be customized

class PaginatedResponse(BaseModel):
    """Paginated response for data queries."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        json_encoders = {
            ObjectId: str
        }

class UserSystemPermission(BaseModel):
    """User permissions for a system instance."""
    user_id: str
    tenant_id: str
    instance_id: str
    permissions: List[SystemPermission]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # MongoDB specific field - not included in JSON serialization
    mongo_id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    class Config:
        json_encoders = {
            ObjectId: str
        }
        allow_population_by_field_name = True

class CacheConfig:
    """Cache configuration for management systems."""
    SYSTEM_DEF_TTL = 3600  # 1 hour
    INSTANCE_TTL = 300  # 5 minutes
    DATA_TTL = 60  # 1 minute
    USER_PERMISSIONS_TTL = 300  # 5 minutes 