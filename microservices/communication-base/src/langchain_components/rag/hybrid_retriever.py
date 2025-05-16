"""
Hybrid Retriever that combines multiple RAG methods.

This module provides a hybrid approach to retrieval, combining:
1. Vector store-based semantic search
2. User details from the User Details microservice
3. Structured database queries
"""

from langchain.retrievers import MultiQueryRetriever
from langchain.retrievers.merger_retriever import MergerRetriever
from langchain.schema.retriever import BaseRetriever
from langchain.schema.document import Document
import structlog
from typing import List, Dict, Any, Optional, Union, Tuple
from src.config.config_integration import ConfigIntegration
from src.langchain_components.rag.vector_store_rag import VectorStoreRAG
from src.langchain_components.rag.user_details_rag import UserDetailsRAG
from src.langchain_components.rag.database_rag import DatabaseRAG
from src.langchain_components.rag.topic_mapper import TopicMapper

# Setup structured logging
logger = structlog.get_logger(__name__)

class HybridRetriever:
    """
    Hybrid retriever that combines multiple retrieval methods.
    
    Features:
    - Combines vector store, user details, and database retrievers
    - Configurable weights for each retriever type
    - Bot-specific retriever configurations
    - Deduplication and reranking of results
    """
    
    def __init__(self):
        """Initialize the hybrid retriever."""
        self.config_integration = ConfigIntegration()
        self.vector_rag = VectorStoreRAG()
        self.user_details_rag = UserDetailsRAG()
        self.database_rag = DatabaseRAG()
        self.topic_mapper = TopicMapper()
        logger.info("HybridRetriever initialized")
    
    def get_retriever(self, bot_type: str, session_id: str, user_id: Optional[str] = None) -> BaseRetriever:
        """
        Get a combined retriever for a specific bot type and session.
        
        Args:
            bot_type: Type of bot (consultancy, sales, support)
            session_id: Current session ID
            user_id: Optional user ID for personalization
            
        Returns:
            Combined LangChain retriever
        """
        logger.info(f"Creating hybrid retriever for {bot_type}", session_id=session_id)
        config = self.config_integration.get_config(bot_type)
        retrievers = []
        retriever_weights = {}
        
        # Get vector store retriever if enabled
        if config.get("rag.vector_store.enabled", True):
            vector_retriever = self._get_vector_retriever(bot_type, session_id)
            if vector_retriever:
                retrievers.append(vector_retriever)
                retriever_weights[vector_retriever] = config.get("rag.vector_store.weight", 1.0)
        
        # Get user details retriever if enabled and user_id is provided
        if config.get("rag.user_details.enabled", True) and user_id:
            user_details_retriever = self._get_user_details_retriever(bot_type, user_id)
            if user_details_retriever:
                retrievers.append(user_details_retriever)
                retriever_weights[user_details_retriever] = config.get("rag.user_details.weight", 1.0)
        
        # Get database retriever if enabled
        if config.get("rag.database.enabled", True):
            database_retriever = self._get_database_retriever(bot_type, session_id)
            if database_retriever:
                retrievers.append(database_retriever)
                retriever_weights[database_retriever] = config.get("rag.database.weight", 0.7)
        
        # If we have multiple retrievers, combine them
        if len(retrievers) > 1:
            # Use a merger retriever to combine results
            merger_retriever = MergerRetriever(
                retrievers=retrievers,
                weights=list(retriever_weights.values()) if retriever_weights else None,
                verbose=True
            )
            return merger_retriever
        elif retrievers:
            # Just return the single retriever
            return retrievers[0]
        else:
            # Create an empty retriever as fallback
            logger.warning(f"No retrievers created for {bot_type}, using empty retriever")
            return self._get_empty_retriever()
    
    def _get_vector_retriever(self, bot_type: str, session_id: str) -> Optional[BaseRetriever]:
        """Get vector store retriever for this bot type."""
        try:
            config = self.config_integration.get_config(bot_type)
            
            # Get collections based on bot type
            collections = []
            if bot_type == "consultancy":
                collections = config.get("rag.vector_store.collections", 
                                        ["business_frameworks", "legal_documents", "expert_insights"])
            elif bot_type == "sales":
                collections = config.get("rag.vector_store.collections", 
                                        ["product_catalog", "customer_reviews", "sales_techniques"])
            elif bot_type == "support":
                collections = config.get("rag.vector_store.collections", 
                                        ["troubleshooting_guides", "kb_articles", "faqs"])
            
            # Create the retriever
            k = config.get("rag.vector_store.k", 4)
            score_threshold = config.get("rag.vector_store.score_threshold", 0.7)
            
            retriever = self.vector_rag.get_retriever(
                collections=collections,
                k=k,
                score_threshold=score_threshold
            )
            
            # Enhance with multi-query if enabled
            if config.get("rag.vector_store.multi_query", False):
                from langchain.llms import HuggingFacePipeline
                from src.models.llm.model_registry import ModelRegistry
                
                llm_manager = ModelRegistry().get_manager(bot_type)
                if llm_manager:
                    llm = llm_manager.create_langchain_wrapper("default")
                    retriever = MultiQueryRetriever.from_llm(
                        retriever=retriever,
                        llm=llm
                    )
            
            return retriever
        except Exception as e:
            logger.error(f"Error creating vector retriever for {bot_type}", error=str(e))
            return None
    
    def _get_user_details_retriever(self, bot_type: str, user_id: str) -> Optional[BaseRetriever]:
        """Get user details retriever for this user."""
        try:
            config = self.config_integration.get_config(bot_type)
            
            # Get relevant topics based on bot type
            topics = []
            if bot_type == "consultancy":
                topics = config.get("rag.user_details.topics", 
                                   ["business_context", "pain_points", "previous_consultations"])
            elif bot_type == "sales":
                topics = config.get("rag.user_details.topics", 
                                   ["preferences", "purchase_history", "campaign_interactions"])
            elif bot_type == "support":
                topics = config.get("rag.user_details.topics", 
                                   ["technical_history", "previous_issues", "product_usage"])
            
            # Map general topics to specific User Details API topics
            mapped_topics = self.topic_mapper.map_topics(topics, bot_type)
            
            # Create the retriever
            retriever = self.user_details_rag.get_retriever(
                user_id=user_id,
                topics=mapped_topics
            )
            
            return retriever
        except Exception as e:
            logger.error(f"Error creating user details retriever for {bot_type}", error=str(e))
            return None
    
    def _get_database_retriever(self, bot_type: str, session_id: str) -> Optional[BaseRetriever]:
        """Get database retriever for this bot type."""
        try:
            config = self.config_integration.get_config(bot_type)
            
            # Get database sources based on bot type
            sources = []
            if bot_type == "consultancy":
                sources = config.get("rag.database.sources", 
                                    ["business_data", "legal_references", "frameworks"])
            elif bot_type == "sales":
                sources = config.get("rag.database.sources", 
                                    ["products", "inventory", "pricing"])
            elif bot_type == "support":
                sources = config.get("rag.database.sources", 
                                    ["kb_articles", "error_codes", "solutions"])
            
            # Create the retriever
            retriever = self.database_rag.get_retriever(
                sources=sources,
                use_cache=config.get("rag.database.use_cache", True)
            )
            
            return retriever
        except Exception as e:
            logger.error(f"Error creating database retriever for {bot_type}", error=str(e))
            return None
    
    def _get_empty_retriever(self) -> BaseRetriever:
        """Get an empty retriever as fallback."""
        class EmptyRetriever(BaseRetriever):
            def _get_relevant_documents(self, query: str) -> List[Document]:
                return []
                
        return EmptyRetriever() 