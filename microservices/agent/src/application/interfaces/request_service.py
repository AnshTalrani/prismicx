"""
Request Service interface for processing requests.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from src.domain.entities.request import Request, BatchRequest
from src.domain.entities.execution_template import ExecutionTemplate
from src.domain.value_objects.batch_type import BatchType, ProcessingMethod, DataSourceType

class IRequestService(ABC):
    """
    Interface for request processing service.
    
    This service provides methods for processing different types of requests:
    - Single requests (individual processing)
    - Batch requests (using the 2x2 matrix model of processing method × data source type)
    
    The 2x2 matrix model consists of:
    - Processing methods: INDIVIDUAL (one-by-one) vs BATCH (all together)
    - Data sources: USERS (from user-data-service) vs CATEGORIES (from category repository)
    
    This gives four possible batch types:
    1. INDIVIDUAL_USERS: Process users one-by-one
    2. BATCH_USERS: Process users all together
    3. INDIVIDUAL_CATEGORIES: Process categories one-by-one
    4. BATCH_CATEGORIES: Process categories all together
    """
    
    @abstractmethod
    async def process_request(self, request: Any, template: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process a single request.
        
        Args:
            request: Request to process
            template: Optional template to use for processing
            
        Returns:
            Processing results
        """
        pass
    
    @abstractmethod
    async def get_processing_templates(self) -> List[Dict[str, Any]]:
        """
        Get available processing templates.
        
        Returns:
            List of available templates
        """
        pass
    
    # Core batch processing methods (2x2 matrix model)
    @abstractmethod
    async def process_batch(self, batch_request: Any) -> Dict[str, Any]:
        """
        Process a batch request based on its batch type.
        
        This method serves as the main entry point for all batch processing,
        delegating to the appropriate specialized method based on the batch type.
        The batch type follows the 2x2 matrix model (processing method × data source type).
        
        Args:
            batch_request: The batch request to process
            
        Returns:
            Batch processing results
        """
        pass
    
    @abstractmethod
    async def process_user_batch(self, batch_request: Any, 
                               process_individually: Optional[bool] = None) -> Dict[str, Any]:
        """
        Process a batch of users.
        
        Args:
            batch_request: The batch request containing user data
            process_individually: Whether to process users individually or as a group.
                                 If None, uses the batch_type from the request.
            
        Returns:
            Batch processing results
        """
        pass
    
    @abstractmethod
    async def process_category_batch(self, batch_request: Any,
                                  process_individually: Optional[bool] = None) -> Dict[str, Any]:
        """
        Process a batch of categories.
        
        Args:
            batch_request: The batch request containing category data
            process_individually: Whether to process categories individually or as a group.
                                 If None, uses the batch_type from the request.
            
        Returns:
            Batch processing results
        """
        pass 