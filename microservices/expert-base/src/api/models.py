"""
API models for the Expert Base microservice.

This module defines Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4


class ExpertRequest(BaseModel):
    """
    Request model for expert processing.
    
    Attributes:
        expert: The ID of the expert to use (e.g., "instagram", "twitter").
        intent: The processing intent (e.g., "generate", "analyze", "review").
        content: The content to process.
        parameters: Additional parameters for the expert processing.
        metadata: Additional metadata for the request.
        tracking_id: Optional tracking ID for the request.
    """
    expert: str
    intent: str
    content: str
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tracking_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))


class ExpertResponse(BaseModel):
    """
    Response model for expert processing.
    
    Attributes:
        expert_id: The ID of the expert that processed the request.
        intent: The processing intent that was used.
        content: The processed content.
        feedback: Additional feedback from the expert.
        metadata: Additional metadata for the response.
        tracking_id: The tracking ID from the request.
    """
    expert_id: str
    intent: str
    content: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tracking_id: Optional[str] = None


class ExpertCapability(BaseModel):
    """
    Model for expert capabilities.
    
    Attributes:
        expert_id: The ID of the expert.
        capabilities: List of capabilities supported by the expert.
        supported_intents: List of intents supported by the expert.
    """
    expert_id: str
    capabilities: List[str]
    supported_intents: List[str]


class ExpertCapabilitiesResponse(BaseModel):
    """
    Response model for expert capabilities.
    
    Attributes:
        experts: Dictionary mapping expert IDs to their capabilities.
    """
    experts: Dict[str, ExpertCapability]


class HealthResponse(BaseModel):
    """
    Response model for health check.
    
    Attributes:
        status: The status of the service.
    """
    status: str 