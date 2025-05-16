"""
Specialized NLP processing for the consultancy bot.
Focused on business-focused entities.
"""

import logging
from typing import Dict, List, Any, Optional

from src.config.config_inheritance import ConfigInheritance
from src.langchain_components.nlp.hybrid_processor import HybridProcessor
from src.langchain_components.nlp.priority_processor import priority_processor
from src.langchain_components.nlp.extractor_factory import extractor_factory

class ConsultancyNLPProcessor:
    """
    Specialized NLP processor for the consultancy bot.
    Focuses on business entity extraction and classification.
    """
    
    def __init__(self):
        """Initialize the consultancy NLP processor."""
        self.config_inheritance = ConfigInheritance()
        self.hybrid_processor = HybridProcessor()
        self.logger = logging.getLogger(__name__)
        self.bot_type = "consultancy"
        
        # Business-specific extractors
        self.business_extractors = {}
        
    def initialize(self):
        """Initialize the consultancy NLP processor with specific components."""
        config = self.config_inheritance.get_config(self.bot_type)
        
        # Load business-specific extractors
        business_extractor_names = config.get("nlp.business_extractors", [])
        for extractor_name in business_extractor_names:
            extractor = extractor_factory.create_extractor(self.bot_type, extractor_name)
            if extractor:
                self.business_extractors[extractor_name] = extractor
        
        self.logger.info(f"Initialized ConsultancyNLPProcessor with {len(self.business_extractors)} business extractors")
    
    async def process_message(self, message: str, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process a user message with consultancy-specific NLP.
        
        Args:
            message: The user's message
            session_id: The session ID
            user_id: The user ID
            
        Returns:
            Dictionary with extracted business entities and metadata
        """
        # First, use the hybrid processor for basic extraction
        base_results = await self.hybrid_processor.process_message(
            message, self.bot_type, session_id, user_id
        )
        
        # Then, apply business-specific extractors
        business_entities = await self._extract_business_entities(message)
        
        # Merge the results
        results = base_results.copy()
        if "entities" not in results:
            results["entities"] = {}
            
        # Add business-specific entities
        for entity_type, entities in business_entities.items():
            results["entities"][entity_type] = entities
        
        # Process entities by priority
        prioritized_entities = priority_processor.process_entities(
            self.bot_type, results["entities"]
        )
        results["prioritized_entities"] = prioritized_entities
        
        # Get action triggers
        action_triggers = priority_processor.get_action_triggers(
            self.bot_type, prioritized_entities
        )
        results["action_triggers"] = action_triggers
        
        # Add business context classification
        results["business_context"] = await self._classify_business_context(message)
        
        return results
    
    async def _extract_business_entities(self, message: str) -> Dict[str, List[Any]]:
        """
        Extract business-specific entities from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary of business entity types to extracted entities
        """
        entities = {}
        
        # Apply each business extractor
        for extractor_name, extractor in self.business_extractors.items():
            try:
                extraction_result = await extractor.arun(message)
                if extraction_result:
                    entities[extractor_name] = extraction_result
            except Exception as e:
                self.logger.error(f"Error in business extractor {extractor_name}: {e}")
        
        return entities
    
    async def _classify_business_context(self, message: str) -> Dict[str, Any]:
        """
        Classify the business context of the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary with business context classification
        """
        # Get specific classifier from config
        config = self.config_inheritance.get_config(self.bot_type)
        classifier_name = config.get("nlp.business_context_classifier", "business_context")
        
        # Get the classifier
        classifier = extractor_factory.create_extractor(self.bot_type, classifier_name)
        
        if not classifier:
            return {"domain": "general", "confidence": 0.0}
        
        try:
            classification = await classifier.arun(message)
            return classification
        except Exception as e:
            self.logger.error(f"Error in business context classification: {e}")
            return {"domain": "general", "confidence": 0.0}

# Global instance
consultancy_nlp = ConsultancyNLPProcessor() 