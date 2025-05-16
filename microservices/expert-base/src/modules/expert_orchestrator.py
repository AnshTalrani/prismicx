"""
Expert Orchestrator for the Expert Base microservice.

This module provides functionality for orchestrating the processing of expert requests.
It coordinates between the Expert Registry, Knowledge Hub, and Processor Factory.
"""

import uuid
from typing import Dict, Any, Optional
from loguru import logger

from src.api.models import ExpertRequest, ExpertResponse
from src.common.exceptions import ExpertNotFoundException, IntentNotSupportedException, ProcessingException
from src.modules.expert_registry import ExpertRegistry
from src.modules.knowledge_hub import KnowledgeHub
from src.processing.factory import ProcessorFactory


class ExpertOrchestrator:
    """
    Expert Orchestrator for coordinating the processing of expert requests.
    
    The Expert Orchestrator is responsible for handling requests, selecting
    the appropriate expert configuration, retrieving relevant knowledge,
    and coordinating the processing pipeline.
    """
    
    def __init__(
        self,
        expert_registry: ExpertRegistry,
        processor_factory: ProcessorFactory,
        knowledge_hub: KnowledgeHub
    ):
        """
        Initialize the Expert Orchestrator.
        
        Args:
            expert_registry: The Expert Registry instance.
            processor_factory: The Processor Factory instance.
            knowledge_hub: The Knowledge Hub instance.
        """
        self.expert_registry = expert_registry
        self.processor_factory = processor_factory
        self.knowledge_hub = knowledge_hub
        logger.info("Initialized Expert Orchestrator")
    
    async def process_request(self, request: ExpertRequest) -> ExpertResponse:
        """
        Process a request using the intent-based configuration model.
        
        Args:
            request: The expert request to process.
            
        Returns:
            The expert response with processed content and feedback.
            
        Raises:
            ExpertNotFoundException: If the expert is not found.
            IntentNotSupportedException: If the intent is not supported.
            ProcessingException: If processing fails.
        """
        # 1. Validate request and extract key components
        expert_id = request.expert
        intent = request.intent
        user_parameters = request.parameters or {}
        content = request.content
        tracking_id = request.tracking_id or str(uuid.uuid4())
        
        logger.info(f"Processing request for expert='{expert_id}', intent='{intent}', tracking_id='{tracking_id}'")
        
        # 2. Verify expert and intent are valid
        if not self.expert_registry.has_expert(expert_id):
            logger.error(f"Expert '{expert_id}' not found")
            raise ExpertNotFoundException(expert_id)
            
        if not self.expert_registry.supports_intent(expert_id, intent):
            logger.error(f"Expert '{expert_id}' does not support intent '{intent}'")
            raise IntentNotSupportedException(expert_id, intent)
        
        # 3. Get expert configuration
        core_config = self.expert_registry.get_core_config(expert_id)
        mode_config = self.expert_registry.get_mode_config(expert_id, intent)
        
        # 4. Merge configurations with user parameters
        working_config = self._merge_configurations(core_config, mode_config, user_parameters)
        
        # 5. Get knowledge context based on configuration
        knowledge_filters = mode_config.get("knowledge_filters", {})
        knowledge_context = await self.knowledge_hub.retrieve_knowledge(
            expert_id=expert_id,
            intent=intent,
            content=content,
            filters=knowledge_filters
        )
        
        # 6. Get appropriate processor for this intent
        processor_id = mode_config.get("processor")
        processor = self.processor_factory.create_processor(processor_id)
        
        # 7. Process the request with merged configuration and knowledge
        try:
            processing_result = await processor.process(
                content=content,
                config=working_config,
                knowledge_context=knowledge_context,
                metadata=request.metadata
            )
            
            # 8. Build and return the response
            return ExpertResponse(
                expert_id=expert_id,
                intent=intent,
                content=processing_result.get("content"),
                feedback=processing_result.get("feedback"),
                metadata=processing_result.get("metadata", {}),
                tracking_id=tracking_id
            )
        except Exception as e:
            error_message = f"Failed to process request: {e}"
            logger.error(error_message)
            raise ProcessingException(error_message)
    
    def _merge_configurations(
        self,
        core_config: Dict[str, Any],
        mode_config: Dict[str, Any],
        user_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge configurations from different sources.
        
        The merging priority is:
        1. User parameters (highest priority)
        2. Mode configuration
        3. Core configuration (lowest priority)
        
        Args:
            core_config: The core configuration.
            mode_config: The mode configuration.
            user_parameters: The user parameters.
            
        Returns:
            The merged configuration.
        """
        # Start with core configuration
        result = {}
        
        # Copy base parameters from core configuration
        if "base_parameters" in core_config:
            result.update(core_config["base_parameters"])
        
        # Add model information
        result["model_id"] = core_config.get("model_id")
        result["adapters"] = core_config.get("adapters", {})
        
        # Add mode configuration parameters
        if "parameters" in mode_config:
            result.update(mode_config["parameters"])
        
        # Add user parameters (highest priority)
        result.update(user_parameters)
        
        return result
    
    async def get_capabilities(self, expert_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get capabilities for a specific expert or all experts.
        
        Args:
            expert_id: Optional ID of the expert to get capabilities for.
                     If not provided, returns capabilities for all experts.
            
        Returns:
            Dictionary of expert capabilities.
        """
        return self.expert_registry.get_capabilities(expert_id) 