"""
Sales Automation Plugin Data Models

This module defines the data models for the Sales Automation plugin.
These models represent leads, products, quotes, sales pipelines, and other sales entities.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr


class SalesLead(BaseModel):
    """Lead model for the Sales Automation plugin."""
    
    lead_id: str = Field(default_factory=lambda: f"lead_{uuid4().hex[:8]}")
    first_name: str
    last_name: str
    company: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: str = "new"  # "new", "contacted", "qualified", "converted", "disqualified"
    source: Optional[str] = None
    score: Optional[int] = None
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_contacted: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "lead_id": "lead_a1b2c3d4",
                "first_name": "Jane",
                "last_name": "Doe",
                "company": "Acme Corporation",
                "email": "jane.doe@acme.com",
                "phone": "+1-555-123-4567",
                "status": "qualified",
                "source": "website",
                "score": 85,
                "assigned_to": "user_sarah",
                "custom_fields": {
                    "job_title": "CIO",
                    "industry": "Technology",
                    "budget": 50000
                }
            }
        }


class SalesProduct(BaseModel):
    """Product model for the Sales Automation plugin."""
    
    product_id: str = Field(default_factory=lambda: f"prod_{uuid4().hex[:8]}")
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    currency: str = "USD"
    unit: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "product_id": "prod_a1b2c3d4",
                "sku": "ENT-PRO-100",
                "name": "Enterprise Pro License",
                "description": "Annual license for enterprise users",
                "category": "Software",
                "price": 199.99,
                "currency": "USD",
                "unit": "user/year",
                "is_active": True,
                "custom_fields": {
                    "features": ["Advanced reporting", "API access", "Priority support"],
                    "min_quantity": 10
                }
            }
        }


class SalesQuote(BaseModel):
    """Quote model for the Sales Automation plugin."""
    
    quote_id: str = Field(default_factory=lambda: f"quote_{uuid4().hex[:8]}")
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    name: str
    status: str = "draft"  # "draft", "sent", "accepted", "rejected", "expired"
    valid_until: Optional[datetime] = None
    total_amount: float
    currency: str = "USD"
    discount_percentage: Optional[float] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "quote_id": "quote_a1b2c3d4",
                "customer_id": "cust_a1b2c3d4",
                "name": "Enterprise License Quote Q3-2023",
                "status": "sent",
                "valid_until": "2023-09-30T23:59:59Z",
                "total_amount": 49975.00,
                "currency": "USD",
                "discount_percentage": 10.0,
                "notes": "Quote includes 10% volume discount",
                "created_by": "user_john",
                "custom_fields": {
                    "payment_terms": "Net 30",
                    "delivery_method": "Electronic"
                }
            }
        }


class SalesQuoteItem(BaseModel):
    """Quote item model for the Sales Automation plugin."""
    
    item_id: str = Field(default_factory=lambda: f"item_{uuid4().hex[:8]}")
    quote_id: str
    product_id: str
    name: str
    description: Optional[str] = None
    quantity: int = 1
    unit_price: float
    currency: str = "USD"
    discount_percentage: Optional[float] = None
    total_price: float
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "item_id": "item_a1b2c3d4",
                "quote_id": "quote_a1b2c3d4",
                "product_id": "prod_a1b2c3d4",
                "name": "Enterprise Pro License",
                "description": "Annual license for enterprise users",
                "quantity": 25,
                "unit_price": 199.99,
                "currency": "USD",
                "discount_percentage": 10.0,
                "total_price": 4499.78
            }
        }


class SalesTarget(BaseModel):
    """Sales target model for the Sales Automation plugin."""
    
    target_id: str = Field(default_factory=lambda: f"target_{uuid4().hex[:8]}")
    owner_id: str
    owner_type: str = "user"  # "user", "team", "department"
    target_type: str  # "revenue", "deals", "leads", "conversions"
    time_period: str  # "daily", "weekly", "monthly", "quarterly", "yearly"
    period_start: datetime
    period_end: datetime
    target_value: float
    currency: Optional[str] = "USD"
    current_value: float = 0.0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "target_id": "target_a1b2c3d4",
                "owner_id": "user_sarah",
                "owner_type": "user",
                "target_type": "revenue",
                "time_period": "quarterly",
                "period_start": "2023-07-01T00:00:00Z",
                "period_end": "2023-09-30T23:59:59Z",
                "target_value": 200000.00,
                "currency": "USD",
                "current_value": 125000.00,
                "notes": "Q3 sales target"
            }
        }


class SalesPipeline(BaseModel):
    """Sales pipeline model for the Sales Automation plugin."""
    
    pipeline_id: str = Field(default_factory=lambda: f"pipe_{uuid4().hex[:8]}")
    name: str
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "pipeline_id": "pipe_a1b2c3d4",
                "name": "Standard Sales Process",
                "description": "Default pipeline for all new sales opportunities",
                "is_default": True,
                "is_active": True
            }
        }


class SalesPipelineStage(BaseModel):
    """Pipeline stage model for the Sales Automation plugin."""
    
    stage_id: str = Field(default_factory=lambda: f"stage_{uuid4().hex[:8]}")
    pipeline_id: str
    name: str
    description: Optional[str] = None
    order: int
    probability: float  # 0.0 to 1.0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "stage_id": "stage_a1b2c3d4",
                "pipeline_id": "pipe_a1b2c3d4",
                "name": "Qualification",
                "description": "Initial qualification of prospect needs and fit",
                "order": 1,
                "probability": 0.2,
                "is_active": True
            }
        }


class SalesDeal(BaseModel):
    """Deal model for the Sales Automation plugin."""
    
    deal_id: str = Field(default_factory=lambda: f"deal_{uuid4().hex[:8]}")
    customer_id: Optional[str] = None
    lead_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    pipeline_id: str
    stage_id: str
    amount: Optional[float] = None
    currency: str = "USD"
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    status: str = "open"  # "open", "won", "lost", "abandoned"
    assigned_to: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "deal_id": "deal_a1b2c3d4",
                "customer_id": "cust_a1b2c3d4",
                "title": "Enterprise License Renewal",
                "description": "Annual renewal of enterprise licenses",
                "pipeline_id": "pipe_a1b2c3d4",
                "stage_id": "stage_b1c2d3e4",
                "amount": 75000.00,
                "currency": "USD",
                "expected_close_date": "2023-08-15T00:00:00Z",
                "status": "open",
                "assigned_to": "user_sarah",
                "created_by": "user_john",
                "custom_fields": {
                    "renewal_rate": 1.05,
                    "previous_contract_id": "cont_z9y8x7w6"
                }
            }
        } 