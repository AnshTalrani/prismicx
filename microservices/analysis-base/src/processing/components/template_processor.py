"""
Template Processor Module

This module is responsible for processing validated templates and orchestrating
the execution of analysis workflows. It provides a flexible pipeline that can be
extended with new processing capabilities as development progresses.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple, Callable
from datetime import datetime
import asyncio
import importlib
import json
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Status tracking for template execution
class ExecutionStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial_success"

class ExecutionResult:
    """Container for execution results"""
    
    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.status = ExecutionStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.results = {}
        self.errors = []
        self.metadata = {}
    
    def start(self):
        """Mark execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()
    
    def complete(self, results: Dict[str, Any]):
        """Mark execution as completed"""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = datetime.now()
        self.results = results
    
    def fail(self, error: str):
        """Mark execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.end_time = datetime.now()
        self.errors.append(error)
    
    def add_error(self, error: str):
        """Add an error without failing the execution"""
        self.errors.append(error)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the execution result"""
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            "results": self.results,
            "errors": self.errors,
            "metadata": self.metadata
        }

# Template models
class InputSpec(BaseModel):
    """Input specification for a template"""
    data_source: str
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class ProcessingSpec(BaseModel):
    """Processing specification for a template"""
    analysis_type: str
    parameters: Optional[Dict[str, Any]] = None

class OutputSpec(BaseModel):
    """Output specification for a template"""
    format: str
    store_in: Optional[str] = None
    metadata_fields: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class TriggerSpec(BaseModel):
    """Trigger specification for a template"""
    type: str
    schedule: Optional[str] = None
    event: Optional[str] = None

class ErrorHandlingSpec(BaseModel):
    """Error handling specification for a template"""
    retry_count: int = 0
    retry_delay: int = 0
    fallback: Optional[str] = None

class AnalysisTemplate(BaseModel):
    """Analysis template model"""
    template_id: str
    name: str
    purpose: str
    scope: str
    trigger: TriggerSpec
    input_spec: InputSpec
    processing: ProcessingSpec
    output: OutputSpec
    error_handling: Optional[ErrorHandlingSpec] = None

class TemplateProcessor:
    """
    Processes templates by orchestrating the execution of analysis workflows.
    Designed to be extensible for future processing capabilities.
    """
    
    def __init__(self):
        """Initialize the template processor"""
        self.executions = {}  # Store execution results by ID
        self.worker_registry = {}  # Registry of available worker functions
        self.templates = {}  # Store validated templates
        self._register_default_workers()
        logger.info("Template processor initialized")
    
    def _register_default_workers(self):
        """Register default worker functions"""
        # This will be populated as workers are implemented
        # Example: self.register_worker("descriptive", self._descriptive_analysis)
        pass
    
    def register_worker(self, analysis_type: str, worker_func: Callable):
        """
        Register a worker function for a specific analysis type.
        
        Args:
            analysis_type: Type of analysis the worker handles
            worker_func: Function that implements the analysis
        """
        self.worker_registry[analysis_type] = worker_func
        logger.info(f"Registered worker for analysis type: {analysis_type}")
    
    def validate_template(self, template_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[AnalysisTemplate]]:
        """
        Validate a template against the schema.
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Tuple of (is_valid, error_message, validated_template)
        """
        try:
            # Validate using Pydantic model
            template = AnalysisTemplate(**template_data)
            
            # Additional validation logic can be added here
            # For example, checking if analysis_type is supported
            
            return True, None, template
            
        except Exception as e:
            logger.error(f"Template validation error: {str(e)}")
            return False, str(e), None
    
    def store_template(self, template: AnalysisTemplate):
        """
        Store a validated template.
        
        Args:
            template: Validated template to store
        """
        self.templates[template.template_id] = template
        logger.info(f"Stored template: {template.template_id}")
    
    def list_templates(self, filters: Optional[Dict[str, Any]] = None) -> List[AnalysisTemplate]:
        """
        List stored templates with optional filtering.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            List of matching templates
        """
        if not filters:
            return list(self.templates.values())
        
        # Apply filters
        result = []
        for template in self.templates.values():
            match = True
            for key, value in filters.items():
                if hasattr(template, key) and getattr(template, key) != value:
                    match = False
                    break
            if match:
                result.append(template)
        
        return result
    
    async def process_template(self, template: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a template asynchronously.
        
        Args:
            template: Template to process (can be dict or AnalysisTemplate)
            input_data: Optional input data (if not specified in template)
            
        Returns:
            Execution ID for tracking
        """
        # Convert dict to AnalysisTemplate if needed
        if isinstance(template, dict):
            is_valid, error_msg, validated_template = self.validate_template(template)
            if not is_valid:
                raise ValueError(f"Invalid template: {error_msg}")
            template = validated_template
        
        # Store template for future reference
        self.store_template(template)
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        result = ExecutionResult(execution_id)
        self.executions[execution_id] = result
        
        # Start processing in background
        asyncio.create_task(self._execute_template(template, result, input_data))
        
        return execution_id
    
    async def _execute_template(self, template: Dict[str, Any], result: ExecutionResult, 
                               input_data: Optional[Dict[str, Any]] = None):
        """
        Execute a template and update the execution result.
        
        Args:
            template: Template to execute
            result: Execution result to update
            input_data: Optional input data
            
        Returns:
            Execution result
        """
        try:
            # Update execution status
            result.status = ExecutionStatus.RUNNING
            result.start_time = datetime.now()
            
            # Import processing engine
            from ..processing.processing_engine import processing_engine
            
            # Run analysis
            analysis_results = await processing_engine.run_analysis(template, input_data)
            
            # Store results
            from ..output.output_manager import output_manager
            final_results = await output_manager.store_results(analysis_results, template)
            
            # Send notification to agent if needed
            if template.get("scope") in ["individual", "batch"] or "user_id" in final_results or "batch_id" in final_results:
                await output_manager.send_updates_to_agent(
                    result.execution_id,
                    {"status": "completed", "results": final_results}
                )
            
            # Update execution result
            result.status = ExecutionStatus.COMPLETED
            result.end_time = datetime.now()
            result.results = final_results
            
            return final_results
            
        except Exception as e:
            # Log error
            logger.error(f"Template execution failed: {str(e)}")
            
            # Update execution result
            result.status = ExecutionStatus.FAILED
            result.end_time = datetime.now()
            result.errors.append(str(e))
            
            # Handle error based on template error_handling configuration
            error_handling = template.get("error_handling", {})
            retry_count = error_handling.get("retry_count", 0)
            
            if retry_count > 0 and result.attempts < retry_count:
                # Retry execution
                result.attempts += 1
                logger.info(f"Retrying template execution (attempt {result.attempts}/{retry_count})")
                return await self._execute_template(template, result, input_data)
            
            # Apply fallback if specified
            fallback = error_handling.get("fallback")
            if fallback:
                logger.info(f"Applying fallback: {fallback}")
                # Implement fallback logic here
                
            # Notify agent about failure
            await output_manager.send_updates_to_agent(
                result.execution_id,
                {"status": "failed", "error": str(e)}
            )
            
            raise
    
    async def _retrieve_data(self, template: AnalysisTemplate, 
                           input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve data based on template input specification.
        
        Args:
            template: Template with input specification
            input_data: Optional override input data
            
        Returns:
            Retrieved data
        """
        # If input data is provided directly, use it
        if input_data:
            return input_data
        
        # Otherwise, retrieve data based on template input spec
        try:
            # This is a placeholder for actual data retrieval logic
            # In a real implementation, this would connect to data sources
            
            # Example implementation:
            # data_source = template.input_spec.data_source
            # query = template.input_spec.query
            # filters = template.input_spec.filters
            
            # For now, return empty data
            logger.info(f"Data retrieval for template {template.template_id} would use source: {template.input_spec.data_source}")
            return {"data": [], "metadata": {"source": template.input_spec.data_source}}
            
        except Exception as e:
            logger.error(f"Data retrieval failed: {str(e)}")
            raise
    
    async def _format_output(self, template: AnalysisTemplate, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format and store output based on template specification.
        
        Args:
            template: Template with output specification
            results: Results to format
            
        Returns:
            Formatted results
        """
        # Extract metadata fields specified in template
        metadata_fields = template.output.metadata_fields or []
        
        # Extract tags
        tags = template.output.tags or []
        
        # Format output
        formatted_output = {
            "results": results,
            "metadata": {
                field: results.get(field) for field in metadata_fields if field in results
            },
            "tags": tags
        }
        
        # Store results if specified
        store_in = template.output.store_in
        if store_in:
            logger.info(f"Results would be stored in: {store_in}")
            # Placeholder for actual storage logic
            # In a real implementation, this would connect to a database or other storage
        
        return formatted_output
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a template execution.
        
        Args:
            execution_id: ID of the execution to check
            
        Returns:
            Execution status as dictionary, or None if not found
        """
        execution = self.executions.get(execution_id)
        if execution:
            return execution.to_dict()
        return None

# Singleton instance for global access
template_processor = TemplateProcessor()
