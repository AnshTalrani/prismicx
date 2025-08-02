"""
Collection manager for vector store collections.
Maps bot types to specific vector collections and provides retrieval capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain.schema import Document
from langchain.vectorstores import FAISS, Chroma
from langchain_openai import OpenAIEmbeddings

from src.config.config_inheritance import ConfigInheritance
from src.models.llm.model_registry import ModelRegistry

class CollectionManager:
    """
    Manages vector store collections for different bot types.
    Provides retrieval and storage capabilities for vector collections.
    """
    
    def __init__(self):
        """Initialize the collection manager."""
        self.config_inheritance = ConfigInheritance()
        self.model_registry = ModelRegistry()
        self.logger = logging.getLogger(__name__)
        self.collections = {}
        self.retrievers = {}
    
    async def initialize_collections(self, bot_type: str):
        """
        Initialize collections for a specific bot type.
        
        Args:
            bot_type: The type of bot
        """
        # Get bot configuration
        config = self.config_inheritance.get_config(bot_type)
        collection_configs = config.get("vector_store.collections_config", {})
        
        if not collection_configs:
            self.logger.warning(f"No collection configurations found for {bot_type}")
            return
        
        for collection_name, collection_config in collection_configs.items():
            # Initialize this collection
            await self._initialize_collection(bot_type, collection_name, collection_config)
    
    async def _initialize_collection(self, bot_type: str, collection_name: str, config: Dict[str, Any]):
        """Initialize a specific collection."""
        collection_type = config.get("type", "faiss")
        collection_path = config.get("path")
        
        # Get embedding model from config or default
        embedding_model_name = config.get("embedding_model", "default_embedding_model")
        embedding_model = self.model_registry.get_embedding_model(embedding_model_name, bot_type)
        
        if not embedding_model:
            self.logger.error(f"No embedding model found for {collection_name}")
            return
        
        # Create storage key
        storage_key = f"{bot_type}_{collection_name}"
        
        try:
            # Load or create the collection based on type
            if collection_type == "faiss":
                if collection_path and await self._path_exists(collection_path):
                    # Load existing FAISS index
                    collection = FAISS.load_local(
                        collection_path,
                        embedding_model,
                        allow_dangerous_deserialization=True
                    )
                else:
                    # Create new empty FAISS index
                    collection = FAISS.from_documents([], embedding_model)
                    # Save if path provided
                    if collection_path:
                        collection.save_local(collection_path)
            
            elif collection_type == "chroma":
                # Load or create Chroma collection
                collection = Chroma(
                    collection_name=collection_name,
                    embedding_function=embedding_model,
                    persist_directory=collection_path
                )
            
            else:
                self.logger.error(f"Unsupported collection type: {collection_type}")
                return
            
            # Store collection and create retriever
            self.collections[storage_key] = collection
            
            # Configure retriever parameters
            retriever_kwargs = {
                "search_type": config.get("search_type", "similarity"),
                "search_kwargs": {"k": config.get("k", 4)}
            }
            
            # Create retriever
            retriever = collection.as_retriever(**retriever_kwargs)
            self.retrievers[storage_key] = retriever
            
            self.logger.info(f"Initialized collection {collection_name} for {bot_type}")
            
        except Exception as e:
            self.logger.error(f"Error initializing collection {collection_name}: {e}")
    
    async def _path_exists(self, path: str) -> bool:
        """Check if a path exists."""
        # In a real implementation, this would check if the file/directory exists
        # For now, just return False to always create a new collection
        return False
    
    async def get_retriever(self, bot_type: str, collection_name: str):
        """
        Get a retriever for a specific collection.
        
        Args:
            bot_type: The type of bot
            collection_name: The name of the collection
            
        Returns:
            Retriever for the collection or None if not found
        """
        storage_key = f"{bot_type}_{collection_name}"
        
        # Check if retriever exists
        if storage_key in self.retrievers:
            return self.retrievers[storage_key]
        
        # If not, try to initialize the collection
        config = self.config_inheritance.get_config(bot_type)
        collection_config = config.get("vector_store.collections_config", {}).get(collection_name)
        
        if collection_config:
            await self._initialize_collection(bot_type, collection_name, collection_config)
            
            # Check again
            if storage_key in self.retrievers:
                return self.retrievers[storage_key]
        
        self.logger.warning(f"No retriever found for {collection_name} in {bot_type}")
        return None
    
    async def get_all_documents(self, bot_type: str, collection_name: str) -> List[Document]:
        """
        Get all documents from a collection.
        
        Args:
            bot_type: The type of bot
            collection_name: The name of the collection
            
        Returns:
            List of all documents in the collection
        """
        storage_key = f"{bot_type}_{collection_name}"
        
        # Check if collection exists
        if storage_key not in self.collections:
            # Try to initialize
            config = self.config_inheritance.get_config(bot_type)
            collection_config = config.get("vector_store.collections_config", {}).get(collection_name)
            
            if collection_config:
                await self._initialize_collection(bot_type, collection_name, collection_config)
        
        # Check again
        if storage_key not in self.collections:
            self.logger.warning(f"No collection found for {collection_name} in {bot_type}")
            return []
        
        try:
            # This would get all documents from the collection
            # However, most vector stores don't have a direct method for this
            
            # For FAISS, we can't easily get all documents
            # For Chroma, we could use collection.get()
            
            # This is a simplified version that would be implemented properly
            # in a real system with the appropriate vector store APIs
            
            collection = self.collections[storage_key]
            if isinstance(collection, Chroma):
                # Get all documents from Chroma
                results = collection.get()
                documents = [
                    Document(page_content=doc, metadata=meta)
                    for doc, meta in zip(results["documents"], results["metadatas"])
                ]
                return documents
            else:
                # For other types, we'd need to implement accordingly
                # For now, return an empty list
                self.logger.warning(f"Getting all documents not implemented for this collection type")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting documents from {collection_name}: {e}")
            return []
    
    async def add_documents(
        self, bot_type: str, collection_name: str, documents: List[Document]
    ) -> bool:
        """
        Add documents to a collection.
        
        Args:
            bot_type: The type of bot
            collection_name: The name of the collection
            documents: The documents to add
            
        Returns:
            True if successful, False otherwise
        """
        storage_key = f"{bot_type}_{collection_name}"
        
        # Check if collection exists
        if storage_key not in self.collections:
            # Try to initialize
            config = self.config_inheritance.get_config(bot_type)
            collection_config = config.get("vector_store.collections_config", {}).get(collection_name)
            
            if collection_config:
                await self._initialize_collection(bot_type, collection_name, collection_config)
        
        # Check again
        if storage_key not in self.collections:
            self.logger.warning(f"No collection found for {collection_name} in {bot_type}")
            return False
        
        try:
            collection = self.collections[storage_key]
            
            # Add documents to collection
            collection.add_documents(documents)
            
            # If collection has save method, save it
            if hasattr(collection, "save_local"):
                # Get path from config
                config = self.config_inheritance.get_config(bot_type)
                collection_config = config.get("vector_store.collections_config", {}).get(collection_name, {})
                collection_path = collection_config.get("path")
                
                if collection_path:
                    collection.save_local(collection_path)
            
            # If collection has persist method, persist it
            if hasattr(collection, "persist"):
                collection.persist()
            
            self.logger.info(f"Added {len(documents)} documents to {collection_name} for {bot_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding documents to {collection_name}: {e}")
            return False

# Global instance
collection_manager = CollectionManager() 