"""
Chain initializer for LangChain extraction chain setup.

This module provides functionality to initialize and configure
LangChain extraction chains with appropriate schemas and models.
"""

import logging
from typing import Dict, Any, List, Optional, Union

from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, ResponseSchema, StructuredOutputParser

class ChainInitializer:
    """
    Chain initializer for setting up LangChain extraction chains.
    
    This class handles the initialization and configuration of LangChain
    chains for entity extraction, intent recognition, and other NLP tasks.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm_manager: Any = None,
        template_compiler: Any = None
    ):
        """
        Initialize chain initializer.
        
        Args:
            config_integration: Integration with the config system
            llm_manager: LLM manager for accessing language models
            template_compiler: Template compiler for creating prompt templates
        """
        self.config_integration = config_integration
        self.llm_manager = llm_manager
        self.template_compiler = template_compiler
        self.logger = logging.getLogger(__name__)
        
        # Cache for frequently used chains
        self.chain_cache: Dict[str, Any] = {}
    
    async def initialize_extraction_chain(
        self,
        bot_type: str,
        schema: Dict[str, Any]
    ) -> Any:
        """
        Initialize an entity extraction chain.
        
        Args:
            bot_type: Type of bot
            schema: Extraction schema configuration
            
        Returns:
            Configured LangChain extraction chain
        """
        # Generate cache key
        cache_key = f"extraction_{bot_type}"
        
        # Check cache first
        if cache_key in self.chain_cache:
            return self.chain_cache[cache_key]
        
        try:
            # Get extraction method from schema
            extraction_method = schema.get("method", "llm_structured")
            
            if extraction_method == "llm_structured":
                chain = await self._create_structured_extraction_chain(bot_type, schema)
            elif extraction_method == "llm_json":
                chain = await self._create_json_extraction_chain(bot_type, schema)
            elif extraction_method == "llm_pydantic":
                chain = await self._create_pydantic_extraction_chain(bot_type, schema)
            else:
                self.logger.warning(f"Unsupported extraction method: {extraction_method}")
                chain = await self._create_structured_extraction_chain(bot_type, schema)
            
            # Cache the chain
            self.chain_cache[cache_key] = chain
            
            return chain
            
        except Exception as e:
            self.logger.error(f"Error initializing extraction chain: {e}", exc_info=True)
            # Return a fallback chain
            return await self._create_fallback_extraction_chain(bot_type)
    
    async def initialize_intent_chain(
        self,
        bot_type: str,
        intents: List[str]
    ) -> Any:
        """
        Initialize an intent recognition chain.
        
        Args:
            bot_type: Type of bot
            intents: List of possible intents
            
        Returns:
            Configured LangChain intent recognition chain
        """
        # Generate cache key
        cache_key = f"intent_{bot_type}"
        
        # Check cache first
        if cache_key in self.chain_cache:
            return self.chain_cache[cache_key]
        
        try:
            # Get LLM for classification
            llm = self.llm_manager.get_model(bot_type, model_type="classification")
            
            # Create intent prompt
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
            
            # Cache the chain
            self.chain_cache[cache_key] = intent_chain
            
            return intent_chain
            
        except Exception as e:
            self.logger.error(f"Error initializing intent chain: {e}", exc_info=True)
            # Return a fallback chain
            return await self._create_fallback_intent_chain(bot_type)
    
    async def initialize_sentiment_chain(
        self,
        bot_type: str
    ) -> Any:
        """
        Initialize a sentiment analysis chain.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Configured LangChain sentiment analysis chain
        """
        # Generate cache key
        cache_key = f"sentiment_{bot_type}"
        
        # Check cache first
        if cache_key in self.chain_cache:
            return self.chain_cache[cache_key]
        
        try:
            # Get LLM for classification
            llm = self.llm_manager.get_model(bot_type, model_type="classification")
            
            # Create sentiment prompt
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
            
            # Cache the chain
            self.chain_cache[cache_key] = sentiment_chain
            
            return sentiment_chain
            
        except Exception as e:
            self.logger.error(f"Error initializing sentiment chain: {e}", exc_info=True)
            # Return a fallback chain
            return await self._create_fallback_sentiment_chain(bot_type)
    
    async def _create_structured_extraction_chain(
        self,
        bot_type: str,
        schema: Dict[str, Any]
    ) -> Any:
        """
        Create a structured output extraction chain.
        
        Args:
            bot_type: Type of bot
            schema: Extraction schema configuration
            
        Returns:
            Configured structured extraction chain
        """
        # Get LLM for extraction
        llm = self.llm_manager.get_model(bot_type, model_type="extraction")
        
        # Create response schemas for structured output parser
        response_schemas = []
        
        entity_types = schema.get("entity_types", {})
        
        for entity_type, entity_config in entity_types.items():
            response_schemas.append(
                ResponseSchema(
                    name=entity_type,
                    description=entity_config.get("description", f"Entities of type {entity_type}"),
                    type="dict"
                )
            )
        
        # Create output parser
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()
        
        # Get the prompt template from schema or use default
        prompt_template = schema.get("prompt_template", 
            "Extract entities from the following text. {format_instructions}\n\nText: {input}"
        )
        
        # Create prompt with format instructions
        prompt = ChatPromptTemplate.from_template(
            prompt_template
        )
        
        # Create extraction chain
        extraction_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_parser=output_parser,
            output_key="entities"
        )
        
        return extraction_chain
    
    async def _create_json_extraction_chain(
        self,
        bot_type: str,
        schema: Dict[str, Any]
    ) -> Any:
        """
        Create a JSON output extraction chain.
        
        Args:
            bot_type: Type of bot
            schema: Extraction schema configuration
            
        Returns:
            Configured JSON extraction chain
        """
        # Get LLM for extraction
        llm = self.llm_manager.get_model(bot_type, model_type="extraction")
        
        # Get entity types for format instructions
        entity_types = schema.get("entity_types", {})
        entity_descriptions = {}
        
        for entity_type, entity_config in entity_types.items():
            entity_descriptions[entity_type] = entity_config.get("description", f"Entities of type {entity_type}")
        
        # Create format instructions
        format_instructions = f"""
        Return the extracted entities as a JSON object with the following structure:
        {{
            "entities": [
                {{
                    "type": "entity_type",
                    "value": "entity_value",
                    "confidence": 0.95,
                    "metadata": {{
                        "additional_info": "value"
                    }}
                }},
                ...
            ]
        }}
        
        Entity types to extract:
        {", ".join(entity_descriptions.keys())}
        
        If no entities are found, return an empty array for "entities".
        """
        
        # Get the prompt template from schema or use default
        prompt_template = schema.get("prompt_template", 
            "Extract entities from the following text.\n\n{format_instructions}\n\nText: {input}"
        )
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(
            prompt_template.replace("{format_instructions}", format_instructions)
        )
        
        # Create extraction chain
        extraction_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_key="extraction_result"
        )
        
        return extraction_chain
    
    async def _create_pydantic_extraction_chain(
        self,
        bot_type: str,
        schema: Dict[str, Any]
    ) -> Any:
        """
        Create a Pydantic output extraction chain.
        
        Args:
            bot_type: Type of bot
            schema: Extraction schema configuration
            
        Returns:
            Configured Pydantic extraction chain
        """
        # This would typically use Pydantic models for structured output
        # For simplicity, we'll create a basic implementation similar to JSON extraction
        
        # Get LLM for extraction
        llm = self.llm_manager.get_model(bot_type, model_type="extraction")
        
        # Get entity types for format instructions
        entity_types = schema.get("entity_types", {})
        entity_descriptions = {}
        
        for entity_type, entity_config in entity_types.items():
            entity_descriptions[entity_type] = entity_config.get("description", f"Entities of type {entity_type}")
        
        # Create format instructions
        format_instructions = f"""
        Extract entities from the text and return them in the specified format.
        Entity types to extract:
        {", ".join(entity_descriptions.keys())}
        """
        
        # Get the prompt template from schema or use default
        prompt_template = schema.get("prompt_template", 
            "Extract entities from the following text.\n\n{format_instructions}\n\nText: {input}"
        )
        
        # Create prompt
        prompt = ChatPromptTemplate.from_template(
            prompt_template.replace("{format_instructions}", format_instructions)
        )
        
        # Create extraction chain
        extraction_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_key="extraction_result"
        )
        
        return extraction_chain
    
    async def _create_fallback_extraction_chain(self, bot_type: str) -> Any:
        """
        Create a fallback extraction chain.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Simple fallback chain
        """
        # Get LLM for extraction
        llm = self.llm_manager.get_model(bot_type, model_type="extraction")
        
        # Create a simple prompt
        prompt = ChatPromptTemplate.from_template(
            "Extract entities from the following text. Return a JSON object with an 'entities' array containing objects with 'type', 'value', and 'confidence' fields.\n\nText: {input}"
        )
        
        # Create fallback chain
        fallback_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_key="entities"
        )
        
        return fallback_chain
    
    async def _create_fallback_intent_chain(self, bot_type: str) -> Any:
        """
        Create a fallback intent recognition chain.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Simple fallback chain
        """
        # Get LLM for classification
        llm = self.llm_manager.get_model(bot_type, model_type="classification")
        
        # Create a simple prompt
        prompt = ChatPromptTemplate.from_template(
            "Classify the intent of the following message. Return a JSON object with 'intent' and 'confidence' fields.\n\nMessage: {input}"
        )
        
        # Create fallback chain
        fallback_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_key="intent_classification"
        )
        
        return fallback_chain
    
    async def _create_fallback_sentiment_chain(self, bot_type: str) -> Any:
        """
        Create a fallback sentiment analysis chain.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Simple fallback chain
        """
        # Get LLM for classification
        llm = self.llm_manager.get_model(bot_type, model_type="classification")
        
        # Create a simple prompt
        prompt = ChatPromptTemplate.from_template(
            "Analyze the sentiment of the following message. Return a JSON object with 'sentiment' (positive, negative, or neutral) and 'score' (0-1) fields.\n\nMessage: {input}"
        )
        
        # Create fallback chain
        fallback_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_key="sentiment_analysis"
        )
        
        return fallback_chain
    
    def clear_cache(self) -> None:
        """
        Clear the chain cache.
        """
        self.chain_cache = {}
        self.logger.info("Chain cache cleared")
    
    def invalidate_chain(self, chain_key: str) -> None:
        """
        Invalidate a specific chain in the cache.
        
        Args:
            chain_key: Key of the chain to invalidate
        """
        if chain_key in self.chain_cache:
            del self.chain_cache[chain_key]
            self.logger.info(f"Chain {chain_key} invalidated in cache") 