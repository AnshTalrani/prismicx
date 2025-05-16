"""
Factory for creating entity extractors based on configuration.
Provides a unified interface for creating different types of extractors.
"""

import logging
from typing import Dict, Any, Optional
from langchain.chains import create_extraction_chain

from src.config.config_inheritance import ConfigInheritance
from src.models.llm.model_registry import ModelRegistry
from src.langchain_components.nlp.schema_loader import schema_loader

class ExtractorFactory:
    """
    Factory for creating entity extractors.
    Builds different types of extractors based on bot configuration.
    """
    
    def __init__(self):
        """Initialize the extractor factory."""
        self.config_inheritance = ConfigInheritance()
        self.model_registry = ModelRegistry()
        self.logger = logging.getLogger(__name__)
        self.extractors = {}
    
    def create_extractor(self, bot_type: str, extractor_name: str) -> Optional[Any]:
        """
        Create an entity extractor based on configuration.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            extractor_name: The name of the extractor to create
            
        Returns:
            The created extractor or None if creation fails
        """
        config = self.config_inheritance.get_config(bot_type)
        extractor_config = config.get(f"nlp.extractors.{extractor_name}", {})
        
        if not extractor_config:
            self.logger.warning(f"No configuration found for extractor {extractor_name}")
            return None
        
        extractor_type = extractor_config.get("type", "llm")
        
        if extractor_type == "llm":
            return self._create_llm_extractor(bot_type, extractor_name, extractor_config)
        elif extractor_type == "regex":
            return self._create_regex_extractor(extractor_config)
        elif extractor_type == "spacy":
            return self._create_spacy_extractor(extractor_config)
        else:
            self.logger.warning(f"Unknown extractor type: {extractor_type}")
            return None
    
    def _create_llm_extractor(self, bot_type: str, extractor_name: str, config: Dict[str, Any]) -> Optional[Any]:
        """Create an LLM-based entity extractor."""
        try:
            # Get model from registry
            model_name = config.get("model", "default_nlp_model")
            llm = self.model_registry.get_model(model_name, bot_type)
            
            # Get schema - first from direct config, then from schema loader
            schema = config.get("schema")
            if not schema:
                schema_name = config.get("schema_name")
                if schema_name:
                    schema = schema_loader.get_schema(bot_type, schema_name)
            
            if not schema:
                self.logger.error(f"No schema found for extractor {extractor_name}")
                return None
            
            # Create extraction chain
            extractor = create_extraction_chain(schema, llm)
            self.logger.info(f"Created LLM extractor {extractor_name} for bot {bot_type}")
            return extractor
            
        except Exception as e:
            self.logger.error(f"Failed to create LLM extractor {extractor_name}: {e}")
            return None
    
    def _create_regex_extractor(self, config: Dict[str, Any]) -> Optional[Any]:
        """Create a regex-based entity extractor."""
        # This would create a regex-based extractor
        # For now, return a simple placeholder
        self.logger.info("Regex extractors not yet implemented")
        return None
    
    def _create_spacy_extractor(self, config: Dict[str, Any]) -> Optional[Any]:
        """Create a spaCy-based entity extractor."""
        # This would create a spaCy-based extractor
        # For now, return a simple placeholder
        self.logger.info("spaCy extractors not yet implemented")
        return None
    
    def get_all_extractors(self, bot_type: str) -> Dict[str, Any]:
        """
        Get all extractors defined for a bot type.
        
        Args:
            bot_type: The type of bot (consultancy, sales, support)
            
        Returns:
            Dictionary of extractor names to extractor instances
        """
        config = self.config_inheritance.get_config(bot_type)
        extractor_configs = config.get("nlp.extractors", {})
        
        for extractor_name in extractor_configs:
            if extractor_name not in self.extractors:
                extractor = self.create_extractor(bot_type, extractor_name)
                if extractor:
                    self.extractors[extractor_name] = extractor
        
        return self.extractors

# Global instance
extractor_factory = ExtractorFactory() 