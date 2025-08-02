"""
Vector Store Service implementation.
Provides methods for managing and querying vector stores.
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import uuid
from pymongo.database import Database
from models.vector_store import (
    Document, DocumentMetadata, StoreMetadata, StoreRequest,
    QueryRequest, QueryResult, VectorStoreType, EmbeddingModelType
)

# Vector store backends
from langchain_community.vectorstores import FAISS, Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger("vector-store-service")

# Base directory for storing vector databases
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "./data/vector_stores")

class VectorStoreService:
    """
    Provides vector store operations for document storage and retrieval.
    """
    
    def __init__(self, db: Database):
        """
        Initialize the vector store service.
        
        Args:
            db: MongoDB database connection
        """
        self.db = db
        
        # Collections for storing metadata
        self.stores_collection = self.db["vector_stores"]
        self.documents_collection = self.db["vector_documents"]
        
        # Ensure indexes
        self._ensure_indexes()
        
        # Get embeddings model registry
        self.embedding_models = self._get_embedding_models()
        
        # Storage mapping - in memory cache of vector stores
        self.stores = {}
        
    def _ensure_indexes(self):
        """Ensure required indexes exist in the database."""
        # Indexes for stores collection
        self.stores_collection.create_index("name", unique=True)
        self.stores_collection.create_index("metadata.bot_type")
        self.stores_collection.create_index("metadata.domain")
        self.stores_collection.create_index("metadata.tags")
        
        # Indexes for documents collection
        self.documents_collection.create_index("id", unique=True)
        self.documents_collection.create_index("collection_name")
        self.documents_collection.create_index([
            ("collection_name", 1),
            ("metadata.tenant_id", 1)
        ])
        self.documents_collection.create_index("metadata.domain")
        self.documents_collection.create_index("metadata.category")
        self.documents_collection.create_index("metadata.tags")
    
    def _get_embedding_models(self) -> Dict:
        """
        Create a registry of available embedding models.
        
        Returns:
            Dictionary mapping embedding types to factory functions
        """
        return {
            EmbeddingModelType.SENTENCE_TRANSFORMERS: self._get_sentence_transformer_embeddings,
            EmbeddingModelType.OPENAI: self._get_openai_embeddings,
            EmbeddingModelType.HUGGINGFACE: self._get_huggingface_embeddings,
        }
    
    def _get_sentence_transformer_embeddings(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Get Sentence Transformer embeddings model.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            Embedding model instance
        """
        return HuggingFaceEmbeddings(model_name=model_name)
    
    def _get_openai_embeddings(self, model_name: str = "text-embedding-ada-002"):
        """
        Get OpenAI embeddings model.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            Embedding model instance
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI embeddings will not work")
        return OpenAIEmbeddings(model=model_name)
        
    def _get_huggingface_embeddings(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Get HuggingFace embeddings model.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            Embedding model instance
        """
        return HuggingFaceEmbeddings(model_name=model_name)
    
    def _get_embedding_model(self, embedding_type: EmbeddingModelType, model_name: Optional[str] = None) -> Any:
        """
        Get embedding model instance by type.
        
        Args:
            embedding_type: Type of embedding model
            model_name: Optional model name (uses default if not provided)
            
        Returns:
            Embedding model instance
        """
        if embedding_type not in self.embedding_models:
            raise ValueError(f"Unsupported embedding type: {embedding_type}")
            
        # Get the factory function
        factory = self.embedding_models[embedding_type]
        
        # Create the model with or without model name
        if model_name:
            return factory(model_name)
        return factory()
    
    def _get_store_path(self, collection_name: str, tenant_id: Optional[str] = None) -> str:
        """
        Get the path for storing vector data.
        
        Args:
            collection_name: Name of the collection
            tenant_id: Optional tenant ID for multi-tenant isolation
            
        Returns:
            Path to the vector store directory
        """
        if tenant_id:
            path = os.path.join(VECTOR_STORE_DIR, tenant_id, collection_name)
        else:
            path = os.path.join(VECTOR_STORE_DIR, "system", collection_name)
            
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)
        return path
    
    async def create_store(self, request: StoreRequest, tenant_id: str = "") -> StoreMetadata:
        """
        Create a new vector store.
        
        Args:
            request: Store creation request
            tenant_id: Optional tenant ID for multi-tenant isolation
            
        Returns:
            Metadata for the created store
        """
        # Check if store already exists
        existing = await self.stores_collection.find_one({"name": request.name})
        if existing:
            raise ValueError(f"Store with name '{request.name}' already exists")
        
        # Create metadata
        metadata = StoreMetadata(
            name=request.name,
            description=request.description,
            bot_type=request.bot_type,
            domain=request.domain,
            tags=request.tags,
            store_type=request.store_type,
            embedding_model=request.embedding_model,
            model_name=request.model_name,
        )
        
        # Store metadata in database
        await self.stores_collection.insert_one({
            "name": request.name,
            "metadata": metadata.dict(),
            "tenant_id": tenant_id
        })
        
        # Initialize the vector store
        embedding_model = self._get_embedding_model(
            request.embedding_model, 
            request.model_name
        )
        
        store_path = self._get_store_path(request.name, tenant_id)
        
        # Create empty vector store by type
        if request.store_type == VectorStoreType.FAISS:
            store = FAISS.from_texts(["placeholder"], embedding_model)
            store.save_local(store_path)
        elif request.store_type == VectorStoreType.CHROMA:
            Chroma.from_texts(
                ["placeholder"], 
                embedding_model,
                persist_directory=store_path
            )
        
        logger.info(f"Created vector store: {request.name}")
        return metadata
    
    async def list_stores(self, tenant_id: str = "") -> List[Dict]:
        """
        List all available vector stores.
        
        Args:
            tenant_id: Optional tenant ID filter
            
        Returns:
            List of store information
        """
        query = {"tenant_id": tenant_id} if tenant_id else {}
        
        stores = []
        async for store in self.stores_collection.find(query):
            # Count documents in store
            document_count = await self.documents_collection.count_documents({
                "collection_name": store["name"],
                "metadata.tenant_id": tenant_id
            })
            
            # Add to result
            stores.append({
                "name": store["name"],
                "metadata": store["metadata"],
                "document_count": document_count
            })
            
        return stores
    
    async def get_store_info(self, collection_name: str, tenant_id: str = "") -> Dict:
        """
        Get information about a specific store.
        
        Args:
            collection_name: Name of the collection
            tenant_id: Optional tenant ID
            
        Returns:
            Store information
        """
        # Query for store metadata
        query = {"name": collection_name}
        if tenant_id:
            query["tenant_id"] = tenant_id
            
        store = await self.stores_collection.find_one(query)
        if not store:
            raise ValueError(f"Store not found: {collection_name}")
            
        # Count documents in store
        document_count = await self.documents_collection.count_documents({
            "collection_name": collection_name,
            "metadata.tenant_id": tenant_id
        })
        
        return {
            "name": store["name"],
            "metadata": store["metadata"],
            "document_count": document_count
        }
    
    async def add_documents(
        self, 
        collection_name: str, 
        documents: List[Document], 
        tenant_id: str = ""
    ) -> List[str]:
        """
        Add documents to a vector store.
        
        Args:
            collection_name: Name of the collection
            documents: List of documents to add
            tenant_id: Optional tenant ID for multi-tenant isolation
            
        Returns:
            List of document IDs
        """
        # Get store metadata
        store_info = await self.get_store_info(collection_name, tenant_id)
        metadata = StoreMetadata(**store_info["metadata"])
        
        # Get embedding model
        embedding_model = self._get_embedding_model(
            metadata.embedding_model,
            metadata.model_name
        )
        
        store_path = self._get_store_path(collection_name, tenant_id)
        
        # Load or create vector store
        if metadata.store_type == VectorStoreType.FAISS:
            try:
                store = FAISS.load_local(store_path, embedding_model)
            except:
                store = FAISS.from_texts(["placeholder"], embedding_model)
        elif metadata.store_type == VectorStoreType.CHROMA:
            store = Chroma(
                persist_directory=store_path,
                embedding_function=embedding_model
            )
        
        # Prepare documents for storage
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            # Generate ID if not provided
            doc_id = doc.id or str(uuid.uuid4())
            ids.append(doc_id)
            
            # Update metadata with tenant ID
            doc.metadata.tenant_id = tenant_id
            
            # Add to lists for vector store
            texts.append(doc.text)
            metadatas.append(doc.metadata.dict())
            
            # Store in MongoDB for querying
            await self.documents_collection.insert_one({
                "id": doc_id,
                "collection_name": collection_name,
                "text": doc.text,
                "metadata": doc.metadata.dict()
            })
        
        # Add to vector store
        if metadata.store_type == VectorStoreType.FAISS:
            store.add_texts(texts, metadatas, ids)
            store.save_local(store_path)
        elif metadata.store_type == VectorStoreType.CHROMA:
            store.add_texts(texts, metadatas, ids)
            store.persist()
        
        # Update metadata
        await self.stores_collection.update_one(
            {"name": collection_name},
            {"$set": {
                "metadata.vector_count": store_info["document_count"] + len(documents),
                "metadata.updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Added {len(documents)} documents to {collection_name}")
        return ids
    
    async def search(
        self,
        query: QueryRequest,
        tenant_id: str = ""
    ) -> List[QueryResult]:
        """
        Search the vector store for similar documents.
        
        Args:
            query: Query request
            tenant_id: Optional tenant ID for multi-tenant isolation
            
        Returns:
            List of query results
        """
        # Get store metadata
        store_info = await self.get_store_info(query.collection_name, tenant_id)
        metadata = StoreMetadata(**store_info["metadata"])
        
        # Get embedding model
        embedding_model = self._get_embedding_model(
            metadata.embedding_model,
            metadata.model_name
        )
        
        store_path = self._get_store_path(query.collection_name, tenant_id)
        
        # Load vector store
        if metadata.store_type == VectorStoreType.FAISS:
            try:
                store = FAISS.load_local(store_path, embedding_model)
            except:
                logger.error(f"Failed to load FAISS store: {query.collection_name}")
                return []
        elif metadata.store_type == VectorStoreType.CHROMA:
            store = Chroma(
                persist_directory=store_path,
                embedding_function=embedding_model
            )
        
        # Build filter
        filter_dict = query.filter_metadata or {}
        
        # Always filter by tenant ID
        if tenant_id:
            filter_dict["tenant_id"] = tenant_id
        
        # Perform search
        results = []
        if metadata.store_type == VectorStoreType.FAISS:
            # FAISS doesn't support filtering directly
            docs_with_scores = store.similarity_search_with_score(
                query.text, 
                k=query.top_k
            )
            
            # Filter manually
            for doc, score in docs_with_scores:
                # Skip if doesn't meet similarity threshold
                if query.similarity_threshold and score < query.similarity_threshold:
                    continue
                    
                # Skip if doesn't match filter
                if not self._matches_filter(doc.metadata, filter_dict):
                    continue
                    
                results.append(QueryResult(
                    text=doc.page_content,
                    metadata=DocumentMetadata(**doc.metadata),
                    id=doc.metadata.get("id", ""),
                    similarity_score=float(score)
                ))
        
        elif metadata.store_type == VectorStoreType.CHROMA:
            # Chroma supports filtering
            docs = store.similarity_search_with_relevance_scores(
                query.text,
                k=query.top_k,
                filter=filter_dict if filter_dict else None
            )
            
            for doc, score in docs:
                # Skip if doesn't meet similarity threshold
                if query.similarity_threshold and score < query.similarity_threshold:
                    continue
                    
                results.append(QueryResult(
                    text=doc.page_content,
                    metadata=DocumentMetadata(**doc.metadata),
                    id=doc.metadata.get("id", ""),
                    similarity_score=float(score)
                ))
        
        return results
    
    def _matches_filter(self, metadata: Dict, filter_dict: Dict) -> bool:
        """
        Check if metadata matches a filter dictionary.
        
        Args:
            metadata: Document metadata
            filter_dict: Filter criteria
            
        Returns:
            True if metadata matches filter
        """
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
                
            if metadata[key] != value:
                return False
                
        return True
    
    async def delete_documents(
        self,
        collection_name: str,
        document_ids: Optional[List[str]] = None,
        filter_metadata: Optional[Dict] = None,
        tenant_id: str = ""
    ) -> int:
        """
        Delete documents from a vector store.
        
        Args:
            collection_name: Name of the collection
            document_ids: Optional list of document IDs to delete
            filter_metadata: Optional metadata filter
            tenant_id: Optional tenant ID
            
        Returns:
            Number of documents deleted
        """
        # Get store metadata
        store_info = await self.get_store_info(collection_name, tenant_id)
        metadata = StoreMetadata(**store_info["metadata"])
        
        # Build query
        query = {"collection_name": collection_name}
        
        if tenant_id:
            query["metadata.tenant_id"] = tenant_id
            
        if document_ids:
            query["id"] = {"$in": document_ids}
            
        if filter_metadata:
            for key, value in filter_metadata.items():
                query[f"metadata.{key}"] = value
        
        # Get documents to delete
        to_delete = []
        async for doc in self.documents_collection.find(query):
            to_delete.append(doc["id"])
            
        if not to_delete:
            return 0
            
        # Delete from MongoDB
        result = await self.documents_collection.delete_many(query)
        deleted_count = result.deleted_count
        
        # Delete from vector store
        # Note: Some vector stores don't support deletion, so we might need to rebuild
        store_path = self._get_store_path(collection_name, tenant_id)
        
        # For now, let's just update the metadata
        await self.stores_collection.update_one(
            {"name": collection_name},
            {"$set": {
                "metadata.vector_count": max(0, store_info["document_count"] - deleted_count),
                "metadata.updated_at": datetime.utcnow()
            }}
        )
        
        logger.info(f"Deleted {deleted_count} documents from {collection_name}")
        return deleted_count 