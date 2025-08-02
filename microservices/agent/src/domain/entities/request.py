"""Request entity for the domain layer."""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

from src.domain.value_objects.execution_status import ExecutionStatus
from src.domain.value_objects.batch_type import BatchType, ProcessingMethod, DataSourceType

@dataclass
class Request:
    """
    Entity representing a processing request in the system.
    
    A request contains all the necessary data for processing, whether as
    an individual request or as part of a batch.
    
    Attributes:
        id: Unique identifier for the request
        text: Request text content (prompt or question)
        data: Structured data associated with the request
        metadata: Additional metadata about the request
        user_id: ID of the user who initiated the request
        purpose_id: Optional purpose ID for categorizing the request
        created_at: Timestamp when the request was created
    """
    
    id: str = field(default_factory=lambda: str(uuid4()))
    text: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    purpose_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert request to dictionary representation.
        
        Returns:
            Dictionary representation of the request
        """
        return {
            "id": self.id,
            "text": self.text,
            "data": self.data,
            "metadata": self.metadata,
            "user_id": self.user_id,
            "purpose_id": self.purpose_id,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Request":
        """
        Create a request from dictionary data.
        
        Args:
            data: Dictionary containing request data
            
        Returns:
            Request instance
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.utcnow()
            
        return cls(
            id=data.get("id", str(uuid4())),
            text=data.get("text"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            user_id=data.get("user_id"),
            purpose_id=data.get("purpose_id"),
            created_at=created_at
        )
    
    def is_batch_item(self) -> bool:
        """
        Check if this request is part of a batch.
        
        Returns:
            True if request is a batch item, False otherwise
        """
        return "batch_id" in self.metadata
    
    def get_batch_id(self) -> Optional[str]:
        """
        Get the batch ID if this request is part of a batch.
        
        Returns:
            Batch ID if request is a batch item, None otherwise
        """
        return self.metadata.get("batch_id")


@dataclass
class BatchRequest:
    """
    Batch request entity representing a batch of items to process.
    
    This class follows the 2x2 matrix model of batch processing:
    - Processing method: Individual (one-by-one) vs Batch (all together)
    - Data source: Users (from user-data-service) vs Categories (from category repository)
    
    Factory methods are provided for all combinations:
    - create_user_batch: For user data with individual/batch processing
    - create_category_batch: For category data with individual/batch processing
    """
    
    source: str
    template_id: str
    items: List[Dict[str, Any]]
    batch_type: BatchType
    id: str = field(default_factory=lambda: str(uuid4()))
    batch_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def processing_method(self) -> ProcessingMethod:
        """Get the processing method (INDIVIDUAL or BATCH) from the batch type."""
        return self.batch_type.processing_method
    
    @property
    def data_source_type(self) -> DataSourceType:
        """Get the data source type (USERS or CATEGORIES) from the batch type."""
        return self.batch_type.data_source_type
            
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert batch request to dictionary representation.
        
        Returns:
            Dictionary representation of the batch request
        """
        return {
            "id": self.id,
            "source": self.source,
            "template_id": self.template_id,
            "items": self.items,
            "batch_type": self.batch_type.value,
            "batch_metadata": self.batch_metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchRequest':
        """
        Create a batch request from dictionary data.
        
        Args:
            data: Dictionary data to convert to batch request
            
        Returns:
            BatchRequest instance
        """
        # Extract and parse dates
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        # Parse batch type
        batch_type_str = data.get("batch_type", "BATCH_USERS")
        try:
            # Check if it's already a BatchType object
            if isinstance(batch_type_str, BatchType):
                batch_type = batch_type_str
            else:
                # Try to get a batch type by name
                batch_type = BatchType.from_dict({
                    "processing_method": batch_type_str.split("_")[0],
                    "data_source_type": batch_type_str.split("_")[1]
                })
        except (ValueError, IndexError):
            # Default to BATCH_USERS if invalid
            batch_type = BatchType(ProcessingMethod.BATCH, DataSourceType.USERS)
            
        return cls(
            source=data.get("source", "unknown"),
            template_id=data.get("template_id"),
            items=data.get("items", []),
            id=data.get("id", str(uuid4())),
            batch_type=batch_type,
            batch_metadata=data.get("batch_metadata", {}),
            created_at=created_at or datetime.utcnow()
        )
    
    @classmethod
    def create_user_batch(cls, source: str, template_id: str, users: List[Dict[str, Any]], 
                        process_individually: bool = True, **kwargs) -> 'BatchRequest':
        """
        Create a batch request for processing users.
        
        Args:
            source: Source of the request
            template_id: Template ID to use for processing
            users: List of user data to process
            process_individually: Whether to process users individually or as a batch
            **kwargs: Additional keyword arguments
            
        Returns:
            BatchRequest instance
        """
        batch_type = BatchType.INDIVIDUAL_USERS if process_individually else BatchType.BATCH_USERS
        return cls(
            source=source,
            template_id=template_id,
            items=users,
            batch_type=batch_type,
            **kwargs
        )
    
    @classmethod
    def create_category_batch(cls, source: str, template_id: str, categories: List[Dict[str, Any]],
                           process_individually: bool = False, **kwargs) -> 'BatchRequest':
        """
        Create a batch request for processing categories.
        
        Args:
            source: Source of the request
            template_id: Template ID to use for processing
            categories: List of category data to process
            process_individually: Whether to process categories individually or as a batch
            **kwargs: Additional keyword arguments
            
        Returns:
            BatchRequest instance
        """
        batch_type = BatchType.INDIVIDUAL_CATEGORIES if process_individually else BatchType.BATCH_CATEGORIES
        return cls(
            source=source,
            template_id=template_id,
            items=categories,
            batch_type=batch_type,
            **kwargs
        )
    
    @classmethod
    def create_from_components(cls, source: str, template_id: str, items: List[Dict[str, Any]],
                            processing_method: ProcessingMethod, data_source_type: DataSourceType,
                            **kwargs) -> 'BatchRequest':
        """
        Create a batch request directly from processing method and data source components.
        
        This factory method allows the most flexible creation of batch requests
        by directly specifying both dimensions of the 2x2 matrix.
        
        Args:
            source: Source of the request
            template_id: Template ID to use for processing
            items: List of items to process (users or categories)
            processing_method: Processing method (INDIVIDUAL or BATCH)
            data_source_type: Data source type (USERS or CATEGORIES)
            **kwargs: Additional keyword arguments
            
        Returns:
            BatchRequest instance
        """
        batch_type = BatchType.from_components(processing_method, data_source_type)
        return cls(
            source=source,
            template_id=template_id,
            items=items,
            batch_type=batch_type,
            **kwargs
        ) 