"""
Query preprocessor for RAG retrieval.

This module provides functionality to analyze query intent and reformulate queries 
for optimal retrieval, and extract key parameters for effective RAG operations.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from langchain.prompts import PromptTemplate
from langchain.llms import BaseLLM
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from src.config.config_inheritance import ConfigInheritance
from src.langchain_components.nlp.hybrid_processor import hybrid_processor

class QueryIntent(BaseModel):
    """
    Model representing query intent analysis results.
    """
    primary_intent: str = Field(..., description="Primary intent of the query")
    secondary_intents: List[str] = Field(default_factory=list, description="Secondary intents of the query")
    question_type: str = Field(..., description="Type of question (informational, procedural, clarification, etc.)")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entities extracted from the query")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters extracted from the query")
    constraints: List[str] = Field(default_factory=list, description="Constraints mentioned in the query")
    keywords: List[str] = Field(default_factory=list, description="Important keywords from the query")

class QueryReformulation(BaseModel):
    """
    Model representing a reformulated query.
    """
    original_query: str = Field(..., description="Original user query")
    reformulated_query: str = Field(..., description="Reformulated query for improved retrieval")
    rag_system: str = Field(..., description="RAG system this reformulation is targeting")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters to apply during retrieval")
    explanation: str = Field(..., description="Explanation of the reformulation")

class QueryPreprocessor:
    """
    Preprocesses queries for RAG systems by analyzing intent and reformulating queries.
    
    This class provides functionality to:
    1. Analyze query intent to determine appropriate RAG systems
    2. Reformulate queries for optimal retrieval from each system
    3. Extract key parameters and constraints from queries
    """
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        """
        Initialize the query preprocessor.
        
        Args:
            llm: Language model for advanced reformulation (optional)
        """
        self.llm = llm
        self.config_inheritance = ConfigInheritance()
        self.logger = logging.getLogger(__name__)
        
        # Initialize output parsers
        self.intent_parser = PydanticOutputParser(pydantic_object=QueryIntent)
        self.reformulation_parser = PydanticOutputParser(pydantic_object=QueryReformulation)
        
        # Initialize prompts
        self._init_prompts()
    
    def _init_prompts(self) -> None:
        """Initialize prompt templates for query processing."""
        self.intent_prompt = PromptTemplate(
            template="""Analyze the following query to identify the user's intent, 
            important entities, parameters, constraints, and keywords.

            Query: {query}

            {format_instructions}
            """,
            input_variables=["query"],
            partial_variables={"format_instructions": self.intent_parser.get_format_instructions()}
        )
        
        self.reformulation_prompt = PromptTemplate(
            template="""Reformulate the following query to optimize retrieval from the specified RAG system.
            Make sure the reformulated query maintains the original meaning but is optimized for retrieval.
            
            Original Query: {query}
            RAG System: {rag_system}
            Query Intent: {intent}
            
            {format_instructions}
            """,
            input_variables=["query", "rag_system", "intent"],
            partial_variables={"format_instructions": self.reformulation_parser.get_format_instructions()}
        )
    
    async def analyze_intent(self, query: str, bot_type: str) -> QueryIntent:
        """
        Analyze the intent of a query.
        
        Args:
            query: User query
            bot_type: Type of bot
            
        Returns:
            Query intent analysis
        """
        try:
            # First, use hybrid processor to extract entities
            nlp_results = await hybrid_processor.process_text(query, bot_type)
            entities = nlp_results.get("entities", [])
            
            # If we have an LLM, use it for more sophisticated intent analysis
            if self.llm:
                intent_prompt = self.intent_prompt.format(query=query)
                intent_raw = self.llm.predict(intent_prompt)
                
                try:
                    intent = self.intent_parser.parse(intent_raw)
                    # Add extracted entities to the intent
                    intent.entities.extend(entities)
                    return intent
                except Exception as e:
                    self.logger.error(f"Failed to parse intent from LLM: {e}")
                    # Fall back to basic intent analysis
            
            # Basic intent analysis if LLM failed or isn't available
            return self._basic_intent_analysis(query, entities)
            
        except Exception as e:
            self.logger.error(f"Error analyzing query intent: {e}")
            # Return a minimal valid intent object
            return QueryIntent(
                primary_intent="unknown",
                question_type="informational",
                entities=entities
            )
    
    def _basic_intent_analysis(self, query: str, entities: List[Dict[str, Any]]) -> QueryIntent:
        """
        Perform basic intent analysis without LLM.
        
        Args:
            query: User query
            entities: Extracted entities
            
        Returns:
            Query intent analysis
        """
        query_lower = query.lower()
        
        # Default intent is informational
        primary_intent = "informational"
        secondary_intents = []
        question_type = "informational"
        
        # Check for procedural intent
        if any(kw in query_lower for kw in ["how to", "how do i", "steps", "process", "procedure"]):
            primary_intent = "procedural"
            question_type = "procedural"
        
        # Check for clarification intent
        elif any(kw in query_lower for kw in ["what does", "what is", "explain", "clarify", "mean"]):
            primary_intent = "clarification"
            question_type = "clarification"
        
        # Check for comparison intent
        elif any(kw in query_lower for kw in ["versus", "vs", "compare", "difference", "better"]):
            primary_intent = "comparison"
            question_type = "comparison"
            
        # Extract parameters
        parameters = {}
        
        # Extract constraints
        constraints = []
        
        # Extract keywords (simple approach)
        stop_words = ["the", "a", "an", "in", "on", "at", "to", "for", "with", "by"]
        words = [w.lower() for w in re.findall(r'\b\w+\b', query_lower) if w.lower() not in stop_words]
        keywords = [w for w in words if len(w) > 3]  # Filter out short words
        
        return QueryIntent(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            question_type=question_type,
            entities=entities,
            parameters=parameters,
            constraints=constraints,
            keywords=keywords
        )
    
    async def reformulate_query(
        self, 
        query: str, 
        rag_system: str, 
        bot_type: str,
        intent: Optional[QueryIntent] = None
    ) -> QueryReformulation:
        """
        Reformulate a query for optimal retrieval from a specific RAG system.
        
        Args:
            query: Original user query
            rag_system: RAG system name ('vector_store', 'database', 'user_details')
            bot_type: Type of bot
            intent: Query intent (optional, will be generated if not provided)
            
        Returns:
            Reformulated query
        """
        try:
            # Get intent if not provided
            if not intent:
                intent = await self.analyze_intent(query, bot_type)
            
            # Get RAG-specific config
            config = self.config_inheritance.get_config(bot_type)
            rag_config = config.get("chain_config", {}).get("retrieval", {})
            
            # If we have an LLM, use it for sophisticated reformulation
            if self.llm:
                reformulation_prompt = self.reformulation_prompt.format(
                    query=query,
                    rag_system=rag_system,
                    intent=intent.json()
                )
                reformulation_raw = self.llm.predict(reformulation_prompt)
                
                try:
                    return self.reformulation_parser.parse(reformulation_raw)
                except Exception as e:
                    self.logger.error(f"Failed to parse reformulation from LLM: {e}")
                    # Fall back to basic reformulation
            
            # Basic reformulation strategies based on RAG system
            return self._basic_reformulation(query, rag_system, bot_type, intent)
            
        except Exception as e:
            self.logger.error(f"Error reformulating query: {e}")
            # Return minimal valid reformulation
            return QueryReformulation(
                original_query=query,
                reformulated_query=query,  # No reformulation
                rag_system=rag_system,
                explanation="Failed to reformulate query due to an error."
            )
    
    def _basic_reformulation(
        self, 
        query: str, 
        rag_system: str, 
        bot_type: str,
        intent: QueryIntent
    ) -> QueryReformulation:
        """
        Apply basic query reformulation strategies based on RAG system.
        
        Args:
            query: Original user query
            rag_system: RAG system name
            bot_type: Type of bot
            intent: Query intent
            
        Returns:
            Reformulated query
        """
        filters = {}
        reformulated = query
        explanation = "Simple pass-through reformulation."
        
        if rag_system == "vector_store":
            # For vector store, expand query with keywords and main intent
            if intent.keywords:
                # Add keywords that aren't already in the query
                additional_keywords = [k for k in intent.keywords[:3] if k.lower() not in query.lower()]
                if additional_keywords:
                    reformulated = f"{query} {' '.join(additional_keywords)}"
                    explanation = "Added relevant keywords to enhance semantic search."
            
            # Add domain restriction for vector search if available
            if bot_type == "consultancy":
                if any(e.get("type") == "BUSINESS" for e in intent.entities):
                    filters["domain"] = "business"
                elif any(e.get("type") == "LEGAL" for e in intent.entities):
                    filters["domain"] = "legal"
                elif any(e.get("type") == "FINANCIAL" for e in intent.entities):
                    filters["domain"] = "finance"
            
        elif rag_system == "database":
            # For database, extract key parameters for structured query
            if intent.entities:
                for entity in intent.entities:
                    if entity.get("type") in ["PRODUCT", "SERVICE", "ISSUE_TYPE"]:
                        filters[entity.get("type").lower()] = entity.get("value")
            
            # Make query more direct for database lookup
            if intent.primary_intent == "procedural":
                reformulated = f"steps for {query}"
                explanation = "Reformulated for procedural database lookup."
            elif intent.primary_intent == "comparison":
                reformulated = f"comparison of {query}"
                explanation = "Reformulated for comparison database lookup."
            
        elif rag_system == "user_details":
            # For user details, focus on user-specific aspects
            if intent.entities:
                # Extract user-related entities
                user_entities = [e for e in intent.entities if e.get("type") in ["PREFERENCE", "HISTORY", "PAIN_POINT"]]
                if user_entities:
                    filters["entity_types"] = [e.get("type") for e in user_entities]
            
            # Modified query based on intent
            if intent.primary_intent == "comparison":
                reformulated = f"personal preferences regarding {query}"
                explanation = "Reformulated to focus on personal preferences for user details lookup."
            
        return QueryReformulation(
            original_query=query,
            reformulated_query=reformulated,
            rag_system=rag_system,
            filters=filters,
            explanation=explanation
        )
    
    async def determine_rag_systems(self, query: str, bot_type: str) -> List[str]:
        """
        Determine which RAG systems to use for a query.
        
        Args:
            query: User query
            bot_type: Type of bot
            
        Returns:
            List of RAG systems to use
        """
        try:
            # Analyze query intent
            intent = await self.analyze_intent(query, bot_type)
            
            # Get config for this bot type
            config = self.config_inheritance.get_config(bot_type)
            rag_config = config.get("chain_config", {}).get("retrieval", {})
            
            # Default to using all systems
            all_systems = ["vector_store", "database", "user_details"]
            
            # Get config-specified systems to use
            default_systems = rag_config.get("rag_systems", all_systems)
            
            # Determine systems based on intent and entity types
            selected_systems = set(default_systems)
            
            # Intent-based selection
            if intent.primary_intent == "procedural":
                # Procedural queries benefit from database lookups
                selected_systems.add("database")
            
            if intent.primary_intent in ["comparison", "clarification"]:
                # These benefit from vector store
                selected_systems.add("vector_store")
            
            # Entity-based selection
            entity_types = [e.get("type") for e in intent.entities]
            
            if any(et in ["PREFERENCE", "HISTORY", "PAIN_POINT"] for et in entity_types):
                # User-specific entities need user details
                selected_systems.add("user_details")
            
            if any(et in ["PRODUCT", "SERVICE", "ISSUE_TYPE"] for et in entity_types):
                # Product/service entities benefit from database
                selected_systems.add("database")
            
            if any(et in ["BUSINESS", "LEGAL", "FINANCIAL", "TECHNICAL"] for et in entity_types):
                # Domain-specific entities benefit from vector store
                selected_systems.add("vector_store")
            
            # Ensure we have at least one system
            if not selected_systems:
                selected_systems = set(default_systems)
            
            # Convert to list and ensure it only contains valid systems
            return [s for s in selected_systems if s in all_systems]
            
        except Exception as e:
            self.logger.error(f"Error determining RAG systems: {e}")
            # Fall back to default systems
            return ["vector_store", "database"]
    
    async def preprocess_query(
        self, 
        query: str, 
        bot_type: str
    ) -> Dict[str, Any]:
        """
        Preprocess a query for RAG retrieval.
        
        This method:
        1. Analyzes query intent
        2. Determines which RAG systems to use
        3. Reformulates the query for each selected system
        
        Args:
            query: User query
            bot_type: Type of bot
            
        Returns:
            Dictionary with preprocessing results
        """
        try:
            # Analyze intent
            intent = await self.analyze_intent(query, bot_type)
            
            # Determine RAG systems
            rag_systems = await self.determine_rag_systems(query, bot_type)
            
            # Reformulate query for each system
            reformulations = {}
            for system in rag_systems:
                reformulation = await self.reformulate_query(query, system, bot_type, intent)
                reformulations[system] = reformulation
            
            return {
                "original_query": query,
                "intent": intent,
                "rag_systems": rag_systems,
                "reformulations": reformulations
            }
            
        except Exception as e:
            self.logger.error(f"Error preprocessing query: {e}")
            # Return minimal valid result
            return {
                "original_query": query,
                "intent": None,
                "rag_systems": ["vector_store"],
                "reformulations": {
                    "vector_store": QueryReformulation(
                        original_query=query,
                        reformulated_query=query,
                        rag_system="vector_store",
                        explanation="Fallback due to preprocessing error."
                    )
                }
            }


# Create singleton instance
query_preprocessor = QueryPreprocessor() 