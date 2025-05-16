"""
Vector Store RAG component for providing domain-specific knowledge.
Uses vector databases for semantic search with hybrid approaches.
"""

import logging
from typing import Dict, List, Any, Optional
import aiohttp
from langchain.schema import Document
from langchain.retrievers import BM25Retriever, EnsembleRetriever

from src.config.config_inheritance import ConfigInheritance
from src.models.llm.model_registry import ModelRegistry
from src.langchain_components.rag.collection_manager import collection_manager

class VectorStoreRAG:
    """
    Vector Store RAG component for domain-specific knowledge retrieval.
    Combines semantic and keyword search for comprehensive retrieval.
    """
    
    def __init__(self):
        """Initialize the Vector Store RAG component."""
        self.config_inheritance = ConfigInheritance()
        self.model_registry = ModelRegistry()
        self.logger = logging.getLogger(__name__)
    
    async def get_relevant_documents(
        self, query: str, bot_type: str, collection_name: Optional[str] = None, limit: int = 5
    ) -> List[Document]:
        """
        Get relevant documents from vector stores.
        
        Args:
            query: The search query
            bot_type: The type of bot
            collection_name: Optional specific collection to search
            limit: Maximum number of documents to return
            
        Returns:
            List of relevant documents
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Determine collections to search
        if collection_name:
            collections = [collection_name]
        else:
            collections = config.get("vector_store.collections", [])
        
        # Check if collections exist
        if not collections:
            self.logger.warning(f"No vector collections configured for {bot_type}")
            return []
        
        # Get retrieval strategy from config
        retrieval_strategy = config.get("vector_store.retrieval_strategy", "hybrid")
        
        # Get documents based on strategy
        if retrieval_strategy == "semantic":
            return await self._semantic_search(query, bot_type, collections, limit)
        elif retrieval_strategy == "keyword":
            return await self._keyword_search(query, bot_type, collections, limit)
        else:  # Default to hybrid
            return await self._hybrid_search(query, bot_type, collections, limit)
    
    async def _semantic_search(
        self, query: str, bot_type: str, collections: List[str], limit: int
    ) -> List[Document]:
        """Perform semantic search using vector embeddings."""
        documents = []
        
        for collection_name in collections:
            # Get collection-specific retriever
            retriever = await collection_manager.get_retriever(bot_type, collection_name)
            if not retriever:
                self.logger.warning(f"No retriever found for collection {collection_name}")
                continue
                
            # Get documents from this collection
            try:
                collection_docs = await retriever.get_relevant_documents(query)
                documents.extend(collection_docs)
            except Exception as e:
                self.logger.error(f"Error retrieving from collection {collection_name}: {e}")
        
        # Sort by relevance (if all retrievers support scoring)
        # This would be implemented if all retrievers provide scores
        
        # For now, just return up to limit documents
        return documents[:limit]
    
    async def _keyword_search(
        self, query: str, bot_type: str, collections: List[str], limit: int
    ) -> List[Document]:
        """Perform keyword search using BM25."""
        all_documents = []
        
        # Gather all documents from collections to build the BM25 index
        for collection_name in collections:
            # Get all documents from this collection
            docs = await collection_manager.get_all_documents(bot_type, collection_name)
            all_documents.extend(docs)
        
        if not all_documents:
            self.logger.warning(f"No documents found for keyword search")
            return []
        
        # Create BM25 retriever
        try:
            bm25_retriever = BM25Retriever.from_documents(all_documents)
            bm25_retriever.k = limit
            
            # Get documents using keyword search
            return bm25_retriever.get_relevant_documents(query)
        except Exception as e:
            self.logger.error(f"Error in keyword search: {e}")
            return []
    
    async def _hybrid_search(
        self, query: str, bot_type: str, collections: List[str], limit: int
    ) -> List[Document]:
        """Perform hybrid search combining semantic and keyword approaches."""
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        # Get weights for hybrid search
        semantic_weight = config.get("vector_store.semantic_weight", 0.7)
        keyword_weight = config.get("vector_store.keyword_weight", 0.3)
        
        all_documents = []
        semantic_retrievers = []
        
        # Get semantic retrievers and gather documents for keyword search
        for collection_name in collections:
            # Get collection-specific retriever
            retriever = await collection_manager.get_retriever(bot_type, collection_name)
            if retriever:
                semantic_retrievers.append(retriever)
            
            # Get all documents for keyword search
            docs = await collection_manager.get_all_documents(bot_type, collection_name)
            all_documents.extend(docs)
        
        if not semantic_retrievers:
            self.logger.warning(f"No semantic retrievers found, falling back to keyword search")
            return await self._keyword_search(query, bot_type, collections, limit)
        
        if not all_documents:
            self.logger.warning(f"No documents found, falling back to semantic search")
            return await self._semantic_search(query, bot_type, collections, limit)
        
        try:
            # Create BM25 retriever for keyword search
            bm25_retriever = BM25Retriever.from_documents(all_documents)
            bm25_retriever.k = limit
            
            # If only one semantic retriever, create ensemble directly
            if len(semantic_retrievers) == 1:
                ensemble_retriever = EnsembleRetriever(
                    retrievers=[semantic_retrievers[0], bm25_retriever],
                    weights=[semantic_weight, keyword_weight]
                )
                return ensemble_retriever.get_relevant_documents(query)
            
            # Otherwise, we need to run separate retrievals and combine manually
            semantic_docs = []
            for retriever in semantic_retrievers:
                docs = await retriever.get_relevant_documents(query)
                semantic_docs.extend(docs)
            
            keyword_docs = bm25_retriever.get_relevant_documents(query)
            
            # Simple weighted merging (ideally would use a proper reranker)
            # This is a simplistic approach that would be improved in a real implementation
            seen_docs = set()
            weighted_docs = []
            
            # Add semantic docs with their weight
            for i, doc in enumerate(semantic_docs):
                doc_id = hash(doc.page_content)
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    # Add weight based on position and semantic weight
                    score = semantic_weight * (1.0 - (i / max(1, len(semantic_docs))))
                    weighted_docs.append((doc, score))
            
            # Add keyword docs with their weight
            for i, doc in enumerate(keyword_docs):
                doc_id = hash(doc.page_content)
                if doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    # Add weight based on position and keyword weight
                    score = keyword_weight * (1.0 - (i / max(1, len(keyword_docs))))
                    weighted_docs.append((doc, score))
            
            # Sort by weight and return top documents
            weighted_docs.sort(key=lambda x: x[1], reverse=True)
            return [doc for doc, _ in weighted_docs[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error in hybrid search: {e}")
            # Fall back to semantic search
            return await self._semantic_search(query, bot_type, collections, limit)
    
    def get_retriever_for_bot(self, bot_type: str):
        """
        Get a specialized retriever for a specific bot type.
        
        Args:
            bot_type: The type of bot
            
        Returns:
            Bot-specific retriever function
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        
        if bot_type == "consultancy":
            # Consultancy bot focuses on domain-specific frameworks, best practices, and industry knowledge
            return self._get_consultancy_retriever(config)
        elif bot_type == "sales":
            # Sales bot focuses on product knowledge across niches
            return self._get_sales_retriever(config)
        elif bot_type == "support":
            # Support bot focuses on complex issue resolution with semantic search
            return self._get_support_retriever(config)
        else:
            # Default retriever
            return self.get_relevant_documents
    
    def _get_consultancy_retriever(self, config: Dict[str, Any]):
        """Get consultancy-specific retriever with focus on business knowledge."""
        async def consultancy_retriever(query: str, bot_type: str, limit: int = 5):
            # Get consultancy-specific collections
            collections = config.get("vector_store.consultancy_collections", [])
            
            # If no consultancy-specific collections, use default collections
            if not collections:
                collections = config.get("vector_store.collections", [])
            
            # Use specified retrieval strategy, defaulting to hybrid
            strategy = config.get("vector_store.consultancy_strategy", "hybrid")
            
            if strategy == "semantic":
                return await self._semantic_search(query, bot_type, collections, limit)
            elif strategy == "keyword":
                return await self._keyword_search(query, bot_type, collections, limit)
            else:
                return await self._hybrid_search(query, bot_type, collections, limit)
                
        return consultancy_retriever
    
    def _get_sales_retriever(self, config: Dict[str, Any]):
        """Get sales-specific retriever with focus on product knowledge."""
        async def sales_retriever(query: str, bot_type: str, limit: int = 5):
            # Get sales-specific collections
            collections = config.get("vector_store.sales_collections", [])
            
            # If no sales-specific collections, use default collections
            if not collections:
                collections = config.get("vector_store.collections", [])
            
            # Use specified retrieval strategy, defaulting to hybrid
            strategy = config.get("vector_store.sales_strategy", "hybrid")
            
            if strategy == "semantic":
                return await self._semantic_search(query, bot_type, collections, limit)
            elif strategy == "keyword":
                return await self._keyword_search(query, bot_type, collections, limit)
            else:
                return await self._hybrid_search(query, bot_type, collections, limit)
                
        return sales_retriever
    
    def _get_support_retriever(self, config: Dict[str, Any]):
        """Get support-specific retriever with focus on issue resolution."""
        async def support_retriever(query: str, bot_type: str, limit: int = 5):
            # Get support-specific collections
            collections = config.get("vector_store.support_collections", [])
            
            # If no support-specific collections, use default collections
            if not collections:
                collections = config.get("vector_store.collections", [])
            
            # Support bot typically benefits from semantic search
            # but we'll still respect the config
            strategy = config.get("vector_store.support_strategy", "semantic")
            
            if strategy == "semantic":
                return await self._semantic_search(query, bot_type, collections, limit)
            elif strategy == "keyword":
                return await self._keyword_search(query, bot_type, collections, limit)
            else:
                return await self._hybrid_search(query, bot_type, collections, limit)
                
        return support_retriever

# Global instance
vector_store_rag = VectorStoreRAG() 