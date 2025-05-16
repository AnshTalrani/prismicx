"""
Specialized NLP processing for the sales bot.
Focused on purchase signals, product interests, and campaign-specific processing.
"""

import logging
from typing import Dict, List, Any, Optional

from src.config.config_inheritance import ConfigInheritance
from src.langchain_components.nlp.hybrid_processor import HybridProcessor
from src.langchain_components.nlp.priority_processor import priority_processor
from src.langchain_components.nlp.extractor_factory import extractor_factory

class SalesNLPProcessor:
    """
    Specialized NLP processor for the sales bot.
    Focuses on identifying purchase signals and product interests.
    """
    
    def __init__(self):
        """Initialize the sales NLP processor."""
        self.config_inheritance = ConfigInheritance()
        self.hybrid_processor = HybridProcessor()
        self.logger = logging.getLogger(__name__)
        self.bot_type = "sales"
        
        # Sales-specific extractors
        self.sales_extractors = {}
        self.campaign_extractors = {}
    
    def initialize(self, campaign_id: Optional[str] = None):
        """
        Initialize the sales NLP processor with specific components.
        
        Args:
            campaign_id: Optional campaign ID to load campaign-specific extractors
        """
        config = self.config_inheritance.get_config(self.bot_type)
        
        # Load sales-specific extractors
        sales_extractor_names = config.get("nlp.sales_extractors", [])
        for extractor_name in sales_extractor_names:
            extractor = extractor_factory.create_extractor(self.bot_type, extractor_name)
            if extractor:
                self.sales_extractors[extractor_name] = extractor
        
        # Load campaign-specific extractors if campaign_id is provided
        if campaign_id:
            campaign_extractor_names = config.get(f"campaigns.{campaign_id}.extractors", [])
            for extractor_name in campaign_extractor_names:
                extractor = extractor_factory.create_extractor(self.bot_type, extractor_name)
                if extractor:
                    self.campaign_extractors[extractor_name] = extractor
        
        self.logger.info(
            f"Initialized SalesNLPProcessor with {len(self.sales_extractors)} sales extractors "
            f"and {len(self.campaign_extractors)} campaign extractors"
        )
    
    async def process_message(
        self, message: str, session_id: str, user_id: str, campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with sales-specific NLP.
        
        Args:
            message: The user's message
            session_id: The session ID
            user_id: The user ID
            campaign_id: Optional campaign ID for campaign-specific processing
            
        Returns:
            Dictionary with extracted sales entities and metadata
        """
        # First, use the hybrid processor for basic extraction
        base_results = await self.hybrid_processor.process_message(
            message, self.bot_type, session_id, user_id
        )
        
        # Initialize if not already done
        if not self.sales_extractors:
            self.initialize(campaign_id)
        
        # Apply sales-specific extractors
        sales_entities = await self._extract_sales_entities(message)
        
        # Apply campaign-specific extractors if campaign_id is provided
        campaign_entities = {}
        if campaign_id:
            campaign_entities = await self._extract_campaign_entities(message, campaign_id)
        
        # Merge the results
        results = base_results.copy()
        if "entities" not in results:
            results["entities"] = {}
            
        # Add sales-specific entities
        for entity_type, entities in sales_entities.items():
            results["entities"][entity_type] = entities
            
        # Add campaign-specific entities
        for entity_type, entities in campaign_entities.items():
            results["entities"][f"campaign_{entity_type}"] = entities
        
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
        
        # Add purchase stage classification
        results["purchase_stage"] = await self._classify_purchase_stage(message, campaign_id)
        
        # Add objection detection
        results["objections"] = await self._detect_objections(message)
        
        return results
    
    async def _extract_sales_entities(self, message: str) -> Dict[str, List[Any]]:
        """
        Extract sales-specific entities from the message.
        
        Args:
            message: The user's message
            
        Returns:
            Dictionary of sales entity types to extracted entities
        """
        entities = {}
        
        # Apply each sales extractor
        for extractor_name, extractor in self.sales_extractors.items():
            try:
                extraction_result = await extractor.arun(message)
                if extraction_result:
                    entities[extractor_name] = extraction_result
            except Exception as e:
                self.logger.error(f"Error in sales extractor {extractor_name}: {e}")
        
        return entities
    
    async def _extract_campaign_entities(self, message: str, campaign_id: str) -> Dict[str, List[Any]]:
        """
        Extract campaign-specific entities from the message.
        
        Args:
            message: The user's message
            campaign_id: The campaign ID
            
        Returns:
            Dictionary of campaign entity types to extracted entities
        """
        entities = {}
        
        # Apply each campaign extractor
        for extractor_name, extractor in self.campaign_extractors.items():
            try:
                extraction_result = await extractor.arun(message)
                if extraction_result:
                    entities[extractor_name] = extraction_result
            except Exception as e:
                self.logger.error(f"Error in campaign extractor {extractor_name}: {e}")
        
        return entities
    
    async def _classify_purchase_stage(self, message: str, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify the purchase stage of the message.
        
        Args:
            message: The user's message
            campaign_id: Optional campaign ID
            
        Returns:
            Dictionary with purchase stage classification
        """
        # Get specific classifier from config
        config = self.config_inheritance.get_config(self.bot_type)
        classifier_name = config.get("nlp.purchase_stage_classifier", "purchase_stage")
        
        # If campaign-specific classifier exists, use it instead
        if campaign_id:
            campaign_classifier = config.get(f"campaigns.{campaign_id}.purchase_stage_classifier")
            if campaign_classifier:
                classifier_name = campaign_classifier
        
        # Get the classifier
        classifier = extractor_factory.create_extractor(self.bot_type, classifier_name)
        
        if not classifier:
            return {"stage": "awareness", "confidence": 0.0}
        
        try:
            classification = await classifier.arun(message)
            return classification
        except Exception as e:
            self.logger.error(f"Error in purchase stage classification: {e}")
            return {"stage": "awareness", "confidence": 0.0}
    
    async def _detect_objections(self, message: str) -> List[Dict[str, Any]]:
        """
        Detect sales objections in the message.
        
        Args:
            message: The user's message
            
        Returns:
            List of detected objections with types and confidence
        """
        # Get specific objection detector from config
        config = self.config_inheritance.get_config(self.bot_type)
        objection_detector_name = config.get("nlp.objection_detector", "objections")
        
        # Get the objection detector
        objection_detector = extractor_factory.create_extractor(self.bot_type, objection_detector_name)
        
        if not objection_detector:
            return []
        
        try:
            objections = await objection_detector.arun(message)
            return objections
        except Exception as e:
            self.logger.error(f"Error in objection detection: {e}")
            return []

# Global instance
sales_nlp = SalesNLPProcessor() 