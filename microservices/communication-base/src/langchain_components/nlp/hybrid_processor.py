"""
Hybrid NLP processor for combining LangChain and custom NLP components.

This module provides a central coordinator for NLP processing that integrates
LangChain components with custom extensions for enhanced capabilities.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Set

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

class HybridNLPProcessor:
    """
    Hybrid NLP processor that combines LangChain with custom components.
    
    This class serves as the central coordinator for NLP processing tasks,
    leveraging both LangChain's capabilities and custom extensions to provide
    enhanced NLP functionality for different bot types.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm_manager: Any = None,
        entity_store: Any = None,
        chain_initializer: Any = None,
        schema_loader: Any = None,
        extraction_registry: Any = None
    ):
        """
        Initialize hybrid NLP processor.
        
        Args:
            config_integration: Integration with the config system
            llm_manager: LLM manager for accessing language models
            entity_store: Storage for extracted entities
            chain_initializer: Initializer for extraction chains
            schema_loader: Loader for NLP extraction schemas
            extraction_registry: Registry for extraction configurations
        """
        self.config_integration = config_integration
        self.llm_manager = llm_manager
        self.entity_store = entity_store
        self.chain_initializer = chain_initializer
        self.schema_loader = schema_loader
        self.extraction_registry = extraction_registry
        self.logger = logging.getLogger(__name__)
        
        # Cache for extraction chains
        self.extraction_chains: Dict[str, Any] = {}
        
        # Custom processors for bot types
        self.custom_processors: Dict[str, Any] = {}
    
    def register_custom_processor(self, bot_type: str, processor: Any) -> None:
        """
        Register a custom NLP processor for a specific bot type.
        
        Args:
            bot_type: Type of bot
            processor: Custom NLP processor instance
        """
        self.custom_processors[bot_type] = processor
        self.logger.info(f"Registered custom NLP processor for bot type: {bot_type}")
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        bot_type: str,
        user_id: str,
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a message with hybrid NLP approach.
        
        Args:
            message: User message to process
            session_id: Session identifier
            bot_type: Type of bot
            user_id: User identifier
            processing_options: Additional processing options
            
        Returns:
            Dictionary with NLP processing results
        """
        # Initialize result container
        result = {
            "original_message": message,
            "entities": [],
            "intents": [],
            "actions": [],
            "sentiment": None,
            "metadata": {}
        }
        
        # Get processing config for this bot type
        processing_config = self._get_processing_config(bot_type)
        
        # Determine processing steps based on config
        extraction_types = processing_config.get("extraction_types", ["entities", "intents", "sentiment"])
        
        try:
            # Apply bot-specific custom processor if available
            if bot_type in self.custom_processors:
                custom_result = await self.custom_processors[bot_type].process(
                    message=message,
                    session_id=session_id,
                    user_id=user_id,
                    options=processing_options
                )
                # Merge custom results with standard results
                self._merge_results(result, custom_result)
            
            # Apply LangChain-based extractions
            if "entities" in extraction_types:
                entities = await self._extract_entities(message, bot_type, session_id)
                result["entities"].extend(entities)
            
            if "intents" in extraction_types:
                intents = await self._extract_intents(message, bot_type)
                result["intents"].extend(intents)
            
            if "sentiment" in extraction_types:
                sentiment = await self._analyze_sentiment(message, bot_type)
                result["sentiment"] = sentiment
            
            # Store extracted entities if entity store is available
            if self.entity_store and result["entities"]:
                await self._store_entities(result["entities"], session_id, user_id, bot_type)
            
            # Determine actions based on extracted information
            if "actions" in extraction_types:
                actions = await self._determine_actions(result, bot_type, session_id, user_id)
                result["actions"].extend(actions)
            
            # Apply additional metadata
            result["metadata"] = {
                "processing_time": 0,  # Replace with actual processing time
                "confidence": self._calculate_confidence(result),
                "bot_type": bot_type,
                "session_id": session_id
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in NLP processing: {e}", exc_info=True)
            # Return partial result with error information
            result["metadata"]["error"] = str(e)
            result["metadata"]["success"] = False
            return result
    
    async def _extract_entities(
        self,
        message: str,
        bot_type: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract entities using LangChain and custom extractors.
        
        Args:
            message: User message
            bot_type: Type of bot
            session_id: Session identifier
            
        Returns:
            List of extracted entities
        """
        # Get extraction chain for this bot type
        extraction_chain = await self._get_extraction_chain(bot_type)
        
        if not extraction_chain:
            self.logger.warning(f"No extraction chain available for bot type: {bot_type}")
            return []
        
        try:
            # Run extraction through LangChain
            extraction_result = await extraction_chain.arun(
                input=message,
                session_id=session_id,
                bot_type=bot_type
            )
            
            # Parse results
            if isinstance(extraction_result, dict) and "entities" in extraction_result:
                return extraction_result["entities"]
            elif isinstance(extraction_result, list):
                return extraction_result
            else:
                self.logger.warning(f"Unexpected entity extraction result format: {type(extraction_result)}")
                return []
                
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}", exc_info=True)
            return []
    
    async def _extract_intents(
        self,
        message: str,
        bot_type: str
    ) -> List[Dict[str, Any]]:
        """
        Extract intents using LangChain and custom classifiers.
        
        Args:
            message: User message
            bot_type: Type of bot
            
        Returns:
            List of extracted intents with confidence scores
        """
        # Get bot-specific intent configurations
        intent_config = self._get_intent_config(bot_type)
        
        if not intent_config or not intent_config.get("enabled", True):
            return []
        
        try:
            # Get appropriate LLM for intent classification
            llm = self.llm_manager.get_model(bot_type, model_type="classification")
            
            # Get available intents from config
            available_intents = intent_config.get("intents", [])
            
            if not available_intents:
                return []
            
            # Create prompt for intent classification
            intent_prompt = ChatPromptTemplate.from_template(
                "Classify the following message into one of these intents: {intents}. "
                "Return the intent name and confidence score (0-1) in JSON format.\n\n"
                "Message: {input}"
            )
            
            # Create intent classification chain
            intent_chain = LLMChain(
                llm=llm,
                prompt=intent_prompt,
                output_key="intent_classification"
            )
            
            # Run intent classification
            intent_result = await intent_chain.arun(
                input=message,
                intents=", ".join(available_intents)
            )
            
            # Parse result (simple parsing, could be enhanced with a proper output parser)
            # Expecting format like: {"intent": "intent_name", "confidence": 0.95}
            import json
            try:
                parsed_intent = json.loads(intent_result)
                if isinstance(parsed_intent, dict) and "intent" in parsed_intent:
                    return [{
                        "name": parsed_intent["intent"],
                        "confidence": parsed_intent.get("confidence", 0.7),
                        "metadata": {}
                    }]
                else:
                    return []
            except json.JSONDecodeError:
                # Fallback parsing for non-JSON output
                for intent in available_intents:
                    if intent.lower() in intent_result.lower():
                        return [{
                            "name": intent,
                            "confidence": 0.7,  # Default confidence when parsing fails
                            "metadata": {"parsing_method": "fallback"}
                        }]
                return []
                
        except Exception as e:
            self.logger.error(f"Intent extraction failed: {e}", exc_info=True)
            return []
    
    async def _analyze_sentiment(
        self,
        message: str,
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Analyze sentiment using LangChain.
        
        Args:
            message: User message
            bot_type: Type of bot
            
        Returns:
            Sentiment analysis result
        """
        # Get bot-specific sentiment configurations
        sentiment_config = self._get_sentiment_config(bot_type)
        
        if not sentiment_config or not sentiment_config.get("enabled", True):
            return {"sentiment": "neutral", "score": 0.5}
        
        try:
            # Get appropriate LLM for sentiment analysis
            llm = self.llm_manager.get_model(bot_type, model_type="classification")
            
            # Create prompt for sentiment analysis
            sentiment_prompt = ChatPromptTemplate.from_template(
                "Analyze the sentiment of the following message and classify it as positive, negative, or neutral. "
                "Also provide a score from 0 (most negative) to 1 (most positive). "
                "Return the result in JSON format with 'sentiment' and 'score' fields.\n\n"
                "Message: {input}"
            )
            
            # Create sentiment analysis chain
            sentiment_chain = LLMChain(
                llm=llm,
                prompt=sentiment_prompt,
                output_key="sentiment_analysis"
            )
            
            # Run sentiment analysis
            sentiment_result = await sentiment_chain.arun(input=message)
            
            # Parse result (simple parsing, could be enhanced with a proper output parser)
            import json
            try:
                parsed_sentiment = json.loads(sentiment_result)
                if isinstance(parsed_sentiment, dict) and "sentiment" in parsed_sentiment:
                    return {
                        "sentiment": parsed_sentiment["sentiment"],
                        "score": parsed_sentiment.get("score", 0.5),
                        "metadata": {}
                    }
                else:
                    return {"sentiment": "neutral", "score": 0.5}
            except json.JSONDecodeError:
                # Fallback parsing for non-JSON output
                sentiment = "neutral"
                score = 0.5
                
                if "positive" in sentiment_result.lower():
                    sentiment = "positive"
                    score = 0.8
                elif "negative" in sentiment_result.lower():
                    sentiment = "negative"
                    score = 0.2
                
                return {
                    "sentiment": sentiment,
                    "score": score,
                    "metadata": {"parsing_method": "fallback"}
                }
                
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            return {"sentiment": "neutral", "score": 0.5}
    
    async def _determine_actions(
        self,
        nlp_result: Dict[str, Any],
        bot_type: str,
        session_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Determine actions based on NLP analysis.
        
        Args:
            nlp_result: Results from NLP processing
            bot_type: Type of bot
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            List of suggested actions
        """
        # Get action configuration for this bot type
        action_config = self._get_action_config(bot_type)
        
        if not action_config:
            return []
        
        actions = []
        
        # Process intent-based actions
        for intent in nlp_result.get("intents", []):
            intent_name = intent.get("name")
            if not intent_name:
                continue
                
            intent_actions = action_config.get("intent_actions", {}).get(intent_name, [])
            for action in intent_actions:
                actions.append({
                    "type": action.get("type", "unknown"),
                    "name": action.get("name", "unknown_action"),
                    "params": action.get("params", {}),
                    "priority": action.get("priority", 5),
                    "source": "intent",
                    "source_name": intent_name
                })
        
        # Process entity-based actions
        for entity in nlp_result.get("entities", []):
            entity_type = entity.get("type")
            if not entity_type:
                continue
                
            entity_actions = action_config.get("entity_actions", {}).get(entity_type, [])
            for action in entity_actions:
                actions.append({
                    "type": action.get("type", "unknown"),
                    "name": action.get("name", "unknown_action"),
                    "params": action.get("params", {}),
                    "priority": action.get("priority", 5),
                    "source": "entity",
                    "source_name": entity_type,
                    "entity_value": entity.get("value")
                })
        
        # Process sentiment-based actions
        sentiment = nlp_result.get("sentiment", {}).get("sentiment")
        if sentiment:
            sentiment_actions = action_config.get("sentiment_actions", {}).get(sentiment, [])
            for action in sentiment_actions:
                actions.append({
                    "type": action.get("type", "unknown"),
                    "name": action.get("name", "unknown_action"),
                    "params": action.get("params", {}),
                    "priority": action.get("priority", 5),
                    "source": "sentiment",
                    "source_name": sentiment
                })
        
        # Sort actions by priority (lower value = higher priority)
        actions.sort(key=lambda x: x.get("priority", 5))
        
        return actions
    
    async def _store_entities(
        self,
        entities: List[Dict[str, Any]],
        session_id: str,
        user_id: str,
        bot_type: str
    ) -> None:
        """
        Store extracted entities in the entity store.
        
        Args:
            entities: List of extracted entities
            session_id: Session identifier
            user_id: User identifier
            bot_type: Type of bot
        """
        if not self.entity_store:
            return
        
        try:
            await self.entity_store.store_entities(
                entities=entities,
                session_id=session_id,
                user_id=user_id,
                bot_type=bot_type
            )
        except Exception as e:
            self.logger.error(f"Failed to store entities: {e}", exc_info=True)
    
    async def _get_extraction_chain(self, bot_type: str) -> Any:
        """
        Get or create extraction chain for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            LangChain extraction chain
        """
        # Check if chain already exists in cache
        if bot_type in self.extraction_chains:
            return self.extraction_chains[bot_type]
        
        # Create new chain using chain initializer
        if self.chain_initializer:
            try:
                # Get extraction schema from registry or schema loader
                extraction_schema = self._get_extraction_schema(bot_type)
                
                # Initialize chain with schema
                extraction_chain = await self.chain_initializer.initialize_extraction_chain(
                    bot_type=bot_type,
                    schema=extraction_schema
                )
                
                # Cache the chain
                self.extraction_chains[bot_type] = extraction_chain
                
                return extraction_chain
                
            except Exception as e:
                self.logger.error(f"Failed to create extraction chain: {e}", exc_info=True)
                return None
        
        return None
    
    def _get_extraction_schema(self, bot_type: str) -> Dict[str, Any]:
        """
        Get extraction schema for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Extraction schema configuration
        """
        # Try to get schema from extraction registry
        if self.extraction_registry:
            schema = self.extraction_registry.get_schema(bot_type)
            if schema:
                return schema
        
        # Try to get schema from schema loader
        if self.schema_loader:
            schema = self.schema_loader.load_schema(bot_type)
            if schema:
                return schema
        
        # Fall back to config-based schema
        if self.config_integration:
            config = self.config_integration.get_config(bot_type)
            return config.get("nlp.extraction_schema", {})
        
        # Return empty schema as last resort
        return {}
    
    def _get_processing_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get NLP processing configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Processing configuration
        """
        # Default processing config
        default_config = {
            "extraction_types": ["entities", "intents", "sentiment"],
            "store_entities": True,
            "determine_actions": True
        }
        
        # Get bot-specific config if available
        if self.config_integration:
            config = self.config_integration.get_config(bot_type)
            processing_config = config.get("nlp.processing", {})
            
            # Merge with defaults
            merged_config = {**default_config, **processing_config}
            return merged_config
        
        return default_config
    
    def _get_intent_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get intent configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Intent configuration
        """
        if self.config_integration:
            config = self.config_integration.get_config(bot_type)
            return config.get("nlp.intents", {})
        
        return {}
    
    def _get_sentiment_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get sentiment configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Sentiment configuration
        """
        if self.config_integration:
            config = self.config_integration.get_config(bot_type)
            return config.get("nlp.sentiment", {})
        
        return {}
    
    def _get_action_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get action configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Action configuration
        """
        if self.config_integration:
            config = self.config_integration.get_config(bot_type)
            return config.get("nlp.actions", {})
        
        return {}
    
    def _merge_results(self, base_result: Dict[str, Any], custom_result: Dict[str, Any]) -> None:
        """
        Merge custom processing results into base results.
        
        Args:
            base_result: Base result dictionary to update
            custom_result: Custom result dictionary to merge in
        """
        # Merge lists
        for key in ["entities", "intents", "actions"]:
            if key in custom_result and isinstance(custom_result[key], list):
                if key not in base_result:
                    base_result[key] = []
                base_result[key].extend(custom_result[key])
        
        # Override sentiment if present
        if "sentiment" in custom_result and custom_result["sentiment"]:
            base_result["sentiment"] = custom_result["sentiment"]
        
        # Merge metadata
        if "metadata" in custom_result and isinstance(custom_result["metadata"], dict):
            if "metadata" not in base_result:
                base_result["metadata"] = {}
            base_result["metadata"].update(custom_result["metadata"])
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate overall processing confidence.
        
        Args:
            result: Processing result
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence_sum = 0.0
        confidence_count = 0
        
        # Average confidence of intents
        for intent in result.get("intents", []):
            if "confidence" in intent:
                confidence_sum += intent["confidence"]
                confidence_count += 1
        
        # Average confidence of entities
        for entity in result.get("entities", []):
            if "confidence" in entity:
                confidence_sum += entity["confidence"]
                confidence_count += 1
        
        # Add sentiment confidence if available
        if result.get("sentiment") and "score" in result["sentiment"]:
            # Convert sentiment score to confidence (distance from neutral 0.5)
            sentiment_confidence = 0.5 + abs(result["sentiment"]["score"] - 0.5)
            confidence_sum += sentiment_confidence
            confidence_count += 1
        
        # Calculate average confidence
        if confidence_count > 0:
            return confidence_sum / confidence_count
        else:
            return 0.7  # Default confidence

# Global instance
hybrid_processor = HybridNLPProcessor() 