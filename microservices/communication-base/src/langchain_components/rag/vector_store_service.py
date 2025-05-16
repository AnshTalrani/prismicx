"""
Vector store service for RAG integration.

This module provides a service for integrating with vectorstores through LangChain,
supporting embeddings, retrieval, and multiple adapters for different vectorstores.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
import json
import os

from langchain.vectorstores import FAISS, Chroma, Pinecone
from langchain.embeddings.base import Embeddings
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain.schema import BaseRetriever, Document

class VectorStoreService:
    """
    Vector store service for RAG integration with LangChain.
    
    This class provides methods for managing vectorstores through LangChain,
    with support for multiple vectorstore backends, caching, and advanced
    retrieval capabilities.
    """
    
    def __init__(
        self,
        config_integration: Any = None,
        llm_manager: Any = None,
        embedding_service: Any = None,
        document_processor: Any = None
    ):
        """
        Initialize vector store service.
        
        Args:
            config_integration: Integration with the config system
            llm_manager: LLM manager for accessing language models
            embedding_service: Service for generating and managing embeddings
            document_processor: Service for processing and preparing documents
        """
        self.config_integration = config_integration
        self.llm_manager = llm_manager
        self.embedding_service = embedding_service
        self.document_processor = document_processor
        self.logger = logging.getLogger(__name__)
        
        # Cache for vectorstores
        self.vectorstores: Dict[str, Any] = {}
        
        # Cache for retrievers
        self.retrievers: Dict[str, BaseRetriever] = {}
    
    async def retrieve(
        self,
        query: str,
        session_id: str,
        bot_type: str,
        collection_name: Optional[str] = None,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve documents from vector store.
        
        Args:
            query: Query for retrieval
            session_id: Session identifier
            bot_type: Type of bot
            collection_name: Name of the vector store collection
            limit: Maximum number of documents to retrieve
            filters: Filters to apply to retrieval
            
        Returns:
            List of retrieved documents
        """
        # Get vector store configuration
        vs_config = self._get_vs_config(bot_type)
        
        # Determine collection name if not provided
        collection_name = collection_name or vs_config.get("default_collection", bot_type)
        
        # Get retriever
        retriever = await self._get_retriever(bot_type, collection_name, vs_config)
        
        if not retriever:
            self.logger.warning(f"No retriever available for {bot_type}/{collection_name}")
            return []
        
        try:
            # Process query if document processor available
            processed_query = query
            if self.document_processor:
                try:
                    processed_query = await self.document_processor.process_query(
                        query=query,
                        bot_type=bot_type,
                        session_id=session_id
                    )
                except Exception as e:
                    self.logger.warning(f"Query processing failed: {e}")
            
            # Retrieve documents
            documents = retriever.get_relevant_documents(processed_query)
            
            # Apply filters if provided
            if filters and documents:
                documents = self._apply_filters(documents, filters)
            
            # Limit the number of documents
            documents = documents[:limit]
            
            # Process documents if document processor available
            if self.document_processor and documents:
                try:
                    documents = await self.document_processor.process_documents(
                        documents=documents,
                        query=query,
                        bot_type=bot_type
                    )
                except Exception as e:
                    self.logger.warning(f"Document processing failed: {e}")
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Vector store retrieval failed: {e}", exc_info=True)
            return []
    
    async def get_langchain_retriever(
        self,
        bot_type: str,
        collection_name: Optional[str] = None,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseRetriever]:
        """
        Get a LangChain retriever for a vector store.
        
        Args:
            bot_type: Type of bot
            collection_name: Name of the vector store collection
            search_type: Type of search to perform (similarity/mmr)
            search_kwargs: Additional search parameters
            
        Returns:
            LangChain retriever or None if not available
        """
        # Get vector store configuration
        vs_config = self._get_vs_config(bot_type)
        
        # Determine collection name if not provided
        collection_name = collection_name or vs_config.get("default_collection", bot_type)
        
        # Generate cache key
        cache_key = f"{bot_type}_{collection_name}_{search_type}"
        
        # Return cached retriever if available
        if cache_key in self.retrievers:
            return self.retrievers[cache_key]
        
        # Get vector store
        vectorstore = await self._get_vectorstore(bot_type, collection_name, vs_config)
        
        if not vectorstore:
            self.logger.warning(f"No vector store available for {bot_type}/{collection_name}")
            return None
        
        # Create retriever based on search type
        try:
            if search_type == "mmr":
                search_kwargs = search_kwargs or {}
                search_kwargs.setdefault("fetch_k", 20)
                search_kwargs.setdefault("lambda_mult", 0.5)
                retriever = vectorstore.as_retriever(
                    search_type="mmr",
                    search_kwargs=search_kwargs
                )
            else:  # Default to similarity
                search_kwargs = search_kwargs or {}
                search_kwargs.setdefault("k", 5)
                retriever = vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs=search_kwargs
                )
            
            # Cache retriever
            self.retrievers[cache_key] = retriever
            return retriever
            
        except Exception as e:
            self.logger.error(f"Failed to create retriever: {e}")
            return None
    
    async def add_documents(
        self,
        documents: List[Document],
        bot_type: str,
        collection_name: Optional[str] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents to a vector store.
        
        Args:
            documents: Documents to add
            bot_type: Type of bot
            collection_name: Name of the vector store collection
            ids: Optional document IDs
            
        Returns:
            True if successful, False otherwise
        """
        # Get vector store configuration
        vs_config = self._get_vs_config(bot_type)
        
        # Determine collection name if not provided
        collection_name = collection_name or vs_config.get("default_collection", bot_type)
        
        # Process documents if document processor available
        if self.document_processor and documents:
            try:
                documents = await self.document_processor.prepare_documents(
                    documents=documents,
                    bot_type=bot_type
                )
            except Exception as e:
                self.logger.warning(f"Document preparation failed: {e}")
        
        # Get vector store
        vectorstore = await self._get_vectorstore(bot_type, collection_name, vs_config)
        
        if not vectorstore:
            self.logger.warning(f"No vector store available for {bot_type}/{collection_name}")
            return False
        
        try:
            # Add documents to vector store
            if hasattr(vectorstore, "add_documents"):
                vectorstore.add_documents(documents)
            else:
                # Fallback using from_documents with existing embeddings
                embeddings = await self._get_embeddings(bot_type, vs_config)
                
                if ids:
                    # Use appropriate method based on vector store type
                    if isinstance(vectorstore, FAISS):
                        FAISS.add_documents(vectorstore, documents, embeddings)
                    elif isinstance(vectorstore, Chroma):
                        Chroma.add_documents(vectorstore, documents, embeddings, ids=ids)
                    elif isinstance(vectorstore, Pinecone):
                        Pinecone.add_documents(vectorstore, documents, embeddings, ids=ids)
                    else:
                        self.logger.warning(f"Unsupported vector store type: {type(vectorstore)}")
                        return False
                else:
                    # No IDs provided
                    if isinstance(vectorstore, FAISS):
                        FAISS.add_documents(vectorstore, documents, embeddings)
                    elif isinstance(vectorstore, Chroma):
                        Chroma.add_documents(vectorstore, documents, embeddings)
                    elif isinstance(vectorstore, Pinecone):
                        Pinecone.add_documents(vectorstore, documents, embeddings)
                    else:
                        self.logger.warning(f"Unsupported vector store type: {type(vectorstore)}")
                        return False
            
            # Invalidate retriever cache for this collection
            self._invalidate_retrievers(bot_type, collection_name)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add documents to vector store: {e}", exc_info=True)
            return False
    
    async def delete_documents(
        self,
        ids: List[str],
        bot_type: str,
        collection_name: Optional[str] = None
    ) -> bool:
        """
        Delete documents from a vector store.
        
        Args:
            ids: IDs of documents to delete
            bot_type: Type of bot
            collection_name: Name of the vector store collection
            
        Returns:
            True if successful, False otherwise
        """
        # Get vector store configuration
        vs_config = self._get_vs_config(bot_type)
        
        # Determine collection name if not provided
        collection_name = collection_name or vs_config.get("default_collection", bot_type)
        
        # Get vector store
        vectorstore = await self._get_vectorstore(bot_type, collection_name, vs_config)
        
        if not vectorstore:
            self.logger.warning(f"No vector store available for {bot_type}/{collection_name}")
            return False
        
        try:
            # Delete documents from vector store
            if hasattr(vectorstore, "delete"):
                vectorstore.delete(ids)
            else:
                self.logger.warning(f"Vector store does not support deletion: {type(vectorstore)}")
                return False
            
            # Invalidate retriever cache for this collection
            self._invalidate_retrievers(bot_type, collection_name)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete documents from vector store: {e}", exc_info=True)
            return False
    
    async def _get_vectorstore(
        self,
        bot_type: str,
        collection_name: str,
        vs_config: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get or create a vector store.
        
        Args:
            bot_type: Type of bot
            collection_name: Name of the vector store collection
            vs_config: Vector store configuration
            
        Returns:
            Vector store instance or None if not available
        """
        # Generate cache key
        cache_key = f"{bot_type}_{collection_name}"
        
        # Return cached vector store if available
        if cache_key in self.vectorstores:
            return self.vectorstores[cache_key]
        
        # Get vector store type
        vs_type = vs_config.get("type", "faiss")
        
        # Get embeddings
        embeddings = await self._get_embeddings(bot_type, vs_config)
        
        if not embeddings:
            self.logger.warning(f"No embeddings available for {bot_type}")
            return None
        
        try:
            # Create vector store based on type
            if vs_type == "faiss":
                # Determine path
                persist_directory = vs_config.get("persist_directory", "./vectorstores")
                if not os.path.exists(persist_directory):
                    os.makedirs(persist_directory)
                
                path = f"{persist_directory}/{bot_type}_{collection_name}"
                
                # Load or create FAISS vector store
                if os.path.exists(f"{path}/index.faiss"):
                    vectorstore = FAISS.load_local(path, embeddings)
                else:
                    # Create empty FAISS index
                    vectorstore = FAISS.from_texts(["placeholder"], embeddings)
                    vectorstore.save_local(path)
                
            elif vs_type == "chroma":
                # Determine path
                persist_directory = vs_config.get("persist_directory", "./vectorstores")
                if not os.path.exists(persist_directory):
                    os.makedirs(persist_directory)
                
                path = f"{persist_directory}/{bot_type}_{collection_name}"
                
                # Load or create Chroma vector store
                vectorstore = Chroma(
                    collection_name=collection_name,
                    embedding_function=embeddings,
                    persist_directory=path
                )
                
            elif vs_type == "pinecone":
                # Get Pinecone configuration
                pinecone_config = vs_config.get("pinecone", {})
                api_key = pinecone_config.get("api_key")
                environment = pinecone_config.get("environment")
                index_name = pinecone_config.get("index_name")
                
                if not api_key or not environment or not index_name:
                    self.logger.warning("Incomplete Pinecone configuration")
                    return None
                
                # Initialize Pinecone
                import pinecone
                
                pinecone.init(api_key=api_key, environment=environment)
                
                # Create or get index
                if index_name not in pinecone.list_indexes():
                    self.logger.warning(f"Pinecone index {index_name} does not exist")
                    return None
                
                # Create vector store
                vectorstore = Pinecone.from_existing_index(
                    index_name=index_name,
                    embedding=embeddings,
                    namespace=collection_name
                )
                
            else:
                self.logger.warning(f"Unsupported vector store type: {vs_type}")
                return None
            
            # Cache vector store
            self.vectorstores[cache_key] = vectorstore
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"Failed to create vector store: {e}", exc_info=True)
            return None
    
    async def _get_retriever(
        self,
        bot_type: str,
        collection_name: str,
        vs_config: Dict[str, Any]
    ) -> Optional[BaseRetriever]:
        """
        Get or create a retriever for a vector store.
        
        Args:
            bot_type: Type of bot
            collection_name: Name of the vector store collection
            vs_config: Vector store configuration
            
        Returns:
            LangChain retriever or None if not available
        """
        # Determine search type and kwargs
        search_type = vs_config.get("search_type", "similarity")
        search_kwargs = vs_config.get("search_kwargs", {})
        
        # Get retriever using public method
        return await self.get_langchain_retriever(
            bot_type=bot_type,
            collection_name=collection_name,
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    async def _get_embeddings(
        self,
        bot_type: str,
        vs_config: Dict[str, Any]
    ) -> Optional[Embeddings]:
        """
        Get an embeddings instance for a bot type.
        
        Args:
            bot_type: Type of bot
            vs_config: Vector store configuration
            
        Returns:
            Embeddings instance or None if not available
        """
        # Use embedding service if available
        if self.embedding_service:
            try:
                return self.embedding_service.get_embeddings(bot_type)
            except Exception as e:
                self.logger.warning(f"Failed to get embeddings from service: {e}")
        
        # Fallback: Create embeddings directly
        embedding_config = vs_config.get("embedding", {})
        embedding_type = embedding_config.get("type", "openai")
        
        try:
            if embedding_type == "openai":
                api_key = embedding_config.get("api_key", os.environ.get("OPENAI_API_KEY"))
                model = embedding_config.get("model", "text-embedding-ada-002")
                
                if not api_key:
                    self.logger.warning("No OpenAI API key available")
                    return None
                
                return OpenAIEmbeddings(
                    openai_api_key=api_key,
                    model=model
                )
                
            elif embedding_type == "huggingface":
                model_name = embedding_config.get("model_name", "all-MiniLM-L6-v2")
                
                return HuggingFaceEmbeddings(
                    model_name=model_name
                )
                
            else:
                self.logger.warning(f"Unsupported embedding type: {embedding_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create embeddings: {e}")
            return None
    
    def _apply_filters(
        self,
        documents: List[Document],
        filters: Dict[str, Any]
    ) -> List[Document]:
        """
        Apply filters to retrieved documents.
        
        Args:
            documents: Retrieved documents
            filters: Filters to apply
            
        Returns:
            Filtered documents
        """
        filtered_docs = []
        
        for doc in documents:
            # Check all filter criteria
            match = True
            
            for key, value in filters.items():
                # Check if document has metadata
                if not hasattr(doc, "metadata") or not doc.metadata:
                    match = False
                    break
                
                # Check if key exists in metadata
                if key not in doc.metadata:
                    match = False
                    break
                
                # Check if value matches
                if doc.metadata[key] != value:
                    match = False
                    break
            
            # Add document if it matches all filters
            if match:
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def _get_vs_config(self, bot_type: str) -> Dict[str, Any]:
        """
        Get vector store configuration for a bot type.
        
        Args:
            bot_type: Type of bot
            
        Returns:
            Vector store configuration
        """
        # Default vector store configuration
        default_config = {
            "type": "faiss",
            "persist_directory": "./vectorstores",
            "default_collection": bot_type,
            "search_type": "similarity",
            "search_kwargs": {
                "k": 5
            },
            "embedding": {
                "type": "openai",
                "model": "text-embedding-ada-002"
            }
        }
        
        # Get bot-specific config if available
        if self.config_integration:
            try:
                config = self.config_integration.get_config(bot_type)
                vs_config = config.get("vector_store", {})
                
                # Merge with defaults
                merged_config = {**default_config, **vs_config}
                return merged_config
            except Exception as e:
                self.logger.warning(f"Failed to get vector store config: {e}")
        
        return default_config
    
    def _invalidate_retrievers(self, bot_type: str, collection_name: str) -> None:
        """
        Invalidate retrievers for a collection.
        
        Args:
            bot_type: Type of bot
            collection_name: Name of the vector store collection
        """
        # Find and remove retrievers for this collection
        keys_to_remove = []
        
        for key in self.retrievers:
            if key.startswith(f"{bot_type}_{collection_name}_"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.retrievers[key]
            self.logger.info(f"Invalidated retriever {key}")
    
    def clear_cache(self) -> None:
        """
        Clear the cache of vectorstores and retrievers.
        """
        self.vectorstores = {}
        self.retrievers = {}
        self.logger.info("Cleared vectorstore and retriever caches") 