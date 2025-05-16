"""
User Extension Model

Defines the structure and behavior of a user extension in the system.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class UserExtension(BaseModel):
    """
    Represents a user extension with metrics and practicality data.
    
    Attributes:
        id: The unique identifier of the extension
        user_id: The identifier of the user this extension belongs to
        tenant_id: The identifier of the tenant
        extension_type: The type of extension
        metrics: A dictionary of metrics associated with the extension
        practicality: A dictionary containing practicality data with factors
    """
    
    id: Optional[str] = Field(None, description="Unique identifier for the extension")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    extension_type: str = Field(..., description="Type of the extension")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Metrics data")
    practicality: Dict[str, Any] = Field(default_factory=dict, description="Practicality data with factors")
    
    class Config:
        populate_by_name = True
        
    def to_document(self) -> Dict[str, Any]:
        """
        Convert the model to a MongoDB document.
        
        Returns:
            Dictionary representation suitable for MongoDB
        """
        doc = self.model_dump(exclude_none=True)
        
        # Don't include id in the document if it's None
        if self.id is None:
            doc.pop("id", None)
        
        return doc
    
    @classmethod
    def from_document(cls, doc: Dict[str, Any]) -> "UserExtension":
        """
        Create a UserExtension from a MongoDB document.
        
        Args:
            doc: MongoDB document
            
        Returns:
            UserExtension instance
        """
        if "_id" in doc and "id" not in doc:
            doc["id"] = str(doc.pop("_id"))
            
        return cls(**doc) 