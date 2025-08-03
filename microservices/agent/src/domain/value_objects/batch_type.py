"""
Value objects for batch processing types according to the 2x2 matrix model.

This module provides enums and utility functions for working with batch processing types.
The 2x2 matrix model consists of two dimensions:
1. Processing Method: INDIVIDUAL vs BATCH
2. Data Source Type: USERS vs CATEGORIES
"""
from enum import Enum, auto
from typing import Dict, Any, Optional


class ProcessingMethod(str, Enum):
    """
    Processing method dimension of the batch processing model.
    
    Defines how items within a batch should be processed:
    - INDIVIDUAL: Process each item individually (one item per request)
    - BATCH: Process multiple items together (multiple items per request)
    """
    INDIVIDUAL = "INDIVIDUAL"
    BATCH = "BATCH"
    
    @classmethod
    def from_string(cls, value: str) -> 'ProcessingMethod':
        """
        Convert a string to a ProcessingMethod enum.
        
        Args:
            value: String representation (case-insensitive)
            
        Returns:
            Corresponding ProcessingMethod enum value
            
        Raises:
            ValueError: If the string does not match any enum value
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_values = ", ".join([m.value for m in cls])
            raise ValueError(f"Invalid processing method: {value}. Valid values: {valid_values}")
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {"name": self.name, "value": self.value}


class DataSourceType(str, Enum):
    """
    Data source type dimension of the batch processing model.
    
    Defines the type of data source for the batch:
    - USERS: Batch contains user-related data (user profiles, preferences, etc.)
    - CATEGORIES: Batch contains category-related data (batch-as-objects, campaigns, factors, etc.)
    """
    USERS = "USERS"
    CATEGORIES = "CATEGORIES"
    
    @classmethod
    def from_string(cls, value: str) -> 'DataSourceType':
        """
        Convert a string to a DataSourceType enum.
        
        Args:
            value: String representation (case-insensitive)
            
        Returns:
            Corresponding DataSourceType enum value
            
        Raises:
            ValueError: If the string does not match any enum value
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_values = ", ".join([m.value for m in cls])
            raise ValueError(f"Invalid data source type: {value}. Valid values: {valid_values}")
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {"name": self.name, "value": self.value}


class BatchType:
    """
    Complete batch type representation combining both dimensions.
    
    Represents a specific cell in the 2x2 matrix model by combining
    a processing method and a data source type.
    """
    
    def __init__(
            self, 
            processing_method: ProcessingMethod, 
            data_source_type: DataSourceType
        ):
        """
        Initialize a batch type.
        
        Args:
            processing_method: Processing method for this batch type
            data_source_type: Data source type for this batch type
        """
        self.processing_method = processing_method
        self.data_source_type = data_source_type
    
    @classmethod
    def from_components(cls, processing_method: ProcessingMethod, data_source_type: DataSourceType) -> 'BatchType':
        """
        Create a BatchType from processing method and data source type components.
        
        Args:
            processing_method: Processing method enum
            data_source_type: Data source type enum
            
        Returns:
            New BatchType instance
        """
        return cls(processing_method, data_source_type)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchType':
        """
        Create a BatchType from a dictionary.
        
        Args:
            data: Dictionary containing processing_method and data_source_type
            
        Returns:
            New BatchType instance
            
        Raises:
            ValueError: If required keys are missing or invalid
        """
        # Validate required keys
        if not isinstance(data, dict):
            raise ValueError("Expected dictionary for BatchType creation")
            
        if "processing_method" not in data:
            raise ValueError("Missing required key: processing_method")
            
        if "data_source_type" not in data:
            raise ValueError("Missing required key: data_source_type")
            
        # Create enums from strings if needed
        proc_method = data["processing_method"]
        if not isinstance(proc_method, ProcessingMethod):
            proc_method = ProcessingMethod.from_string(proc_method)
            
        data_source = data["data_source_type"]
        if not isinstance(data_source, DataSourceType):
            data_source = DataSourceType.from_string(data_source)
            
        return cls(proc_method, data_source)
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with processing_method and data_source_type
        """
        return {
            "processing_method": self.processing_method,
            "data_source_type": self.data_source_type
        }
    
    def __str__(self) -> str:
        """String representation of the batch type."""
        return f"{self.processing_method}_{self.data_source_type}"
        
    def __eq__(self, other: Any) -> bool:
        """Equality comparison."""
        if not isinstance(other, BatchType):
            return False
        return (
            self.processing_method == other.processing_method and
            self.data_source_type == other.data_source_type
        )


# Convenience constants for common batch types
INDIVIDUAL_USERS = BatchType(ProcessingMethod.INDIVIDUAL, DataSourceType.USERS)
INDIVIDUAL_CATEGORIES = BatchType(ProcessingMethod.INDIVIDUAL, DataSourceType.CATEGORIES)
BATCH_USERS = BatchType(ProcessingMethod.BATCH, DataSourceType.USERS)
BATCH_CATEGORIES = BatchType(ProcessingMethod.BATCH, DataSourceType.CATEGORIES)

# Add convenience constants as class attributes for easier access
BatchType.INDIVIDUAL_USERS = INDIVIDUAL_USERS
BatchType.INDIVIDUAL_CATEGORIES = INDIVIDUAL_CATEGORIES
BatchType.BATCH_USERS = BATCH_USERS
BatchType.BATCH_CATEGORIES = BATCH_CATEGORIES


def get_batch_type_by_name(name: str) -> Optional[BatchType]:
    """
    Get a batch type by its string representation.
    
    Args:
        name: String name in format "PROCESSING_METHOD_DATA_SOURCE_TYPE"
        
    Returns:
        Corresponding BatchType or None if not found
    """
    parts = name.upper().split('_', 1)
    if len(parts) != 2:
        return None
        
    try:
        proc_method = ProcessingMethod.from_string(parts[0])
        data_source = DataSourceType.from_string(parts[1])
        return BatchType(proc_method, data_source)
    except ValueError:
        return None 