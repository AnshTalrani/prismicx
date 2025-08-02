"""
Pipeline Executor Module

This module provides the pipeline execution engine for processing templates with stages.
It handles both individual and batch processing with pipeline flow.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from .class_registry import ClassRegistry

# Configure structured logging
logger = structlog.get_logger(__name__)

class PipelineExecutor:
    """
    Executes processing pipelines with progressive stages.
    
    This executor:
    - Processes templates with multiple stages
    - Handles batch processing with pipeline flow
    - Instantiates classes dynamically based on template instructions
    - Allows individual items to progress through stages independently
    """
    
    def __init__(self, class_registry: ClassRegistry):
        """
        Initialize the pipeline executor.
        
        Args:
            class_registry: Registry for loading classes dynamically
        """
        self.class_registry = class_registry
        logger.info("Pipeline executor initialized")
        
    async def execute(self, template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a template for a single context.
        
        Args:
            template: Template specification
            context: Execution context
            
        Returns:
            Execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract stages from template
            stages = template.get("stages", [])
            if not stages:
                return {
                    "success": False,
                    "error": "No stages defined in template"
                }
                
            # Initialize result with original context
            result = {
                "input": context.get("input", {}),
                "metadata": {
                    "started_at": start_time.isoformat()
                },
                "stages": {}
            }
            
            # Process each stage sequentially
            stage_context = context.copy()
            
            for i, stage in enumerate(stages):
                stage_name = stage.get("name", f"stage_{i}")
                stage_result = await self._execute_stage(stage, stage_context)
                
                # Add stage result to overall result
                result["stages"][stage_name] = stage_result
                
                # Update context for next stage
                stage_context.update(stage_result.get("output", {}))
                
                # If stage failed, stop processing
                if not stage_result.get("success", True):
                    logger.warning(f"Stage {stage_name} failed, stopping processing")
                    result["success"] = False
                    result["error"] = stage_result.get("error", "Stage execution failed")
                    break
            
            # Set overall success if not already set
            if "success" not in result:
                result["success"] = True
                
            # Record completion time
            end_time = datetime.utcnow()
            result["metadata"]["completed_at"] = end_time.isoformat()
            result["metadata"]["processing_time_ms"] = (end_time - start_time).total_seconds() * 1000
            
            return result
            
        except Exception as e:
            logger.exception("Error executing template")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "started_at": start_time.isoformat(),
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
    
    async def execute_batch(self, template: Dict[str, Any], batch_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a template for a batch of items with pipeline flow.
        
        Args:
            template: Template specification
            batch_items: List of batch items
            
        Returns:
            Batch execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract stages from template
            stages = template.get("stages", [])
            if not stages:
                return {
                    "success": False,
                    "error": "No stages defined in template",
                    "items": []
                }
                
            # Initialize result
            result = {
                "metadata": {
                    "started_at": start_time.isoformat(),
                    "total_items": len(batch_items)
                },
                "items": [],
                "summary": {}
            }
            
            # Create a copy of batch items for processing
            # Each item will track its own progress through the pipeline
            processing_items = []
            for item in batch_items:
                processing_items.append({
                    "item_id": item.get("item_id", f"item_{len(processing_items)}"),
                    "original_data": item.copy(),
                    "current_stage": 0,
                    "completed_stages": [],
                    "processing_data": item.copy(),
                    "status": "pending",
                    "results": {}
                })
                
            # Process stages in sequence, but allow items to flow through independently
            # For each stage, process all items that are ready for that stage
            for stage_idx, stage in enumerate(stages):
                stage_name = stage.get("name", f"stage_{stage_idx}")
                logger.info(f"Processing batch stage: {stage_name}")
                
                # Find all items ready for this stage
                stage_items = [
                    item for item in processing_items
                    if item["current_stage"] == stage_idx and item["status"] != "failed"
                ]
                
                if not stage_items:
                    logger.info(f"No items to process for stage {stage_name}")
                    continue
                    
                logger.info(f"Processing {len(stage_items)} items in stage {stage_name}")
                
                # Process all items for this stage in parallel
                tasks = []
                for item in stage_items:
                    tasks.append(self._process_batch_item_stage(
                        item=item,
                        stage=stage,
                        stage_idx=stage_idx
                    ))
                    
                # Wait for all items to complete this stage
                await asyncio.gather(*tasks)
                
                # Update stage in processing items
                for item in stage_items:
                    if item["status"] != "failed":
                        item["current_stage"] = stage_idx + 1
                        
            # Compile final results
            for item in processing_items:
                result["items"].append({
                    "item_id": item["item_id"],
                    "status": item["status"],
                    "results": item["results"],
                    "completed_stages": item["completed_stages"],
                    "error": item.get("error")
                })
                
            # Calculate summary statistics
            completed_count = sum(1 for item in result["items"] if item["status"] == "completed")
            failed_count = sum(1 for item in result["items"] if item["status"] == "failed")
            
            result["summary"] = {
                "total": len(batch_items),
                "completed": completed_count,
                "failed": failed_count,
                "success_rate": completed_count / len(batch_items) if batch_items else 0
            }
            
            # Set overall success
            result["success"] = failed_count == 0
            
            # Record completion time
            end_time = datetime.utcnow()
            result["metadata"]["completed_at"] = end_time.isoformat()
            result["metadata"]["processing_time_ms"] = (end_time - start_time).total_seconds() * 1000
            
            return result
            
        except Exception as e:
            logger.exception("Error executing batch template")
            return {
                "success": False,
                "error": str(e),
                "items": [],
                "metadata": {
                    "started_at": start_time.isoformat(),
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
    
    async def _execute_stage(self, stage: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single stage.
        
        Args:
            stage: Stage configuration
            context: Stage execution context
            
        Returns:
            Stage execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract stage configuration
            class_name = stage.get("class")
            method = stage.get("method", "process")
            parameters = stage.get("parameters", {})
            
            if not class_name:
                raise ValueError("Stage missing required 'class' field")
                
            # Create processor instance
            processor = self.class_registry.instantiate(class_name)
            
            # Get method to call
            method_func = getattr(processor, method, None)
            if not method_func:
                raise ValueError(f"Method '{method}' not found on class '{class_name}'")
                
            # Inject context into parameters if needed
            for param_name, param_value in list(parameters.items()):
                if isinstance(param_value, str) and param_value.startswith("$context."):
                    context_path = param_value[9:].split(".")
                    
                    # Navigate the context path
                    value = context
                    for key in context_path:
                        if key in value:
                            value = value[key]
                        else:
                            logger.warning(f"Context path {param_value} not found")
                            value = None
                            break
                            
                    parameters[param_name] = value
                    
            # Execute method
            logger.debug(f"Executing {class_name}.{method}()")
            result = await method_func(context=context, **parameters)
            
            # Ensure result is properly formatted
            if not isinstance(result, dict):
                result = {"output": result}
                
            if "success" not in result:
                result["success"] = True
                
            # Add metadata
            end_time = datetime.utcnow()
            result["metadata"] = result.get("metadata", {})
            result["metadata"]["class"] = class_name
            result["metadata"]["method"] = method
            result["metadata"]["processing_time_ms"] = (end_time - start_time).total_seconds() * 1000
            
            return result
            
        except Exception as e:
            logger.exception(f"Error executing stage: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "processing_time_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
                }
            }
    
    async def _process_batch_item_stage(self, item: Dict[str, Any], stage: Dict[str, Any], stage_idx: int) -> None:
        """
        Process a batch item for a specific stage.
        
        Args:
            item: Item to process
            stage: Stage configuration
            stage_idx: Stage index
            
        Note:
            This method updates the item in place.
        """
        try:
            # Execute stage
            stage_result = await self._execute_stage(stage, item["processing_data"])
            
            # Update item with stage result
            stage_name = stage.get("name", f"stage_{stage_idx}")
            item["results"][stage_name] = stage_result
            
            # Update processing data with stage output
            if stage_result.get("success", False) and "output" in stage_result:
                item["processing_data"].update(stage_result["output"])
                item["completed_stages"].append(stage_idx)
            else:
                # Mark item as failed
                item["status"] = "failed"
                item["error"] = stage_result.get("error", "Unknown error")
                
            # Check if all stages completed
            if (
                item["status"] != "failed" and 
                item["current_stage"] == stage_idx + 1 and 
                stage_idx == len(item["results"]) - 1
            ):
                item["status"] = "completed"
                
        except Exception as e:
            logger.exception(f"Error processing batch item {item['item_id']} at stage {stage_idx}")
            item["status"] = "failed"
            item["error"] = str(e)


