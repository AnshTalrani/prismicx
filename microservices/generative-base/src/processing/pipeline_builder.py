"""
Pipeline Builder Module

This module provides functionality to construct processing pipelines based on
flow definitions from YAML configuration files.
"""

import logging
from typing import Dict, Any, List, Optional

from .pipeline import ProcessingPipeline
from .base_component import BaseComponent
from ..common.config_loader import ConfigurationLoader

logger = logging.getLogger(__name__)

class PipelineBuilder:
    """
    Builds processing pipelines based on flow definitions from YAML configuration.
    """
    
    def __init__(self, config_loader: ConfigurationLoader, component_registry):
        """
        Initialize the pipeline builder.
        
        Args:
            config_loader: Configuration loader for YAML configs
            component_registry: Registry of available components
        """
        self.config_loader = config_loader
        self.component_registry = component_registry
        logger.info("Pipeline builder initialized")
    
    def build_pipeline_for_template(self, template_id: str, repository, settings) -> Optional[ProcessingPipeline]:
        """
        Build a processing pipeline for a specific template.
        
        Args:
            template_id: The template ID to build a pipeline for
            repository: Data repository to use
            settings: Application settings
            
        Returns:
            Configured processing pipeline or None if not found
        """
        # Get the flow configuration for this template
        flow_config = self.config_loader.get_flow_for_template(template_id)
        if not flow_config:
            logger.error(f"No flow configuration found for template: {template_id}")
            return None
        
        # Build the pipeline from the flow configuration
        return self.build_pipeline(flow_config, repository, settings)
    
    def build_pipeline(self, flow_config: Dict[str, Any], repository, settings) -> ProcessingPipeline:
        """
        Build a processing pipeline from a flow configuration.
        
        Args:
            flow_config: Flow configuration from YAML
            repository: Data repository to use
            settings: Application settings
            
        Returns:
            Configured processing pipeline
            
        Raises:
            ValueError: If the flow configuration is invalid
        """
        flow_id = flow_config.get('id', 'unnamed_flow')
        flow_modules = flow_config.get('modules', [])
        
        if not flow_modules:
            raise ValueError(f"Flow '{flow_id}' has no modules defined")
        
        # Create the components for this flow
        components = []
        for module_config in flow_modules:
            module_id = module_config.get('id')
            if not module_id:
                logger.warning(f"Skipping module with no ID in flow: {flow_id}")
                continue
            
            # Get any configuration overrides
            config_override = module_config.get('config_override', {})
            
            try:
                # Create the component from its configuration
                component = self.component_registry.create_from_config(
                    module_id=module_id,
                    override_config=config_override
                )
                components.append(component)
                logger.info(f"Added component {module_id} to pipeline for flow: {flow_id}")
                
            except Exception as e:
                logger.error(f"Failed to create component {module_id} for flow {flow_id}: {str(e)}")
                raise ValueError(f"Failed to create component {module_id}: {str(e)}")
        
        # Create the pipeline with the components
        pipeline = ProcessingPipeline(
            components=components,
            repository=repository,
            settings=settings
        )
        
        logger.info(f"Built pipeline for flow '{flow_id}' with {len(components)} components")
        return pipeline
    
    def build_component_chain(self, flow_config: Dict[str, Any]) -> List[BaseComponent]:
        """
        Build a chain of components from a flow configuration.
        
        Args:
            flow_config: Flow configuration from YAML
            
        Returns:
            List of configured components
            
        Raises:
            ValueError: If the flow configuration is invalid
        """
        flow_id = flow_config.get('id', 'unnamed_flow')
        flow_modules = flow_config.get('modules', [])
        
        if not flow_modules:
            raise ValueError(f"Flow '{flow_id}' has no modules defined")
        
        # Create the components for this flow
        components = []
        for module_config in flow_modules:
            module_id = module_config.get('id')
            if not module_id:
                logger.warning(f"Skipping module with no ID in flow: {flow_id}")
                continue
            
            # Get any configuration overrides
            config_override = module_config.get('config_override', {})
            
            try:
                # Create the component from its configuration
                component = self.component_registry.create_from_config(
                    module_id=module_id,
                    override_config=config_override
                )
                components.append(component)
                logger.info(f"Added component {module_id} to component chain for flow: {flow_id}")
                
            except Exception as e:
                logger.error(f"Failed to create component {module_id} for flow {flow_id}: {str(e)}")
                raise ValueError(f"Failed to create component {module_id}: {str(e)}")
        
        return components 