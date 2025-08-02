"""
Execution Template entity representing a processing template in the system.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from src.domain.value_objects.service_type import ServiceType

@dataclass
class ExecutionTemplate:
    """
    Entity representing a template for request execution.
    
    Templates define how requests should be processed, including
    service configuration, preprocessing steps, and execution parameters.
    
    Attributes:
        id: Unique identifier for the template
        name: Display name of the template
        description: Description of the template's purpose
        service_type: Type of service to use for processing
        version: Template version
        parameters: Processing parameters for the service
        metadata: Additional metadata about the template
        created_at: Timestamp when the template was created
        updated_at: Timestamp when the template was last updated
    """
    
    name: str
    service_type: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    version: str = "1.0.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert template to dictionary representation.
        
        Returns:
            Dictionary representation of the template
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "service_type": self.service_type,
            "version": self.version,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionTemplate":
        """
        Create a template from dictionary data.
        
        Args:
            data: Dictionary containing template data
            
        Returns:
            ExecutionTemplate instance
            
        Raises:
            ValueError: If required fields are missing
        """
        if not data.get("name") or not data.get("service_type"):
            raise ValueError("Template name and service_type are required")
            
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.utcnow()
            
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
            
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description"),
            service_type=data["service_type"],
            version=data.get("version", "1.0.0"),
            parameters=data.get("parameters", {}),
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def supports_batch_processing(self) -> bool:
        """
        Check if this template supports batch processing.
        
        Returns:
            True if template supports batch processing, False otherwise
        """
        return self.metadata.get("supports_batch", False)
    
    def get_max_batch_size(self) -> int:
        """
        Get the maximum batch size for this template.
        
        Returns:
            Maximum number of items that can be processed in a batch
        """
        return self.metadata.get("max_batch_size", 100)

    def get_service_template(self) -> Dict[str, Any]:
        """
        Get the service-specific template.
        
        Returns:
            Service-specific template data
        """
        return self.service_template 