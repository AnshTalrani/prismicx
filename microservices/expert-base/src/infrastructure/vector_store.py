"""
Vector store client for the Expert Base microservice.

This module provides a vector store client for storing and retrieving
knowledge embeddings using ChromaDB as an open source vector database.
"""

import os
from typing import Dict, List, Any, Optional, Union
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    logger.warning("ChromaDB/SentenceTransformers not available. Using placeholder vector store.")
    CHROMA_AVAILABLE = False


class VectorStoreClient:
    """
    Vector store client for knowledge retrieval.
    
    This class provides a unified interface for storing and retrieving
    knowledge embeddings from a vector database.
    """
    
    def __init__(self, persistent_directory: Optional[str] = None):
        """
        Initialize the vector store client.
        
        Args:
            persistent_directory: Optional directory for persistent storage.
                If not provided, an in-memory database will be used.
        """
        if CHROMA_AVAILABLE:
            try:
                # Initialize a real ChromaDB client
                self.client = ChromaDBClient(persistent_directory)
                logger.info(f"Initialized ChromaDB client with persistent_directory={persistent_directory}")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB client: {e}")
                # Fall back to placeholder client
                self.client = PlaceholderVectorClient()
                logger.warning("Using placeholder vector client due to ChromaDB initialization error")
        else:
            # Use a placeholder client if ChromaDB is not available
            self.client = PlaceholderVectorClient()
            logger.warning("Using placeholder vector client due to missing dependencies")
    
    async def store(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Store documents in the vector store.
        
        Args:
            collection_name: The name of the collection.
            texts: The texts to store.
            metadata: The metadata for each text.
            ids: Optional IDs for the documents.
        """
        return await self.client.store(collection_name, texts, metadata, ids)
    
    async def query(
        self, 
        collection_name: str, 
        text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents.
        
        Args:
            collection_name: The name of the collection.
            text: The text to find similar documents for.
            filters: Optional filters to apply.
            limit: The maximum number of results to return.
            
        Returns:
            A list of similar documents with their metadata.
        """
        return await self.client.query(collection_name, text, filters, limit)
    
    async def delete(
        self, 
        collection_name: str, 
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            collection_name: The name of the collection.
            ids: Optional IDs of documents to delete.
            filters: Optional filters to apply.
        """
        return await self.client.delete(collection_name, ids, filters)


class BaseVectorClient:
    """
    Base class for vector clients.
    
    This class defines the interface that all vector clients must implement.
    """
    
    async def store(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Store documents in the vector store.
        
        Args:
            collection_name: The name of the collection.
            texts: The texts to store.
            metadata: The metadata for each text.
            ids: Optional IDs for the documents.
        """
        raise NotImplementedError("Subclasses must implement store()")
    
    async def query(
        self, 
        collection_name: str, 
        text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents.
        
        Args:
            collection_name: The name of the collection.
            text: The text to find similar documents for.
            filters: Optional filters to apply.
            limit: The maximum number of results to return.
            
        Returns:
            A list of similar documents with their metadata.
        """
        raise NotImplementedError("Subclasses must implement query()")
    
    async def delete(
        self, 
        collection_name: str, 
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            collection_name: The name of the collection.
            ids: Optional IDs of documents to delete.
            filters: Optional filters to apply.
        """
        raise NotImplementedError("Subclasses must implement delete()")


class ChromaDBClient(BaseVectorClient):
    """
    ChromaDB vector client.
    
    This class wraps ChromaDB for use in the Expert Base microservice.
    """
    
    def __init__(self, persistent_directory: Optional[str] = None):
        """
        Initialize the ChromaDB client.
        
        Args:
            persistent_directory: Optional directory for persistent storage.
                If not provided, an in-memory database will be used.
        """
        # Configure ChromaDB settings
        settings = ChromaSettings()
        
        if persistent_directory:
            # Use persistent storage
            self.chroma_client = chromadb.PersistentClient(
                path=persistent_directory,
                settings=settings
            )
        else:
            # Use in-memory database
            self.chroma_client = chromadb.EphemeralClient(settings=settings)
        
        # Initialize collections cache
        self.collections = {}
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        logger.info("Initialized ChromaDBClient")
    
    def _get_collection(self, collection_name: str):
        """
        Get or create a collection.
        
        Args:
            collection_name: The name of the collection.
            
        Returns:
            A ChromaDB collection.
        """
        if collection_name not in self.collections:
            # Create collection if it doesn't exist
            self.collections[collection_name] = self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        
        return self.collections[collection_name]
    
    def _convert_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert filters to ChromaDB format.
        
        Args:
            filters: The filters to convert.
            
        Returns:
            Filters in ChromaDB format.
        """
        if not filters:
            return {}
        
        # Convert filters to ChromaDB format
        chroma_filters = {"$and": []}
        
        for key, value in filters.items():
            if isinstance(value, list):
                # Handle list values with OR
                or_conditions = [{"$eq": {key: v}} for v in value]
                chroma_filters["$and"].append({"$or": or_conditions})
            else:
                # Handle single values with AND
                chroma_filters["$and"].append({"$eq": {key: value}})
        
        return chroma_filters
    
    async def store(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Store documents in ChromaDB.
        
        Args:
            collection_name: The name of the collection.
            texts: The texts to store.
            metadata: The metadata for each text.
            ids: Optional IDs for the documents.
        """
        try:
            # Generate unique IDs if not provided
            if ids is None:
                ids = [str(i) for i in range(len(texts))]
            
            # Get or create collection
            collection = self._get_collection(collection_name)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Add documents to collection
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Stored {len(texts)} documents in collection '{collection_name}'")
        except Exception as e:
            logger.error(f"Error storing documents in ChromaDB: {e}")
            raise
    
    async def query(
        self, 
        collection_name: str, 
        text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query ChromaDB for similar documents.
        
        Args:
            collection_name: The name of the collection.
            text: The text to find similar documents for.
            filters: Optional filters to apply.
            limit: The maximum number of results to return.
            
        Returns:
            A list of similar documents with their metadata.
        """
        try:
            # Get collection
            collection = self._get_collection(collection_name)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(text).tolist()
            
            # Convert filters to ChromaDB format
            chroma_filters = self._convert_filters(filters) if filters else None
            
            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=chroma_filters
            )
            
            # Format results
            formatted_results = []
            
            if results and results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i] if "distances" in results else None
                    })
            
            logger.info(f"Found {len(formatted_results)} results in collection '{collection_name}'")
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []
    
    async def delete(
        self, 
        collection_name: str, 
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Delete documents from ChromaDB.
        
        Args:
            collection_name: The name of the collection.
            ids: Optional IDs of documents to delete.
            filters: Optional filters to apply.
        """
        try:
            # Get collection
            collection = self._get_collection(collection_name)
            
            # Convert filters to ChromaDB format
            chroma_filters = self._convert_filters(filters) if filters else None
            
            # Delete documents
            if ids:
                collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents from collection '{collection_name}'")
            elif chroma_filters:
                collection.delete(where=chroma_filters)
                logger.info(f"Deleted documents matching filters from collection '{collection_name}'")
            else:
                logger.warning(f"No IDs or filters provided for deletion in collection '{collection_name}'")
        except Exception as e:
            logger.error(f"Error deleting documents from ChromaDB: {e}")
            raise


class PlaceholderVectorClient(BaseVectorClient):
    """
    Placeholder vector client for when real vector databases are not available.
    
    This class provides a simple in-memory placeholder that simulates the
    behavior of a vector database.
    """
    
    def __init__(self):
        """
        Initialize the placeholder vector client.
        """
        self.collections = {}
        logger.warning("Using placeholder vector client")
    
    async def store(
        self, 
        collection_name: str, 
        texts: List[str], 
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Store documents in the placeholder vector store.
        
        Args:
            collection_name: The name of the collection.
            texts: The texts to store.
            metadata: The metadata for each text.
            ids: Optional IDs for the documents.
        """
        # Generate unique IDs if not provided
        if ids is None:
            ids = [str(i) for i in range(len(texts))]
        
        # Create collection if it doesn't exist
        if collection_name not in self.collections:
            self.collections[collection_name] = []
        
        # Add documents to collection
        for i in range(len(texts)):
            self.collections[collection_name].append({
                "id": ids[i],
                "text": texts[i],
                "metadata": metadata[i]
            })
        
        logger.info(f"Stored {len(texts)} documents in placeholder collection '{collection_name}'")
    
    async def query(
        self, 
        collection_name: str, 
        text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query the placeholder vector store for similar documents.
        
        Args:
            collection_name: The name of the collection.
            text: The text to find similar documents for.
            filters: Optional filters to apply.
            limit: The maximum number of results to return.
            
        Returns:
            A list of similar documents with their metadata.
        """
        # Return placeholder results
        if collection_name not in self.collections:
            logger.warning(f"Collection '{collection_name}' does not exist in placeholder vector store")
            return []
        
        # Apply filters if provided
        results = self.collections[collection_name]
        
        if filters:
            filtered_results = []
            
            for doc in results:
                match = True
                
                for key, value in filters.items():
                    if key not in doc["metadata"] or doc["metadata"][key] != value:
                        match = False
                        break
                
                if match:
                    filtered_results.append(doc)
            
            results = filtered_results
        
        # Return results
        return results[:limit]
    
    async def delete(
        self, 
        collection_name: str, 
        ids: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Delete documents from the placeholder vector store.
        
        Args:
            collection_name: The name of the collection.
            ids: Optional IDs of documents to delete.
            filters: Optional filters to apply.
        """
        if collection_name not in self.collections:
            logger.warning(f"Collection '{collection_name}' does not exist in placeholder vector store")
            return
        
        if ids:
            # Delete by ID
            self.collections[collection_name] = [
                doc for doc in self.collections[collection_name]
                if doc["id"] not in ids
            ]
            
            logger.info(f"Deleted {len(ids)} documents from placeholder collection '{collection_name}'")
        elif filters:
            # Delete by filter
            original_count = len(self.collections[collection_name])
            
            self.collections[collection_name] = [
                doc for doc in self.collections[collection_name]
                if not all(doc["metadata"].get(k) == v for k, v in filters.items())
            ]
            
            deleted_count = original_count - len(self.collections[collection_name])
            logger.info(f"Deleted {deleted_count} documents matching filters from placeholder collection '{collection_name}'")
        else:
            logger.warning(f"No IDs or filters provided for deletion in placeholder collection '{collection_name}'")


def get_vector_db_client() -> VectorStoreClient:
    """
    Get a vector store client.
    
    Returns:
        A VectorStoreClient instance.
    """
    # Get persistent directory from environment or use a default
    persistent_directory = os.environ.get("VECTOR_DB_PATH", None)
    
    return VectorStoreClient(persistent_directory) 