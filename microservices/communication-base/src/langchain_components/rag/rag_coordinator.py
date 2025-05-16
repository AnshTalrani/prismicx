"""
RAG coordinator for integrating different retrieval systems.

This module provides a central coordinator that orchestrates different RAG
components (user details, vector stores, databases) and integrates them with LangChain.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple

from langchain.schema import Document
from langchain.vectorstores import VectorStore
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressor

class RAGCoordinator:
    """
    RAG coordinator for managing and orchestrating retrieval augmented generation.
    
    This class serves as the central hub for RAG operations, coordinating
    across multiple retrieval sources, including vector stores, user details,
    and structured databases.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm_manager: Any = None,
        user_details_rag: Any = None,
        vector_store_rag: Any = None,
        database_rag: Any = None,
        query_preprocessor: Any = None,
        relevance_scorer: Any = None,
        reranker: Any = None
    ):
        """
        Initialize RAG coordinator.
        
        Args:
            config_integration: Integration with the config system
            llm_manager: LLM manager for accessing language models
            user_details_rag: RAG component for user details
            vector_store_rag: RAG component for vector stores
            database_rag: RAG component for structured databases
            query_preprocessor: Preprocessor for query optimization
            relevance_scorer: Scorer for assessing document relevance
            reranker: Reranker for optimizing document order
        """
        self.config_integration = config_integration
        self.llm_manager = llm_manager
        self.user_details_rag = user_details_rag
        self.vector_store_rag = vector_store_rag
        self.database_rag = database_rag
        self.query_preprocessor = query_preprocessor
        self.relevance_scorer = relevance_scorer
        self.reranker = reranker
        self.logger = logging.getLogger(__name__)
        
        # Cache for retrievers
        self.retrievers: Dict[str, Any] = {}
    
    async def retrieve_relevant(
        self,
        query: str,
        session_id: str,
        bot_type: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        sources: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents from all configured sources.
        
        Args:
            query: User query
            session_id: Session identifier
            bot_type: Type of bot
            user_id: User identifier (if available)
            limit: Maximum number of documents to retrieve
            sources: Specific sources to retrieve from (defaults to all)
            filters: Additional filters to apply to retrieval
            
        Returns:
            List of relevant documents
        """
        # Get RAG configuration for this bot type
        rag_config = self._get_rag_config(bot_type)
        
        # Process query if preprocessor available
        processed_query = query
        if self.query_preprocessor:
            try:
                processed_query = await self.query_preprocessor.process_query(
                    query=query, 
                    bot_type=bot_type,
                    session_id=session_id
                )
            except Exception as e:
                self.logger.warning(f"Query preprocessing failed: {e}")
        
        # Determine sources to use
        retrieval_sources = sources or rag_config.get("sources", ["vector_store", "user_details", "database"])
        
        # Set up retrieval tasks
        retrieval_tasks = []
        
        if "user_details" in retrieval_sources and self.user_details_rag and user_id:
            retrieval_tasks.append(
                self._retrieve_from_user_details(
                    query=processed_query,
                    user_id=user_id,
                    session_id=session_id,
                    bot_type=bot_type,
                    limit=rag_config.get("user_details_limit", limit),
                    filters=filters
                )
            )
        
        if "vector_store" in retrieval_sources and self.vector_store_rag:
            retrieval_tasks.append(
                self._retrieve_from_vector_store(
                    query=processed_query,
                    session_id=session_id,
                    bot_type=bot_type,
                    limit=rag_config.get("vector_store_limit", limit),
                    filters=filters
                )
            )
        
        if "database" in retrieval_sources and self.database_rag:
            retrieval_tasks.append(
                self._retrieve_from_database(
                    query=processed_query,
                    session_id=session_id,
                    bot_type=bot_type,
                    limit=rag_config.get("database_limit", limit),
                    filters=filters
                )
            )
        
        # Execute retrieval tasks concurrently
        if not retrieval_tasks:
            return []
        
        results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
        
        # Process results
        all_documents = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Retrieval error: {result}")
                continue
            
            if isinstance(result, list):
                all_documents.extend(result)
        
        # Apply scoring if available
        if self.relevance_scorer:
            try:
                all_documents = await self.relevance_scorer.score_documents(
                    documents=all_documents,
                    query=query,
                    bot_type=bot_type
                )
            except Exception as e:
                self.logger.warning(f"Relevance scoring failed: {e}")
        
        # Apply reranking if available
        if self.reranker:
            try:
                all_documents = await self.reranker.rerank(
                    documents=all_documents,
                    query=query,
                    bot_type=bot_type
                )
            except Exception as e:
                self.logger.warning(f"Reranking failed: {e}")
        
        # Limit the number of documents
        return all_documents[:limit]
    
    def get_langchain_retriever(
        self,
        bot_type: str,
        session_id: str,
        user_id: Optional[str] = None,
        sources: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Get a LangChain retriever that integrates all RAG sources.
        
        Args:
            bot_type: Type of bot
            session_id: Session identifier
            user_id: User identifier (optional)
            sources: Specific sources to retrieve from (defaults to all)
            filters: Additional filters to apply to retrieval
            
        Returns:
            LangChain retriever instance
        """
        # Generate cache key
        cache_key = f"{bot_type}_{session_id}_{user_id}_{'-'.join(sources or [])}"
        
        # Check cache first
        if cache_key in self.retrievers:
            return self.retrievers[cache_key]
        
        # Create custom retriever that wraps our retrieve_relevant method
        class HybridRetriever:
            def __init__(self, coordinator, bot_type, session_id, user_id, sources, filters):
                self.coordinator = coordinator
                self.bot_type = bot_type
                self.session_id = session_id
                self.user_id = user_id
                self.sources = sources
                self.filters = filters
            
            def get_relevant_documents(self, query):
                # This method needs to be synchronous for LangChain compatibility
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    self.coordinator.retrieve_relevant(
                        query=query,
                        session_id=self.session_id,
                        bot_type=self.bot_type,
                        user_id=self.user_id,
                        sources=self.sources,
                        filters=self.filters
                    )
                )
            
            async def aget_relevant_documents(self, query):
                # Async version for newer LangChain versions
                return await self.coordinator.retrieve_relevant(
                    query=query,
                    session_id=self.session_id,
                    bot_type=self.bot_type,
                    user_id=self.user_id,
                    sources=self.sources,
                    filters=self.filters
                )
        
        # Create retriever instance
        retriever = HybridRetriever(
            coordinator=self,
            bot_type=bot_type,
            session_id=session_id,
            user_id=user_id,
            sources=sources,
            filters=filters
        )
        
        # Apply contextual compression if configured
        rag_config = self._get_rag_config(bot_type)
        
        if rag_config.get("use_compression", False) and self.llm_manager:
            try:
                # Create a document compressor that uses LLM to filter irrelevant content
                class LLMDocumentCompressor(DocumentCompressor):
                    def __init__(self, llm):
                        self.llm = llm
                    
                    def compress_documents(self, documents, query):
                        # Simple implementation - could be enhanced
                        return documents
                    
                    async def acompress_documents(self, documents, query):
                        # Simple implementation - could be enhanced
                        return documents
                
                # Get LLM for compression
                llm = self.llm_manager.get_model(bot_type, model_type="compression")
                
                # Create compressor and compressed retriever
                compressor = LLMDocumentCompressor(llm)
                compressed_retriever = ContextualCompressionRetriever(
                    base_compressor=compressor,
                    base_retriever=retriever
                )
                
                # Cache and return compressed retriever
                self.retrievers[cache_key] = compressed_retriever
                return compressed_retriever
                
            except Exception as e:
                self.logger.warning(f"Failed to create compressed retriever: {e}")
                # Fall back to base retriever
        
        # Cache and return base retriever
        self.retrievers[cache_key] = retriever
        return retriever
    
    async def _retrieve_from_user_details(
        self,
        query: str,
        user_id: str,
        session_id: str,
        bot_type: str,
        limit: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents from user details service.
        
        Args:
            query: User query
            user_id: User identifier
            session_id: Session identifier
            bot_type: Type of bot
            limit: Maximum number of documents to retrieve
            filters: Additional filters to apply to retrieval
            
        Returns:
            List of relevant documents
        """
        if not self.user_details_rag:
            return []
        
        try:
            return await self.user_details_rag.retrieve(
                query=query,
                user_id=user_id,
                session_id=session_id,
                bot_type=bot_type,
                limit=limit,
                filters=filters
            )
        except Exception as e:
            self.logger.error(f"User details retrieval failed: {e}", exc_info=True)
            return []
    
    async def _retrieve_from_vector_store(
        self,
        query: str,
        session_id: str,
        bot_type: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents from vector store.
        
        Args:
            query: User query
            session_id: Session identifier
            bot_type: Type of bot
            limit: Maximum number of documents to retrieve
            filters: Additional filters to apply to retrieval
            
        Returns:
            List of relevant documents
        """
        if not self.vector_store_rag:
            return []
        
        try:
            return await self.vector_store_rag.retrieve(
                query=query,
                session_id=session_id,
                bot_type=bot_type,
                limit=limit,
                filters=filters
            )
        except Exception as e:
            self.logger.error(f"Vector store retrieval failed: {e}", exc_info=True)
            return []
    
    async def _retrieve_from_database(
        self,
        query: str,
        session_id: str,
        bot_type: str,
        limit: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents from structured database.
        
        Args:
            query: User query
            session_id: Session identifier
            bot_type: Type of bot
            limit: Maximum number of documents to retrieve
            filters: Additional filters to apply to retrieval
            
        Returns:
            List of relevant documents
        """
        if not self.database_rag:
            return []
        
        try:
            return await self.database_rag.retrieve(
                query=query,
                session_id=session_id,
                bot_type=bot_type,
                limit=limit,
                filters=filters
            )
        except Exception as e:
            self.logger.error(f"Database retrieval failed: {e}", exc_info=True)
            return []
    
    def _get_rag_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get RAG configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            RAG configuration
        """
        # Default RAG configuration
        default_config = {
            "sources": ["vector_store", "user_details", "database"],
            "use_compression": False,
            "user_details_limit": 3,
            "vector_store_limit": 5,
            "database_limit": 3,
            "source_weights": {
                "user_details": 1.5,
                "vector_store": 1.0,
                "database": 1.0
            }
        }
        
        # Get bot-specific config if available
        if self.config_integration:
            config = self.config_integration.get_config(bot_type)
            rag_config = config.get("rag", {})
            
            # Merge with defaults
            merged_config = {**default_config, **rag_config}
            return merged_config
        
        return default_config
    
    def clear_retrievers_cache(self) -> None:
        """
        Clear the retrievers cache.
        """
        self.retrievers = {}
        self.logger.info("Retrievers cache cleared")
    
    def invalidate_retriever(self, cache_key: str) -> None:
        """
        Invalidate a specific retriever in the cache.
        
        Args:
            cache_key: Key of the retriever to invalidate
        """
        if cache_key in self.retrievers:
            del self.retrievers[cache_key]
            self.logger.info(f"Retriever {cache_key} invalidated in cache") 