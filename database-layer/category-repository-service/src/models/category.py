"""
Category data models.

This module defines Pydantic models for categories, factors, campaigns, batch as objects, and entity assignments.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator


class CategoryBase(BaseModel):
    """Base model for categories."""
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    type: str  # "factor", "campaign", "batch_as_object"
    category_id: Optional[str] = None


class Category(CategoryBase):
    """Full category model."""
    category_id: str
    type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class Metrics(BaseModel):
    """Base metrics model."""
    performance: Optional[float] = None
    engagement: Optional[float] = None
    conversion: Optional[float] = None
    other_metrics: Dict[str, Any] = Field(default_factory=dict)


class FactorBase(BaseModel):
    """Base model for factors."""
    name: str
    category_id: str
    definition: Dict[str, Any] = Field(default_factory=dict)
    purpose: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FactorCreate(FactorBase):
    """Model for creating a new factor."""
    factor_id: Optional[str] = None
    metrics: Optional[Metrics] = None


class Factor(FactorBase):
    """Full factor model."""
    factor_id: str
    metrics: Metrics = Field(default_factory=Metrics)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class BatchAsObjectBase(BaseModel):
    """Base model for batch as objects."""
    name: str
    category_id: str
    json_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchAsObjectCreate(BatchAsObjectBase):
    """Model for creating a new batch as object."""
    bao_id: Optional[str] = None
    metrics: Optional[Metrics] = None


class BatchAsObject(BatchAsObjectBase):
    """Full batch as object model."""
    bao_id: str
    metrics: Metrics = Field(default_factory=Metrics)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class CampaignBase(BaseModel):
    """Base model for campaigns."""
    name: str
    category_id: str
    structure: Dict[str, Any] = Field(default_factory=dict)
    purpose: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignCreate(CampaignBase):
    """Model for creating a new campaign."""
    campaign_id: Optional[str] = None
    metrics: Optional[Metrics] = None


class Campaign(CampaignBase):
    """Full campaign model."""
    campaign_id: str
    metrics: Metrics = Field(default_factory=Metrics)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class EntityAssignmentBase(BaseModel):
    """Base model for entity assignments."""
    entity_type: str  # "user", "content", etc.
    entity_id: str
    category_type: str  # "factor", "campaign", "batch_as_object"
    item_id: str  # factor_id, campaign_id, or bao_id


class EntityAssignmentCreate(EntityAssignmentBase):
    """Model for creating a new entity assignment."""
    pass


class EntityAssignment(EntityAssignmentBase):
    """Full entity assignment model."""
    assignment_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class MetricsUpdate(BaseModel):
    """Model for updating metrics."""
    metrics: Metrics 