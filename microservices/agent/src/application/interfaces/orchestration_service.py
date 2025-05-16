"""
Interface for the orchestration service.
"""
from typing import Dict, Any, Optional, List, Protocol

from src.domain.entities.execution_template import ExecutionTemplate

class IOrchestrationService(Protocol):
    """
    Interface for orchestration service.
    
    This service is responsible for executing templates based on their type.
    """
    
    async def execute_template(self, 
                              template: ExecutionTemplate, 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a template.
        
        Args:
            template: Template to execute
            context: Execution context
            
        Returns:
            Execution result
        """
        ...
    
    async def execute_step(self, 
                          step_data: Dict[str, Any], 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step in a template.
        
        Args:
            step_data: Step data
            context: Execution context
            
        Returns:
            Step execution result
        """
        ...
    
    async def process_request(self,
                            request_id: str,
                            template: ExecutionTemplate,
                            data: Dict[str, Any],
                            metadata: Optional[Dict[str, Any]] = None,
                            user: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process a request using a template.
        
        Args:
            request_id: Request ID
            template: Template to execute
            data: Request data
            metadata: Request metadata
            user: User making the request
            
        Returns:
            Processing result
        """
        ...
    
    async def process_batch_item(self,
                               batch_id: str,
                               item_id: str,
                               template: ExecutionTemplate,
                               data: Dict[str, Any],
                               metadata: Optional[Dict[str, Any]] = None,
                               batch_metadata: Optional[Dict[str, Any]] = None,
                               source: Optional[str] = None,
                               user: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process a batch item using a template.
        
        Args:
            batch_id: Batch ID
            item_id: Item ID
            template: Template to execute
            data: Item data
            metadata: Item metadata
            batch_metadata: Batch metadata
            source: Source of the batch
            user: User making the request
            
        Returns:
            Processing result
        """
        ...
    
    async def process_data(self, 
                          data: Dict[str, Any], 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data without a template.
        
        Args:
            data: Data to process
            context: Execution context
            
        Returns:
            Processing result
        """
        ...
    
    async def execute_pipeline(self, 
                              steps: List[Dict[str, Any]], 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a sequence of steps.
        
        Args:
            steps: List of step configurations
            context: Execution context
            
        Returns:
            Pipeline execution result
        """
        ... 