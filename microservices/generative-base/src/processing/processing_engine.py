"""
Processing Engine Module

This module provides the core processing engine for generative tasks.
It handles template loading, execution, and result processing.
"""

from typing import Dict, Any, List, Optional
import asyncio
import time
import structlog
from datetime import datetime
import uuid

from ..common.config import Settings
from ..common.exceptions import ProcessingError
from .component_registry import ComponentRegistry
from .pipeline_executor import PipelineExecutor

# Configure structured logging
logger = structlog.get_logger(__name__)

class ProcessingEngine:
    """
    Engine for processing generative tasks.
    
    This class is responsible for:
    - Loading and validating templates
    - Executing generative operations through the pipeline executor
    - Post-processing results
    - Error handling and recovery
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the processing engine.
        
        Args:
            settings: Application configuration settings
        """
        self.settings = settings
        self.template_cache = {}
        
        # Initialize component registry
        self.component_registry = ComponentRegistry()
        
        # Initialize pipeline executor
        self.pipeline_executor = PipelineExecutor(self.component_registry)
        
        logger.info("Processing engine initialized")
    
    async def process_context(self, context: Dict[str, Any], template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a single context.
        
        Args:
            context: Task context including inputs
            template: Template specification with stages (if None, will be loaded from context's template_id)
            
        Returns:
            Processing results
            
        Raises:
            ProcessingError: If processing fails
        """
        start_time = time.time()
        context_id = context.get("_id", "unknown")
        template_id = context.get("template_id", "unknown") if not template else template.get("id", "unknown")
        
        try:
            # If template not provided, load it from template_id in context
            if not template and "template_id" in context:
                template = await self._load_template(context["template_id"])
            
            if not template:
                raise ProcessingError(
                    message="Template not found or invalid", 
                    component="processing_engine",
                    retry_recommended=False
                )
            
            # Validate template
            if not self._validate_template(template):
                raise ProcessingError(
                    message="Invalid template structure",
                    component="processing_engine",
                    retry_recommended=False
                )
            
            # Execute template with pipeline executor
            result = await self.pipeline_executor.execute(template, context)
            
            # Add metadata
            processing_time = time.time() - start_time
            
            if "metadata" not in result:
                result["metadata"] = {}
                
            result["metadata"].update({
                "processing_time": processing_time,
                "template_id": template_id,
                "context_id": context_id,
                "processed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(
                "Context processed successfully",
                context_id=context_id,
                template_id=template_id,
                processing_time=processing_time
            )
            
            return result
            
        except ProcessingError as e:
            # Re-raise ProcessingError as is
            raise e
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)
            
            logger.exception(
                "Context processing failed",
                context_id=context_id,
                template_id=template_id,
                error=error_message,
                processing_time=processing_time
            )
            
            raise ProcessingError(
                message=f"Unexpected error processing context: {error_message}",
                component="processing_engine",
                retry_recommended=True,
                original_error=e
            )
    
    async def process_batch(self, contexts: List[Dict[str, Any]], template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a batch of contexts with the same template.
        
        Args:
            contexts: List of contexts to process
            template_id: Optional template ID (if None, each context must have its own template_id)
            
        Returns:
            Batch processing results
        """
        start_time = time.time()
        batch_id = str(uuid.uuid4())
        
        # If template_id provided, load it once for all contexts
        template = None
        if template_id:
            try:
                template = await self._load_template(template_id)
                if not template:
                    return {
                        "success": False,
                        "error": f"Template not found: {template_id}",
                        "items": [],
                        "batch_id": batch_id
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error loading template: {str(e)}",
                    "items": [],
                    "batch_id": batch_id
                }
        
        results = []
        completed = 0
        failed = 0
        
        # Process each context in the batch
        for context in contexts:
            try:
                # Use the pre-loaded template or process with context's template_id
                result = await self.process_context(context, template)
                results.append({
                    "context_id": context.get("_id", "unknown"),
                    "success": True,
                    "result": result
                })
                completed += 1
            except Exception as e:
                error_message = str(e)
                if isinstance(e, ProcessingError):
                    error_message = e.message
                
                results.append({
                    "context_id": context.get("_id", "unknown"),
                    "success": False,
                    "error": error_message
                })
                failed += 1
        
        # Build batch result
        processing_time = time.time() - start_time
        batch_result = {
            "success": failed == 0,
            "items": results,
            "summary": {
                "total": len(contexts),
                "completed": completed,
                "failed": failed
            },
            "metadata": {
                "processing_time": processing_time,
                "batch_id": batch_id,
                "template_id": template_id if template_id else "multiple",
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(
            "Batch processed",
            batch_id=batch_id,
            template_id=template_id if template_id else "multiple",
            batch_size=len(contexts),
            processing_time=processing_time,
            completed=completed,
            failed=failed
        )
        
        return batch_result
    
    async def _load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template or None if not found
            
        Raises:
            ProcessingError: If template loading fails
        """
        # Check cache first
        if template_id in self.template_cache:
            return self.template_cache[template_id]
        
        # If no repository available, fail gracefully
        if not hasattr(self, "repository") or not self.repository:
            raise ProcessingError(
                message="Repository not configured for template loading",
                component="processing_engine",
                retry_recommended=False
            )
        
        try:
            template = await self.repository.get_template(template_id)
            
            if template:
                # Cache the template
                self.template_cache[template_id] = template
                
            return template
            
        except Exception as e:
            raise ProcessingError(
                message=f"Failed to load template: {str(e)}",
                component="processing_engine",
                retry_recommended=True,
                original_error=e
            )
    
    def _validate_template(self, template: Dict[str, Any]) -> bool:
        """
        Validate a template structure.
        
        Args:
            template: Template to validate
            
        Returns:
            Validation result
        """
        if not template:
            return False
            
        # Template must have an ID and stages
        if "id" not in template:
            logger.warning("Template missing ID")
            return False
            
        if "stages" not in template or not isinstance(template["stages"], list):
            logger.warning("Template missing stages array", template_id=template.get("id"))
            return False
            
        # Validate each stage
        for i, stage in enumerate(template["stages"]):
            if not isinstance(stage, dict):
                logger.warning(
                    "Invalid stage object",
                    template_id=template.get("id"),
                    stage_index=i
                )
                return False
                
            if "component" not in stage:
                logger.warning(
                    "Stage missing component",
                    template_id=template.get("id"),
                    stage_index=i
                )
                return False
        
        return True
    
    async def close(self):
        """Clean up resources."""
        # Close pipeline executor if it has a close method
        if hasattr(self.pipeline_executor, "close"):
            await self.pipeline_executor.close()
            
        logger.info("Processing engine closed")