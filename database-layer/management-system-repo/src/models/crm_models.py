"""
CRM Plugin Data Models

This module defines the data models for the CRM (Customer Relationship Management) plugin.
These models represent customer data, interactions, opportunities, and other CRM entities.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr


class CRMCustomer(BaseModel):
    """Customer model for the CRM plugin."""
    
    customer_id: str = Field(default_factory=lambda: f"cust_{uuid4().hex[:8]}")
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: str = "active"
    type: Optional[str] = None
    segment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "customer_id": "cust_a1b2c3d4",
                "name": "Acme Corporation",
                "email": "contact@acme.com",
                "phone": "+1-555-123-4567",
                "status": "active",
                "type": "business",
                "segment": "enterprise",
                "custom_fields": {
                    "industry": "Manufacturing",
                    "employee_count": 500,
                    "annual_revenue": 5000000
                }
            }
        }


class CRMInteraction(BaseModel):
    """Customer interaction model for the CRM plugin."""
    
    interaction_id: str = Field(default_factory=lambda: f"int_{uuid4().hex[:8]}")
    customer_id: str
    type: str  # "email", "call", "meeting", "note", etc.
    title: str
    content: Optional[str] = None
    interaction_date: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: Optional[int] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "interaction_id": "int_a1b2c3d4",
                "customer_id": "cust_a1b2c3d4",
                "type": "call",
                "title": "Initial sales call",
                "content": "Discussed product features and pricing options.",
                "interaction_date": "2023-06-15T14:30:00Z",
                "duration_minutes": 45,
                "created_by": "user_john",
                "metadata": {
                    "call_outcome": "positive",
                    "next_steps": "Send proposal"
                }
            }
        }


class CRMOpportunity(BaseModel):
    """Sales opportunity model for the CRM plugin."""
    
    opportunity_id: str = Field(default_factory=lambda: f"opp_{uuid4().hex[:8]}")
    customer_id: str
    title: str
    description: Optional[str] = None
    value: Optional[float] = None
    currency: str = "USD"
    stage: str  # "lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"
    probability: Optional[float] = None  # 0.0 to 1.0
    source: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "opportunity_id": "opp_a1b2c3d4",
                "customer_id": "cust_a1b2c3d4",
                "title": "Enterprise License Agreement",
                "description": "Annual software license for 500 users",
                "value": 75000.00,
                "currency": "USD",
                "stage": "proposal",
                "probability": 0.7,
                "source": "direct",
                "expected_close_date": "2023-07-30T00:00:00Z",
                "assigned_to": "user_sarah",
                "custom_fields": {
                    "decision_makers": ["John Smith", "Mary Johnson"],
                    "competitive_situation": "Replacing competitor product"
                }
            }
        }


class CRMContact(BaseModel):
    """Contact person model for the CRM plugin."""
    
    contact_id: str = Field(default_factory=lambda: f"cont_{uuid4().hex[:8]}")
    customer_id: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    is_primary: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "contact_id": "cont_a1b2c3d4",
                "customer_id": "cust_a1b2c3d4",
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@acme.com",
                "phone": "+1-555-987-6543",
                "position": "CTO",
                "department": "IT",
                "is_primary": True,
                "custom_fields": {
                    "linkedin": "https://linkedin.com/in/johnsmith",
                    "preferred_contact_method": "email"
                }
            }
        }


class CRMTask(BaseModel):
    """Task model for the CRM plugin."""
    
    task_id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:8]}")
    related_to_type: str  # "customer", "opportunity", "contact"
    related_to_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"  # "high", "medium", "low"
    status: str = "pending"  # "pending", "in_progress", "completed", "cancelled"
    assigned_to: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "task_id": "task_a1b2c3d4",
                "related_to_type": "opportunity",
                "related_to_id": "opp_a1b2c3d4",
                "title": "Send proposal",
                "description": "Prepare and send the formal proposal document",
                "due_date": "2023-06-20T17:00:00Z",
                "priority": "high",
                "status": "pending",
                "assigned_to": "user_sarah",
                "created_by": "user_john"
            }
        }


class CRMNote(BaseModel):
    """Note model for the CRM plugin."""
    
    note_id: str = Field(default_factory=lambda: f"note_{uuid4().hex[:8]}")
    related_to_type: str  # "customer", "opportunity", "contact"
    related_to_id: str
    title: Optional[str] = None
    content: str
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "note_id": "note_a1b2c3d4",
                "related_to_type": "customer",
                "related_to_id": "cust_a1b2c3d4",
                "title": "Meeting notes",
                "content": "Met with the customer to discuss their needs. They are interested in our enterprise offering.",
                "created_by": "user_john"
            }
        } 