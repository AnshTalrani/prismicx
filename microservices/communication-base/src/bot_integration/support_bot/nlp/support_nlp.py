"""
Specialized NLP processing for the support bot.
Focused on issue classification, urgency detection, and technical terminology recognition.
"""

import logging
from typing import Dict, List, Any, Optional

from src.config.config_inheritance import ConfigInheritance
from src.langchain_components.nlp.hybrid_processor import HybridProcessor
from src.langchain_components.nlp.priority_processor import priority_processor
from src.langchain_components.nlp.extractor_factory import extractor_factory

class SupportNLPProcessor:
    """
    Specialized NLP processor for the support bot.
    Focuses on identifying issues, their urgency, and technical details.
    """
    
    def __init__(self):
        """Initialize the support NLP processor."""
        self.config_inheritance = ConfigInheritance()
        self.hybrid_processor = HybridProcessor()
        self.logger = logging.getLogger(__name__)
        self.bot_type = "support"
        
        # Support-specific extractors
        self.issue_extractors = {}
        self.urgency_detector = None
        self.technical_extractors = {}
    
    def initialize(self):
        """Initialize the support NLP processor with specific components."""
        config = self.config_inheritance.get_config(self.bot_type)
        
        # Load issue extractors
        issue_extractor_names = config.get("nlp.issue_extractors", [])
        for extractor_name in issue_extractor_names:
            extractor = extractor_factory.create_extractor(self.bot_type, extractor_name)
            if extractor:
                self.issue_extractors[extractor_name] = extractor
        
        # Load urgency detector
        urgency_detector_name = config.get("nlp.urgency_detector", "urgency")
        self.urgency_detector = extractor_factory.create_extractor(self.bot_type, urgency_detector_name)
        
        # Load technical extractors
        technical_extractor_names = config.get("nlp.technical_extractors", [])
        for extractor_name in technical_extractor_names:
            extractor = extractor_factory.create_extractor(self.bot_type, extractor_name)
            if extractor:
                self.technical_extractors[extractor_name] = extractor
        
        self.logger.info(
            f"Initialized SupportNLPProcessor with {len(self.issue_extractors)} issue extractors "
            f"and {len(self.technical_extractors)} technical extractors"
        )
    
    async def process_message(self, message: str, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process a user message with support-specific NLP.
        
        Args:
            message: The user's message
            session_id: The session ID
            user_id: The user ID
            
        Returns:
            Dictionary with extracted support entities and metadata
        """
        # First, use the hybrid processor for basic extraction
        base_results = await self.hybrid_processor.process_message(
            message, self.bot_type, session_id, user_id
        )
        
        # Initialize if not already done
        if not self.issue_extractors:
            self.initialize()
        
        # Extract issue-specific entities
        issue_entities = await self._extract_issue_entities(message)
        
        # Extract technical entities
        technical_entities = await self._extract_technical_entities(message)
        
        # Detect urgency
        urgency = await self._detect_urgency(message)
        
        # Merge the results
        results = base_results.copy()
        if "entities" not in results:
            results["entities"] = {}
            
        # Add issue-specific entities
        for entity_type, entities in issue_entities.items():
            results["entities"][entity_type] = entities
            
        # Add technical entities
        for entity_type, entities in technical_entities.items():
            results["entities"][entity_type] = entities
        
        # Add urgency information
        results["urgency"] = urgency
        
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
        
        # Add issue classification
        results["issue_classification"] = await self._classify_issue(message)
        
        return results
    
    async def _extract_issue_entities(self, message: str) -> Dict[str, List[Any]]:
        """
        Extract issue-specific entities from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary of issue entity types to extracted entities
        """
        entities = {}
        
        # Apply each issue extractor
        for extractor_name, extractor in self.issue_extractors.items():
            try:
                extraction_result = await extractor.arun(message)
                if extraction_result:
                    entities[extractor_name] = extraction_result
            except Exception as e:
                self.logger.error(f"Error in issue extractor {extractor_name}: {e}")
        
        return entities
    
    async def _extract_technical_entities(self, message: str) -> Dict[str, List[Any]]:
        """
        Extract technical entities from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary of technical entity types to extracted entities
        """
        entities = {}
        
        # Apply each technical extractor
        for extractor_name, extractor in self.technical_extractors.items():
            try:
                extraction_result = await extractor.arun(message)
                if extraction_result:
                    entities[extractor_name] = extraction_result
            except Exception as e:
                self.logger.error(f"Error in technical extractor {extractor_name}: {e}")
        
        return entities
    
    async def _detect_urgency(self, message: str) -> Dict[str, Any]:
        """
        Detect the urgency level of the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary with urgency level and confidence
        """
        if not self.urgency_detector:
            return {"level": "medium", "confidence": 0.0}
        
        try:
            urgency_result = await self.urgency_detector.arun(message)
            return urgency_result
        except Exception as e:
            self.logger.error(f"Error in urgency detection: {e}")
            return {"level": "medium", "confidence": 0.0}
    
    async def _classify_issue(self, message: str) -> Dict[str, Any]:
        """
        Classify the support issue in the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary with issue classification and metadata
        """
        # Get specific classifier from config
        config = self.config_inheritance.get_config(self.bot_type)
        classifier_name = config.get("nlp.issue_classifier", "issue_type")
        
        # Get the classifier
        classifier = extractor_factory.create_extractor(self.bot_type, classifier_name)
        
        if not classifier:
            return {"type": "general", "tier": 3, "confidence": 0.0}
        
        try:
            classification = await classifier.arun(message)
            
            # Get tier information from config
            issue_type = classification.get("type", "general")
            tier = config.get(f"support.issue_types.{issue_type}.tier", 3)
            
            # Add tier to classification
            classification["tier"] = tier
            
            # Get timeout from tier
            timeout = config.get(f"support.tiers.{tier}.timeout", 1800)  # Default 30 minutes
            classification["timeout"] = timeout
            
            return classification
        except Exception as e:
            self.logger.error(f"Error in issue classification: {e}")
            return {"type": "general", "tier": 3, "confidence": 0.0}

# Global instance
support_nlp = SupportNLPProcessor() 